"""initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('sha256', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('agent_id', sa.String(255), sa.ForeignKey('agents.id'), nullable=False, index=True),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('mime_type', sa.String(127), nullable=False),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('ocr', sa.Boolean(), default=False, nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create sections table
    op.create_table(
        'sections',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('document_id', sa.UUID(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('start_idx', sa.Integer(), nullable=True),
        sa.Column('end_idx', sa.Integer(), nullable=True),
    )

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('document_id', sa.UUID(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('section_id', sa.UUID(), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('model', sa.String(255), nullable=False),
        sa.Column('dim', sa.Integer(), nullable=False),
        sa.Column('vector', Vector(dim=3072), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create candidates table
    op.create_table(
        'candidates',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('document_id', sa.UUID(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create availability table
    op.create_table(
        'availability',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('candidate_id', sa.UUID(), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('available_from', sa.Date(), nullable=False),
        sa.Column('capacity_pct', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create ontology tables
    op.create_table(
        'ontology_skills',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
    )

    op.create_table(
        'ontology_aliases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('alias', sa.String(255), unique=True, nullable=False),
        sa.Column('canonical_skill', sa.String(255), nullable=False),
    )

    op.create_table(
        'ontology_certs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
    )

    # Create decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('candidate_id', sa.UUID(), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('decision', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
    )

    # Create LLM events table
    op.create_table(
        'llm_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ts', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('feature', sa.String(50), nullable=False, index=True),
        sa.Column('model', sa.String(255), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False),
        sa.Column('tokens_out', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(10, 6), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), default=False, nullable=False),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('input_hash', sa.String(64), nullable=True, index=True),
    )

    # Create metrics_search table
    op.create_table(
        'metrics_search',
        sa.Column('query_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('ts', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('use_llm', sa.Boolean(), default=False, nullable=False),
        sa.Column('p95_ms', sa.Integer(), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('zero_result', sa.Boolean(), default=False, nullable=False),
    )

    # Create HNSW index on embeddings.vector
    op.execute('CREATE INDEX idx_embeddings_hnsw ON embeddings USING hnsw (vector vector_cosine_ops)')


def downgrade() -> None:
    op.drop_table('metrics_search')
    op.drop_table('llm_events')
    op.drop_table('decisions')
    op.drop_table('ontology_certs')
    op.drop_table('ontology_aliases')
    op.drop_table('ontology_skills')
    op.drop_table('availability')
    op.drop_table('candidates')
    op.drop_table('embeddings')
    op.drop_table('sections')
    op.drop_table('documents')
    op.drop_table('agents')
