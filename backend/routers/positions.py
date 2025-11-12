"""
Positions Router

Provides CRUD endpoints for managing positions.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Position, Department
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/positions", tags=["positions"])


class PositionCreate(BaseModel):
    """Payload for creating a position."""
    position_name: str = Field(..., max_length=100, description="Name of the position")
    description: str | None = Field(None, description="Description of the position")
    department_id: int | None = Field(None, description="Department ID this position belongs to")


class PositionUpdate(BaseModel):
    """Payload for updating a position."""
    position_name: str | None = Field(None, max_length=100, description="Name of the position")
    description: str | None = Field(None, description="Description of the position")
    department_id: int | None = Field(None, description="Department ID this position belongs to")


class PositionOut(BaseModel):
    """Response model for positions."""
    position_id: int
    position_name: str
    description: str | None
    department_id: int | None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


@router.post("/", response_model=PositionOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_positions")
def create_position(
    position: PositionCreate, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_positions"))
):
    """
    Create a new position.
    
    - **position_name**: Must be unique across all positions.
    - **description**: Optional description of the position.
    - **department_id**: Optional department ID this position belongs to.
    """
    # Check if position with this name already exists
    existing = db.query(Position).filter(Position.position_name == position.position_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Position with this name already exists")
    
    # Validate department_id if provided
    if position.department_id:
        department = db.query(Department).filter(Department.department_id == position.department_id).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found")
    
    db_position = Position(
        position_name=position.position_name,
        description=position.description,
        department_id=position.department_id
    )
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    
    # Convert datetime fields to strings for response
    position_data = {
        "position_id": db_position.position_id,
        "position_name": db_position.position_name,
        "description": db_position.description,
        "department_id": db_position.department_id,
        "created_at": db_position.created_at.isoformat() if db_position.created_at else None,
        "updated_at": db_position.updated_at.isoformat() if db_position.updated_at else None
    }
    
    return position_data


@router.get("/", response_model=List[PositionOut])
@has_permission("view_positions")
def list_positions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_positions"))
):
    """
    Retrieve a paginated list of positions.
    """
    positions = db.query(Position).offset(skip).limit(limit).all()
    
    # Convert datetime fields to strings for response
    position_list = []
    for position in positions:
        position_data = {
            "position_id": position.position_id,
            "position_name": position.position_name,
            "description": position.description,
            "department_id": position.department_id,
            "created_at": position.created_at.isoformat() if position.created_at else None,
            "updated_at": position.updated_at.isoformat() if position.updated_at else None
        }
        position_list.append(position_data)
    
    return position_list


@router.get("/{position_id}", response_model=PositionOut)
@has_permission("view_positions")
def get_position(
    position_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_positions"))
):
    """
    Get a single position by its ID.
    """
    position = db.query(Position).filter(Position.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Convert datetime fields to strings for response
    position_data = {
        "position_id": position.position_id,
        "position_name": position.position_name,
        "description": position.description,
        "department_id": position.department_id,
        "created_at": position.created_at.isoformat() if position.created_at else None,
        "updated_at": position.updated_at.isoformat() if position.updated_at else None
    }
    
    return position_data


@router.put("/{position_id}", response_model=PositionOut)
@has_permission("manage_positions")
def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("manage_positions"))
):
    """
    Update an existing position.
    """
    position = db.query(Position).filter(Position.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Update fields if provided
    update_data = position_update.model_dump(exclude_unset=True)
    
    # Check for duplicate position name if position_name is being updated
    if 'position_name' in update_data:
        existing = db.query(Position).filter(
            Position.position_name == update_data['position_name'],
            Position.position_id != position_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Position with this name already exists")
    
    # Validate department_id if provided
    if "department_id" in update_data and update_data["department_id"]:
        department = db.query(Department).filter(Department.department_id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found")
    
    for attr, value in update_data.items():
        setattr(position, attr, value)
    
    db.commit()
    db.refresh(position)
    
    # Convert datetime fields to strings for response
    position_data = {
        "position_id": position.position_id,
        "position_name": position.position_name,
        "description": position.description,
        "department_id": position.department_id,
        "created_at": position.created_at.isoformat() if position.created_at else None,
        "updated_at": position.updated_at.isoformat() if position.updated_at else None
    }
    
    return position_data


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_positions")
def delete_position(
    position_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_positions"))
):
    """
    Delete a position.
    """
    position = db.query(Position).filter(Position.position_id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Check if any employees are assigned to this position
    from backend.models import Employee
    employees_with_position = db.query(Employee).filter(Employee.job_title == position.position_name).count()
    if employees_with_position > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete position: {employees_with_position} employees are assigned to this position"
        )
    
    db.delete(position)
    db.commit()
    return