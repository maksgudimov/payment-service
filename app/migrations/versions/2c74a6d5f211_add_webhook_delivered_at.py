"""Add webhook delivery timestamp.

Revision ID: 2c74a6d5f211
Revises: f5500c95bb2f
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "2c74a6d5f211"
down_revision: str | Sequence[str] | None = "f5500c95bb2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("webhook_delivered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payments", "webhook_delivered_at")
