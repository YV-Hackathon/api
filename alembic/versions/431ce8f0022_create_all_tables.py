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
    
    # Create enum types only if they don't exist
    def create_enum_if_not_exists(enum_name, values):
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM pg_type WHERE typname = '{enum_name}'
        """)).fetchone()
        if not result:
            enum_obj = sa.Enum(*values, name=enum_name)
            enum_obj.create(connection)
            print(f"Created enum {enum_name}")
        else:
            print(f"Enum {enum_name} already exists, skipping...")
    
    # Create all enum types
    create_enum_if_not_exists('teachingstyle', ['ACADEMIC', 'RELATABLE', 'BALANCED'])
    create_enum_if_not_exists('bibleapproach', ['MORE_SCRIPTURE', 'MORE_APPLICATION', 'BALANCED'])
    create_enum_if_not_exists('environmentstyle', ['TRADITIONAL', 'CONTEMPORARY', 'BLENDED'])
    
    # Create tables only if they don't exist
    def create_table_if_not_exists(table_name, table_func):
        result = connection.execute(sa.text(f"""
            SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'
        """)).fetchone()
        if not result:
            table_func()
            print(f"Created table {table_name}")
        else:
            print(f"Table {table_name} already exists, skipping...")
    
    # Create churches table
    def create_churches_table():
        op.create_table('churches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('denomination', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.JSON(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('membership_count', sa.Integer(), nullable=True),
        sa.Column('service_times', sa.JSON(), nullable=True),
        sa.Column('social_media', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_churches_id'), 'churches', ['id'], unique=False)
    
    create_table_if_not_exists('churches', create_churches_table)
    
    # Create speakers table
    def create_speakers_table():
        op.create_table('speakers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('years_of_service', sa.Integer(), nullable=True),
        sa.Column('social_media', sa.JSON(), nullable=True),
        sa.Column('speaking_topics', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('teaching_style', sa.Enum('EXPOSITORY', 'TOPICAL', 'NARRATIVE', 'BALANCED', name='teachingstyle'), nullable=True),
        sa.Column('bible_approach', sa.Enum('LITERAL', 'ALLEGORICAL', 'MORAL', 'ANAGOGICAL', 'BALANCED', name='bibleapproach'), nullable=True),
        sa.Column('environment_style', sa.Enum('TRADITIONAL', 'CONTEMPORARY', 'BLENDED', name='environmentstyle'), nullable=True),
        sa.Column('is_recommended', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('church_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['church_id'], ['churches.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_speakers_id'), 'speakers', ['id'], unique=False)
    
    create_table_if_not_exists('speakers', create_speakers_table)
    
    # Create users table
    def create_users_table():
        op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('bible_reading_preference', sa.Enum('LITERAL', 'ALLEGORICAL', 'MORAL', 'ANAGOGICAL', 'BALANCED', name='bibleapproach'), nullable=True),
        sa.Column('teaching_style_preference', sa.Enum('EXPOSITORY', 'TOPICAL', 'NARRATIVE', 'BALANCED', name='teachingstyle'), nullable=True),
        sa.Column('environment_preference', sa.Enum('TRADITIONAL', 'CONTEMPORARY', 'BLENDED', name='environmentstyle'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    
    create_table_if_not_exists('users', create_users_table)
    
    # Create user_speaker_preferences table
    def create_user_speaker_preferences_table():
        op.create_table('user_speaker_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('speaker_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['speaker_id'], ['speakers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_speaker_preferences_id'), 'user_speaker_preferences', ['id'], unique=False)
    
    create_table_if_not_exists('user_speaker_preferences', create_user_speaker_preferences_table)
    
    # Create onboarding_questions table
    def create_onboarding_questions_table():
        op.create_table('onboarding_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_onboarding_questions_id'), 'onboarding_questions', ['id'], unique=False)
    
    create_table_if_not_exists('onboarding_questions', create_onboarding_questions_table)
    
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
