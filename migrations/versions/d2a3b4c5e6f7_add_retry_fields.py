"""add retry fields

Revision ID: d2a3b4c5e6f7
Revises: f6c81adfcb29
Create Date: 2026-02-12 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2a3b4c5e6f7'
down_revision: Union[str, Sequence[str], None] = '9d2b0f7a8c9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('events', sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('events', 'next_retry_at')
    op.drop_column('events', 'retry_count')
