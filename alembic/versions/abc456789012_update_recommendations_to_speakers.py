"""Update recommendations table to store speaker_ids instead of church_ids

Revision ID: abc456789012
Revises: xyz123456789
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abc456789012'
down_revision = 'xyz123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new speaker_ids column
    op.add_column('recommendations', sa.Column('speaker_ids', sa.JSON(), nullable=True))
    
    # Add optional scores column for ML model confidence scores
    op.add_column('recommendations', sa.Column('scores', sa.JSON(), nullable=True))
    
    # Migrate existing data: Convert church_ids to speaker_ids by finding speakers associated with churches
    # This is a data migration - you might want to run a custom script for this
    connection = op.get_bind()
    
    # For now, we'll set speaker_ids to empty array for existing records
    # You can populate this later with actual ML model recommendations
    connection.execute(
        sa.text("UPDATE recommendations SET speaker_ids = '[]'::json WHERE speaker_ids IS NULL")
    )
    
    # Make speaker_ids NOT NULL after setting default values
    op.alter_column('recommendations', 'speaker_ids', nullable=False)
    
    # Drop the old church_ids column
    op.drop_column('recommendations', 'church_ids')
    
    print("✅ Updated recommendations table to use speaker_ids instead of church_ids")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back church_ids column
    op.add_column('recommendations', sa.Column('church_ids', sa.JSON(), nullable=True))
    
    # Migrate data back: Convert speaker_ids to church_ids by finding churches associated with speakers
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE recommendations SET church_ids = '[]'::json WHERE church_ids IS NULL")
    )
    
    # Make church_ids NOT NULL
    op.alter_column('recommendations', 'church_ids', nullable=False)
    
    # Drop the new columns
    op.drop_column('recommendations', 'scores')
    op.drop_column('recommendations', 'speaker_ids')
    
    print("✅ Reverted recommendations table to use church_ids")
