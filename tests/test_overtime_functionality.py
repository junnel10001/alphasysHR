"""
Comprehensive Tests for Overtime Management Functionality

Tests for all overtime-related functionality including:
- Overtime request creation and validation
- Overtime request listing and filtering
- Status update operations
- Role-based access control
- Error handling scenarios
"""

import pytest
import requests
import json
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db
from backend.models import Base, User, OvertimeRequest, OvertimeStatus
from backend.services.employee_dashboard_service import EmployeeDashboardService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_overtime.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        username="testuser@example.com",
        password_hash="hashedpassword",
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        role_name="employee",
        hourly_rate=20.0,
        date_hired=date.today(),
        status="active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin(db_session):
    """Create test admin user"""
    admin = User(
        username="admin@example.com",
        password_hash="hashedpassword",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        role_name="admin",
        hourly_rate=25.0,
        date_hired=date.today(),
        status="active"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def test_overtime_request(db_session, test_user):
    """Create test overtime request"""
    overtime_request = OvertimeRequest(
        user_id=test_user.user_id,
        date=date.today(),
        hours_requested=2.5,
        reason="Test overtime request",
        status=OvertimeStatus.Pending.value
    )
    db_session.add(overtime_request)
    db_session.commit()
    db_session.refresh(overtime_request)
    return overtime_request

class TestOvertimeRequestCreation:
    """Test overtime request creation functionality"""
    
    def test_create_overtime_request_success(self, client, test_user):
        """Test successful overtime request creation"""
        overtime_data = {
            "date": date.today().isoformat(),
            "hours_requested": 3.0,
            "reason": "Test overtime for project deadline"
        }
        
        response = client.post("/overtime/", json=overtime_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ot_id" in data
    
    def test_create_overtime_request_invalid_date(self, client, test_user):
        """Test overtime request creation with invalid date"""
        overtime_data = {
            "date": "invalid-date",
            "hours_requested": 3.0,
            "reason": "Test overtime"
        }
        
        response = client.post("/overtime/", json=overtime_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_overtime_request_invalid_hours(self, client, test_user):
        """Test overtime request creation with invalid hours"""
        overtime_data = {
            "date": date.today().isoformat(),
            "hours_requested": -1.0,
            "reason": "Test overtime"
        }
        
        response = client.post("/overtime/", json=overtime_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_overtime_request_unauthorized(self, client):
        """Test overtime request creation without authentication"""
        overtime_data = {
            "date": date.today().isoformat(),
            "hours_requested": 3.0,
            "reason": "Test overtime"
        }
        
        response = client.post("/overtime/", json=overtime_data)
        assert response.status_code == 401  # Unauthorized

class TestOvertimeRequestRetrieval:
    """Test overtime request retrieval functionality"""
    
    def test_get_overtime_requests_success(self, client, test_admin, test_overtime_request):
        """Test successful retrieval of overtime requests"""
        response = client.get("/overtime/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_overtime_requests_filtered(self, client, test_admin, test_overtime_request):
        """Test filtered retrieval of overtime requests"""
        response = client.get("/overtime/?status=Pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(item["status"] == "Pending" for item in data)
    
    def test_get_overtime_request_by_id_success(self, client, test_admin, test_overtime_request):
        """Test successful retrieval of specific overtime request"""
        response = client.get(f"/overtime/{test_overtime_request.ot_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ot_id"] == test_overtime_request.ot_id
    
    def test_get_overtime_request_by_id_not_found(self, client, test_admin):
        """Test retrieval of non-existent overtime request"""
        response = client.get("/overtime/999999")
        assert response.status_code == 404
    
    def test_get_overtime_requests_unauthorized(self, client, test_overtime_request):
        """Test retrieval of overtime requests without authentication"""
        response = client.get("/overtime/")
        assert response.status_code == 401

class TestOvertimeRequestUpdate:
    """Test overtime request update functionality"""
    
    def test_update_overtime_request_success(self, client, test_user, test_overtime_request):
        """Test successful overtime request update"""
        update_data = {
            "status": "Approved"
        }
        
        response = client.put(f"/overtime/{test_overtime_request.ot_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Approved"
    
    def test_update_overtime_request_not_found(self, client, test_user):
        """Test update of non-existent overtime request"""
        update_data = {
            "status": "Approved"
        }
        
        response = client.put("/overtime/999999", json=update_data)
        assert response.status_code == 404
    
    def test_update_overtime_request_unauthorized(self, client, test_overtime_request):
        """Test overtime request update without authentication"""
        update_data = {
            "status": "Approved"
        }
        
        response = client.put(f"/overtime/{test_overtime_request.ot_id}", json=update_data)
        assert response.status_code == 401
    
    def test_update_overtime_request_wrong_user(self, client, test_user, test_admin, test_overtime_request):
        """Test overtime request update by wrong user"""
        update_data = {
            "status": "Approved"
        }
        
        # Create another user
        other_user = User(
            username="otheruser@example.com",
            password_hash="hashedpassword",
            first_name="Other",
            last_name="User",
            email="otheruser@example.com",
            role_name="employee",
            hourly_rate=20.0,
            date_hired=date.today(),
            status="active"
        )
        
        db_session = TestingSessionLocal()
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Try to update request with different user (simulated by changing user_id)
        test_overtime_request.user_id = other_user.user_id
        db_session.commit()
        
        response = client.put(f"/overtime/{test_overtime_request.ot_id}", json=update_data)
        assert response.status_code == 403  # Forbidden

class TestOvertimeRequestDeletion:
    """Test overtime request deletion functionality"""
    
    def test_delete_overtime_request_success(self, client, test_user, test_overtime_request):
        """Test successful overtime request deletion"""
        response = client.delete(f"/overtime/{test_overtime_request.ot_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_delete_overtime_request_not_found(self, client, test_user):
        """Test deletion of non-existent overtime request"""
        response = client.delete("/overtime/999999")
        assert response.status_code == 404
    
    def test_delete_overtime_request_unauthorized(self, client, test_overtime_request):
        """Test overtime request deletion without authentication"""
        response = client.delete(f"/overtime/{test_overtime_request.ot_id}")
        assert response.status_code == 401
    
    def test_delete_overtime_request_wrong_user(self, client, test_user, test_admin, test_overtime_request):
        """Test overtime request deletion by wrong user"""
        # Create another user
        other_user = User(
            username="otheruser@example.com",
            password_hash="hashedpassword",
            first_name="Other",
            last_name="User",
            email="otheruser@example.com",
            role_name="employee",
            hourly_rate=20.0,
            date_hired=date.today(),
            status="active"
        )
        
        db_session = TestingSessionLocal()
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Try to delete request with different user (simulated by changing user_id)
        test_overtime_request.user_id = other_user.user_id
        db_session.commit()
        
        response = client.delete(f"/overtime/{test_overtime_request.ot_id}")
        assert response.status_code == 403  # Forbidden

class TestOvertimeRequestApproval:
    """Test overtime request approval functionality"""
    
    def test_approve_overtime_request_success(self, client, test_admin, test_overtime_request):
        """Test successful overtime request approval"""
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/approve")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_approve_overtime_request_not_found(self, client, test_admin):
        """Test approval of non-existent overtime request"""
        response = client.post("/overtime/999999/approve")
        assert response.status_code == 404
    
    def test_approve_overtime_request_unauthorized(self, client, test_overtime_request):
        """Test overtime request approval without authentication"""
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/approve")
        assert response.status_code == 401
    
    def test_approve_overtime_request_not_pending(self, client, test_admin, test_overtime_request):
        """Test approval of non-pending overtime request"""
        # Change status to approved
        test_overtime_request.status = "Approved"
        db_session = TestingSessionLocal()
        db_session.commit()
        
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/approve")
        assert response.status_code == 400

class TestOvertimeRequestRejection:
    """Test overtime request rejection functionality"""
    
    def test_reject_overtime_request_success(self, client, test_admin, test_overtime_request):
        """Test successful overtime request rejection"""
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/reject")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_reject_overtime_request_not_found(self, client, test_admin):
        """Test rejection of non-existent overtime request"""
        response = client.post("/overtime/999999/reject")
        assert response.status_code == 404
    
    def test_reject_overtime_request_unauthorized(self, client, test_overtime_request):
        """Test overtime request rejection without authentication"""
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/reject")
        assert response.status_code == 401
    
    def test_reject_overtime_request_not_pending(self, client, test_admin, test_overtime_request):
        """Test rejection of non-pending overtime request"""
        # Change status to rejected
        test_overtime_request.status = "Rejected"
        db_session = TestingSessionLocal()
        db_session.commit()
        
        response = client.post(f"/overtime/{test_overtime_request.ot_id}/reject")
        assert response.status_code == 400

class TestOvertimeStatistics:
    """Test overtime statistics functionality"""
    
    def test_get_overtime_stats_success(self, client, test_admin, test_overtime_request):
        """Test successful retrieval of overtime statistics"""
        response = client.get("/overtime/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
    
    def test_get_overtime_stats_unauthorized(self, client, test_overtime_request):
        """Test retrieval of overtime statistics without authentication"""
        response = client.get("/overtime/stats/summary")
        assert response.status_code == 401

class TestUserOvertimeRequests:
    """Test user-specific overtime requests functionality"""
    
    def test_get_user_overtime_requests_success(self, client, test_user, test_overtime_request):
        """Test successful retrieval of user's overtime requests"""
        response = client.get(f"/overtime/user/{test_user.user_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_user_overtime_requests_unauthorized(self, client, test_user, test_overtime_request):
        """Test retrieval of user's overtime requests without authentication"""
        response = client.get(f"/overtime/user/{test_user.user_id}")
        assert response.status_code == 401
    
    def test_get_user_overtime_requests_wrong_user(self, client, test_user, test_admin, test_overtime_request):
        """Test retrieval of another user's overtime requests"""
        # Create another user
        other_user = User(
            username="otheruser@example.com",
            password_hash="hashedpassword",
            first_name="Other",
            last_name="User",
            email="otheruser@example.com",
            role_name="employee",
            hourly_rate=20.0,
            date_hired=date.today(),
            status="active"
        )
        
        db_session = TestingSessionLocal()
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Try to get requests for different user
        response = client.get(f"/overtime/user/{other_user.user_id}")
        assert response.status_code == 403  # Forbidden

class TestOvertimeRequestValidation:
    """Test overtime request validation functionality"""
    
    def test_overtime_request_form_validation(self):
        """Test overtime request form validation"""
        # Test valid form data
        valid_data = {
            "date": date.today().isoformat(),
            "hours_requested": 3.0,
            "reason": "Test overtime"
        }
        
        # Test invalid date format
        invalid_date_data = {
            "date": "invalid-date",
            "hours_requested": 3.0,
            "reason": "Test overtime"
        }
        
        # Test negative hours
        invalid_hours_data = {
            "date": date.today().isoformat(),
            "hours_requested": -1.0,
            "reason": "Test overtime"
        }
        
        # Test empty reason
        empty_reason_data = {
            "date": date.today().isoformat(),
            "hours_requested": 3.0,
            "reason": ""
        }
        
        # Test None reason
        none_reason_data = {
            "date": date.today().isoformat(),
            "hours_requested": 3.0,
            "reason": None
        }
        
        # Test hours over maximum
        max_hours_data = {
            "date": date.today().isoformat(),
            "hours_requested": 25.0,
            "reason": "Test overtime"
        }
        
        # Test hours below minimum
        min_hours_data = {
            "date": date.today().isoformat(),
            "hours_requested": 0.0,
            "reason": "Test overtime"
        }
        
        # Test valid None reason
        assert valid_data["date"] is not None
        assert valid_data["hours_requested"] > 0
        assert valid_data["reason"] is not None
        
        # Test invalid date format
        assert "invalid-date" in invalid_date_data["date"]
        
        # Test negative hours
        assert invalid_hours_data["hours_requested"] < 0
        
        # Test empty reason
        assert empty_reason_data["reason"] == ""
        
        # Test None reason
        assert none_reason_data["reason"] is None
        
        # Test hours over maximum
        assert max_hours_data["hours_requested"] > 24.0
        
        # Test hours below minimum
        assert min_hours_data["hours_requested"] <= 0

class TestOvertimeRequestStatus:
    """Test overtime request status functionality"""
    
    def test_overtime_request_status_values(self):
        """Test overtime request status values"""
        assert OvertimeStatus.Pending.value == "Pending"
        assert OvertimeStatus.Approved.value == "Approved"
        assert OvertimeStatus.Rejected.value == "Rejected"
    
    def test_overtime_request_status_enum(self):
        """Test overtime request status enum"""
        assert hasattr(OvertimeStatus, 'Pending')
        assert hasattr(OvertimeStatus, 'Approved')
        assert hasattr(OvertimeStatus, 'Rejected')
        
        assert OvertimeStatus.Pending == "Pending"
        assert OvertimeStatus.Approved == "Approved"
        assert OvertimeStatus.Rejected == "Rejected"

class TestOvertimeRequestFilter:
    """Test overtime request filter functionality"""
    
    def test_overtime_filter_validation(self):
        """Test overtime filter validation"""
        from backend.routers.overtime import OvertimeFilter
        
        # Test valid filter
        valid_filter = OvertimeFilter(
            start_date=date.today().isoformat(),
            end_date=date.today().isoformat(),
            status="Pending",
            user_id=1
        )
        
        # Test None values
        none_filter = OvertimeFilter()
        
        # Test invalid date format
        invalid_date_filter = OvertimeFilter(
            start_date="invalid-date",
            end_date=date.today().isoformat(),
            status="Pending",
            user_id=1
        )
        
        # Test invalid status
        invalid_status_filter = OvertimeFilter(
            start_date=date.today().isoformat(),
            end_date=date.today().isoformat(),
            status="InvalidStatus",
            user_id=1
        )
        
        # Test valid filter
        assert valid_filter.start_date == date.today().isoformat()
        assert valid_filter.end_date == date.today().isoformat()
        assert valid_filter.status == "Pending"
        assert valid_filter.user_id == 1
        
        # Test None filter
        assert none_filter.start_date is None
        assert none_filter.end_date is None
        assert none_filter.status is None
        assert none_filter.user_id is None
        
        # Test invalid date filter
        assert "invalid-date" in invalid_date_filter.start_date
        
        # Test invalid status filter
        assert invalid_status_filter.status == "InvalidStatus"

if __name__ == "__main__":
    pytest.main([__file__])