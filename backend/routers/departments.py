"""
Departments Router

Provides CRUD endpoints for managing departments.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Department
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/departments", tags=["departments"])


class DepartmentCreate(BaseModel):
    """Payload for creating a department."""
    department_name: str = Field(..., max_length=100, description="Name of the department")


class DepartmentUpdate(BaseModel):
    """Payload for updating a department."""
    department_name: str | None = Field(None, max_length=100, description="Name of the department")


class DepartmentOut(BaseModel):
    """Response model for departments."""
    department_id: int
    department_name: str

    model_config = {"from_attributes": True}


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("manage_departments"))
):
    """
    Create a new department.
    
    - **department_name**: Must be unique across all departments.
    """
    # Check if department with this name already exists
    existing = db.query(Department).filter(Department.department_name == department.department_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    
    db_department = Department(department_name=department.department_name)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


@router.get("/", response_model=List[DepartmentOut])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    """
    Retrieve a paginated list of departments.
    """
    departments = db.query(Department).offset(skip).limit(limit).all()
    return departments


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    """
    Get a single department by its ID.
    """
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("manage_departments"))
):
    """
    Update an existing department.
    """
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Update fields if provided
    update_data = department_update.model_dump(exclude_unset=True)
    
    # Check if department name is being updated and if it conflicts with existing department
    if 'department_name' in update_data:
        new_name = update_data['department_name']
        # Check if another department with this name already exists (excluding current department)
        existing = db.query(Department).filter(
            Department.department_name == new_name,
            Department.department_id != department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Department with this name already exists"
            )
    
    # Apply updates
    for attr, value in update_data.items():
        setattr(department, attr, value)
    
    try:
        db.commit()
        db.refresh(department)
        return department
    except Exception as e:
        db.rollback()
        # Handle any database constraint violations
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Department with this name already exists"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while updating the department"
            )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("manage_departments"))
):
    """
    Delete a department.
    """
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if any employees are assigned to this department
    from backend.models import Employee
    employees_in_dept = db.query(Employee).filter(Employee.department_id == department_id).count()
    if employees_in_dept > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete department: {employees_in_dept} employees are assigned to this department"
        )
    
    db.delete(department)
    db.commit()
    return