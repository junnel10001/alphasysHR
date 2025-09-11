"""Add PDF metadata fields to Payslip model

Revision ID: 20250909_update_payslip_model
Revises: 20250908_initial_schema
Create Date: 2025-09-09 10:52:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250909_update_payslip_model'
down_revision = '20250908_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to payslips table
    op.add_column('payslips', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('payslips', sa.Column('file_hash', sa.String(64), nullable=True))
    op.add_column('payslips', sa.Column('generation_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('payslips', sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('payslips', sa.Column('generated_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('payslips', sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade():
    # Remove columns from payslips table
    op.drop_column('payslips', 'file_size')
    op.drop_column('payslips', 'file_hash')
    op.drop_column('payslips', 'generation_status')
    op.drop_column('payslips', 'download_count')
    op.drop_column('payslips', 'generated_at')
    op.drop_column('payslips', 'updated_at')