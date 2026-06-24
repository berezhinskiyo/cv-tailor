from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import User

CONSENT_VERSION = "2026-06-24"


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def create(self, *, email: str, password_hash: str, consent_accepted: bool) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            consent_at=datetime.now(UTC) if consent_accepted else None,
            consent_version=CONSENT_VERSION if consent_accepted else None,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def increment_analysis_count(self, user: User) -> User:
        user.analysis_count += 1
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
