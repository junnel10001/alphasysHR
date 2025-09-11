"""
Employee Service Layer

Provides CRUD operations for the Employee (User) model using a SQLAlchemy Session.
All business logic related to employees should be placed here to keep routers thin.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models import User
from ..main import get_password_hash

def get_employee(db: Session, user_id: int) -> Optional[User]:
    """Retrieve a single employee by its ID."""
    return db.query(User).filter(User.user_id == user_id).first()

def get_employee_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieve an employee by username (used for authentication)."""
    return db.query(User).filter(User.username == username).first()

def get_employee_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve an employee by email."""
    return db.query(User).filter(User.email == email).first()

def list_employees(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Return a paginated list of employees."""
    return db.query(User).offset(skip).limit(limit).all()

def create_employee(db: Session, *, username: str, password: str, first_name: str,
                    last_name: str, email: str, phone_number: Optional[str] = None,
                    department_id: Optional[int] = None, role_id: Optional[int] = None,
                    hourly_rate: float) -> User:
    """
    Create a new employee record.

    Password is hashed before storage.
    """
    hashed = get_password_hash(password)
    db_user = User(
        username=username,
        password_hash=hashed,
        role="employee",
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        department_id=department_id,
        role_id=role_id,
        hourly_rate=hourly_rate,
        date_hired=datetime.utcnow().date(),
        status="active"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_employee(db: Session, db_user: User, updates: dict) -> User:
    """
    Update fields of an existing employee.

    `updates` may contain any of the model fields; password will be re‑hashed if present.
    """
    for field, value in updates.items():
        if field == "password":
            setattr(db_user, "password_hash", get_password_hash(value))
        else:
            setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_employee(db: Session, db_user: User) -> None:
    """Remove an employee from the database."""
    db.delete(db_user)
    db.commit()