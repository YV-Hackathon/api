"""fix duplicate enum error

Revision ID: 6098c2625a7
Revises: 7eaca4c4b7b
Create Date: 2025-01-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6098c2625a7'
down_revision: Union[str, Sequence[str], None] = '7eaca4c4b7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if speakers table exists, if not create it
    connection = op.get_bind()
    
    # Check if speakers table exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'speakers'
    """)).fetchone()
    
    if not result:
        # Create speakers table using existing enum types
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
    
    # Check if churches table exists
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
    
    # Check if users table exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'users'
    """)).fetchone()
    
    if not result:
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
    
    # Check if user_speaker_preferences table exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'user_speaker_preferences'
    """)).fetchone()
    
    if not result:
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
    
    # Check if onboarding_questions table exists
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = 'onboarding_questions'
    """)).fetchone()
    
    if not result:
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
    # This migration is a no-op
    pass
