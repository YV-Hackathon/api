"""update teaching style enum values

Revision ID: ghi789012345
Revises: def456789012
Create Date: 2025-01-27 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ghi789012345'
down_revision: Union[str, Sequence[str], None] = 'def456789012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # First, update any existing teaching_style values to null to avoid constraint violations
    try:
        connection.execute(sa.text("""
            UPDATE speakers 
            SET teaching_style = NULL 
            WHERE teaching_style IN ('ACADEMIC', 'RELATABLE', 'BALANCED')
        """))
        print("Updated existing teaching_style values to NULL")
    except Exception as e:
        print(f"Failed to update existing teaching_style values: {e}")
    
    try:
        connection.execute(sa.text("""
            UPDATE users 
            SET teaching_style_preference = NULL 
            WHERE teaching_style_preference IN ('ACADEMIC', 'RELATABLE', 'BALANCED')
        """))
        print("Updated existing teaching_style_preference values to NULL")
    except Exception as e:
        print(f"Failed to update existing teaching_style_preference values: {e}")
    
    # Drop the old enum and create the new one
    try:
        # Create new enum type with new values
        connection.execute(sa.text("""
            ALTER TYPE teachingstyle RENAME TO teachingstyle_old
        """))
        connection.execute(sa.text("""
            CREATE TYPE teachingstyle AS ENUM ('WARM_AND_CONVERSATIONAL', 'CALM_AND_REFLECTIVE', 'PASSIONATE_AND_HIGH_ENERGY')
        """))
        
        # Update columns to use the new enum
        connection.execute(sa.text("""
            ALTER TABLE speakers 
            ALTER COLUMN teaching_style TYPE teachingstyle USING NULL
        """))
        connection.execute(sa.text("""
            ALTER TABLE users 
            ALTER COLUMN teaching_style_preference TYPE teachingstyle USING NULL
        """))
        
        # Drop the old enum
        connection.execute(sa.text("DROP TYPE teachingstyle_old"))
        
        print("Updated teachingstyle enum with new values")
    except Exception as e:
        print(f"Failed to update teachingstyle enum: {e}")
    
    print("✅ Teaching style enum migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Update any existing values to null first
    try:
        connection.execute(sa.text("""
            UPDATE speakers 
            SET teaching_style = NULL 
            WHERE teaching_style IN ('WARM_AND_CONVERSATIONAL', 'CALM_AND_REFLECTIVE', 'PASSIONATE_AND_HIGH_ENERGY')
        """))
        connection.execute(sa.text("""
            UPDATE users 
            SET teaching_style_preference = NULL 
            WHERE teaching_style_preference IN ('WARM_AND_CONVERSATIONAL', 'CALM_AND_REFLECTIVE', 'PASSIONATE_AND_HIGH_ENERGY')
        """))
        print("Updated existing values to NULL")
    except Exception as e:
        print(f"Failed to update existing values: {e}")
    
    # Restore the old enum
    try:
        connection.execute(sa.text("ALTER TYPE teachingstyle RENAME TO teachingstyle_new"))
        connection.execute(sa.text("CREATE TYPE teachingstyle AS ENUM ('ACADEMIC', 'RELATABLE', 'BALANCED')"))
        
        connection.execute(sa.text("""
            ALTER TABLE speakers 
            ALTER COLUMN teaching_style TYPE teachingstyle USING NULL
        """))
        connection.execute(sa.text("""
            ALTER TABLE users 
            ALTER COLUMN teaching_style_preference TYPE teachingstyle USING NULL
        """))
        
        connection.execute(sa.text("DROP TYPE teachingstyle_new"))
        
        print("Restored old teachingstyle enum values")
    except Exception as e:
        print(f"Failed to restore old teachingstyle enum: {e}")
    
    print("✅ Teaching style enum rollback completed successfully!")
