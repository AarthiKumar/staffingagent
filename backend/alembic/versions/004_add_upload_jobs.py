"""Add upload_jobs table for async CV processing

Revision ID: 004
Revises: 003
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create upload_jobs table
    op.create_table(
        'upload_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(200), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('missing_fields', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(), nullable=True),
        sa.Column('sections_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('embeddings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('merge_proposal', postgresql.JSON(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on status for querying
    op.create_index('ix_upload_jobs_status', 'upload_jobs', ['status'])
    op.create_index('ix_upload_jobs_created_at', 'upload_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_upload_jobs_created_at', table_name='upload_jobs')
    op.drop_index('ix_upload_jobs_status', table_name='upload_jobs')
    op.drop_table('upload_jobs')
