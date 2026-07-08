"""add users.subscription_until (срок платной подписки)"""

from alembic import op
import sqlalchemy as sa

revision = "0006_subscription_until"
down_revision = "0005_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("subscription_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "subscription_until")
