"""add user consent fields"""

from alembic import op
import sqlalchemy as sa

revision = "0002_user_consent"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("consent_version", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "consent_version")
    op.drop_column("users", "consent_at")
