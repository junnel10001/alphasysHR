"""
RBAC System Tests

Comprehensive tests for the RBAC system including permissions, roles,
and permission validation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.main import app
from backend.database import get_db
from backend.models import Base, User, Role, Permission, RolePermission
from backend.utils.rbac import RBACUtils

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rbac.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    # Seed the RBAC data
    db = TestingSessionLocal()
    try:
        RBACUtils.seed_default_permissions(db)
        RBACUtils.seed_default_roles(db)
        yield db
    finally:
        db.close()
        # Drop the tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash="hashedpassword",
        role_name="employee",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        hourly_rate=15.00,
        date_hired=date(2023, 1, 1),
        status="active"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_admin(test_db):
    """Create a test admin user."""
    admin = User(
        username="admin",
        password_hash="hashedpassword",
        role_name="admin",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        hourly_rate=25.00,
        date_hired=date(2023, 1, 1),
        status="active"
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin

class TestRBACPermissions:
    """Test permission CRUD operations."""
    
    def test_create_permission(self, test_db):
        """Test creating a permission."""
        permission_data = {
            "permission_name": "test_permission",
            "description": "Test permission description"
        }
        
        response = client.post("/permissions/", json=permission_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["permission_name"] == "test_permission"
        assert data["description"] == "Test permission description"
    
    def test_create_permission_duplicate(self, test_db):
        """Test creating a duplicate permission."""
        # Create a permission first
        permission = RBACUtils.create_permission(test_db, "test_permission", "Test description")
        
        # Try to create the same permission again
        permission_data = {
            "permission_name": "test_permission",
            "description": "Test permission description"
        }
        
        response = client.post("/permissions/", json=permission_data)
        assert response.status_code == 400
    
    def test_get_permissions(self, test_db):
        """Test getting all permissions."""
        # Create some permissions
        RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        RBACUtils.create_permission(test_db, "perm2", "Permission 2")
        
        response = client.get("/permissions/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 2
        assert any(p["permission_name"] == "perm1" for p in data)
        assert any(p["permission_name"] == "perm2" for p in data)
    
    def test_get_permission_by_id(self, test_db):
        """Test getting a permission by ID."""
        permission = RBACUtils.create_permission(test_db, "test_permission", "Test description")
        
        response = client.get(f"/permissions/{permission.permission_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["permission_id"] == permission.permission_id
        assert data["permission_name"] == "test_permission"
    
    def test_get_permission_not_found(self, test_db):
        """Test getting a non-existent permission."""
        response = client.get("/permissions/999")
        assert response.status_code == 404
    
    def test_update_permission(self, test_db):
        """Test updating a permission."""
        permission = RBACUtils.create_permission(test_db, "test_permission", "Test description")
        
        update_data = {
            "permission_name": "updated_permission",
            "description": "Updated description"
        }
        
        response = client.put(f"/permissions/{permission.permission_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["permission_name"] == "updated_permission"
        assert data["description"] == "Updated description"
    
    def test_delete_permission(self, test_db):
        """Test deleting a permission."""
        permission = RBACUtils.create_permission(test_db, "test_permission", "Test description")
        
        response = client.delete(f"/permissions/{permission.permission_id}")
        assert response.status_code == 204
        
        # Verify the permission is deleted
        response = client.get(f"/permissions/{permission.permission_id}")
        assert response.status_code == 404

class TestRBACRoles:
    """Test role CRUD operations."""
    
    def test_create_role(self, test_db):
        """Test creating a role."""
        role_data = {
            "role_name": "test_role",
            "description": "Test role description"
        }
        
        response = client.post("/roles/", json=role_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["role_name"] == "test_role"
        assert data["description"] == "Test role description"
    
    def test_create_role_duplicate(self, test_db):
        """Test creating a duplicate role."""
        # Create a role first
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Try to create the same role again
        role_data = {
            "role_name": "test_role",
            "description": "Test role description"
        }
        
        response = client.post("/roles/", json=role_data)
        assert response.status_code == 400
    
    def test_get_roles(self, test_db):
        """Test getting all roles."""
        # Create some roles
        RBACUtils.create_role(test_db, "role1", "Role 1")
        RBACUtils.create_role(test_db, "role2", "Role 2")
        
        response = client.get("/roles/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 2
        assert any(r["role_name"] == "role1" for r in data)
        assert any(r["role_name"] == "role2" for r in data)
    
    def test_get_role_by_id(self, test_db):
        """Test getting a role by ID."""
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        response = client.get(f"/roles/{role.role_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["role_id"] == role.role_id
        assert data["role_name"] == "test_role"
    
    def test_update_role(self, test_db):
        """Test updating a role."""
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        update_data = {
            "role_name": "updated_role",
            "description": "Updated description"
        }
        
        response = client.put(f"/roles/{role.role_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role_name"] == "updated_role"
        assert data["description"] == "Updated description"
    
    def test_delete_role(self, test_db):
        """Test deleting a role."""
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        response = client.delete(f"/roles/{role.role_id}")
        assert response.status_code == 204
        
        # Verify the role is deleted
        response = client.get(f"/roles/{role.role_id}")
        assert response.status_code == 404
    
    def test_delete_role_with_users(self, test_db, test_user):
        """Test deleting a role that has users assigned."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Assign the user to this role
        test_user.role_id = role.role_id
        test_db.commit()
        
        # Try to delete the role
        response = client.delete(f"/roles/{role.role_id}")
        assert response.status_code == 400

