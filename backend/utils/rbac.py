"""
RBAC Utility Functions

Provides utility functions for permission checking and role management.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import User, Permission, Role, RolePermission


class RBACUtils:
    """
    Utility class for RBAC operations.
    """
    
    @staticmethod
    def create_permission(db: Session, permission_name: str, description: str) -> Permission:
        """
        Create a new permission.
        
        Args:
            db: Database session
            permission_name: Name of the permission
            description: Description of the permission
            
        Returns:
            Permission: The created permission
            
        Raises:
            HTTPException: If permission with same name already exists
        """
        from fastapi import HTTPException, status
        
        existing = db.query(Permission).filter(Permission.permission_name == permission_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Permission with this name already exists")
        
        permission = Permission(
            permission_name=permission_name,
            description=description
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def create_role(db: Session, role_name: str, description: str = None) -> Role:
        """
        Create a new role.
        
        Args:
            db: Database session
            role_name: Name of the role
            description: Description of the role
            
        Returns:
            Role: The created role
            
        Raises:
            HTTPException: If role with same name already exists
        """
        from fastapi import HTTPException, status
        
        existing = db.query(Role).filter(Role.role_name == role_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
        
        role = Role(
            role_name=role_name,
            description=description
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> RolePermission:
        """
        Assign a permission to a role.
        
        Args:
            db: Database session
            role_id: ID of the role
            permission_id: ID of the permission
            
        Returns:
            RolePermission: The created role-permission association
            
        Raises:
            HTTPException: If role or permission not found, or already assigned
        """
        from fastapi import HTTPException, status
        
        # Check if role exists
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if permission exists
        permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Check if already assigned
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Permission already assigned to role")
        
        # Create assignment
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission
    
    @staticmethod
    def remove_permission_from_role(db: Session, role_id: int, permission_id: int) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            db: Database session
            role_id: ID of the role
            permission_id: ID of the permission
            
        Returns:
            bool: True if successfully removed, False if not found
            
        Raises:
            HTTPException: If role or permission not found
        """
        from fastapi import HTTPException, status
        
        # Check if role exists
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if permission exists
        permission = db.query(Permission).filter(Permission.permission_id == permission_id).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Remove assignment
        role_permission = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        
        if role_permission:
            db.delete(role_permission)
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_user_permissions(user: User, db: Session) -> List[Permission]:
        """
        Get all permissions for a user.
        
        Args:
            user: The user
            db: Database session
            
        Returns:
            List[Permission]: List of permissions
        """
        return db.query(Permission).join(RolePermission).join(Role).filter(
            Role.role_id == user.role_id
        ).all()
    
    @staticmethod
    def get_user_permission_names(user: User, db: Session) -> List[str]:
        """
        Get all permission names for a user.
        
        Args:
            user: The user
            db: Database session
            
        Returns:
            List[str]: List of permission names
        """
        permissions = RBACUtils.get_user_permissions(user, db)
        return [p.permission_name for p in permissions]
    
    @staticmethod
    def get_role_permissions(role: Role, db: Session) -> List[Permission]:
        """
        Get all permissions for a role.
        
        Args:
            role: The role
            db: Database session
            
        Returns:
            List[Permission]: List of permissions
        """
        return db.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == role.role_id
        ).all()
    
    @staticmethod
    def get_role_permission_names(role: Role, db: Session) -> List[str]:
        """
        Get all permission names for a role.
        
        Args:
            role: The role
            db: Database session
            
        Returns:
            List[str]: List of permission names
        """
        permissions = RBACUtils.get_role_permissions(role, db)
        return [p.permission_name for p in permissions]
    
    @staticmethod
    def user_has_permission(user: User, permission_name: str, db: Session) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: The user to check
            permission_name: The permission name to check for
            db: Database session
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        permission = db.query(Permission).filter(
            Permission.permission_name == permission_name
        ).first()
        
        if not permission:
            return False
        
        role_permission = db.query(RolePermission).filter(
            RolePermission.role_id == user.role_id,
            RolePermission.permission_id == permission.permission_id
        ).first()
        
        return role_permission is not None
    
    @staticmethod
    def user_has_role(user: User, role_name: str) -> bool:
        """
        Check if a user has a specific role.
        
        Args:
            user: The user to check
            role_name: The role name to check for
            
        Returns:
            bool: True if user has role, False otherwise
        """
        return user.role_name == role_name
    
    @staticmethod
    def get_users_with_permission(permission_name: str, db: Session) -> List[User]:
        """
        Get all users with a specific permission.
        
        Args:
            permission_name: The permission name
            db: Database session
            
        Returns:
            List[User]: List of users with the permission
        """
        permission = db.query(Permission).filter(
            Permission.permission_name == permission_name
        ).first()
        
        if not permission:
            return []
        
        return db.query(User).join(Role).join(RolePermission).filter(
            RolePermission.permission_id == permission.permission_id
        ).all()
    
    @staticmethod
    def get_users_with_role(role_name: str, db: Session) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role_name: The role name
            db: Database session
            
        Returns:
            List[User]: List of users with the role
        """
        return db.query(User).filter(User.role_name == role_name).all()
    
    @staticmethod
    def get_permission_hierarchy(db: Session) -> Dict[str, List[str]]:
        """
        Get the permission hierarchy (which permissions are assigned to which roles).
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping role names to lists of permission names
        """
        hierarchy = {}
        
        roles = db.query(Role).all()
        for role in roles:
            permissions = RBACUtils.get_role_permission_names(role, db)
            hierarchy[role.role_name] = permissions
        
        return hierarchy
    
    @staticmethod
    def seed_default_permissions(db: Session) -> List[Permission]:
        """
        Seed default permissions.
        
        Args:
            db: Database session
            
        Returns:
            List[Permission]: List of created permissions
        """
        default_permissions = [
            ("create_employee", "Create new employees"),
            ("read_employee", "View employee information"),
            ("update_employee", "Update employee information"),
            ("delete_employee", "Delete employee records"),
            ("create_attendance", "Create attendance records"),
            ("read_attendance", "View attendance records"),
            ("update_attendance", "Update attendance records"),
            ("delete_attendance", "Delete attendance records"),
            ("create_leave", "Create leave requests"),
            ("read_leave", "View leave requests"),
            ("update_leave", "Update leave requests"),
            ("delete_leave", "Delete leave requests"),
            ("create_payroll", "Create payroll records"),
            ("read_payroll", "View payroll records"),
            ("update_payroll", "Update payroll records"),
            ("delete_payroll", "Delete payroll records"),
            ("manage_permissions", "Manage system permissions"),
            ("manage_roles", "Manage system roles"),
            ("manage_users", "Manage system users"),
            ("admin_access", "Full administrative access"),
            ("export_data", "Export HR data in various formats"),
            ("download_files", "Download exported files"),
            ("view_files", "View exported files in browser"),
            ("employee_export", "Export employee data"),
            ("payroll_export", "Export payroll data"),
            ("overtime_export", "Export overtime data"),
            ("activity_export", "Export activity data"),
            ("cleanup_exports", "Clean up old export files")
        ]
        
        created_permissions = []
        for perm_name, perm_desc in default_permissions:
            if not db.query(Permission).filter(Permission.permission_name == perm_name).first():
                permission = RBACUtils.create_permission(db, perm_name, perm_desc)
                created_permissions.append(permission)
        
        return created_permissions
    
    @staticmethod
    def seed_default_roles(db: Session) -> List[Role]:
        """
        Seed default roles with default permissions.
        
        Args:
            db: Database session
            
        Returns:
            List[Role]: List of created roles
        """
        # Create default roles
        admin_role = None
        manager_role = None
        employee_role = None
        
        # Admin role
        if not db.query(Role).filter(Role.role_name == "admin").first():
            admin_role = RBACUtils.create_role(db, "admin", "System administrator with full access")
        
        # Manager role
        if not db.query(Role).filter(Role.role_name == "manager").first():
            manager_role = RBACUtils.create_role(db, "manager", "Department manager with management access")
        
        # Employee role
        if not db.query(Role).filter(Role.role_name == "employee").first():
            employee_role = RBACUtils.create_role(db, "employee", "Regular employee with basic access")
        
        created_roles = []
        for role in [admin_role, manager_role, employee_role]:
            if role:
                created_roles.append(role)
        
        # Assign permissions to roles
        admin_permissions = db.query(Permission).filter(
            Permission.permission_name.in_([
                "admin_access", "manage_permissions", "manage_roles", "manage_users",
                "create_employee", "read_employee", "update_employee", "delete_employee",
                "create_attendance", "read_attendance", "update_attendance", "delete_attendance",
                "create_leave", "read_leave", "update_leave", "delete_leave",
                "create_payroll", "read_payroll", "update_payroll", "delete_payroll",
                "export_data", "download_files", "view_files", "employee_export",
                "payroll_export", "overtime_export", "activity_export", "cleanup_exports"
            ])
        ).all()
        
        manager_permissions = db.query(Permission).filter(
            Permission.permission_name.in_([
                "read_employee", "update_employee",
                "create_attendance", "read_attendance", "update_attendance", "delete_attendance",
                "create_leave", "read_leave", "update_leave", "delete_leave",
                "create_payroll", "read_payroll", "update_payroll", "delete_payroll",
                "export_data", "download_files", "view_files", "employee_export",
                "payroll_export", "overtime_export", "activity_export"
            ])
        ).all()
        
        employee_permissions = db.query(Permission).filter(
            Permission.permission_name.in_([
                "read_employee", "read_attendance", "read_leave", "read_payroll",
                "view_files"
            ])
        ).all()
        
        # Assign permissions to admin role
        if admin_role:
            for permission in admin_permissions:
                RBACUtils.assign_permission_to_role(db, admin_role.role_id, permission.permission_id)
        
        # Assign permissions to manager role
        if manager_role:
            for permission in manager_permissions:
                RBACUtils.assign_permission_to_role(db, manager_role.role_id, permission.permission_id)
        
        # Assign permissions to employee role
        if employee_role:
            for permission in employee_permissions:
                RBACUtils.assign_permission_to_role(db, employee_role.role_id, permission.permission_id)
        
        return created_roles