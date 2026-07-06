from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import ResumeCreateRequest, ResumeResponse
from app.repositories.resume_repository import ResumeRepository

router = APIRouter()


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    request: ResumeCreateRequest,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ResumeResponse:
    resume = await ResumeRepository(db).create(
        user_id=user.id, title=request.title, original_text=request.original_text
    )
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[ResumeResponse]:
    items = await ResumeRepository(db).list_for_user(user.id)
    return [ResumeResponse.model_validate(item) for item in items]


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int, db: DbSession, user: Annotated[User, Depends(get_current_user)]
) -> ResumeResponse:
    resume = await ResumeRepository(db).get_for_user(user.id, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Резюме не найдено.")
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int, db: DbSession, user: Annotated[User, Depends(get_current_user)]
) -> None:
    repository = ResumeRepository(db)
    resume = await repository.get_for_user(user.id, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Резюме не найдено.")
    await repository.delete(resume)
