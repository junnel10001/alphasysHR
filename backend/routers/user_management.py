"""
User Management Router

Provides endpoints for user role assignment and deactivation.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.models import User, Role, UserRole, ActivityLog, Employee
from sqlalchemy.orm import joinedload
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/user-management", tags=["user-management"])


class UserRoleAssignment(BaseModel):
    """Payload for assigning roles to a user."""
    user_id: int = Field(..., description="ID of the user")
    role_ids: List[int] = Field(..., description="List of role IDs to assign to the user")


class UserDeactivation(BaseModel):
    """Payload for deactivating a user."""
    user_id: int = Field(..., description="ID of the user to deactivate")
    reason: str = Field(..., description="Reason for deactivation")


class UserRoleOut(BaseModel):
    """Response model for user role assignments."""
    user_id: int
    username: str
    full_name: str
    email: str
    roles: List[dict]
    status: str

    model_config = {"from_attributes": True}


class UserSummaryOut(BaseModel):
    """Response model for user summary."""
    user_id: int
    username: str
    full_name: str
    email: str
    role_name: str
    status: str
    date_hired: str

    model_config = {"from_attributes": True}


@router.get("/users", response_model=List[UserSummaryOut])
@has_permission("manage_users")
def list_users_for_management(
    skip: int = 0, 
    limit: int = 100,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_users"))
):
    """
    Retrieve a paginated list of users for management purposes.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **status_filter**: Filter users by status (active/inactive)
    - **role_filter**: Filter users by role name
    - **search**: Search users by name, username, or email
    """
    query = db.query(User).outerjoin(Employee, User.user_id == Employee.employee_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    if role_filter:
        query = query.filter(User.role_name == role_filter)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    # Format response to get date_hired from Employee table
    formatted_users = []
    for user in users:
        # Get date_hired from Employee table if available, otherwise from User table as fallback
        date_hired = None
        if hasattr(user, '_fields') and 'date_hired' in user._fields:
            # This is a direct query result
            date_hired = user.date_hired if user.date_hired else "N/A"
        else:
            # This is a joined result, check employee relationship
            employee = db.query(Employee).filter(Employee.employee_id == user.user_id).first()
            date_hired = employee.date_hired if employee and employee.date_hired else "N/A"
        
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "full_name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "role_name": user.role_name,
            "status": user.status,
            "date_hired": date_hired.strftime('%Y-%m-%d') if hasattr(date_hired, 'strftime') else str(date_hired)
        }
        formatted_users.append(user_data)
    
    return formatted_users


@router.get("/users/{user_id}/roles", response_model=UserRoleOut)
@has_permission("manage_user_roles")
def get_user_roles(
    user_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_user_roles"))
):
    """
    Get a user's current role assignments.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's roles with permissions
    roles_data = []
    for role in user.roles_m2m:
        roles_data.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "permissions": [
                {
                    "permission_id": perm.permission_id,
                    "permission_name": perm.permission_name,
                    "description": perm.description
                }
                for perm in role.permissions
            ]
        })
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "full_name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "roles": roles_data,
        "status": user.status
    }


@router.post("/users/assign-roles")
@has_permission("manage_user_roles")
def assign_user_roles(
    assignment: UserRoleAssignment,
    db: Session = Depends(get_db), 
    current_user = Depends(PermissionChecker.require_permission("manage_user_roles"))
):
    """
    Assign roles to a user.
    
    - **user_id**: ID of the user to assign roles to
    - **role_ids**: List of role IDs to assign
    """
    user = db.query(User).filter(User.user_id == assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate all role IDs exist
    valid_roles = db.query(Role).filter(Role.role_id.in_(assignment.role_ids)).all()
    valid_role_ids = {role.role_id for role in valid_roles}
    
    invalid_ids = set(assignment.role_ids) - valid_role_ids
    if invalid_ids:
        raise HTTPException(status_code=400, detail=f"Roles not found: {list(invalid_ids)}")
    
    # Remove existing role assignments
    db.query(UserRole).filter(UserRole.user_id == assignment.user_id).delete()
    
    # Add new role assignments
    for role_id in assignment.role_ids:
        user_role = UserRole(user_id=assignment.user_id, role_id=role_id)
        db.add(user_role)
    
    db.commit()
    
    # Log the action
    activity_log = ActivityLog(
        user_id=current_user.user_id,
        action=f"Assigned roles {[role.role_name for role in valid_roles]} to user {user.username}"
    )
    db.add(activity_log)
    db.commit()
    
    return {"message": f"Successfully assigned {len(assignment.role_ids)} roles to user {user.username}"}


@router.post("/users/deactivate")
@has_permission("deactivate_users")
def deactivate_user(
    deactivation: UserDeactivation,
    db: Session = Depends(get_db), 
    current_user = Depends(PermissionChecker.require_permission("deactivate_users"))
):
    """
    Deactivate a user account.
    
    - **user_id**: ID of the user to deactivate
    - **reason**: Reason for deactivation
    """
    user = db.query(User).filter(User.user_id == deactivation.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status == "inactive":
        raise HTTPException(status_code=400, detail="User is already inactive")
    
    # Prevent self-deactivation
    if deactivation.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    # Update user status
    user.status = "inactive"
    db.commit()
    
    # Log the action
    activity_log = ActivityLog(
        user_id=current_user.user_id,
        action=f"Deactivated user {user.username}. Reason: {deactivation.reason}"
    )
    db.add(activity_log)
    db.commit()
    
    return {"message": f"Successfully deactivated user {user.username}"}


@router.post("/users/{user_id}/activate")
@has_permission("deactivate_users")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db), 
    current_user = Depends(PermissionChecker.require_permission("deactivate_users"))
):
    """
    Activate a user account.
    
    - **user_id**: ID of the user to activate
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status == "active":
        raise HTTPException(status_code=400, detail="User is already active")
    
    # Update user status
    user.status = "active"
    db.commit()
    
    # Log the action
    activity_log = ActivityLog(
        user_id=current_user.user_id,
        action=f"Activated user {user.username}"
    )
    db.add(activity_log)
    db.commit()
    
    return {"message": f"Successfully activated user {user.username}"}


@router.get("/roles/summary")
@has_permission("manage_user_roles")
def get_roles_summary(
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("manage_user_roles"))
):
    """
    Get a summary of all roles with user counts.
    """
    roles = db.query(Role).all()
    roles_summary = []
    
    for role in roles:
        # Count users assigned to this role
        user_count = db.query(UserRole).filter(UserRole.role_id == role.role_id).count()
        
        roles_summary.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "user_count": user_count,
            "permissions_count": len(role.permissions)
        })
    
    return roles_summary