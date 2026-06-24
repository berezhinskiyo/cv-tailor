from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db_session
from app.core.security import hash_refresh_token, new_refresh_token_plain
from app.domain.models import RefreshToken, User
from app.repositories.user_repository import UserRepository

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


DbSession = Annotated[Session, Depends(get_db_session)]


def persist_refresh_token(db: Session, user_id: int) -> str:
    """Создаёт refresh-токен, сохраняет его хеш и возвращает «сырое» значение."""
    plain = new_refresh_token_plain()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    db.add(RefreshToken(user_id=user_id, token_hash=hash_refresh_token(plain), expires_at=expires_at))
    db.commit()
    return plain


def client_ip(request: Request) -> str:
    """Реальный IP клиента за nginx (X-Forwarded-For / X-Real-IP)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


def get_current_user_optional(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен.") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user


def get_current_user(user: Annotated[User | None, Depends(get_current_user_optional)]) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация.")
    return user


def get_anonymous_id(x_anonymous_id: Annotated[str | None, Header()] = None) -> str | None:
    return x_anonymous_id


def get_current_user_from_query(
    db: DbSession,
    access_token: Annotated[str | None, Query()] = None,
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация.")
    try:
        payload = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен.") from exc
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user
