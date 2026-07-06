from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Vacancy


class VacancyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: int, title: str, vacancy_text: str) -> Vacancy:
        vacancy = Vacancy(user_id=user_id, title=title, vacancy_text=vacancy_text)
        self.session.add(vacancy)
        await self.session.commit()
        await self.session.refresh(vacancy)
        return vacancy

    async def list_for_user(self, user_id: int) -> list[Vacancy]:
        result = await self.session.scalars(
            select(Vacancy).where(Vacancy.user_id == user_id).order_by(Vacancy.created_at.desc())
        )
        return list(result)

    async def get_for_user(self, user_id: int, vacancy_id: int) -> Vacancy | None:
        return await self.session.scalar(
            select(Vacancy).where(Vacancy.user_id == user_id, Vacancy.id == vacancy_id)
        )

    async def delete(self, vacancy: Vacancy) -> None:
        await self.session.delete(vacancy)
        await self.session.commit()
