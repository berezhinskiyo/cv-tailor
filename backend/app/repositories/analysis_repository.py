from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Analysis


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
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
        )
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_for_user(self, user_id: int, analysis_id: int) -> Analysis | None:
        return self.session.scalar(select(Analysis).where(Analysis.user_id == user_id, Analysis.id == analysis_id))

    def list_for_user(self, user_id: int) -> list[Analysis]:
        return list(self.session.scalars(select(Analysis).where(Analysis.user_id == user_id).order_by(Analysis.created_at.desc())))

