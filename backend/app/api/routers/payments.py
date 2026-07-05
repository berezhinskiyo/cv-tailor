"""Оплата PRO-подписки (Т-Банк) через общий пакет auth-billing-core."""
from authbilling import make_payments_router

from app.api.deps import get_current_user
from app.core.db import get_db_session
from app.services.payment import create_payment, handle_success

router = make_payments_router(
    get_db=get_db_session,
    get_current_user=get_current_user,
    create_payment=create_payment,
    handle_success=handle_success,
    route_prefix="/api/payments",
)
