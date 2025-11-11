"""
Permissions Router

Provides CRUD endpoints for managing permissions.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Permission, Role, RolePermission, User
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission, has_role

router = APIRouter(prefix="/permissions", tags=["permissions"])


class PermissionCreate(BaseModel):
    """Payload for creating a permission."""
    permission_name: str = Field(..., max_length=50, description="Name of the permission")
    description: str = Field(..., description="Description of the permission")


class PermissionUpdate(BaseModel):
    """Payload for updating a permission."""
    permission_name: str | None = Field(None, max_length=50, description="Name of the permission")
    description: str | None = Field(None, description="Description of the permission")


class PermissionOut(BaseModel):
    """Response model for permissions."""
    permission_id: int
    permission_name: str
    description: str

    model_config = {"from_attributes": True}


@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_permissions")
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Create a new permission.
    
    - **permission_name**: Must be unique across all permissions.
    - **description**: Detailed description of what the permission allows.
    """
    # Check if permission with this name already exists
    existing = db.query(Permission).filter(Permission.permission_name == permission.permission_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission with this name already exists")
    
    db_permission = Permission(
        permission_name=permission.permission_name,
        description=permission.description
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


@router.get("/", response_model=List[PermissionOut])
@has_permission("manage_permissions")
def list_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Retrieve a paginated list of permissions.
    """
    permissions = db.query(Permission).offset(skip).limit(limit).all()
    return permissions


@router.get("/{permission_id}", response_model=PermissionOut)
@has_permission("manage_permissions")
def get_permission(permission_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Get a single permission by its ID.
    """
    permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.put("/{permission_id}", response_model=PermissionOut)
@has_permission("manage_permissions")
def update_permission(permission_id: int, permission_update: PermissionUpdate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Update an existing permission.
    """
    permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Update fields if provided
    update_data = permission_update.model_dump(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(permission, attr, value)
    
    db.commit()
    db.refresh(permission)
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_permissions")
def delete_permission(permission_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Delete a permission.
    """
    permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()
    return