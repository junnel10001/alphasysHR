"""
Employment Statuses Router

Provides CRUD endpoints for managing employment statuses.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import EmploymentStatus
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/employment-statuses", tags=["employment-statuses"])


class EmploymentStatusCreate(BaseModel):
    """Payload for creating an employment status."""
    status_name: str = Field(..., max_length=50, description="Name of the employment status")
    description: str | None = Field(None, description="Description of the employment status")
    is_active: bool = Field(True, description="Whether this employment status is active")


class EmploymentStatusUpdate(BaseModel):
    """Payload for updating an employment status."""
    status_name: str | None = Field(None, max_length=50, description="Name of the employment status")
    description: str | None = Field(None, description="Description of the employment status")
    is_active: bool | None = Field(None, description="Whether this employment status is active")


class EmploymentStatusOut(BaseModel):
    """Response model for employment statuses."""
    employment_status_id: int
    status_name: str
    description: str | None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


@router.post("/", response_model=EmploymentStatusOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_employment_statuses")
def create_employment_status(
    employment_status: EmploymentStatusCreate, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_employment_statuses"))
):
    """
    Create a new employment status.
    
    - **status_name**: Must be unique across all employment statuses.
    - **description**: Optional description of the employment status.
    - **is_active**: Whether this employment status is active.
    """
    # Check if employment status with this name already exists
    existing = db.query(EmploymentStatus).filter(EmploymentStatus.status_name == employment_status.status_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employment status with this name already exists")
    
    db_employment_status = EmploymentStatus(
        status_name=employment_status.status_name,
        description=employment_status.description,
        is_active=employment_status.is_active
    )
    db.add(db_employment_status)
    db.commit()
    db.refresh(db_employment_status)
    
    # Convert datetime fields to strings for response
    status_data = {
        "employment_status_id": db_employment_status.employment_status_id,
        "status_name": db_employment_status.status_name,
        "description": db_employment_status.description,
        "is_active": db_employment_status.is_active,
        "created_at": db_employment_status.created_at.isoformat() if db_employment_status.created_at else None,
        "updated_at": db_employment_status.updated_at.isoformat() if db_employment_status.updated_at else None
    }
    
    return status_data


@router.get("/", response_model=List[EmploymentStatusOut])
@has_permission("view_employment_statuses")
def list_employment_statuses(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_employment_statuses"))
):
    """
    Retrieve a paginated list of employment statuses.
    """
    employment_statuses = db.query(EmploymentStatus).offset(skip).limit(limit).all()
    
    # Convert datetime fields to strings for response
    status_list = []
    for status in employment_statuses:
        status_data = {
            "employment_status_id": status.employment_status_id,
            "status_name": status.status_name,
            "description": status.description,
            "is_active": status.is_active,
            "created_at": status.created_at.isoformat() if status.created_at else None,
            "updated_at": status.updated_at.isoformat() if status.updated_at else None
        }
        status_list.append(status_data)
    
    return status_list


@router.get("/{employment_status_id}", response_model=EmploymentStatusOut)
@has_permission("view_employment_statuses")
def get_employment_status(
    employment_status_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_employment_statuses"))
):
    """
    Get a single employment status by its ID.
    """
    employment_status = db.query(EmploymentStatus).filter(EmploymentStatus.employment_status_id == employment_status_id).first()
    if not employment_status:
        raise HTTPException(status_code=404, detail="Employment status not found")
    
    # Convert datetime fields to strings for response
    status_data = {
        "employment_status_id": employment_status.employment_status_id,
        "status_name": employment_status.status_name,
        "description": employment_status.description,
        "is_active": employment_status.is_active,
        "created_at": employment_status.created_at.isoformat() if employment_status.created_at else None,
        "updated_at": employment_status.updated_at.isoformat() if employment_status.updated_at else None
    }
    
    return status_data


@router.put("/{employment_status_id}", response_model=EmploymentStatusOut)
@has_permission("manage_employment_statuses")
def update_employment_status(
    employment_status_id: int,
    employment_status_update: EmploymentStatusUpdate,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("manage_employment_statuses"))
):
    """
    Update an existing employment status.
    """
    employment_status = db.query(EmploymentStatus).filter(EmploymentStatus.employment_status_id == employment_status_id).first()
    if not employment_status:
        raise HTTPException(status_code=404, detail="Employment status not found")
    
    # Update fields if provided
    update_data = employment_status_update.model_dump(exclude_unset=True)
    
    # Check for duplicate employment status name if status_name is being updated
    if 'status_name' in update_data:
        existing = db.query(EmploymentStatus).filter(
            EmploymentStatus.status_name == update_data['status_name'],
            EmploymentStatus.employment_status_id != employment_status_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employment status with this name already exists")
    
    for attr, value in update_data.items():
        setattr(employment_status, attr, value)
    
    db.commit()
    db.refresh(employment_status)
    
    # Convert datetime fields to strings for response
    status_data = {
        "employment_status_id": employment_status.employment_status_id,
        "status_name": employment_status.status_name,
        "description": employment_status.description,
        "is_active": employment_status.is_active,
        "created_at": employment_status.created_at.isoformat() if employment_status.created_at else None,
        "updated_at": employment_status.updated_at.isoformat() if employment_status.updated_at else None
    }
    
    return status_data


@router.delete("/{employment_status_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_employment_statuses")
def delete_employment_status(
    employment_status_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_employment_statuses"))
):
    """
    Delete an employment status.
    """
    employment_status = db.query(EmploymentStatus).filter(EmploymentStatus.employment_status_id == employment_status_id).first()
    if not employment_status:
        raise HTTPException(status_code=404, detail="Employment status not found")
    
    # Check if any employees are assigned to this employment status
    from backend.models import Employee
    employees_with_status = db.query(Employee).filter(Employee.employment_status == employment_status.status_name).count()
    if employees_with_status > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete employment status: {employees_with_status} employees are assigned to this status"
        )
    
    db.delete(employment_status)
    db.commit()
    return