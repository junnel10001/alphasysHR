"""initial schema

Revision ID: 20250908_initial_schema
Revises: 
Create Date: 2025-09-08 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250908_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.department_id")),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.role_id")),
        sa.Column("role_name", sa.String(50), server_default="employee"),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("date_hired", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), server_default="active")
    )

    # Roles table
    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer, primary_key=True),
        sa.Column("role_name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text)
    )

    # Permissions table
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.Integer, primary_key=True),
        sa.Column("permission_name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text)
    )

    # Role-Permissions many‑to‑many
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.role_id"), primary_key=True),
        sa.Column("permission_id", sa.Integer, sa.ForeignKey("permissions.permission_id"), primary_key=True)
    )

    # Departments table
    op.create_table(
        "departments",
        sa.Column("department_id", sa.Integer, primary_key=True),
        sa.Column("department_name", sa.String(100), nullable=False, unique=True)
    )

    # Attendance table
    op.create_table(
        "attendance",
        sa.Column("attendance_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time_in", sa.DateTime),
        sa.Column("time_out", sa.DateTime),
        sa.Column("hours_worked", sa.Numeric(5, 2)),
        sa.Column("status", sa.String(20), 
                  server_default="Present")
    )

    # Payroll table
    op.create_table(
        "payroll",
        sa.Column("payroll_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("cutoff_start", sa.Date, nullable=False),
        sa.Column("cutoff_end", sa.Date, nullable=False),
        sa.Column("basic_pay", sa.Numeric(10, 2), nullable=False),
        sa.Column("overtime_pay", sa.Numeric(10, 2), server_default="0"),
        sa.Column("deductions", sa.Numeric(10, 2), server_default="0"),
        sa.Column("net_pay", sa.Numeric(10, 2), nullable=False),
        sa.Column("generated_at", sa.DateTime, server_default=sa.func.now())
    )

    # Payslips table
    op.create_table(
        "payslips",
        sa.Column("payslip_id", sa.Integer, primary_key=True),
        sa.Column("payroll_id", sa.Integer, sa.ForeignKey("payroll.payroll_id"), nullable=False),
        sa.Column("file_path", sa.String(255), nullable=False)
    )

    # Leave Types table
    op.create_table(
        "leave_types",
        sa.Column("leave_type_id", sa.Integer, primary_key=True),
        sa.Column("leave_name", sa.String(50), nullable=False, unique=True),
        sa.Column("default_allocation", sa.Integer, nullable=False)
    )

    # Leave Requests table
    op.create_table(
        "leave_requests",
        sa.Column("leave_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("leave_type_id", sa.Integer, sa.ForeignKey("leave_types.leave_type_id"), nullable=False),
        sa.Column("date_from", sa.Date, nullable=False),
        sa.Column("date_to", sa.Date, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("status", sa.String(20), server_default="Pending"),
        sa.Column("approver_id", sa.Integer, sa.ForeignKey("users.user_id")),
        sa.Column("approved_at", sa.DateTime)
    )

    # Overtime Requests table
    op.create_table(
        "overtime_requests",
        sa.Column("ot_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("hours_requested", sa.Numeric(4, 2), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("status", sa.String(20), server_default="Pending"),
        sa.Column("approver_id", sa.Integer, sa.ForeignKey("users.user_id")),
        sa.Column("approved_at", sa.DateTime)
    )

    # Activity Logs table
    op.create_table(
        "activity_logs",
        sa.Column("log_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now())
    )

def downgrade():
    op.drop_table("activity_logs")
    op.drop_table("overtime_requests")
    op.drop_table("leave_requests")
    op.drop_table("leave_types")
    op.drop_table("payslips")
    op.drop_table("payroll")
    op.drop_table("attendance")
    op.drop_table("departments")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")