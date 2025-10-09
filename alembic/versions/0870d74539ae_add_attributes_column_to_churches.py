"""add_attributes_column_to_churches

Revision ID: 0870d74539ae
Revises: 77c12e3f6d52
Create Date: 2025-10-09 16:50:45.523642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0870d74539ae'
down_revision: Union[str, Sequence[str], None] = '77c12e3f6d52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add attributes column to churches table as TEXT[] array
    op.add_column('churches', sa.Column('attributes', sa.ARRAY(sa.String()), nullable=True))
    
    print("✅ Added attributes column to churches table successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove attributes column from churches table
    op.drop_column('churches', 'attributes')
    
    print("✅ Removed attributes column from churches table successfully!")
