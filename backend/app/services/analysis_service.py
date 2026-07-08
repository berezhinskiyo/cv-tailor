from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User
from app.domain.schemas import AnalysisCreateRequest, AnalysisResponse
from app.infrastructure.openai_client import OpenAIGenerator
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vacancy_repository import VacancyRepository
from app.services.limit_service import LimitService
from app.services.skill_extractor import extract_skills


@dataclass
class AnalysisPayload:
    resume_text: str
    vacancy_text: str
    resume_id: int | None
    vacancy_id: int | None


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resume_repository = ResumeRepository(session)
        self.vacancy_repository = VacancyRepository(session)
        self.analysis_repository = AnalysisRepository(session)
        self.user_repository = UserRepository(session)
        self.limit_service = LimitService()
        self.generator = OpenAIGenerator()

    async def create_analysis(self, request: AnalysisCreateRequest, user: User | None) -> AnalysisResponse:
        payload = await self._build_payload(request, user)
        vacancy_skills = extract_skills(payload.vacancy_text)
        resume_skills = extract_skills(payload.resume_text)
        matched_skills = sorted(set(vacancy_skills) & set(resume_skills))
        missing_skills = sorted(set(vacancy_skills) - set(resume_skills))
        score = int(round((len(matched_skills) / len(vacancy_skills)) * 100)) if vacancy_skills else 0

        generated = self.generator.generate(
            resume_text=payload.resume_text,
            vacancy_text=payload.vacancy_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

        if user is None:
            return AnalysisResponse(
                score=score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                improved_resume=generated.improved_resume,
                cover_letter=generated.cover_letter,
                resume_document=generated.document or None,
            )

        stored = await self.analysis_repository.create(
            user_id=user.id,
            resume_id=payload.resume_id,
            vacancy_id=payload.vacancy_id,
            score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            improved_resume=generated.improved_resume,
            cover_letter=generated.cover_letter,
            resume_document=generated.document or None,
        )
        await self.user_repository.increment_analysis_count(user)
        return AnalysisResponse.model_validate(stored)

    async def _build_payload(self, request: AnalysisCreateRequest, user: User | None) -> AnalysisPayload:
        if user is None:
            self.limit_service.assert_anonymous_limit(request.anonymous_id)
            if not request.resume_text:
                raise ValueError("Для анонимного анализа нужно передать resume_text.")
            return AnalysisPayload(
                resume_text=request.resume_text,
                vacancy_text=request.vacancy_text,
                resume_id=None,
                vacancy_id=None,
            )

        self.limit_service.assert_user_limit(
            user.analysis_count, user.subscription_type, user.subscription_until
        )
        resume_text = request.resume_text
        resume_id = request.resume_id
        vacancy_id = request.vacancy_id

        if resume_id is not None:
            resume = await self.resume_repository.get_for_user(user.id, resume_id)
            if resume is None:
                raise ValueError("Резюме не найдено.")
            resume_text = resume.original_text

        if not resume_text:
            raise ValueError("Нужно передать resume_text или resume_id.")

        vacancy_text = request.vacancy_text
        if vacancy_id is not None:
            vacancy = await self.vacancy_repository.get_for_user(user.id, vacancy_id)
            if vacancy is None:
                raise ValueError("Вакансия не найдена.")
            vacancy_text = vacancy.vacancy_text

        return AnalysisPayload(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
        )
