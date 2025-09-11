from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List

from ..models import User
from ..database import get_db
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/employees", tags=["employees"])

class EmployeeCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str | None = None
    department_id: int | None = None
    role_id: int | None = None
    hourly_rate: float

class EmployeeOut(BaseModel):
    user_id: int
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str | None = None
    department_id: int | None = None
    role_id: int | None = None
    hourly_rate: float
    date_hired: str
    status: str

    @classmethod
    def from_orm(cls, obj):
        """Custom serialization to handle date conversion"""
        data = {
            **obj.__dict__,
            "date_hired": obj.date_hired.isoformat() if obj.date_hired else None
        }
        return cls(**data)

@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    # check username/email uniqueness
    if db.query(User).filter(User.username == emp.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == emp.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    # create user
    from ..main import get_password_hash  # import utility from main
    hashed = get_password_hash(emp.password)
    db_user = User(
        username=emp.username,
        password_hash=hashed,
        role_name="employee",
        first_name=emp.first_name,
        last_name=emp.last_name,
        email=emp.email,
        phone_number=emp.phone_number,
        department_id=emp.department_id,
        role_id=emp.role_id,
        hourly_rate=emp.hourly_rate,
        date_hired=datetime.utcnow().date(),
        status="active"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return EmployeeOut.from_orm(db_user)

@router.get("/", response_model=List[EmployeeOut])
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return [EmployeeOut.from_orm(user) for user in users]

@router.get("/{user_id}", response_model=EmployeeOut)
def get_employee(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeOut.from_orm(user)

@router.put("/{user_id}", response_model=EmployeeOut)
def update_employee(user_id: int, emp: EmployeeCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    # update fields
    for attr, value in emp.model_dump(exclude_unset=True).items():
        if attr == "password":
            from ..main import get_password_hash
            setattr(user, "password_hash", get_password_hash(value))
        else:
            setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    return EmployeeOut.from_orm(user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(user)
    db.commit()
    return