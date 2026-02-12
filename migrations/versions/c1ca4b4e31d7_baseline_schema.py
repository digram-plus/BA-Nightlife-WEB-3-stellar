"""baseline schema

Revision ID: c1ca4b4e31d7
Revises: 
Create Date: 2025-10-20 11:00:14.216229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1ca4b4e31d7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create events table."""
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('title_norm', sa.String(length=255), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.Time(), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=120), server_default='Buenos Aires', nullable=True),
        sa.Column('genres', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('artists', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('source_name', sa.String(length=64), nullable=False),
        sa.Column('source_link', sa.Text(), nullable=True),
        sa.Column('source_msg_id', sa.BigInteger(), nullable=True),
        sa.Column('media_url', sa.Text(), nullable=True),
        sa.Column('dedupe_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='queued', nullable=False),
        sa.Column('published_msg_id', sa.BigInteger(), nullable=True),
        sa.Column('published_topic_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedupe_hash')
    )
    op.create_index(op.f('ix_events_date'), 'events', ['date'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_events_title_norm'), 'events', ['title_norm'], unique=False)


def downgrade() -> None:
    """Drop events table."""
    op.drop_table('events')
