"""Add user-employee relationship

Revision ID: 20251112_add_user_employee_relationship
Revises: 20251111_104500_add_position_and_employment_status_tables
Create Date: 2025-11-12 05:46:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251112_add_user_employee_relationship'
down_revision = '20251111_104500'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_id foreign key to employees table
    op.add_column('employees', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_employees_user_id_users', 'employees', 'users', ['user_id'], ['user_id']
    )


def downgrade():
    # Remove the foreign key and column
    op.drop_constraint('fk_employees_user_id_users', 'employees', type_='foreignkey')
    op.drop_column('employees', 'user_id')