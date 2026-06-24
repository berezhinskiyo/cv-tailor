import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import DbSession, client_ip, get_current_user, persist_refresh_token
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.domain.models import EmailVerificationCode, OAuthIdentity, RefreshToken, User
from app.domain.schemas import (
    EmailCodeRequest,
    EmailCodeVerify,
    RefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.infrastructure.emailer import send_email_code

router = APIRouter()
settings = get_settings()


# ── Вспомогательное ─────────────────────────────────────────────────────────
def _access_ttl_seconds() -> int:
    return settings.access_token_expire_minutes * 60


def _issue_tokens(user: User, db: Session) -> TokenResponse:
    access = create_access_token(str(user.id))
    refresh_plain = persist_refresh_token(db, user.id)
    return TokenResponse(access_token=access, refresh_token=refresh_plain, expires_in=_access_ttl_seconds())


def _hash_code(code: str) -> str:
    return hash_refresh_token(code)


def _as_aware(dt: datetime) -> datetime:
    """SQLite возвращает naive-datetime; приводим к aware-UTC для сравнения."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _is_bootstrap_admin(email: str) -> bool:
    admin = settings.bootstrap_admin_email.strip().lower()
    return bool(admin and email.lower() == admin)


def verify_smartcaptcha(token: str | None, ip: str | None) -> None:
    """Проверка токена Яндекс SmartCaptcha. Активна только если задан серверный ключ."""
    server_key = settings.smartcaptcha_server_key.strip()
    if not server_key:
        return
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Подтвердите, что вы не робот")
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                "https://smartcaptcha.yandexcloud.net/validate",
                data={"secret": server_key, "token": token, "ip": ip or ""},
            )
        ok = resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:  # noqa: BLE001 — недоступность капчи не должна ронять регистрацию
        ok = True
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Проверка капчи не пройдена")


# ── Регистрация по e-mail с кодом ───────────────────────────────────────────
@router.post("/register/request-code")
def request_register_code(payload: EmailCodeRequest, db: DbSession, ip: Annotated[str, Depends(client_ip)]):
    verify_smartcaptcha(payload.captcha_token, ip)
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован")

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        EmailVerificationCode(
            email=email,
            code_hash=_hash_code(code),
            password_hash=get_password_hash(payload.password),
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
    )
    db.commit()
    send_email_code(email, code)
    return {"ok": True, "message": "Код отправлен на почту"}


@router.post("/register/verify", response_model=TokenResponse)
def verify_register_code(payload: EmailCodeVerify, db: DbSession) -> TokenResponse:
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже зарегистрирован")

    now = datetime.now(UTC)
    row = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )
    if not row or row.code_hash != _hash_code(payload.code.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный или истёкший код")

    user = User(
        email=email,
        password_hash=row.password_hash,
        is_admin=_is_bootstrap_admin(email),
        email_verified=True,
        consent_at=now,  # согласие на обработку ПДн дано при регистрации (152-ФЗ)
        consent_version=settings.consent_version,
    )
    row.consumed_at = now
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user, db)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: DbSession) -> TokenResponse:
    """Прямая регистрация без e-mail-кода (для API-клиентов и интеграций).

    Веб-интерфейс использует поток `/register/request-code` → `/register/verify`.
    """
    if not payload.consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нужно принять оферту и политику обработки персональных данных.",
        )
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует.")
    now = datetime.now(UTC)
    user = User(
        email=email,
        password_hash=get_password_hash(payload.password),
        is_admin=_is_bootstrap_admin(email),
        email_verified=True,
        consent_at=now,
        consent_version=settings.consent_version,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: DbSession) -> TokenResponse:
    email = str(payload.email).lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    if _is_bootstrap_admin(email) and not user.is_admin:
        user.is_admin = True
        db.commit()
    return _issue_tokens(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_session(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    token_hash = hash_refresh_token(payload.refresh_token)
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    now = datetime.now(UTC)
    if not row or row.revoked_at or _as_aware(row.expires_at) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # ротация: старый токен отзываем, выдаём новую пару
    row.revoked_at = now
    db.commit()

    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _issue_tokens(user, db)


@router.post("/logout")
def logout(payload: RefreshRequest, db: DbSession):
    token_hash = hash_refresh_token(payload.refresh_token)
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if row and not row.revoked_at:
        row.revoked_at = datetime.now(UTC)
        db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)


# ── OAuth (Яндекс / VK) ─────────────────────────────────────────────────────
def _oauth_config(provider: str) -> dict:
    configs = {
        "yandex": {
            "client_id": settings.yandex_client_id,
            "client_secret": settings.yandex_client_secret,
            "auth_url": "https://oauth.yandex.ru/authorize",
            "token_url": "https://oauth.yandex.ru/token",
            "userinfo_url": "https://login.yandex.ru/info?format=json",
            "scope": "login:email login:info",
        },
        "vk": {
            "client_id": settings.vk_client_id,
            "client_secret": settings.vk_client_secret,
            "auth_url": "https://id.vk.com/authorize",
            "token_url": "https://id.vk.com/oauth2/auth",
            "userinfo_url": "https://id.vk.com/oauth2/user_info",
            "scope": "email",
        },
    }
    if provider not in configs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    cfg = configs[provider]
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{provider} OAuth is not configured"
        )
    return cfg


def _oauth_redirect_uri(provider: str) -> str:
    return f"{settings.backend_url.rstrip('/')}/api/auth/oauth/{provider}/callback"


def _frontend_url(path: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}{path}"


def _vk_pkce_store_path(state: str) -> str:
    safe = "".join(c for c in state if c.isalnum() or c in "-_")
    return f"/tmp/cv_tailor_vk_pkce_{safe}.txt"


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str):
    cfg = _oauth_config(provider)
    state = secrets.token_urlsafe(18)
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": _oauth_redirect_uri(provider),
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state,
    }
    if provider == "vk":
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        with open(_vk_pkce_store_path(state), "w") as f:
            f.write(code_verifier)
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    return RedirectResponse(f"{cfg['auth_url']}?{urlencode(params)}")


def _get_or_create_oauth_user(
    db: Session, provider: str, provider_user_id: str, email: str, display_name: str | None
) -> User:
    identity = (
        db.query(OAuthIdentity)
        .filter(OAuthIdentity.provider == provider, OAuthIdentity.provider_user_id == provider_user_id)
        .first()
    )
    if identity:
        user = db.query(User).filter(User.id == identity.user_id).first()
        if user:
            if display_name and not user.display_name:
                user.display_name = display_name
                db.commit()
                db.refresh(user)
            return user

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=get_password_hash(secrets.token_urlsafe(24)[:32]),
            email_verified=True,
            display_name=display_name,
            is_admin=_is_bootstrap_admin(email),
            # вход через провайдера = акцепт оферты и согласие на обработку ПДн
            consent_at=datetime.now(UTC),
            consent_version=settings.consent_version,
        )
        db.add(user)
        db.flush()
    else:
        if not user.email_verified:
            user.email_verified = True
        if display_name and not user.display_name:
            user.display_name = display_name

    db.add(OAuthIdentity(user_id=user.id, provider=provider, provider_user_id=provider_user_id, email=email))
    db.commit()
    db.refresh(user)
    return user


@router.get("/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    code: str,
    db: DbSession,
    state: str | None = None,
    device_id: str | None = None,
):
    cfg = _oauth_config(provider)
    if provider == "vk":
        if not state or not device_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VK callback missing state/device_id")
        try:
            with open(_vk_pkce_store_path(state)) as f:
                code_verifier = f.read().strip()
            import os

            os.remove(_vk_pkce_store_path(state))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VK OAuth state expired") from exc
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": cfg["client_id"],
            "device_id": device_id,
            "redirect_uri": _oauth_redirect_uri(provider),
            "code_verifier": code_verifier,
        }
    else:
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": _oauth_redirect_uri(provider),
        }

    with httpx.Client(timeout=15.0) as client:
        token_resp = client.post(cfg["token_url"], data=token_payload)
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth token exchange failed")
        if provider == "vk":
            info_resp = client.post(
                cfg["userinfo_url"], data={"client_id": cfg["client_id"], "access_token": access_token}
            )
        else:
            info_resp = client.get(cfg["userinfo_url"], headers={"Authorization": f"Bearer {access_token}"})
        info_resp.raise_for_status()
        info = info_resp.json()

    if provider == "vk":
        user_data = info.get("user") or {}
        provider_user_id = str(user_data.get("user_id") or "")
        email = user_data.get("email") or token_data.get("email") or f"vk-{provider_user_id}@oauth.local"
        first = (user_data.get("first_name") or "").strip()
        last = (user_data.get("last_name") or "").strip()
        display_name = f"{first} {last}".strip() or None
    else:
        provider_user_id = str(info.get("id") or info.get("sub") or "")
        email = info.get("default_email") or info.get("email")
        display_name = (
            info.get("real_name")
            or info.get("display_name")
            or " ".join(filter(None, [info.get("first_name"), info.get("last_name")])).strip()
            or None
        )
    if not provider_user_id or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth user profile has no email")

    user = _get_or_create_oauth_user(db, provider, provider_user_id, str(email).lower(), display_name)
    tokens = _issue_tokens(user, db)
    params = urlencode({"access_token": tokens.access_token, "refresh_token": tokens.refresh_token or ""})
    return RedirectResponse(_frontend_url(f"/auth/oauth/callback?{params}"))
