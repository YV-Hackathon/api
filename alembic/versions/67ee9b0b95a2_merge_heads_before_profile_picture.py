"""merge_heads_before_profile_picture

Revision ID: 67ee9b0b95a2
Revises: abc456789012, de24cba2f224
Create Date: 2025-10-08 14:58:26.003365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67ee9b0b95a2'
down_revision: Union[str, Sequence[str], None] = ('abc456789012', 'de24cba2f224')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
