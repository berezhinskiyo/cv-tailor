"""Оплата PRO-подписки (Т-Банк) через общий пакет auth-billing-core."""
from typing import Annotated

from authbilling import make_payments_router
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db_session
from app.domain.models import Payment, User
from app.domain.schemas import PaymentResponse
from app.services.payment import create_payment, handle_success

router = make_payments_router(
    get_db=get_db_session,
    get_current_user=get_current_user,
    create_payment=create_payment,
    handle_success=handle_success,
    route_prefix="/api/payments",
)


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Payment]:
    """История платежей текущего пользователя (новые сверху)."""
    rows = await db.scalars(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc())
    )
    return list(rows)
