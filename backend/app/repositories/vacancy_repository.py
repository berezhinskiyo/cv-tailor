from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Vacancy


class VacancyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: int, title: str, vacancy_text: str) -> Vacancy:
        vacancy = Vacancy(user_id=user_id, title=title, vacancy_text=vacancy_text)
        self.session.add(vacancy)
        self.session.commit()
        self.session.refresh(vacancy)
        return vacancy

    def list_for_user(self, user_id: int) -> list[Vacancy]:
        return list(self.session.scalars(select(Vacancy).where(Vacancy.user_id == user_id).order_by(Vacancy.created_at.desc())))

    def get_for_user(self, user_id: int, vacancy_id: int) -> Vacancy | None:
        return self.session.scalar(select(Vacancy).where(Vacancy.user_id == user_id, Vacancy.id == vacancy_id))

    def delete(self, vacancy: Vacancy) -> None:
        self.session.delete(vacancy)
        self.session.commit()

