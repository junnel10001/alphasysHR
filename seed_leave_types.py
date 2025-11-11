import sys
sys.path.append('backend')
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import LeaveType

def seed_leave_types():
    """Seed the leave_types table with default values."""
    db: Session = SessionLocal()
    try:
        # Check if leave types already exist
        existing_count = db.query(LeaveType).count()
        if existing_count > 0:
            print(f"Leave types already exist ({existing_count} found)")
            return
        
        # Default leave types
        leave_types = [
            LeaveType(leave_type_id=1, leave_name="Annual Leave", default_allocation=20),
            LeaveType(leave_type_id=2, leave_name="Sick Leave", default_allocation=10),
            LeaveType(leave_type_id=3, leave_name="Personal Leave", default_allocation=5),
            LeaveType(leave_type_id=4, leave_name="Maternity Leave", default_allocation=12),
            LeaveType(leave_type_id=5, leave_name="Paternity Leave", default_allocation=5),
        ]
        
        # Insert leave types
        for leave_type in leave_types:
            db.add(leave_type)
        
        db.commit()
        print(f"Seeded {len(leave_types)} leave types")
        
        # Verify insertion
        types = db.query(LeaveType).all()
        print("Leave types in database:")
        for leave_type in types:
            print(f"  - ID: {leave_type.leave_type_id}, Name: {leave_type.leave_name}, Allocation: {leave_type.default_allocation}")
            
    except Exception as e:
        db.rollback()
        print(f"Error seeding leave types: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_leave_types()