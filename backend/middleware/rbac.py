"""
RBAC Middleware and Decorators

Provides permission validation middleware and decorators for route handlers.
"""

# Permission constants for employee management
CREATE_EMPLOYEE = "create_employee"
UPDATE_EMPLOYEE = "update_employee"
DELETE_EMPLOYEE = "delete_employee"

from functools import wraps
from typing import List, Callable, Any
from fastapi import HTTPException, status, Depends
from backend.config import JWT_SECRET, JWT_ALGORITHM
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Permission, Role, RolePermission
import jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Import directly to avoid circular imports
    
    try:
        # Decode the JWT token using the shared secret and algorithm defined in backend.main
        # Decode the JWT token using the shared secret and algorithm defined in backend.config
        from backend.config import JWT_SECRET, JWT_ALGORITHM
        # Decode the JWT token using the shared secret and algorithm defined in backend.main
        # Decode the JWT token using the shared secret and algorithm defined in backend.main
        # Decode the JWT token using the shared secret and algorithm defined in backend.main
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database - try username first, then email as fallback
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            # Fallback: try to find by email
            user = db.query(User).filter(User.email == username).first()
            
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def has_permission(permission_name: str):
    """
    Decorator to check if the current user has a specific permission.
    
    Args:
        permission_name: The name of the permission to check
        
    Returns:
        Decorator function that checks permission
    """
    def permission_checker(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user from kwargs (assuming it's passed as user parameter)
            user = kwargs.get('user') or kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get database session
            db = kwargs.get('db')
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check if user has the permission
            if not user_has_permission(user, permission_name, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' required"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return permission_checker


def has_role(role_name: str):
    """
    Decorator to check if the current user has a specific role.
    
    Args:
        role_name: The name of the role to check
        
    Returns:
        Decorator function that checks role
    """
    def role_checker(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user from kwargs (assuming it's passed as user parameter)
            user = kwargs.get('user') or kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user has the role
            if user.role_name != role_name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role_name}' required"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return role_checker


def user_has_permission(user: User, permission_name: str, db: Session) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user to check
        permission_name: The name of the permission
        db: Database session
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    # If role_id is None, try to use role_name to find the role
    if user.role_id is None and user.role_name:
        role = db.query(Role).filter(Role.role_name == user.role_name).first()
        if role:
            role_id = role.role_id
        else:
            return False
    elif user.role_id is not None:
        role_id = user.role_id
    else:
        return False
    
    # Get all permissions for the user's role through the association table
    permissions = db.query(Permission).join(
        RolePermission, Permission.permission_id == RolePermission.permission_id
    ).join(
        Role, RolePermission.role_id == Role.role_id
    ).filter(
        Role.role_id == role_id,
        Permission.permission_name == permission_name
    ).all()
    
    return len(permissions) > 0


def user_has_role(user: User, role_name: str) -> bool:
    """
    Check if a user has a specific role.
    
    Args:
        user: The user to check
        role_name: The name of the role
        
    Returns:
        bool: True if user has role, False otherwise
    """
    return user.role_name == role_name


def get_user_permissions(user: User, db: Session) -> List[str]:
    """
    Get all permission names for a user.
    
    Args:
        user: The user to get permissions for
        db: Database session
        
    Returns:
        List[str]: List of permission names
    """
    permissions = db.query(Permission).join(
        RolePermission, Permission.permission_id == RolePermission.permission_id
    ).join(
        Role, RolePermission.role_id == Role.role_id
    ).filter(
        Role.role_id == user.role_id
    ).all()
    
    return [p.permission_name for p in permissions]


def get_user_roles(user: User) -> List[str]:
    """
    Get all role names for a user.
    
    Args:
        user: The user to get roles for
        
    Returns:
        List[str]: List of role names
    """
    return [user.role_name]


class PermissionChecker:
    """
    Utility class for permission checking.
    """
    
    @staticmethod
    def user_has_permission(user: User, permission_name: str, db: Session) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: The user to check
            permission_name: The name of the permission
            db: Database session
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Admin shortcuts - check for admin role first
        if getattr(user, "role_name", None) == "admin":
            return True
        # Additional shortcut: if the user's linked Role object is admin
        if getattr(user, "role_obj", None) and user.role_obj.role_name == "admin":
            return True
        
        # If role_id is None, try to use role_name to find the role
        if user.role_id is None and user.role_name:
            role = db.query(Role).filter(Role.role_name == user.role_name).first()
            if role:
                role_id = role.role_id
            else:
                return False
        elif user.role_id is not None:
            role_id = user.role_id
        else:
            return False
        
        # Get all permissions for the user's role through the association table
        permissions = db.query(Permission).join(
            RolePermission, Permission.permission_id == RolePermission.permission_id
        ).join(
            Role, RolePermission.role_id == Role.role_id
        ).filter(
            Role.role_id == role_id,
            Permission.permission_name == permission_name
        ).all()
        
        return len(permissions) > 0
    
    @staticmethod
    def require_permission(permission_name: str):
        """
        Middleware to require a specific permission.
        
        Args:
            permission_name: The name of the required permission
            
        Returns:
            Dependency function for FastAPI
        """
        async def checker(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
            user = get_current_user(credentials, db)
            if not PermissionChecker.user_has_permission(user, permission_name, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' required"
                )
            return user
        return checker
    
    @staticmethod
    def require_permission_with_db(permission_name: str):
        """
        Middleware to require a specific permission and return the database session.
        
        Args:
            permission_name: The name of the required permission
            
        Returns:
            Dependency function for FastAPI that returns (user, db)
        """
        async def checker(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> tuple[User, Session]:
            # Decode the JWT token using the shared secret
            try:
                payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                # Load the user (including role relationship) in the current DB session
                from sqlalchemy.orm import joinedload
                user = (
                    db.query(User)
                    .options(joinedload(User.role_obj))
                    .filter(User.username == username)
                    .first()
                )
                if user is None:
                    # Fallback: try to find by email
                    user = (
                        db.query(User)
                        .options(joinedload(User.role_obj))
                        .filter(User.email == username)
                        .first()
                    )
                    
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                # Verify the required permission
                if not PermissionChecker.user_has_permission(user, permission_name, db):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission_name}' required",
                    )
                return user, db
            except jwt.PyJWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return checker
    
    @staticmethod
    def require_role(role_name: str):
        """
        Middleware to require a specific role.
        
        Args:
            role_name: The name of the required role
            
        Returns:
            Dependency function for FastAPI
        """
        async def checker(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
            user = get_current_user(credentials, db)
            if not PermissionChecker.user_has_role(user, role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role_name}' required"
                )
            return user
        return checker
    
    @staticmethod
    def require_role_with_db(role_name: str):
        """
        Middleware to require a specific role and return the database session.
        
        Args:
            role_name: The name of the required role
            
        Returns:
            Dependency function for FastAPI that returns (user, db)
        """
        async def checker(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> tuple[User, Session]:
            user = get_current_user(credentials, db)
            if not PermissionChecker.user_has_role(user, role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role_name}' required"
                )
            return user, db
        return checker
    
    @staticmethod
    def get_permissions_for_user(user: User, db: Session) -> List[str]:
        """
        Get all permission names for a specific user.
        
        Args:
            user: The user to get permissions for
            db: Database session
            
        Returns:
            List[str]: List of permission names
        """
        return get_user_permissions(user, db)
    
    @staticmethod
    def get_roles_for_user(user: User) -> List[str]:
        """
        Get all role names for a specific user.
        
        Args:
            user: The user to get roles for
            
        Returns:
            List[str]: List of role names
        """
        return get_user_roles(user)