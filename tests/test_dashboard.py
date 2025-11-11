"""
Dashboard Tests

Comprehensive tests for dashboard endpoints and components.
"""

import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db
from backend.models import Base, User, Attendance, LeaveRequest, OvertimeRequest, Payroll, LeaveStatus, OvertimeStatus, AttendanceStatus
from backend.services.dashboard_service import DashboardService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard.db"
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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test admin user
    admin_user = User(
        username="admin@test.com",
        password_hash="hashed_password",
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        role_name="admin",
        hourly_rate=50.0,
        date_hired=date.today(),
        status="active"
    )
    db.add(admin_user)
    
    # Create test employee user
    employee_user = User(
        username="employee@test.com",
        password_hash="hashed_password",
        first_name="John",
        last_name="Doe",
        email="employee@test.com",
        role_name="employee",
        hourly_rate=25.0,
        date_hired=date.today(),
        status="active"
    )
    db.add(employee_user)
    
    # Create test attendance records
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    attendance1 = Attendance(
        user_id=1,
        date=today,
        time_in=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
        time_out=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
        hours_worked=8.0,
        status=AttendanceStatus.Present.value
    )
    db.add(attendance1)
    
    attendance2 = Attendance(
        user_id=2,
        date=today,
        time_in=datetime.now().replace(hour=9, minute=30, second=0, microsecond=0),
        time_out=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
        hours_worked=7.5,
        status=AttendanceStatus.Late.value
    )
    db.add(attendance2)
    
    # Create test leave requests
    leave1 = LeaveRequest(
        user_id=2,
        leave_type_id=1,
        date_from=today,
        date_to=today + timedelta(days=1),
        reason="Personal leave",
        status=LeaveStatus.Pending.value
    )
    db.add(leave1)
    
    leave2 = LeaveRequest(
        user_id=2,
        leave_type_id=1,
        date_from=yesterday,
        date_to=yesterday + timedelta(days=1),
        reason="Vacation",
        status=LeaveStatus.Approved.value
    )
    db.add(leave2)
    
    # Create test overtime requests
    overtime1 = OvertimeRequest(
        user_id=2,
        date=today,
        hours_requested=2.0,
        reason="Project deadline",
        status=OvertimeStatus.Pending.value
    )
    db.add(overtime1)
    
    # Create test payroll records
    payroll1 = Payroll(
        user_id=1,
        cutoff_start=today.replace(day=1),
        cutoff_end=today,
        basic_pay=2000.00,
        overtime_pay=100.00,
        deductions=200.00,
        net_pay=1900.00
    )
    db.add(payroll1)
    
    payroll2 = Payroll(
        user_id=2,
        cutoff_start=today.replace(day=1),
        cutoff_end=today,
        basic_pay=1500.00,
        overtime_pay=50.00,
        deductions=100.00,
        net_pay=1450.00
    )
    db.add(payroll2)
    
    db.commit()
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers(test_db):
    """Get authentication headers for admin user."""
    login_data = {
        "username": "admin@test.com",
        "password": "password"  # This would normally be hashed
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_dashboard_kpi_endpoint(test_db, auth_headers):
    """Test the main dashboard KPI endpoint."""
    response = client.get("/dashboard/kpi", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required fields
    required_fields = [
        "employees_present_today",
        "late_absent_today",
        "pending_leave_requests",
        "pending_overtime_requests",
        "attendance_overview",
        "today_attendance",
        "payroll_summary",
        "leave_stats",
        "overtime_stats"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Check data types and values
    assert isinstance(data["employees_present_today"], int)
    assert isinstance(data["late_absent_today"], dict)
    assert isinstance(data["pending_leave_requests"], int)
    assert isinstance(data["pending_overtime_requests"], int)
    assert isinstance(data["attendance_overview"], list)
    assert isinstance(data["today_attendance"], list)
    assert isinstance(data["payroll_summary"], dict)
    assert isinstance(data["leave_stats"], dict)
    assert isinstance(data["overtime_stats"], dict)
    
    # Check specific values
    assert data["employees_present_today"] >= 0
    assert data["pending_leave_requests"] >= 0
    assert data["pending_overtime_requests"] >= 0
    assert data["late_absent_today"]["late"] >= 0
    assert data["late_absent_today"]["absent"] >= 0

def test_dashboard_kpi_employees_present(test_db, auth_headers):
    """Test employees present today endpoint."""
    response = client.get("/dashboard/kpi/employees-present", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "employees_present_today" in data
    assert isinstance(data["employees_present_today"], int)
    assert data["employees_present_today"] >= 0

def test_dashboard_kpi_late_absent(test_db, auth_headers):
    """Test late/absent endpoint."""
    response = client.get("/dashboard/kpi/late-absent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "late" in data
    assert "absent" in data
    assert isinstance(data["late"], int)
    assert isinstance(data["absent"], int)
    assert data["late"] >= 0
    assert data["absent"] >= 0

def test_dashboard_kpi_pending_leave(test_db, auth_headers):
    """Test pending leave requests endpoint."""
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pending_leave_requests" in data
    assert isinstance(data["pending_leave_requests"], int)
    assert data["pending_leave_requests"] >= 0

def test_dashboard_kpi_pending_overtime(test_db, auth_headers):
    """Test pending overtime requests endpoint."""
    response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pending_overtime_requests" in data
    assert isinstance(data["pending_overtime_requests"], int)
    assert data["pending_overtime_requests"] >= 0

def test_dashboard_kpi_attendance_overview(test_db, auth_headers):
    """Test attendance overview endpoint."""
    response = client.get("/dashboard/kpi/attendance-overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "attendance_overview" in data
    assert isinstance(data["attendance_overview"], list)
    
    # Check structure of attendance overview items
    if data["attendance_overview"]:
        item = data["attendance_overview"][0]
        required_fields = ["date", "total", "present", "late", "absent"]
        for field in required_fields:
            assert field in item, f"Missing field in attendance overview: {field}"

def test_dashboard_kpi_today_attendance(test_db, auth_headers):
    """Test today's attendance endpoint."""
    response = client.get("/dashboard/kpi/today-attendance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "today_attendance" in data
    assert isinstance(data["today_attendance"], list)
    
    # Check structure of attendance items
    if data["today_attendance"]:
        item = data["today_attendance"][0]
        required_fields = ["attendance_id", "user_id", "name", "email", "date", "time_in", "time_out", "hours_worked", "status"]
        for field in required_fields:
            assert field in item, f"Missing field in today's attendance: {field}"

def test_dashboard_kpi_payroll_summary(test_db, auth_headers):
    """Test payroll summary endpoint."""
    response = client.get("/dashboard/kpi/payroll-summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "payroll_summary" in data
    assert isinstance(data["payroll_summary"], dict)
    
    # Check required fields in payroll summary
    required_fields = ["total_payrolls", "total_basic_pay", "total_overtime_pay", "total_deductions", "total_net_pay"]
    for field in required_fields:
        assert field in data["payroll_summary"], f"Missing field in payroll summary: {field}"

def test_dashboard_kpi_leave_stats(test_db, auth_headers):
    """Test leave stats endpoint."""
    response = client.get("/dashboard/kpi/leave-stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "leave_stats" in data
    assert isinstance(data["leave_stats"], dict)
    
    # Check all leave statuses are present
    expected_statuses = ["pending", "approved", "rejected", "cancelled"]
    for status in expected_statuses:
        assert status in data["leave_stats"], f"Missing leave status: {status}"

def test_dashboard_kpi_overtime_stats(test_db, auth_headers):
    """Test overtime stats endpoint."""
    response = client.get("/dashboard/kpi/overtime-stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "overtime_stats" in data
    assert isinstance(data["overtime_stats"], dict)
    
    # Check all overtime statuses are present
    expected_statuses = ["pending", "approved", "rejected"]
    for status in expected_statuses:
        assert status in data["overtime_stats"], f"Missing overtime status: {status}"

def test_dashboard_leave_approve(test_db, auth_headers):
    """Test leave request approval."""
    # First, get a leave request ID
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    pending_leaves = response.json()["pending_leave_requests"]
    assert pending_leaves > 0
    
    # Get all leaves to find a pending one
    response = client.get("/leaves/", headers=auth_headers)
    assert response.status_code == 200
    leaves = response.json()
    pending_leave = next((leave for leave in leaves if leave["status"] == "Pending"), None)
    assert pending_leave is not None
    
    leave_id = pending_leave["leave_id"]
    
    # Test approval
    response = client.post(f"/dashboard/leaves/{leave_id}/approve", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify the leave is now approved
    response = client.get("/leaves/", headers=auth_headers)
    assert response.status_code == 200
    updated_leave = next((leave for leave in response.json() if leave["leave_id"] == leave_id), None)
    assert updated_leave["status"] == "Approved"

def test_dashboard_leave_reject(test_db, auth_headers):
    """Test leave request rejection."""
    # First, get a leave request ID
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    pending_leaves = response.json()["pending_leave_requests"]
    assert pending_leaves > 0
    
    # Get all leaves to find a pending one
    response = client.get("/leaves/", headers=auth_headers)
    assert response.status_code == 200
    leaves = response.json()
    pending_leave = next((leave for leave in leaves if leave["status"] == "Pending"), None)
    assert pending_leave is not None
    
    leave_id = pending_leave["leave_id"]
    
    # Test rejection
    response = client.post(f"/dashboard/leaves/{leave_id}/reject", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify the leave is now rejected
    response = client.get("/leaves/", headers=auth_headers)
    assert response.status_code == 200
    updated_leave = next((leave for leave in response.json() if leave["leave_id"] == leave_id), None)
    assert updated_leave["status"] == "Rejected"

def test_dashboard_overtime_approve(test_db, auth_headers):
    """Test overtime request approval."""
    # First, get an overtime request ID
    response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
    assert response.status_code == 200
    pending_overtime = response.json()["pending_overtime_requests"]
    assert pending_overtime > 0
    
    # Get all overtime requests to find a pending one
    response = client.get("/overtime/", headers=auth_headers)
    assert response.status_code == 200
    overtime_requests = response.json()
    pending_overtime_req = next((req for req in overtime_requests if req["status"] == "Pending"), None)
    assert pending_overtime_req is not None
    
    ot_id = pending_overtime_req["ot_id"]
    
    # Test approval
    response = client.post(f"/dashboard/overtime/{ot_id}/approve", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify the overtime is now approved
    response = client.get("/overtime/", headers=auth_headers)
    assert response.status_code == 200
    updated_overtime = next((req for req in response.json() if req["ot_id"] == ot_id), None)
    assert updated_overtime["status"] == "Approved"

def test_dashboard_overtime_reject(test_db, auth_headers):
    """Test overtime request rejection."""
    # First, get an overtime request ID
    response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
    assert response.status_code == 200
    pending_overtime = response.json()["pending_overtime_requests"]
    assert pending_overtime > 0
    
    # Get all overtime requests to find a pending one
    response = client.get("/overtime/", headers=auth_headers)
    assert response.status_code == 200
    overtime_requests = response.json()
    pending_overtime_req = next((req for req in overtime_requests if req["status"] == "Pending"), None)
    assert pending_overtime_req is not None
    
    ot_id = pending_overtime_req["ot_id"]
    
    # Test rejection
    response = client.post(f"/dashboard/overtime/{ot_id}/reject", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify the overtime is now rejected
    response = client.get("/overtime/", headers=auth_headers)
    assert response.status_code == 200
    updated_overtime = next((req for req in response.json() if req["ot_id"] == ot_id), None)
    assert updated_overtime["status"] == "Rejected"

def test_dashboard_unauthorized_access(test_db):
    """Test that unauthorized access is denied."""
    response = client.get("/dashboard/kpi")
    assert response.status_code == 401

def test_dashboard_leave_approve_unauthorized(test_db):
    """Test that unauthorized leave approval is denied."""
    response = client.post("/dashboard/leaves/1/approve")
    assert response.status_code == 401

def test_dashboard_leave_reject_unauthorized(test_db):
    """Test that unauthorized leave rejection is denied."""
    response = client.post("/dashboard/leaves/1/reject")
    assert response.status_code == 401

def test_dashboard_overtime_approve_unauthorized(test_db):
    """Test that unauthorized overtime approval is denied."""
    response = client.post("/dashboard/overtime/1/approve")
    assert response.status_code == 401

def test_dashboard_overtime_reject_unauthorized(test_db):
    """Test that unauthorized overtime rejection is denied."""
    response = client.post("/dashboard/overtime/1/reject")
    assert response.status_code == 401

def test_dashboard_leave_approve_not_found(test_db, auth_headers):
    """Test leave approval for non-existent leave request."""
    response = client.post("/dashboard/leaves/999/approve", headers=auth_headers)
    assert response.status_code == 404

def test_dashboard_leave_reject_not_found(test_db, auth_headers):
    """Test leave rejection for non-existent leave request."""
    response = client.post("/dashboard/leaves/999/reject", headers=auth_headers)
    assert response.status_code == 404

def test_dashboard_overtime_approve_not_found(test_db, auth_headers):
    """Test overtime approval for non-existent overtime request."""
    response = client.post("/dashboard/overtime/999/approve", headers=auth_headers)
    assert response.status_code == 404

def test_dashboard_overtime_reject_not_found(test_db, auth_headers):
    """Test overtime rejection for non-existent overtime request."""
    response = client.post("/dashboard/overtime/999/reject", headers=auth_headers)
    assert response.status_code == 404

def test_dashboard_leave_approve_not_pending(test_db, auth_headers):
    """Test leave approval for non-pending leave request."""
    # Create an approved leave request
    leave = LeaveRequest(
        user_id=1,
        leave_type_id=1,
        date_from=date.today(),
        date_to=date.today() + timedelta(days=1),
        reason="Test leave",
        status=LeaveStatus.Approved.value
    )
    test_db.add(leave)
    test_db.commit()
    
    response = client.post(f"/dashboard/leaves/{leave.leave_id}/approve", headers=auth_headers)
    assert response.status_code == 400

def test_dashboard_leave_reject_not_pending(test_db, auth_headers):
    """Test leave rejection for non-pending leave request."""
    # Create an approved leave request
    leave = LeaveRequest(
        user_id=1,
        leave_type_id=1,
        date_from=date.today(),
        date_to=date.today() + timedelta(days=1),
        reason="Test leave",
        status=LeaveStatus.Approved.value
    )
    test_db.add(leave)
    test_db.commit()
    
    response = client.post(f"/dashboard/leaves/{leave.leave_id}/reject", headers=auth_headers)
    assert response.status_code == 400

def test_dashboard_overtime_approve_not_pending(test_db, auth_headers):
    """Test overtime approval for non-pending overtime request."""
    # Create an approved overtime request
    overtime = OvertimeRequest(
        user_id=1,
        date=date.today(),
        hours_requested=2.0,
        reason="Test overtime",
        status=OvertimeStatus.Approved.value
    )
    test_db.add(overtime)
    test_db.commit()
    
    response = client.post(f"/dashboard/overtime/{overtime.ot_id}/approve", headers=auth_headers)
    assert response.status_code == 400

def test_dashboard_overtime_reject_not_pending(test_db, auth_headers):
    """Test overtime rejection for non-pending overtime request."""
    # Create an approved overtime request
    overtime = OvertimeRequest(
        user_id=1,
        date=date.today(),
        hours_requested=2.0,
        reason="Test overtime",
        status=OvertimeStatus.Approved.value
    )
    test_db.add(overtime)
    test_db.commit()
    
    response = client.post(f"/dashboard/overtime/{overtime.ot_id}/reject", headers=auth_headers)
    assert response.status_code == 400

# Test the DashboardService methods directly
def test_dashboard_service_employees_present(test_db):
    """Test DashboardService.get_employees_present_today."""
    count = DashboardService.get_employees_present_today(test_db)
    assert isinstance(count, int)
    assert count >= 0

def test_dashboard_service_late_absent(test_db):
    """Test DashboardService.get_late_absent_today."""
    data = DashboardService.get_late_absent_today(test_db)
    assert isinstance(data, dict)
    assert "late" in data
    assert "absent" in data
    assert isinstance(data["late"], int)
    assert isinstance(data["absent"], int)

def test_dashboard_service_pending_leave(test_db):
    """Test DashboardService.get_pending_leave_requests."""
    count = DashboardService.get_pending_leave_requests(test_db)
    assert isinstance(count, int)
    assert count >= 0

def test_dashboard_service_pending_overtime(test_db):
    """Test DashboardService.get_pending_overtime_requests."""
    count = DashboardService.get_pending_overtime_requests(test_db)
    assert isinstance(count, int)
    assert count >= 0

def test_dashboard_service_attendance_overview(test_db):
    """Test DashboardService.get_attendance_overview."""
    data = DashboardService.get_attendance_overview(test_db)
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert isinstance(item, dict)
        required_fields = ["date", "total", "present", "late", "absent"]
        for field in required_fields:
            assert field in item

def test_dashboard_service_today_attendance(test_db):
    """Test DashboardService.get_today_attendance_table."""
    data = DashboardService.get_today_attendance_table(test_db)
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert isinstance(item, dict)
        required_fields = ["attendance_id", "user_id", "name", "email", "date", "time_in", "time_out", "hours_worked", "status"]
        for field in required_fields:
            assert field in item

def test_dashboard_service_payroll_summary(test_db):
    """Test DashboardService.get_payroll_summary."""
    data = DashboardService.get_payroll_summary(test_db)
    assert isinstance(data, dict)
    required_fields = ["total_payrolls", "total_basic_pay", "total_overtime_pay", "total_deductions", "total_net_pay"]
    for field in required_fields:
        assert field in data

def test_dashboard_service_leave_stats(test_db):
    """Test DashboardService.get_leave_request_stats."""
    data = DashboardService.get_leave_request_stats(test_db)
    assert isinstance(data, dict)
    expected_statuses = ["pending", "approved", "rejected", "cancelled"]
    for status in expected_statuses:
        assert status in data

def test_dashboard_service_overtime_stats(test_db):
    """Test DashboardService.get_overtime_request_stats."""
    data = DashboardService.get_overtime_request_stats(test_db)
    assert isinstance(data, dict)
    expected_statuses = ["pending", "approved", "rejected"]
    for status in expected_statuses:
        assert status in data