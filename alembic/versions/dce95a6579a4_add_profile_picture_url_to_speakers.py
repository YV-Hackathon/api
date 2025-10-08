"""add_profile_picture_url_to_speakers

Revision ID: dce95a6579a4
Revises: 67ee9b0b95a2
Create Date: 2025-10-08 14:58:30.459570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dce95a6579a4'
down_revision: Union[str, Sequence[str], None] = '67ee9b0b95a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add profile_picture_url column to speakers table
    op.add_column('speakers', sa.Column('profile_picture_url', sa.String(500), nullable=True))
    print("✅ Added profile_picture_url column to speakers table")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove profile_picture_url column from speakers table
    op.drop_column('speakers', 'profile_picture_url')
    print("✅ Removed profile_picture_url column from speakers table")
