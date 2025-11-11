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
    # Assign admin role for admin users
    role = None
    if username in ("admin", "junnel@alphasys.com.au"):
        role = db.query(models.Role).filter(models.Role.role_name == "admin").first()
    user = models.User(
        username=username,
        password_hash=password_hash,
        first_name="Admin",
        last_name="User",
        email=username,
        hourly_rate=0,
        date_hired=datetime.date(2020, 1, 1),
        status=models.UserStatus.active.value,
        role_id=role.role_id if role else None,
        role_name=role.role_name if role else None,
    )
    db.add(user)
    db.commit()
    print(f"User '{username}' created successfully.")

def main():
    db = SessionLocal()
    try:
        create_user("admin", "admin123", db)
        # Ensure junnel has admin role
        user = db.query(models.User).filter(models.User.email == "junnel@alphasys.com.au").first()
        if user:
            admin_role = db.query(models.Role).filter(models.Role.role_name == "admin").first()
            if admin_role:
                user.role_id = admin_role.role_id
                user.role_name = admin_role.role_name
                db.add(user)
                db.commit()
                print("Assigned admin role to junnel@alphasys.com.au")
        else:
            create_user("junnel@alphasys.com.au", "password", db)
    finally:
        db.close()

if __name__ == "__main__":
    main()