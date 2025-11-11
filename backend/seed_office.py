import sqlalchemy as sa
from backend.database import engine, Base, SessionLocal
from backend.models import Office

def seed_offices():
    """Seed offices data into the database."""
    offices = [
        {"office_name": "Philippines-Ozamiz", "location": "Ozamiz, Philippines"},
        {"office_name": "Philippines-Cebu", "location": "Cebu, Philippines"},
        {"office_name": "Australia-Sydney", "location": "Sydney, Australia"},
        {"office_name": "Australia-Melbourne", "location": "Melbourne, Australia"},
    ]

    # Check if offices already exist to avoid duplicates
    db = SessionLocal()
    try:
        existing_offices = db.query(Office).all()
        existing_names = {office.office_name for office in existing_offices}
        
        # Only add offices that don't already exist
        for office_data in offices:
            if office_data["office_name"] not in existing_names:
                office = Office(**office_data)
                db.add(office)
        
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_offices()