"""
Roles Router

Provides CRUD endpoints for managing roles and their permissions.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Role, Permission, RolePermission, User
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission, has_role

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleCreate(BaseModel):
    """Payload for creating a role."""
    role_name: str = Field(..., max_length=50, description="Name of the role")
    description: str | None = Field(None, description="Description of the role")


class RoleUpdate(BaseModel):
    """Payload for updating a role."""
    role_name: str | None = Field(None, max_length=50, description="Name of the role")
    description: str | None = Field(None, description="Description of the role")


class RoleOut(BaseModel):
    """Response model for roles."""
    role_id: int
    role_name: str
    description: str | None
    permissions: List[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PermissionAssignment(BaseModel):
    """Payload for assigning permissions to a role."""
    permission_ids: List[int] = Field(..., description="List of permission IDs to assign")


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
@has_permission("manage_roles")
def create_role(role: RoleCreate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_roles"))):
    """
    Create a new role.
    
    - **role_name**: Must be unique across all roles.
    - **description**: Optional description of the role.
    """
    # Check if role with this name already exists
    existing = db.query(Role).filter(Role.role_name == role.role_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    
    db_role = Role(
        role_name=role.role_name,
        description=role.description
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@router.get("/", response_model=List[RoleOut])
@has_permission("view_roles")
def list_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("view_roles"))):
    """
    Retrieve a paginated list of roles with their permissions.
    """
    roles = db.query(Role).offset(skip).limit(limit).all()
    
    # Convert database models to Pydantic-compatible format
    formatted_roles = []
    for role in roles:
        permissions = [{"permission_id": p.permission_id, "permission_name": p.permission_name, "description": p.description}
                     for p in role.permissions]
        formatted_role = {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "permissions": permissions
        }
        formatted_roles.append(formatted_role)
    
    return formatted_roles


@router.get("/{role_id}", response_model=RoleOut)
@has_permission("view_roles")
def get_role(role_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("view_roles"))):
    """
    Get a single role by its ID with its permissions.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # Convert database model to Pydantic-compatible format
    permissions = [{"permission_id": p.permission_id, "permission_name": p.permission_name, "description": p.description}
                 for p in role.permissions]
    formatted_role = {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "description": role.description,
        "permissions": permissions
    }
    return formatted_role


@router.put("/{role_id}", response_model=RoleOut)
@has_permission("manage_roles")
def update_role(role_id: int, role_update: RoleUpdate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_roles"))):
    """
    Update an existing role.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Update fields if provided
    update_data = role_update.model_dump(exclude_unset=True)
    for attr, value in update_data.items():
        setattr(role, attr, value)
    
    db.commit()
    db.refresh(role)
    # Convert database model to Pydantic-compatible format
    permissions = [{"permission_id": p.permission_id, "permission_name": p.permission_name, "description": p.description}
                 for p in role.permissions]
    formatted_role = {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "description": role.description,
        "permissions": permissions
    }
    return formatted_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_roles")
def delete_role(role_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_roles"))):
    """
    Delete a role.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if any users are assigned to this role
    users_with_role = db.query(User).filter(User.role_id == role_id).count()
    if users_with_role > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete role: {users_with_role} users are assigned to this role")
    
    db.delete(role)
    db.commit()
    return


@router.post("/{role_id}/permissions", response_model=dict)
@has_permission("manage_permissions")
def assign_permissions_to_role(
    role_id: int,
    assignment: PermissionAssignment,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("manage_permissions"))
):
    """
    Assign permissions to a role.
    
    - **role_id**: The ID of the role to assign permissions to.
    - **permission_ids**: List of permission IDs to assign to the role.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if all permission IDs exist
    permission_ids = assignment.permission_ids
    existing_permissions = db.query(Permission).filter(Permission.permission_id.in_(permission_ids)).all()
    existing_ids = {p.permission_id for p in existing_permissions}
    
    invalid_ids = set(permission_ids) - existing_ids
    if invalid_ids:
        raise HTTPException(status_code=404, detail=f"Permissions not found: {list(invalid_ids)}")
    
    # Remove existing permissions for this role
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    # Add new permissions
    for permission_id in permission_ids:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
    
    db.commit()
    return {"message": f"Successfully assigned {len(permission_ids)} permissions to role {role.role_name}"}


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("manage_permissions")
def remove_permission_from_role(role_id: int, permission_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Remove a permission from a role.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()
    
    if not role_permission:
        raise HTTPException(status_code=404, detail="Permission is not assigned to this role")
    
    db.delete(role_permission)
    db.commit()
    return


@router.get("/{role_id}/permissions", response_model=List[dict])
@has_permission("manage_permissions")
def get_role_permissions(role_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("manage_permissions"))):
    """
    Get all permissions assigned to a role.
    """
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == role_id
    ).all()
    
    return [{"permission_id": p.permission_id, "permission_name": p.permission_name, "description": p.description} for p in permissions]