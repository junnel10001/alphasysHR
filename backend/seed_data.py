import random
import bcrypt
import logging

# ----------------------------------------------------------------------
# Global helper to hash passwords (used for both sample users and the admin)
# ----------------------------------------------------------------------
def _hash_password(pw: str) -> str:
    """Return a bcrypt hash for the given password string."""
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode()

# (Removed duplicate helper; using the global definition above)
from datetime import datetime, timedelta

from database import SessionLocal
from models import (
    User,
    Role,
    Department,
    ActivityLog,
    Attendance,
    LeaveRequest,
    OvertimeRequest,
    Payroll,
    LeaveType,
    Permission,
)

def _get_random_date(days_back: int = 30) -> datetime:
    """Return a random datetime within the past `days_back` days."""
    return datetime.utcnow() - timedelta(days=random.randint(0, days_back))

# ----------------------------------------------------------------------
# Helper to assign roles to a user (many‑to‑many)
# ----------------------------------------------------------------------
def assign_roles_to_user(db: SessionLocal, user: User, role_names: list[str]) -> None:
    """
    Attach the given role names to the user via the ``user.roles`` relationship.
    """
    roles = (
        db.query(Role)
        .filter(Role.role_name.in_(role_names))
        .all()
    )
    for role in roles:
        if role not in user.roles:
            user.roles.append(role)
    db.flush()

def seed_users(db: SessionLocal) -> None:
    logger = logging.getLogger(__name__)
    """Create a few sample users."""
    from datetime import datetime

    # Desired user data

    desired_users = [
        {
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@example.com",
            "password_hash": _hash_password("password"),
            "hourly_rate": 500.00,
            "date_hired": datetime.utcnow().date(),
        },
        {
            "username": "bob",
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "password_hash": _hash_password("password"),
            "hourly_rate": 550.00,
            "date_hired": datetime.utcnow().date(),
        },
        {
            "username": "charlie",
            "first_name": "Charlie",
            "last_name": "Lee",
            "email": "charlie@example.com",
            "password_hash": _hash_password("password"),
            "hourly_rate": 600.00,
            "date_hired": datetime.utcnow().date(),
        },
    ]

    # Avoid duplicate emails
    existing_emails = {
        email
        for (email,) in db.query(User.email)
        .filter(User.email.in_([u["email"] for u in desired_users]))
        .all()
    }

    new_users = [
        User(**data)
        for data in desired_users
        if data["email"] not in existing_emails
    ]

    if new_users:
        db.bulk_save_objects(new_users)
        logger.debug("Seeded new users: %s", [u.username for u in new_users])
    else:
        logger.debug("No new users to seed.")

def seed_roles(db: SessionLocal) -> None:
    """Create basic roles, avoiding duplicates."""
    role_definitions = [
        ("admin", "Administrator with full access"),
        ("manager", "Manager with limited access"),
        ("employee", "Regular employee"),
    ]
    for role_name, description in role_definitions:
        existing = db.query(Role).filter(Role.role_name == role_name).first()
        if not existing:
            db.add(Role(role_name=role_name, description=description))
    db.flush()

def seed_permissions(db: SessionLocal) -> None:
    """Create permissions and assign them to the admin role."""
    permission_definitions = [
        ("view_dashboard", "Access to view the dashboard"),
        ("view_kpi", "Access to KPI endpoint"),
        ("manage_users", "Create, update, delete users"),
        ("manage_roles", "Create, update, delete roles"),
        ("manage_departments", "Create, update, delete departments"),
        ("create_employee", "Create a new employee record"),
        ("update_employee", "Update an existing employee record"),
        ("delete_employee", "Delete an employee record"),
    ]

    # ------------------------------------------------------------------
    # Ensure the admin role exists BEFORE we assign permissions
    # ------------------------------------------------------------------
    admin_role = db.query(Role).filter(Role.role_name == "admin").first()
    if not admin_role:
        admin_role = Role(role_name="admin", description="Administrator with full access")
        db.add(admin_role)
       

    # ------------------------------------------------------------------
    # Insert missing permissions
    # ------------------------------------------------------------------
    for perm_name, description in permission_definitions:
        existing = (
            db.query(Permission)
            .filter(Permission.permission_name == perm_name)
            .first()
        )
        if not existing:
            db.add(Permission(permission_name=perm_name, description=description))
    db.flush()

    # ------------------------------------------------------------------
    # Assign every permission to the admin role (many‑to‑many)
    # ------------------------------------------------------------------
    for perm_name, _ in permission_definitions:
        perm = db.query(Permission).filter(Permission.permission_name == perm_name).first()
        if perm and perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
    db.flush()

def seed_departments(db: SessionLocal) -> None:
    """Create a few departments."""
    department_names = ["Human Resources", "Engineering", "Finance"]
    existing = {
        d.department_name
        for d in db.query(Department)
        .filter(Department.department_name.in_(department_names))
        .all()
    }
    new_departments = [
        Department(department_name=name)
        for name in department_names
        if name not in existing
    ]
    if new_departments:
        db.add_all(new_departments)
        db.flush()

