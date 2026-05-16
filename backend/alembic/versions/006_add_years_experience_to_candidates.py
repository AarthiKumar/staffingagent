"""add years_experience to candidates

Revision ID: 006_add_years_experience_to_candidates
Revises: 005_add_users_and_availability_update
Create Date: 2026-04-09 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_add_years_experience_to_candidates"
down_revision: Union[str, Sequence[str], None] = "005_add_users_and_availability_update"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("years_experience", sa.Float(), nullable=True))
    op.create_index("ix_candidates_years_experience", "candidates", ["years_experience"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_candidates_years_experience", table_name="candidates")
    op.drop_column("candidates", "years_experience")
