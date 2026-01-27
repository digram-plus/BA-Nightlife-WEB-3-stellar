"""add checkins table

Revision ID: 9d2b0f7a8c9a
Revises: f6c81adfcb29
Create Date: 2026-01-26 10:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d2b0f7a8c9a"
down_revision: Union[str, Sequence[str], None] = "f6c81adfcb29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("wallet_address", sa.String(length=42), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("nonce", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "wallet_address", name="uq_checkins_event_wallet"),
        sa.UniqueConstraint("nonce", name="uq_checkins_nonce"),
    )
    op.create_index(op.f("ix_checkins_event_id"), "checkins", ["event_id"], unique=False)
    op.create_index(op.f("ix_checkins_wallet_address"), "checkins", ["wallet_address"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_checkins_wallet_address"), table_name="checkins")
    op.drop_index(op.f("ix_checkins_event_id"), table_name="checkins")
    op.drop_table("checkins")
