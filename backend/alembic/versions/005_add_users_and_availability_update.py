"""Add users table and availability.available_to column

Revision ID: 005
Revises: 004
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('auth0_sub', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='candidate'),
        sa.Column('candidate_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('auth0_sub'),
    )
    op.create_index('ix_users_auth0_sub', 'users', ['auth0_sub'])
    op.create_index('ix_users_candidate_id', 'users', ['candidate_id'])

    # Add available_to column to availability table
    op.add_column('availability', sa.Column('available_to', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('availability', 'available_to')
    op.drop_index('ix_users_candidate_id', table_name='users')
    op.drop_index('ix_users_auth0_sub', table_name='users')
    op.drop_table('users')
