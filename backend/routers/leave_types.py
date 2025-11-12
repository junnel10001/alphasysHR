"""
Leave Types Router

Provides CRUD endpoints for managing leave types.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import LeaveType
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/leave-types", tags=["leave-types"])


class LeaveTypeCreate(BaseModel):
    """Payload for creating a leave type."""
    leave_name: str = Field(..., max_length=50, description="Name of leave type")
    description: str | None = Field(None, description="Description of leave type")
    default_allocation: int = Field(0, description="Default allocation in days")


class LeaveTypeUpdate(BaseModel):
    """Payload for updating a leave type."""
    leave_name: str | None = Field(None, max_length=50, description="Name of leave type")
    description: str | None = Field(None, description="Description of leave type")
    default_allocation: int | None = Field(None, description="Default allocation in days")


class LeaveTypeOut(BaseModel):
    """Response model for leave types."""
    leave_type_id: int
    leave_name: str
    description: str | None
    default_allocation: int

    model_config = {"from_attributes": True}


@router.post("/", response_model=LeaveTypeOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_leave_types")
def create_leave_type(
    leave_type: LeaveTypeCreate, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_leave_types"))
):
    """
    Create a new leave type.
    
    - **leave_name**: Must be unique across all leave types.
    - **description**: Optional description of leave type.
    - **default_allocation**: Default allocation in days.
    """
    # Check if leave type with this name already exists
    existing = db.query(LeaveType).filter(LeaveType.leave_name == leave_type.leave_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Leave type with this name already exists")
    
    db_leave_type = LeaveType(
        leave_name=leave_type.leave_name,
        description=leave_type.description,
        default_allocation=leave_type.default_allocation
    )
    db.add(db_leave_type)
    db.commit()
    db.refresh(db_leave_type)
    return db_leave_type


@router.get("/", response_model=List[LeaveTypeOut])
@has_permission("view_leave_types")
def list_leave_types(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_leave_types"))
):
    """
    Retrieve a paginated list of leave types.
    """
    leave_types = db.query(LeaveType).offset(skip).limit(limit).all()
    return leave_types


@router.get("/{leave_type_id}", response_model=LeaveTypeOut)
@has_permission("view_leave_types")
def get_leave_type(
    leave_type_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_leave_types"))
):
    """
    Get a single leave type by its ID.
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    return leave_type


@router.put("/{leave_type_id}", response_model=LeaveTypeOut)
@has_permission("manage_leave_types")
def update_leave_type(
    leave_type_id: int, 
    leave_type_update: LeaveTypeUpdate, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_leave_types"))
):
    """
    Update an existing leave type.
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    # Update fields if provided
    update_data = leave_type_update.model_dump(exclude_unset=True)
    
    # Check for duplicate leave type name if leave_name is being updated
    if 'leave_name' in update_data:
        existing = db.query(LeaveType).filter(
            LeaveType.leave_name == update_data['leave_name'],
            LeaveType.leave_type_id != leave_type_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Leave type with this name already exists")
    
    for attr, value in update_data.items():
        setattr(leave_type, attr, value)
    
    db.commit()
    db.refresh(leave_type)
    return leave_type


@router.delete("/{leave_type_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_leave_types")
def delete_leave_type(
    leave_type_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_leave_types"))
):
    """
    Delete a leave type.
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    # Check if any leave requests are assigned to this leave type
    from backend.models import LeaveRequest
    leave_requests_with_type = db.query(LeaveRequest).filter(LeaveRequest.leave_type_id == leave_type_id).count()
    if leave_requests_with_type > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete leave type: {leave_requests_with_type} leave requests are assigned to this type"
        )
    
    db.delete(leave_type)
    db.commit()
    return