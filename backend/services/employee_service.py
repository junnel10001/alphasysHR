"""
Employee Service Layer

Provides CRUD operations for the Employee (User) model using a SQLAlchemy Session.
All business logic related to employees should be placed here to keep routers thin.
"""
  
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
  
from backend.models import User, Employee, Department, Role, Office
from backend.utils.auth import get_password_hash
from fastapi import HTTPException, status
from backend.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut

# ----------------------------------------------------------------------
# Employee CRUD helpers (operating on the new Employee model)
# ----------------------------------------------------------------------
def get_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    """Retrieve a single employee record."""
    return db.query(Employee).filter(Employee.employee_id == employee_id).first()

def list_employees_new(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
    """Return a paginated list of employees from the new Employee model."""
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee_new(db: Session, employee_in: EmployeeCreate) -> EmployeeOut:
    """Create a new employee record using the new Employee model."""
    db_employee = Employee(**employee_in.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return EmployeeOut.from_orm(db_employee)

def update_employee_new(db: Session, employee_id: int, updates: EmployeeUpdate) -> EmployeeOut:
    """Update an existing employee using the new Employee model."""
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)
    db.commit()
    db.refresh(db_employee)
    return EmployeeOut.from_orm(db_employee)

def delete_employee_new(db: Session, employee_id: int) -> dict:
    """Delete an employee using the new Employee model."""
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    db.delete(db_employee)
    db.commit()
    return {"detail": "Employee deleted successfully"}

# ----------------------------------------------------------------------
# User CRUD helpers (operating on the User model)
# ----------------------------------------------------------------------
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
    """Return a paginated list of employees (delegates to filtered version)."""
    return list_employees_with_filters(db, skip=skip, limit=limit)
 
def list_employees_with_filters(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
) -> List[User]:
    """
    Return a paginated list of employees applying optional filters.
    """
    query = db.query(User)
 
    if department_id is not None:
        query = query.filter(User.department_id == department_id)
 
    if role is not None:
        query = query.filter(User.role == role)
 
    if status is not None:
        query = query.filter(User.status == status)
 
    return query.offset(skip).limit(limit).all()
 
def create_employee(db: Session, employee_in: EmployeeCreate) -> EmployeeOut:
    """
    Create a new employee record using the User model.
    """
    # Basic validation
    if not employee_in.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username is required")
    if not employee_in.password or len(employee_in.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password must be at least 8 characters")
    if not employee_in.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email is required")
    if employee_in.hourly_rate < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Hourly rate must be non‑negative")
 
    # Uniqueness checks
    if db.query(User).filter(User.username == employee_in.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already exists")
    if db.query(User).filter(User.email == employee_in.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already exists")
 
    hashed = get_password_hash(employee_in.password)
    db_user = User(
        username=employee_in.username,
        password_hash=hashed,
        role="employee",
        first_name=employee_in.first_name,
        last_name=employee_in.last_name,
        email=employee_in.email,
        phone_number=employee_in.phone_number,
        department_id=employee_in.department_id,
        role_id=employee_in.role_id,
        hourly_rate=employee_in.hourly_rate,
        date_hired=datetime.utcnow().date(),
        status="active"
    )
    # Transactional insertion
    with db.begin():
        db.add(db_user)
        db.flush()
        db.refresh(db_user)
 
    return EmployeeOut.from_orm(db_user)
 
def update_employee(db: Session, user_id: int, updates: EmployeeUpdate) -> EmployeeOut:
    """
    Update an employee record transactionally using the User model.
    """
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Employee not found")
 
    # Validate updates
    if updates.username:
        if db.query(User).filter(User.username == updates.username,
                                 User.user_id != user_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Username already taken")
    if updates.email:
        if db.query(User).filter(User.email == updates.email,
                                 User.user_id != user_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Email already taken")
    if updates.hourly_rate is not None and updates.hourly_rate < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Hourly rate must be non‑negative")
    if updates.password:
        if not updates.password or len(updates.password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Password must be at least 8 characters")
 
    # Apply updates
    for field, value in updates.dict(exclude_unset=True).items():
        if field == "password":
            setattr(db_user, "password_hash", get_password_hash(value))
        else:
            setattr(db_user, field, value)
 
    with db.begin():
        db.flush()
        db.refresh(db_user)
 
    return EmployeeOut.from_orm(db_user)
 
def delete_employee(db: Session, user_id: int) -> dict:
    """
    Delete an employee record transactionally using the User model.
    """
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Employee not found")
    with db.begin():
        db.delete(db_user)
    return {"detail": "Employee deleted successfully"}

# ----------------------------------------------------------------------
# Lookup helpers for dropdown data
# ----------------------------------------------------------------------
def list_departments(db: Session) -> List[Department]:
    return db.query(Department).all()

def list_roles(db: Session) -> List[Role]:
    return db.query(Role).all()

def list_offices(db: Session) -> List[Office]:
    return db.query(Office).all()

def list_line_managers(db: Session) -> List[User]:
    # Assuming line managers have role_name "manager"
    return db.query(User).filter(User.role_name == "manager").all()
