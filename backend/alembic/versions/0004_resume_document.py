"""add structured resume_document to analyses"""

from alembic import op
import sqlalchemy as sa

revision = "0004_resume_document"
down_revision = "0003_auth_refresh_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("resume_document", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "resume_document")