def seed_leave_types(db: SessionLocal) -> None:
    """Create leave type entries."""
    leave_type_names = ["Sick Leave", "Annual Leave", "Maternity Leave"]
    existing = {
        lt.leave_name
        for lt in db.query(LeaveType)
        .filter(LeaveType.leave_name.in_(leave_type_names))
        .all()
    }
    new_leave_types = [
        LeaveType(
            leave_name=name,
            default_allocation=10
            if name == "Sick Leave"
            else 15
            if name == "Annual Leave"
            else 90,
        )
        for name in leave_type_names
        if name not in existing
    ]
    if new_leave_types:
        db.bulk_save_objects(new_leave_types)

def seed_admin(db: SessionLocal) -> None:
    """Create an admin user and assign the admin role."""
    # Look up the admin by the correct email (including .au domain)
    admin_user = (
        db.query(User)
        .filter(User.email == "junnel@alphasys.com.au")
        .first()
    )
    if not admin_user:
        admin_user = User(
            # Use the email as the username to satisfy the unique constraint
            username="junnel@alphasys.com.au",
            first_name="Junnel",
            last_name="Admin",
            email="junnel@alphasys.com.au",
            password_hash=_hash_password("password"),  # Store a proper bcrypt hash
            hourly_rate=0,
            date_hired=datetime.utcnow().date(),
        )
        db.add(admin_user)
        db.flush()  # Populate admin_user.user_id
    else:
        # Ensure the admin credentials are up‑to‑date
        admin_user.username = "junnel@alphasys.com.au"
        admin_user.email = "junnel@alphasys.com.au"
        admin_user.password_hash = _hash_password("password")

    admin_role = db.query(Role).filter(Role.role_name == "admin").first()
    if admin_role:
        admin_user.role_id = admin_role.role_id
        admin_user.role_name = admin_role.role_name
        admin_user.role_obj = admin_role
        assign_roles_to_user(db, admin_user, ["admin"])

def seed_activity_logs(db: SessionLocal) -> None:
    """Create a few activity log entries."""
    logs = [
        ActivityLog(
            user_id=1,
            action="login",
            timestamp=_get_random_date(),
        ),
        ActivityLog(
            user_id=2,
            action="view_dashboard",
            timestamp=_get_random_date(),
        ),
    ]
    db.bulk_save_objects(logs)

def seed_attendance(db: SessionLocal) -> None:
    """Create attendance records for the past 7 days."""
    from backend.models import AttendanceStatus

    records = []
    for user_id in range(1, 4):
        for days_ago in range(7):
            record_date = datetime.utcnow().date() - timedelta(days=days_ago)
            records.append(
                Attendance(
                    user_id=user_id,
                    date=record_date,
                    status=random.choice(
                        [
                            AttendanceStatus.Present.value,
                            AttendanceStatus.Late.value,
                            AttendanceStatus.Absent.value,
                        ]
                    ),
                )
            )
    db.bulk_save_objects(records)

def seed_leave_requests(db: SessionLocal) -> None:
    """Create some leave request entries."""
    requests = [
        LeaveRequest(
            user_id=1,
            leave_type_id=1,
            date_from=datetime.utcnow().date() - timedelta(days=5),
            date_to=datetime.utcnow().date() - timedelta(days=3),
            status="approved",
        ),
        LeaveRequest(
            user_id=2,
            leave_type_id=2,
            date_from=datetime.utcnow().date() - timedelta(days=10),
            date_to=datetime.utcnow().date() - timedelta(days=8),
            status="pending",
        ),
    ]
    db.bulk_save_objects(requests)

def seed_overtime_requests(db: SessionLocal) -> None:
    """Create overtime request entries."""
    overtime = [
        OvertimeRequest(
            user_id=1,
            date=datetime.utcnow().date() - timedelta(days=2),
            hours_requested=2.5,
            status="approved",
        ),
        OvertimeRequest(
            user_id=3,
            date=datetime.utcnow().date() - timedelta(days=1),
            hours_requested=1.0,
            status="pending",
        ),
    ]
    db.bulk_save_objects(overtime)

def seed_payroll(db: SessionLocal) -> None:
    """Create payroll records for the current month."""
    today = datetime.utcnow().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    last_day = next_month - timedelta(days=1)

    payrolls = [
        Payroll(
            user_id=1,
            cutoff_start=first_day,
            cutoff_end=last_day,
            basic_pay=50000,
            overtime_pay=5000,
            deductions=2000,
            net_pay=53000,
        ),
        Payroll(
            user_id=2,
            cutoff_start=first_day,
            cutoff_end=last_day,
            basic_pay=48000,
            overtime_pay=3000,
            deductions=1500,
            net_pay=49500,
        ),
    ]
    db.bulk_save_objects(payrolls)

def run_seeds(db: SessionLocal) -> None:
    seed_roles(db)
    seed_permissions(db)
    seed_users(db)
    # Assign default employee role to the sample users
    for user in db.query(User).filter(User.email.in_(
        ["alice@example.com", "bob@example.com", "charlie@example.com"]
    )).all():
        assign_roles_to_user(db, user, ["employee"])
    seed_admin(db)
    seed_departments(db)
    seed_leave_types(db)
    seed_attendance(db)
    seed_leave_requests(db)
    seed_overtime_requests(db)
    seed_payroll(db)
    seed_activity_logs(db)

if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_seeds(db)
        db.commit()
    finally:
        db.close()