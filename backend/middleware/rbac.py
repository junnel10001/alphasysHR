"""
RBAC Middleware and Decorators

Provides permission validation middleware and decorators for route handlers.
"""

from functools import wraps
from typing import List, Callable, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User, Permission, Role, RolePermission

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
    from main import SECRET_KEY, ALGORITHM
    import jwt
    
    try:
        # Decode the JWT token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except jwt.PyJWTError:
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
        async def wrapper(*args, **kwargs):
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
            
            return await func(*args, **kwargs)
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
        async def wrapper(*args, **kwargs):
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
            
            return await func(*args, **kwargs)
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
    print(f'DEBUG: user_has_permission called with user_id={user.user_id}, role_id={user.role_id}, role_name={user.role_name}, permission_name={permission_name}')
    
    # If role_id is None, try to use role_name to find the role
    if user.role_id is None and user.role_name:
        print(f'DEBUG: role_id is None, using role_name={user.role_name} to find role')
        role = db.query(Role).filter(Role.role_name == user.role_name).first()
        if role:
            print(f'DEBUG: Found role: {role} with role_id={role.role_id}')
            # Use the found role_id for permission check
            role_id = role.role_id
        else:
            print(f'DEBUG: No role found with name {user.role_name}')
            return False
    elif user.role_id is not None:
        role_id = user.role_id
    else:
        print(f'DEBUG: No role_id or role_name available')
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
    
    print(f'DEBUG: Query returned {len(permissions)} permissions')
    for p in permissions:
        print(f'DEBUG: Found permission: {p.permission_name}')
    
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
            if not user_has_permission(user, permission_name, db):
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
            # Get the user using the current database session
            from main import SECRET_KEY, ALGORITHM
            import jwt
            
            try:
                # Decode the JWT token
                payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                # Get user from the same database session with explicit join to load role
                print(f'DEBUG: Looking for user with username: {username}')
                from sqlalchemy.orm import joinedload
                user = db.query(User).options(joinedload(User.role_obj)).filter(User.username == username).first()
                print(f'DEBUG: Found user: {user}')
                if user:
                    print(f'DEBUG: User role_id: {user.role_id}')
                    print(f'DEBUG: User role_name: {user.role_name}')
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                # Check permission using the same database session
                if not user_has_permission(user, permission_name, db):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission_name}' required"
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
            if not user_has_role(user, role_name):
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
            if not user_has_role(user, role_name):
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