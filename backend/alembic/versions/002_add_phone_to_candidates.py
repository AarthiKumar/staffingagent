"""add phone to candidates

Revision ID: 002
Revises: 001
Create Date: 2026-01-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add phone column to candidates table
    op.add_column('candidates', sa.Column('phone', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove phone column from candidates table
    op.drop_column('candidates', 'phone')
