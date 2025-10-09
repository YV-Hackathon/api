"""create_featured_sermons_table

Revision ID: 828eb11c5c48
Revises: 567debb69ec9
Create Date: 2025-10-08 20:52:17.282054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '828eb11c5c48'
down_revision: Union[str, Sequence[str], None] = '567debb69ec9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'featured_sermons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('church_id', sa.Integer(), nullable=False),
        sa.Column('sermon_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['church_id'], ['churches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sermon_id'], ['sermons.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('church_id', 'sermon_id', name='uq_church_sermon_featured')
    )
    op.create_index('ix_featured_sermons_church_id', 'featured_sermons', ['church_id'])
    op.create_index('ix_featured_sermons_sermon_id', 'featured_sermons', ['sermon_id'])
    op.create_index('ix_featured_sermons_sort_order', 'featured_sermons', ['sort_order'])
    print("✅ Created featured_sermons table with indexes and constraints")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_featured_sermons_sort_order', table_name='featured_sermons')
    op.drop_index('ix_featured_sermons_sermon_id', table_name='featured_sermons')
    op.drop_index('ix_featured_sermons_church_id', table_name='featured_sermons')
    op.drop_table('featured_sermons')
    print("✅ Dropped featured_sermons table")
