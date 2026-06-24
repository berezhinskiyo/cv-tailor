from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import DbSession, get_anonymous_id, get_current_user, get_current_user_from_query, get_current_user_optional
from app.domain.models import User
from app.domain.schemas import AnalysisCreateRequest, AnalysisResponse
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_service import AnalysisService
from app.services.pdf_service import PdfService

router = APIRouter()


@router.post("", response_model=AnalysisResponse)
def create_analysis(
    request: AnalysisCreateRequest,
    db: DbSession,
    anonymous_id: Annotated[str | None, Depends(get_anonymous_id)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> AnalysisResponse:
    service = AnalysisService(db)
    try:
        merged = request.model_copy(update={"anonymous_id": request.anonymous_id or anonymous_id})
        return service.create_analysis(merged, user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[AnalysisResponse]:
    items = AnalysisRepository(db).list_for_user(user.id)
    return [AnalysisResponse.model_validate(item) for item in items]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int, db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> AnalysisResponse:
    analysis = AnalysisRepository(db).get_for_user(user.id, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Анализ не найден.")
    return AnalysisResponse.model_validate(analysis)


@router.get("/{analysis_id}/pdf")
def download_analysis_pdf(
    analysis_id: int,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user_from_query)],
) -> Response:
    analysis = AnalysisRepository(db).get_for_user(user.id, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Анализ не найден.")
    payload = AnalysisResponse.model_validate(analysis)
    pdf = PdfService().build_analysis_pdf(payload)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="analysis-{analysis_id}.pdf"'},
    )
