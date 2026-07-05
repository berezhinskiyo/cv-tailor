"""Оплата подписки PRO через Т-Банк. Логика подписи/Init — в auth-billing-core."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from authbilling import tinkoff
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.models import Payment, User

settings = get_settings()

PRO_PRICE_KOPECKS = 49000  # 490 ₽ за месяц PRO


async def create_payment(db: AsyncSession, user: User, payload: dict) -> tuple[str, Any]:
    if not tinkoff.is_configured():
        raise ValueError("Оплата временно недоступна")
    period_months = max(1, int(payload.get("period_months", 1)))
    amount_kopecks = PRO_PRICE_KOPECKS * period_months
    amount_rub = amount_kopecks // 100

    payment = Payment(
        user_id=user.id, amount_kopecks=amount_kopecks, plan="pro",
        period_months=period_months, status="pending",
    )
    db.add(payment)
    await db.flush()

    front = settings.frontend_url.rstrip("/")
    base = settings.backend_url.rstrip("/")
    result = await tinkoff.init_payment(
        amount_rub=amount_rub,
        order_id=str(payment.id),
        description=f"Подписка PRO — CV Tailor ({period_months} мес.)",
        success_url=f"{front}/billing?paid=1",
        fail_url=f"{front}/billing?failed=1",
        notification_url=f"{base}/api/payments/webhook",
        data={"payment_id": str(payment.id), "user_id": str(user.id)},
        receipt=tinkoff.build_receipt(
            email=user.email, item_name="Подписка PRO — CV Tailor", amount_rub=amount_rub
        ),
    )
    payment_url = result.get("PaymentURL")
    if not payment_url:
        raise ValueError("Провайдер не вернул ссылку на оплату")
    payment.external_payment_id = str(result.get("PaymentId") or "")
    await db.commit()
    return payment_url, payment.id


async def handle_success(db: AsyncSession, payload: dict) -> None:
    """Активация подписки после успешной оплаты (подпись Token уже проверена)."""
    data = payload.get("DATA") or {}
    payment_id = data.get("payment_id") or payload.get("OrderId")
    if not payment_id:
        return
    try:
        payment = await db.get(Payment, int(payment_id))
    except (ValueError, TypeError):
        payment = None
    if payment is None or payment.status == "succeeded":
        return

    payment.status = "succeeded"
    payment.completed_at = datetime.now(UTC)
    payment.external_payment_id = str(payload.get("PaymentId") or payment.external_payment_id or "")

    user = await db.scalar(select(User).where(User.id == payment.user_id))
    if user is not None:
        user.subscription_type = "pro"
        user.analysis_count = 0  # новый оплаченный период — сбрасываем счётчик
    await db.commit()