class TestRBACRolePermissions:
    """Test role-permission assignment operations."""
    
    def test_assign_permissions_to_role(self, test_db):
        """Test assigning permissions to a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create some permissions
        perm1 = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        perm2 = RBACUtils.create_permission(test_db, "perm2", "Permission 2")
        
        # Assign permissions to the role
        assignment_data = {
            "permission_ids": [perm1.permission_id, perm2.permission_id]
        }
        
        response = client.post(f"/roles/{role.role_id}/permissions", json=assignment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "Successfully assigned" in data["message"]
        assert data["message"].endswith("permissions to role test_role")
    
    def test_assign_permissions_to_nonexistent_role(self, test_db):
        """Test assigning permissions to a non-existent role."""
        # Create a permission
        perm = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        
        assignment_data = {
            "permission_ids": [perm.permission_id]
        }
        
        response = client.post("/roles/999/permissions", json=assignment_data)
        assert response.status_code == 404
    
    def test_assign_nonexistent_permissions(self, test_db):
        """Test assigning non-existent permissions to a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        assignment_data = {
            "permission_ids": [999]  # Non-existent permission
        }
        
        response = client.post(f"/roles/{role.role_id}/permissions", json=assignment_data)
        assert response.status_code == 404
    
    def test_remove_permission_from_role(self, test_db):
        """Test removing a permission from a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create a permission
        perm = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        
        # Assign the permission to the role
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm.permission_id)
        
        # Remove the permission from the role
        response = client.delete(f"/roles/{role.role_id}/permissions/{perm.permission_id}")
        assert response.status_code == 204
        
        # Verify the permission is removed
        role_permissions = test_db.query(RolePermission).filter(
            RolePermission.role_id == role.role_id
        ).all()
        assert len(role_permissions) == 0
    
    def test_remove_nonexistent_permission(self, test_db):
        """Test removing a non-existent permission from a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        response = client.delete(f"/roles/{role.role_id}/permissions/999")
        assert response.status_code == 404
    
    def test_remove_permission_from_nonexistent_role(self, test_db):
        """Test removing a permission from a non-existent role."""
        # Create a permission
        perm = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        
        response = client.delete("/roles/999/permissions/1")
        assert response.status_code == 404
    
    def test_get_role_permissions(self, test_db):
        """Test getting permissions for a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create some permissions
        perm1 = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        perm2 = RBACUtils.create_permission(test_db, "perm2", "Permission 2")
        
        # Assign permissions to the role
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm1.permission_id)
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm2.permission_id)
        
        response = client.get(f"/roles/{role.role_id}/permissions")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert any(p["permission_name"] == "perm1" for p in data)
        assert any(p["permission_name"] == "perm2" for p in data)

class TestRBACUtils:
    """Test RBAC utility functions."""
    
    def test_user_has_permission(self, test_db):
        """Test checking if a user has a permission."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create a permission
        perm = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        
        # Assign permission to role
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm.permission_id)
        
        # Create a user with this role
        user = User(
            username="testuser",
            password_hash="hashedpassword",
            role_name="test_role",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            hourly_rate=15.00,
            date_hired=date(2023, 1, 1),
            status="active",
            role_id=role.role_id
        )
        test_db.add(user)
        test_db.commit()
        
        # Test user has permission
        assert RBACUtils.user_has_permission(user, "perm1", test_db) is True
        
        # Test user doesn't have permission
        assert RBACUtils.user_has_permission(user, "nonexistent", test_db) is False
    
    def test_user_has_role(self, test_db):
        """Test checking if a user has a role."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create a user with this role
        user = User(
            username="testuser",
            password_hash="hashedpassword",
            role_name="test_role",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            hourly_rate=15.00,
            date_hired=date(2023, 1, 1),
            status="active",
            role_id=role.role_id
        )
        test_db.add(user)
        test_db.commit()
        
        # Test user has role
        assert RBACUtils.user_has_role(user, "test_role") is True
        
        # Test user doesn't have role
        assert RBACUtils.user_has_role(user, "nonexistent") is False
    
    def test_get_user_permissions(self, test_db):
        """Test getting user permissions."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create some permissions
        perm1 = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        perm2 = RBACUtils.create_permission(test_db, "perm2", "Permission 2")
        
        # Assign permissions to role
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm1.permission_id)
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm2.permission_id)
        
        # Create a user with this role
        user = User(
            username="testuser",
            password_hash="hashedpassword",
            role_name="test_role",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            hourly_rate=15.00,
            date_hired=date(2023, 1, 1),
            status="active",
            role_id=role.role_id
        )
        test_db.add(user)
        test_db.commit()
        
        # Test getting user permissions
        permissions = RBACUtils.get_user_permissions(user, test_db)
        assert len(permissions) == 2
        assert any(p.permission_name == "perm1" for p in permissions)
        assert any(p.permission_name == "perm2" for p in permissions)
    
    def test_get_user_permission_names(self, test_db):
        """Test getting user permission names."""
        # Create a role
        role = RBACUtils.create_role(test_db, "test_role", "Test description")
        
        # Create some permissions
        perm1 = RBACUtils.create_permission(test_db, "perm1", "Permission 1")
        perm2 = RBACUtils.create_permission(test_db, "perm2", "Permission 2")
        
        # Assign permissions to role
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm1.permission_id)
        RBACUtils.assign_permission_to_role(test_db, role.role_id, perm2.permission_id)
        
        # Create a user with this role
        user = User(
            username="testuser",
            password_hash="hashedpassword",
            role_name="test_role",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            hourly_rate=15.00,
            date_hired=date(2023, 1, 1),
            status="active",
            role_id=role.role_id
        )
        test_db.add(user)
        test_db.commit()
        
        # Test getting user permission names
        permission_names = RBACUtils.get_user_permission_names(user, test_db)
        assert len(permission_names) == 2
        assert "perm1" in permission_names
        assert "perm2" in permission_names

if __name__ == "__main__":
    pytest.main([__file__])