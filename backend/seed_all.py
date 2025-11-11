import os
import subprocess
import sys
from pathlib import Path
# Ensure the project root is in the Python path when running the script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Ensure the project root is in the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from backend.database import SessionLocal, engine, Base
from backend.seed_office import seed_offices
from backend.seed_data import (
    seed_users,
    seed_roles,
    seed_departments,
    seed_activity_logs,
    seed_attendance,
    seed_leave_requests,
    seed_overtime_requests,
    seed_payroll,
    seed_leave_types,
    seed_admin,
)
# Import new seed functions
from backend.seed_extra import (
    seed_late_arrivals,
    seed_sick_leave,
    seed_overtime_stats,
    seed_top_employee_stats,
)

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)

def run_seeds():
    """Run all seed functions in order."""
    db = SessionLocal()
    try:
        # Core seed data
        seed_users(db)
        seed_roles(db)
        seed_departments(db)
        # seed_roles_departments(db)  # Removed: function not defined
        seed_leave_types(db)
        seed_admin(db)

        # Transactional data
        seed_attendance(db)
        seed_leave_requests(db)
        seed_overtime_requests(db)
        seed_payroll(db)
        seed_activity_logs(db)

        # New seed data for dashboard visualizations
        # Seed office locations
        seed_offices(db)
        seed_late_arrivals(db)
        seed_sick_leave(db)
        seed_overtime_stats(db)
        # Placeholder for top employee stats (queries are handled in service)
        seed_top_employee_stats(db)

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    run_seeds()