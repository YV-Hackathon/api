"""Add sermon preferences table

Revision ID: pqr123456789
Revises: mno123456789
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pqr123456789'
down_revision = 'mno123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create user_sermon_preferences table
    create_table_if_not_exists('user_sermon_preferences', """
        CREATE TABLE user_sermon_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            sermon_id INTEGER NOT NULL REFERENCES sermons(id),
            preference VARCHAR(10) NOT NULL CHECK (preference IN ('thumbs_up', 'thumbs_down')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_user_sermon_preference UNIQUE (user_id, sermon_id)
        )
    """)
    
    # Create indexes for better performance
    op.create_index('ix_user_sermon_preferences_user_id', 'user_sermon_preferences', ['user_id'])
    op.create_index('ix_user_sermon_preferences_sermon_id', 'user_sermon_preferences', ['sermon_id'])
    op.create_index('ix_user_sermon_preferences_preference', 'user_sermon_preferences', ['preference'])
    
    print("✅ Sermon preferences table migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Drop indexes
    op.drop_index('ix_user_sermon_preferences_preference', table_name='user_sermon_preferences')
    op.drop_index('ix_user_sermon_preferences_sermon_id', table_name='user_sermon_preferences')
    op.drop_index('ix_user_sermon_preferences_user_id', table_name='user_sermon_preferences')
    
    # Drop table
    op.drop_table('user_sermon_preferences')
    
    print("✅ Sermon preferences table rollback completed successfully!")


def create_table_if_not_exists(table_name: str, create_sql: str):
    """Helper function to create table only if it doesn't exist."""
    connection = op.get_bind()
    
    # Check if table exists
    result = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """), {"table_name": table_name}
    )
    
    table_exists = result.scalar()
    
    if not table_exists:
        connection.execute(sa.text(create_sql))
        print(f"✅ Created table: {table_name}")
    else:
        print(f"⚠️  Table {table_name} already exists, skipping creation")
