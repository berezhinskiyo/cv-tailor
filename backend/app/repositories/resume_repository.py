from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Resume


class ResumeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: int, title: str, original_text: str) -> Resume:
        resume = Resume(user_id=user_id, title=title, original_text=original_text)
        self.session.add(resume)
        self.session.commit()
        self.session.refresh(resume)
        return resume

    def list_for_user(self, user_id: int) -> list[Resume]:
        return list(self.session.scalars(select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())))

    def get_for_user(self, user_id: int, resume_id: int) -> Resume | None:
        return self.session.scalar(select(Resume).where(Resume.user_id == user_id, Resume.id == resume_id))

    def delete(self, resume: Resume) -> None:
        self.session.delete(resume)
        self.session.commit()

