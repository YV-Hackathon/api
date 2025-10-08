"""merge multiple heads

Revision ID: de24cba2f224
Revises: hij012345678, xyz123456789
Create Date: 2025-10-08 11:26:51.183679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de24cba2f224'
down_revision: Union[str, Sequence[str], None] = ('hij012345678', 'xyz123456789')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
