from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Analysis


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int | None,
        resume_id: int | None,
        vacancy_id: int | None,
        score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        improved_resume: str,
        cover_letter: str,
        resume_document: dict | None = None,
    ) -> Analysis:
        analysis = Analysis(
            user_id=user_id,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            improved_resume=improved_resume,
            cover_letter=cover_letter,
            resume_document=resume_document,
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def update_document(
        self, analysis: Analysis, *, resume_document: dict, cover_letter: str | None, improved_resume: str
    ) -> Analysis:
        analysis.resume_document = resume_document
        analysis.improved_resume = improved_resume
        if cover_letter is not None:
            analysis.cover_letter = cover_letter
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def get_for_user(self, user_id: int, analysis_id: int) -> Analysis | None:
        return await self.session.scalar(
            select(Analysis).where(Analysis.user_id == user_id, Analysis.id == analysis_id)
        )

    async def list_for_user(self, user_id: int) -> list[Analysis]:
        result = await self.session.scalars(
            select(Analysis).where(Analysis.user_id == user_id).order_by(Analysis.created_at.desc())
        )
        return list(result)
