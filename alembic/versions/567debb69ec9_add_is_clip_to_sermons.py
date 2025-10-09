"""add_is_clip_to_sermons

Revision ID: 567debb69ec9
Revises: 66547c674a5f
Create Date: 2025-10-08 20:51:57.151125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '567debb69ec9'
down_revision: Union[str, Sequence[str], None] = '66547c674a5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sermons', sa.Column('is_clip', sa.Boolean(), nullable=False, server_default='true'))
    print("✅ Added is_clip column to sermons table")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sermons', 'is_clip')
    print("✅ Removed is_clip column from sermons table")
