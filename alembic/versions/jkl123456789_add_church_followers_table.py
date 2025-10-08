"""add church followers table

Revision ID: jkl123456789
Revises: ghi789012345
Create Date: 2025-01-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'jkl123456789'
down_revision: Union[str, Sequence[str], None] = 'ghi789012345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create church_followers table
    op.create_table('church_followers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('church_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['church_id'], ['churches.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_church_followers_id'), 'church_followers', ['id'], unique=False)
    
    # Create unique constraint to prevent duplicate follows
    op.create_unique_constraint('uq_church_user_follow', 'church_followers', ['church_id', 'user_id'])
    
    print("✅ Church followers table created successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique constraint first
    op.drop_constraint('uq_church_user_follow', 'church_followers', type_='unique')
    
    # Drop the table
    op.drop_index(op.f('ix_church_followers_id'), table_name='church_followers')
    op.drop_table('church_followers')
    
    print("✅ Church followers table dropped successfully!")
