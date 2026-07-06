from typing import Annotated

from authbilling import make_get_current_user
from authbilling import persist_refresh_token as _persist_refresh_token
from authbilling.ratelimit import client_ip  # noqa: F401 — реэкспорт для роутеров
from authbilling.security import decode_user_id
from fastapi import Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.db import get_db_session
from app.domain.models import RefreshToken, User
from app.repositories.user_repository import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def persist_refresh_token(db: AsyncSession, user_id: int) -> str:
    """Создаёт refresh-токен, сохраняет его хеш и возвращает «сырое» значение."""
    return await _persist_refresh_token(db, RefreshToken, user_id)


# Обязательная авторизация (Bearer) — общая фабрика пакета. cv-tailor: int-идентификаторы.
get_current_user = make_get_current_user(User, get_db_session, id_cast=int, check_deleted=False)


async def get_current_user_optional(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    user_id = decode_user_id(authorization.split(" ", 1)[1])
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен.")
    user = await UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user


def get_anonymous_id(x_anonymous_id: Annotated[str | None, Header()] = None) -> str | None:
    return x_anonymous_id


async def get_current_user_from_query(
    db: DbSession,
    access_token: Annotated[str | None, Query()] = None,
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация.")
    user_id = decode_user_id(access_token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен.")
    user = await UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user
