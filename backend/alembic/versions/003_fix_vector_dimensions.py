"""Fix vector dimensions to support flexible embedding sizes

Revision ID: 003
Revises: 002
Create Date: 2026-01-20 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop and recreate the vector column without dimension constraints.
    This allows using any embedding model (1536, 3072, etc.) dynamically.
    """
    # Drop the existing vector column
    op.execute('ALTER TABLE embeddings DROP COLUMN vector')

    # Recreate it without dimension constraint
    op.add_column('embeddings', sa.Column('vector', Vector(dim=None), nullable=False))


def downgrade() -> None:
    """Revert to previous state"""
    # Just recreate with None dimension again (same as current state)
    op.execute('ALTER TABLE embeddings DROP COLUMN vector')
    op.add_column('embeddings', sa.Column('vector', Vector(dim=None), nullable=False))
