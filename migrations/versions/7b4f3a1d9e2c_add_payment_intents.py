"""add payment intents

Revision ID: 7b4f3a1d9e2c
Revises: d2a3b4c5e6f7
Create Date: 2026-02-14 14:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b4f3a1d9e2c"
down_revision: Union[str, Sequence[str], None] = "d2a3b4c5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_intents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False, server_default="ticket"),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("provider_status", sa.String(length=64), nullable=True),
        sa.Column("provider_session_id", sa.String(length=128), nullable=True),
        sa.Column("fiat_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("fiat_currency", sa.String(length=8), nullable=False, server_default="ARS"),
        sa.Column("asset_code", sa.String(length=16), nullable=False, server_default="USDC"),
        sa.Column("asset_issuer", sa.String(length=80), nullable=True),
        sa.Column("checkout_url", sa.Text(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("user_wallet", sa.String(length=128), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("provider_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_payment_intents_public_id"),
    )
    op.create_index(op.f("ix_payment_intents_event_id"), "payment_intents", ["event_id"], unique=False)
    op.create_index(op.f("ix_payment_intents_provider"), "payment_intents", ["provider"], unique=False)
    op.create_index(
        op.f("ix_payment_intents_provider_session_id"),
        "payment_intents",
        ["provider_session_id"],
        unique=False,
    )
    op.create_index(op.f("ix_payment_intents_public_id"), "payment_intents", ["public_id"], unique=False)
    op.create_index(op.f("ix_payment_intents_status"), "payment_intents", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_intents_status"), table_name="payment_intents")
    op.drop_index(op.f("ix_payment_intents_public_id"), table_name="payment_intents")
    op.drop_index(op.f("ix_payment_intents_provider_session_id"), table_name="payment_intents")
    op.drop_index(op.f("ix_payment_intents_provider"), table_name="payment_intents")
    op.drop_index(op.f("ix_payment_intents_event_id"), table_name="payment_intents")
    op.drop_table("payment_intents")
