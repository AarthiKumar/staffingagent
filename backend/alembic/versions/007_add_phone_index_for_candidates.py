"""add phone index for candidates

Revision ID: 007_add_phone_index_for_candidates
Revises: 006_add_years_experience_to_candidates
Create Date: 2026-05-04 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "007_add_phone_index_for_candidates"
down_revision: Union[str, Sequence[str], None] = "006_add_years_experience_to_candidates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_candidates_phone", "candidates", ["phone"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_candidates_phone", table_name="candidates")
