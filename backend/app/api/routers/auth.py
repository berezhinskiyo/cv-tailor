"""Аутентификация CV Tailor поверх общего пакета auth-billing-core.

Регистрация по коду / вход / refresh / OAuth (Яндекс, ВК) / logout / me собираются
фабрикой `make_auth_router`. Дополнительно сохранён прямой `POST /register`
(без e-mail-кода) — для API-клиентов и интеграций.
"""
from datetime import UTC, datetime

from authbilling import make_auth_router
from authbilling.emailer import send_email_code
from authbilling.security import create_access_token, get_password_hash
from fastapi import HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user, persist_refresh_token
from app.core.config import get_settings
from app.core.db import get_db_session
from app.domain.models import EmailVerificationCode, OAuthIdentity, RefreshToken, User
from app.domain.schemas import TokenResponse, UserRegisterRequest, UserResponse

settings = get_settings()


def _me(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


router = make_auth_router(
    user_model=User,
    refresh_model=RefreshToken,
    email_code_model=EmailVerificationCode,
    oauth_model=OAuthIdentity,
    get_db=get_db_session,
    get_current_user=get_current_user,
    send_email_code=send_email_code,
    me_response=_me,
    route_prefix="/api/auth",
    frontend_callback_path="/auth/oauth/callback",
    include_register=False,  # прямой /register определяем ниже
)


def _is_bootstrap_admin(email: str) -> bool:
    admin = settings.bootstrap_admin_email.strip().lower()
    return bool(admin and email.lower() == admin)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: DbSession) -> TokenResponse:
    """Прямая регистрация без e-mail-кода. Веб использует /register/request-code → verify."""
    if not payload.consent_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нужно принять оферту и политику обработки персональных данных.",
        )
    email = str(payload.email).lower()
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
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
    await db.commit()
    await db.refresh(user)
    access = create_access_token(str(user.id))
    refresh_plain = await persist_refresh_token(db, user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_plain,
        expires_in=settings.access_token_expire_minutes * 60,
    )
