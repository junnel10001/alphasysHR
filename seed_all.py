import random
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.seed_data import seed_admin
from seed_roles_departments import run as run_roles_departments
from backend.seed_extra import seed_top_employee_stats
from seed_leave_types import seed_leave_types as run_leave_types
from seed_users import run as run_users
from seed_attendance import run as run_attendance
from seed_payroll import run as run_payroll
from seed_leave_requests import run as run_leave_requests
from seed_overtime_requests import run as run_overtime_requests
from seed_activity_logs import run as run_activity_logs

def main():
    random.seed(42)
    # Create a single DB session for all seeders
    db: Session = SessionLocal()
    try:
        # Reference data
        run_roles_departments(db)
        run_leave_types()
        # Core data
        run_users(db)
        run_attendance(db)
        run_payroll(db)
        run_leave_requests(db)
        run_overtime_requests(db)
        # Seed top‑leave statistics for the admin dashboard
        seed_top_employee_stats(db)
        # Optional logs
        run_activity_logs(db)
        # Seed admin user after core data
        # seed_admin(db)  # Disabled to avoid duplicate username errors
        db.commit()
        print("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()