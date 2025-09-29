"""add missing tables

Revision ID: 7eaca4c4b7b
Revises: 88681f158517
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7eaca4c4b7b'
down_revision: Union[str, Sequence[str], None] = '88681f158517'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types only if they don't exist
    connection = op.get_bind()
    
    # Check if teachingstyle enum exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'teachingstyle'
    """)).fetchone()
    if not result:
        teaching_style_enum = sa.Enum('EXPOSITORY', 'TOPICAL', 'NARRATIVE', 'BALANCED', name='teachingstyle')
        teaching_style_enum.create(connection)
    
    # Check if bibleapproach enum exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'bibleapproach'
    """)).fetchone()
    if not result:
        bible_approach_enum = sa.Enum('LITERAL', 'ALLEGORICAL', 'MORAL', 'ANAGOGICAL', 'BALANCED', name='bibleapproach')
        bible_approach_enum.create(connection)
    
    # Check if environmentstyle enum exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'environmentstyle'
    """)).fetchone()
    if not result:
        environment_style_enum = sa.Enum('TRADITIONAL', 'CONTEMPORARY', 'BLENDED', name='environmentstyle')
        environment_style_enum.create(connection)
    
    # Create churches table only if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'churches'
    """)).fetchone()
    if not result:
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
    
    # Create speakers table only if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'speakers'
    """)).fetchone()
    if not result:
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
    
    # Create users table
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
    
    # Create user_speaker_preferences table
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
    
    # Create onboarding_questions table
    op.create_table('onboarding_questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('questions', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_onboarding_questions_id'), 'onboarding_questions', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_index(op.f('ix_onboarding_questions_id'), table_name='onboarding_questions')
    op.drop_table('onboarding_questions')
    
    op.drop_index(op.f('ix_user_speaker_preferences_id'), table_name='user_speaker_preferences')
    op.drop_table('user_speaker_preferences')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_speakers_id'), table_name='speakers')
    op.drop_table('speakers')
    
    op.drop_index(op.f('ix_churches_id'), table_name='churches')
    op.drop_table('churches')
    
    # Drop enum types only if they exist
    connection = op.get_bind()
    
    # Check if environmentstyle enum exists before dropping
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'environmentstyle'
    """)).fetchone()
    if result:
        sa.Enum(name='environmentstyle').drop(connection)
    
    # Check if bibleapproach enum exists before dropping
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'bibleapproach'
    """)).fetchone()
    if result:
        sa.Enum(name='bibleapproach').drop(connection)
    
    # Check if teachingstyle enum exists before dropping
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_type WHERE typname = 'teachingstyle'
    """)).fetchone()
    if result:
        sa.Enum(name='teachingstyle').drop(connection)
