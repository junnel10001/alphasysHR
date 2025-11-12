from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from backend.database import get_db
from backend.models import Employee, Department, Role
from backend.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=List[EmployeeOut])
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.role)
    ).offset(skip).limit(limit).all()
    return employees


@router.get("/by-user/{user_id}")
def get_employee_by_user_id(user_id: int, db: Session = Depends(get_db)):
    """
    Get employee information by user_id.
    This endpoint is used when you have a user_id and need to find the corresponding employee record.
    Returns 200 status with either the employee data or a response indicating no employee found.
    """
    employee = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.role)
    ).filter(Employee.user_id == user_id).first()
    
    if not employee:
        return {
            "employee_found": False,
            "message": "No employee profile found for this user. The user account exists but hasn't been linked to an employee record yet.",
            "user_id": user_id
        }
    
    # Convert employee to dict and add the employee_found flag
    employee_data = {
        "employee_found": True,
        "employee_id": employee.employee_id,
        "user_id": employee.user_id,
        "company_id": employee.company_id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.personal_email,  # Use personal_email field
        "mobile_number": employee.mobile_number,
        "current_address": employee.current_address,
        "date_hired": employee.date_hired.isoformat() if employee.date_hired else None,
        "employment_status": employee.employment_status,
        "basic_salary": float(employee.basic_salary) if employee.basic_salary else None,
        "department": {
            "department_id": employee.department.department_id,
            "department_name": employee.department.department_name
        } if employee.department else None,
        "role": {
            "role_id": employee.role.role_id,
            "role_name": employee.role.role_name,
            "description": employee.role.description
        } if employee.role else None
    }
    
    return employee_data


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.role)
    ).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(employee_in: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = Employee(**employee_in.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, employee_in: EmployeeUpdate, db: Session = Depends(get_db)):
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    update_data = employee_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    db.delete(db_employee)
    db.commit()
    return