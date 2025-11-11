import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    """
    Create a few activity log entries for the admin user.
    """
    admin = db.query(models.User).filter(
        (models.User.email == "admin@alphasys.com") |
        (models.User.username == "admin")
    ).first()
    if not admin:
        # Create a minimal admin user if missing
        admin_role = db.query(models.Role).filter(models.Role.role_name == "admin").first()
        admin_dept = db.query(models.Department).first()
        admin = models.User(
            username="admin",
            password_hash="",
            first_name="System",
            last_name="Admin",
            email="admin@alphasys.com",
            phone_number="",
            department_id=admin_dept.department_id if admin_dept else None,
            role_id=admin_role.role_id if admin_role else None,
            role_name="admin",
            hourly_rate=0.0,
            date_hired=datetime.date(2025, 1, 1),
            status=models.UserStatus.active.value,
        )
        db.add(admin)
        db.flush()

    actions = [
        "Created initial admin account",
        "Seeded reference data (roles, departments, permissions)",
        "Generated dummy employee users",
        "Populated attendance records",
        "Generated payroll entries",
        "Created leave and overtime requests",
    ]

    for action in actions:
        log = models.ActivityLog(
            user_id=admin.user_id,
            action=action,
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(log)

    db.commit()
    print("Activity log records seeded.")