"""add speaker followers table

Revision ID: mno123456789
Revises: jkl123456789
Create Date: 2025-01-27 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'mno123456789'
down_revision: Union[str, Sequence[str], None] = 'jkl123456789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create speaker_followers table
    op.create_table('speaker_followers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('speaker_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['speaker_id'], ['speakers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_speaker_followers_id'), 'speaker_followers', ['id'], unique=False)
    
    # Create unique constraint to prevent duplicate follows
    op.create_unique_constraint('uq_speaker_user_follow', 'speaker_followers', ['speaker_id', 'user_id'])
    
    print("✅ Speaker followers table created successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique constraint
    op.drop_constraint('uq_speaker_user_follow', 'speaker_followers', type_='unique')
    
    # Drop the table
    op.drop_table('speaker_followers')
    
    print("✅ Speaker followers table dropped successfully!")
