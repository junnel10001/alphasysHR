"""Add position and employment status tables

Revision ID: 20251111_104500
Revises: 20251111_104000_add_user_invitations_table
Create Date: 2025-11-11 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111_104500'
down_revision = '20251111_104000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('position_id', sa.Integer(), nullable=False),
        sa.Column('position_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.department_id'], ),
        sa.PrimaryKeyConstraint('position_id'),
        sa.UniqueConstraint('position_name')
    )
    op.create_index(op.f('ix_positions_position_id'), 'positions', ['position_id'], unique=False)

    # Create employment_statuses table
    op.create_table(
        'employment_statuses',
        sa.Column('employment_status_id', sa.Integer(), nullable=False),
        sa.Column('status_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('employment_status_id'),
        sa.UniqueConstraint('status_name')
    )
    op.create_index(op.f('ix_employment_statuses_employment_status_id'), 'employment_statuses', ['employment_status_id'], unique=False)


def downgrade() -> None:
    # Drop employment_statuses table
    op.drop_index(op.f('ix_employment_statuses_employment_status_id'), table_name='employment_statuses')
    op.drop_table('employment_statuses')
    
    # Drop positions table
    op.drop_index(op.f('ix_positions_position_id'), table_name='positions')
    op.drop_table('positions')