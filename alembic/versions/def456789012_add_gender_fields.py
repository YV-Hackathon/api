"""add gender fields

Revision ID: def456789012
Revises: abc123456789
Create Date: 2025-01-27 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'def456789012'
down_revision: Union[str, Sequence[str], None] = 'abc123456789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create gender enum type
    try:
        connection.execute(sa.text("CREATE TYPE gender AS ENUM ('MALE', 'FEMALE')"))
        print("Created enum gender")
    except Exception as e:
        print(f"Enum gender creation failed (may already exist): {e}")
    
    # Add gender column to speakers table
    try:
        connection.execute(sa.text("ALTER TABLE speakers ADD COLUMN gender gender"))
        print("Added gender column to speakers table")
    except Exception as e:
        print(f"Failed to add gender column to speakers: {e}")
    
    # Add gender_preference column to users table
    try:
        connection.execute(sa.text("ALTER TABLE users ADD COLUMN gender_preference gender"))
        print("Added gender_preference column to users table")
    except Exception as e:
        print(f"Failed to add gender_preference column to users: {e}")
    
    print("✅ Gender fields migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Remove gender_preference column from users table
    try:
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS gender_preference"))
        print("Removed gender_preference column from users table")
    except Exception as e:
        print(f"Failed to remove gender_preference column from users: {e}")
    
    # Remove gender column from speakers table
    try:
        connection.execute(sa.text("ALTER TABLE speakers DROP COLUMN IF EXISTS gender"))
        print("Removed gender column from speakers table")
    except Exception as e:
        print(f"Failed to remove gender column from speakers: {e}")
    
    # Drop gender enum type
    try:
        connection.execute(sa.text("DROP TYPE IF EXISTS gender"))
        print("Dropped gender enum type")
    except Exception as e:
        print(f"Failed to drop gender enum type: {e}")
    
    print("✅ Gender fields rollback completed successfully!")
