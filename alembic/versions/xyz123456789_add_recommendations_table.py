"""Add recommendations table

Revision ID: xyz123456789
Revises: pqr123456789
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'xyz123456789'
down_revision = 'pqr123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create recommendations table
    create_table_if_not_exists('recommendations', """
        CREATE TABLE recommendations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            church_ids JSON NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_user_recommendations UNIQUE (user_id)
        )
    """)
    
    # Create indexes for better performance
    op.create_index('ix_recommendations_user_id', 'recommendations', ['user_id'])
    op.create_index('ix_recommendations_created_at', 'recommendations', ['created_at'])
    
    print("✅ Recommendations table migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Drop indexes
    op.drop_index('ix_recommendations_created_at', table_name='recommendations')
    op.drop_index('ix_recommendations_user_id', table_name='recommendations')
    
    # Drop table
    op.drop_table('recommendations')
    
    print("✅ Recommendations table rollback completed successfully!")


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
