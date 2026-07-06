from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: int, title: str, original_text: str) -> Resume:
        resume = Resume(user_id=user_id, title=title, original_text=original_text)
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def list_for_user(self, user_id: int) -> list[Resume]:
        result = await self.session.scalars(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        )
        return list(result)

    async def get_for_user(self, user_id: int, resume_id: int) -> Resume | None:
        return await self.session.scalar(
            select(Resume).where(Resume.user_id == user_id, Resume.id == resume_id)
        )

    async def delete(self, resume: Resume) -> None:
        await self.session.delete(resume)
        await self.session.commit()
