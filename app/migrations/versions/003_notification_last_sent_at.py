"""add last_sent_at to notification preferences

Revision ID: 003_notification_last_sent_at
Revises: 002_notification_preferences
Create Date: 2026-04-14 00:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_notification_last_sent_at"
down_revision = "002_notification_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_preferences", sa.Column("last_sent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("notification_preferences", "last_sent_at")
