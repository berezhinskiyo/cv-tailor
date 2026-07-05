from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User

CONSENT_VERSION = "2026-06-24"


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def create(self, *, email: str, password_hash: str, consent_accepted: bool) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            consent_at=datetime.now(UTC) if consent_accepted else None,
            consent_version=CONSENT_VERSION if consent_accepted else None,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def increment_analysis_count(self, user: User) -> User:
        user.analysis_count += 1
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
