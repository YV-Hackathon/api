"""add_attributes_column_to_speakers

Revision ID: 7d488b46c1e7
Revises: 0870d74539ae
Create Date: 2025-10-09 16:53:15.487202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d488b46c1e7'
down_revision: Union[str, Sequence[str], None] = '0870d74539ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add attributes column to speakers table as TEXT[] array
    op.add_column('speakers', sa.Column('attributes', sa.ARRAY(sa.String()), nullable=True))
    
    print("✅ Added attributes column to speakers table successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove attributes column from speakers table
    op.drop_column('speakers', 'attributes')
    
    print("✅ Removed attributes column from speakers table successfully!")
