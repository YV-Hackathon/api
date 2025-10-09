"""increase_preference_column_size

Revision ID: 77c12e3f6d52
Revises: 828eb11c5c48
Create Date: 2025-10-09 14:12:33.383408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77c12e3f6d52'
down_revision: Union[str, Sequence[str], None] = '828eb11c5c48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase the preference column size from VARCHAR(10) to VARCHAR(15)
    # to accommodate 'thumbs_down' (11 characters) and future values
    op.alter_column('user_sermon_preferences', 'preference',
                   existing_type=sa.String(10),
                   type_=sa.String(15),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert the preference column size back to VARCHAR(10)
    op.alter_column('user_sermon_preferences', 'preference',
                   existing_type=sa.String(15),
                   type_=sa.String(10),
                   existing_nullable=False)
