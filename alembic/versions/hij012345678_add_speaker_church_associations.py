"""add speaker church associations table

Revision ID: hij012345678
Revises: ghi789012345
Create Date: 2025-01-27 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'hij012345678'
down_revision: Union[str, Sequence[str], None] = 'ghi789012345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create speaker_church_associations table
    def create_table_if_not_exists(table_name, create_sql):
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'
        """)).fetchone()
        if not result:
            connection.execute(sa.text(create_sql))
            print(f"Created table {table_name}")
        else:
            print(f"Table {table_name} already exists, skipping...")
    
    create_table_if_not_exists('speaker_church_associations', """
        CREATE TABLE speaker_church_associations (
            speaker_id INTEGER NOT NULL REFERENCES speakers(id),
            church_id INTEGER NOT NULL REFERENCES churches(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (speaker_id, church_id)
        )
    """)
    
    print("✅ Speaker-Church associations table migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Check if table exists before dropping
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'speaker_church_associations'
    """)).fetchone()
    
    if result:
        print("Dropping table speaker_church_associations...")
        op.drop_table('speaker_church_associations')
    else:
        print("Table speaker_church_associations does not exist, skipping...")
    
    print("✅ Speaker-Church associations rollback completed successfully!")
