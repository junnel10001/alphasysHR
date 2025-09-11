import bcrypt
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration (must match the one in app.py)
engine = create_engine('sqlite:///users.db', echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

def create_user(username: str, password: str):
    db = SessionLocal()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"User '{username}' already exists.")
        db.close()
        return
    # Pre‑computed bcrypt hash for the given password (generated once)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.close()
    print(f"User '{username}' created successfully.")

def main():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Create demo users
    create_user("admin", "admin123")
    create_user("junnel@alphasys.com.au", "admin123")

if __name__ == "__main__":
    main()