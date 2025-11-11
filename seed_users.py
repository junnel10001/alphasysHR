import bcrypt
import random
import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    # Ensure admin user exists (idempotent)
    admin_email = "admin@alphasys.com"
    admin_username = "admin"
    # Strip possible whitespace from stored emails
    admin = (
        db.query(models.User)
        .filter(
            (models.User.email == admin_email) | (models.User.username == admin_username)
        )
        .first()
    )
    if not admin:
        hashed = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode()
        # Assign first department and admin role (will be created by seed_roles_departments)
        admin_role = db.query(models.Role).filter(models.Role.role_name == "admin").first()
        admin_dept = db.query(models.Department).first()
        admin = models.User(
            username=admin_username,
            password_hash=hashed,
            first_name="System",
            last_name="Admin",
            email=admin_email,
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
        print("Admin user created.")

    # Create demo employees
    existing_emails = {u.email for u in db.query(models.User).all()}
    departments = db.query(models.Department).all()
    roles = db.query(models.Role).filter(models.Role.role_name == "employee").all()
    if not roles:
        employee_role = db.query(models.Role).filter(models.Role.role_name == "employee").first()
    else:
        employee_role = roles[0]

    for i in range(1, 11):
        email = f"employee{i}@demo.com"
        if email in existing_emails:
            continue
        username = f"employee{i}"
        hashed = bcrypt.hashpw(f"password{i}".encode("utf-8"), bcrypt.gensalt()).decode()
        dept = random.choice(departments) if departments else None
        user = models.User(
            username=username,
            password_hash=hashed,
            first_name=f"Employee{i}",
            last_name="Demo",
            email=email,
            phone_number="",
            department_id=dept.department_id if dept else None,
            role_id=employee_role.role_id if employee_role else None,
            role_name="employee",
            hourly_rate=round(random.uniform(15.0, 30.0), 2),
            date_hired=datetime.date(2025, 1, 1),
            status=models.UserStatus.active.value,
        )
        db.add(user)

    db.commit()
    print("Demo employee users seeded.")