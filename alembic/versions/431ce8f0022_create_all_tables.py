"""create all tables

Revision ID: 431ce8f0022
Revises: 88681f158517
Create Date: 2025-01-27 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '431ce8f0022'
down_revision: Union[str, Sequence[str], None] = '88681f158517'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Create enum types using raw SQL to avoid SQLAlchemy issues
    try:
        connection.execute(sa.text("CREATE TYPE teachingstyle AS ENUM ('ACADEMIC', 'RELATABLE', 'BALANCED')"))
        print("Created enum teachingstyle")
    except Exception as e:
        print(f"Enum teachingstyle creation failed (may already exist): {e}")
    
    try:
        connection.execute(sa.text("CREATE TYPE bibleapproach AS ENUM ('MORE_SCRIPTURE', 'MORE_APPLICATION', 'BALANCED')"))
        print("Created enum bibleapproach")
    except Exception as e:
        print(f"Enum bibleapproach creation failed (may already exist): {e}")
    
    try:
        connection.execute(sa.text("CREATE TYPE environmentstyle AS ENUM ('TRADITIONAL', 'CONTEMPORARY', 'BLENDED')"))
        print("Created enum environmentstyle")
    except Exception as e:
        print(f"Enum environmentstyle creation failed (may already exist): {e}")
    
    # Create tables using raw SQL to avoid SQLAlchemy enum issues
    def create_table_if_not_exists(table_name, create_sql):
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'
        """)).fetchone()
        if not result:
            connection.execute(sa.text(create_sql))
            print(f"Created table {table_name}")
        else:
            print(f"Table {table_name} already exists, skipping...")
    
    # Create churches table
    create_table_if_not_exists('churches', """
        CREATE TABLE churches (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            denomination VARCHAR(100) NOT NULL,
            description TEXT,
            address JSON,
            phone VARCHAR(50),
            email VARCHAR(255),
            website VARCHAR(255),
            founded_year INTEGER,
            membership_count INTEGER,
            service_times JSON,
            social_media JSON,
            is_active BOOLEAN,
            sort_order INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create speakers table
    create_table_if_not_exists('speakers', """
        CREATE TABLE speakers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            title VARCHAR(255),
            bio TEXT,
            email VARCHAR(255),
            phone VARCHAR(50),
            years_of_service INTEGER,
            social_media JSON,
            speaking_topics JSON,
            sort_order INTEGER,
            teaching_style teachingstyle,
            bible_approach bibleapproach,
            environment_style environmentstyle,
            is_recommended BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            church_id INTEGER REFERENCES churches(id)
        )
    """)
    
    # Create users table
    create_table_if_not_exists('users', """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            is_active BOOLEAN,
            onboarding_completed BOOLEAN,
            bible_reading_preference bibleapproach,
            teaching_style_preference teachingstyle,
            environment_preference environmentstyle,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create user_speaker_preferences table
    create_table_if_not_exists('user_speaker_preferences', """
        CREATE TABLE user_speaker_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            speaker_id INTEGER NOT NULL REFERENCES speakers(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Create onboarding_questions table
    create_table_if_not_exists('onboarding_questions', """
        CREATE TABLE onboarding_questions (
            id SERIAL PRIMARY KEY,
            questions JSON,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    print("✅ Migration completed successfully!")


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Drop tables in reverse order
    tables_to_drop = [
        'onboarding_questions',
        'user_speaker_preferences', 
        'users',
        'speakers',
        'churches'
    ]
    
    for table_name in tables_to_drop:
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'
        """)).fetchone()
        
        if result:
            print(f"Dropping table {table_name}...")
            op.drop_table(table_name)
    
    # Drop enum types
    enums_to_drop = ['environmentstyle', 'bibleapproach', 'teachingstyle']
    for enum_name in enums_to_drop:
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM pg_type WHERE typname = '{enum_name}'
        """)).fetchone()
        
        if result:
            print(f"Dropping enum {enum_name}...")
            sa.Enum(name=enum_name).drop(connection)
