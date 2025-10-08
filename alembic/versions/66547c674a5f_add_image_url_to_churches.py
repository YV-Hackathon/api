"""add_image_url_to_churches

Revision ID: 66547c674a5f
Revises: dce95a6579a4
Create Date: 2025-10-08 16:51:23.907852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66547c674a5f'
down_revision: Union[str, Sequence[str], None] = 'dce95a6579a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add image_url column to churches table
    op.add_column('churches', sa.Column('image_url', sa.String(500), nullable=True))
    print("✅ Added image_url column to churches table")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove image_url column from churches table
    op.drop_column('churches', 'image_url')
    print("✅ Removed image_url column from churches table")
