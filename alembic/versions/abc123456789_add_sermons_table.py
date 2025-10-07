"""add sermons table

Revision ID: abc123456789
Revises: 431ce8f0022
Create Date: 2025-01-27 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123456789'
down_revision: Union[str, Sequence[str], None] = '431ce8f0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create sermons table
    def create_table_if_not_exists(table_name, create_sql):
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'
        """)).fetchone()
        if not result:
            connection.execute(sa.text(create_sql))
            print(f"Created table {table_name}")
        else:
            print(f"Table {table_name} already exists, skipping...")
    
    create_table_if_not_exists('sermons', """
        CREATE TABLE sermons (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            gcs_url VARCHAR(500) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            speaker_id INTEGER NOT NULL REFERENCES speakers(id)
        )
    """)
    
    print("✅ Sermons table migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Check if table exists before dropping
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'sermons'
    """)).fetchone()
    
    if result:
        print("Dropping table sermons...")
        op.drop_table('sermons')
    else:
        print("Table sermons does not exist, skipping...")
