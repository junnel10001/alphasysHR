"""
Offices Router

Provides CRUD endpoints for managing office locations.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Office
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/offices", tags=["offices"])


class OfficeCreate(BaseModel):
    """Payload for creating an office."""
    office_name: str = Field(..., max_length=100, description="Name of the office")
    location: str | None = Field(None, max_length=255, description="Location of the office")


class OfficeUpdate(BaseModel):
    """Payload for updating an office."""
    office_name: str | None = Field(None, max_length=100, description="Name of the office")
    location: str | None = Field(None, max_length=255, description="Location of the office")


class OfficeOut(BaseModel):
    """Response model for offices."""
    office_id: int
    office_name: str
    location: str | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=OfficeOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_departments")
def create_office(office: OfficeCreate, db: Session = Depends(get_db), user = Depends(PermissionChecker.require_permission("manage_departments"))):
    """
    Create a new office.
    
    - **office_name**: Must be unique across all offices.
    - **location**: Optional location of the office.
    """
    # Check if office with this name already exists
    existing = db.query(Office).filter(Office.office_name == office.office_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Office with this name already exists")
    
    db_office = Office(
        office_name=office.office_name,
        location=office.location
    )
    db.add(db_office)
    db.commit()
    db.refresh(db_office)
    return db_office


@router.get("/", response_model=List[OfficeOut])
@has_permission("view_departments")
def list_offices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(PermissionChecker.require_permission("view_departments"))):
    """
    Retrieve a paginated list of offices.
    """
    offices = db.query(Office).offset(skip).limit(limit).all()
    return offices


@router.get("/{office_id}", response_model=OfficeOut)
@has_permission("view_departments")
def get_office(office_id: int, db: Session = Depends(get_db), user = Depends(PermissionChecker.require_permission("view_departments"))):
    """
    Get a single office by its ID.
    """
    office = db.query(Office).filter(Office.office_id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    return office


@router.put("/{office_id}", response_model=OfficeOut)
@has_permission("manage_departments")
def update_office(office_id: int, office_update: OfficeUpdate, db: Session = Depends(get_db), user = Depends(PermissionChecker.require_permission("manage_departments"))):
    """
    Update an existing office.
    """
    office = db.query(Office).filter(Office.office_id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    
    # Update fields if provided
    update_data = office_update.model_dump(exclude_unset=True)
    
    # Check for duplicate office name if office_name is being updated
    if 'office_name' in update_data:
        existing = db.query(Office).filter(
            Office.office_name == update_data['office_name'],
            Office.office_id != office_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Office with this name already exists")
    
    for attr, value in update_data.items():
        setattr(office, attr, value)
    
    db.commit()
    db.refresh(office)
    return office


@router.delete("/{office_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_departments")
def delete_office(office_id: int, db: Session = Depends(get_db), user = Depends(PermissionChecker.require_permission("manage_departments"))):
    """
    Delete an office.
    """
    office = db.query(Office).filter(Office.office_id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    
    # Check if any employees are assigned to this office
    from backend.models import Employee
    employees_with_office = db.query(Employee).filter(Employee.office_id == office_id).count()
    if employees_with_office > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete office: {employees_with_office} employees are assigned to this office")
    
    db.delete(office)
    db.commit()
    return