"""Initial migration with User, Lecture, and StudyNotes tables

Revision ID: 001
Revises: 
Create Date: 2024-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create lectures table
    op.create_table(
        'lectures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('lecture_type', sa.Enum('LIVE', 'UPLOAD', name='lecturetype'), nullable=False),
        sa.Column('audio_file_path', sa.String(length=1000), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('processing_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lectures_user_id'), 'lectures', ['user_id'], unique=False)
    
    # Create study_notes table
    op.create_table(
        'study_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lecture_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topics', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_points', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lecture_id'], ['lectures.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_notes_lecture_id'), 'study_notes', ['lecture_id'], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_study_notes_lecture_id'), table_name='study_notes')
    op.drop_table('study_notes')
    op.drop_index(op.f('ix_lectures_user_id'), table_name='lectures')
    op.drop_table('lectures')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS lecturetype')
