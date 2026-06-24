from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import VacancyCreateRequest, VacancyResponse
from app.repositories.vacancy_repository import VacancyRepository

router = APIRouter()


@router.post("", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
def create_vacancy(
    request: VacancyCreateRequest,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> VacancyResponse:
    vacancy = VacancyRepository(db).create(user_id=user.id, title=request.title, vacancy_text=request.vacancy_text)
    return VacancyResponse.model_validate(vacancy)


@router.get("", response_model=list[VacancyResponse])
def list_vacancies(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[VacancyResponse]:
    items = VacancyRepository(db).list_for_user(user.id)
    return [VacancyResponse.model_validate(item) for item in items]


@router.get("/{vacancy_id}", response_model=VacancyResponse)
def get_vacancy(vacancy_id: int, db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> VacancyResponse:
    vacancy = VacancyRepository(db).get_for_user(user.id, vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена.")
    return VacancyResponse.model_validate(vacancy)


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vacancy(vacancy_id: int, db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> None:
    repository = VacancyRepository(db)
    vacancy = repository.get_for_user(user.id, vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена.")
    repository.delete(vacancy)

