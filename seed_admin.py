from backend.database import SessionLocal, engine
from backend import models
from sqlalchemy.orm import Session
import bcrypt
import datetime

def create_user(username: str, password: str, db: Session):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        print(f"User '{username}' already exists.")
        return
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    user = models.User(
        username=username,
        password_hash=password_hash,
        first_name="Admin",
        last_name="User",
        email=username,
        hourly_rate=0,
        date_hired=datetime.date(2020, 1, 1),
        status=models.UserStatus.active.value,
    )
    db.add(user)
    db.commit()
    print(f"User '{username}' created successfully.")

def main():
    db = SessionLocal()
    try:
        create_user("admin", "admin123", db)
        create_user("junnel@alphasys.com.au", "admin123", db)
    finally:
        db.close()

if __name__ == "__main__":
    main()