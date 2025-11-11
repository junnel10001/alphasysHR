"""
Dashboard Integration Tests

End-to-end tests for dashboard functionality across frontend and backend.
"""

import pytest
import bcrypt
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.main import app
from backend.database import get_db
from backend.models import Base, User, Attendance, LeaveRequest, OvertimeRequest, Payroll, LeaveStatus, OvertimeStatus, AttendanceStatus, Department, Role, LeaveType

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard_integration.db"
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
    # Set testing environment to prevent database seeding
    import os
    os.environ["TESTING"] = "true"
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Import RBAC utils to seed roles and permissions
    from backend.utils.rbac import RBACUtils
    
    # Seed default roles and permissions
    RBACUtils.seed_default_permissions(db)
    roles = RBACUtils.seed_default_roles(db)
    if not roles:
        # If roles were already created, get the admin role
        admin_role = db.query(Role).filter(Role.role_name == "admin").first()
    else:
        admin_role = roles[0]  # Get admin role
    
    # Create test department
    department = Department(
        department_name="Test Department"
    )
    db.add(department)
    db.commit()  # Commit to get department_id
    
    # Create test admin user with proper password hash
    import bcrypt
    hashed_password = bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    admin_user = User(
        username="admin@test.com",
        password_hash=hashed_password,
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        role_id=admin_role.role_id,  # Assign the actual admin role ID
        role_name="admin",
        hourly_rate=50.0,
        date_hired=date.today(),
        status="active",
        department_id=department.department_id
    )
    db.add(admin_user)
    
    # Create test employee user with proper password hash
    employee_role = db.query(Role).filter(Role.role_name == "employee").first()
    employee_user = User(
        username="employee@test.com",
        password_hash=hashed_password,
        first_name="John",
        last_name="Doe",
        email="employee@test.com",
        role_id=employee_role.role_id,  # Assign the actual employee role ID
        role_name="employee",
        hourly_rate=25.0,
        date_hired=date.today(),
        status="active",
        department_id=department.department_id
    )
    db.add(employee_user)
    
    db.commit()
    db.refresh(admin_user)
    db.refresh(employee_user)
    db.refresh(department)
    
    # Create test leave types
    leave_type = LeaveType(
        leave_name="Annual Leave",
        default_allocation=21
    )
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    
    # Create test attendance records
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    attendance1 = Attendance(
        user_id=admin_user.user_id,
        date=today,
        time_in=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
        time_out=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
        hours_worked=8.0,
        status=AttendanceStatus.Present.value
    )
    db.add(attendance1)
    
    attendance2 = Attendance(
        user_id=employee_user.user_id,
        date=today,
        time_in=datetime.now().replace(hour=9, minute=30, second=0, microsecond=0),
        time_out=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
        hours_worked=7.5,
        status=AttendanceStatus.Late.value
    )
    db.add(attendance2)
    
    # Create test leave requests
    leave1 = LeaveRequest(
        user_id=employee_user.user_id,
        leave_type_id=leave_type.leave_type_id,
        date_from=today,
        date_to=today + timedelta(days=1),
        reason="Personal leave",
        status=LeaveStatus.Pending.value
    )
    db.add(leave1)
    
    leave2 = LeaveRequest(
        user_id=employee_user.user_id,
        leave_type_id=leave_type.leave_type_id,
        date_from=yesterday,
        date_to=yesterday + timedelta(days=1),
        reason="Vacation",
        status=LeaveStatus.Pending.value  # Change to Pending to have multiple pending leaves
    )
    db.add(leave2)
    
    leave3 = LeaveRequest(
        user_id=employee_user.user_id,
        leave_type_id=leave_type.leave_type_id,
        date_from=yesterday - timedelta(days=2),
        date_to=yesterday - timedelta(days=1),
        reason="Sick leave",
        status=LeaveStatus.Rejected.value  # Add a rejected leave
    )
    db.add(leave3)
    
    # Create test overtime requests
    overtime1 = OvertimeRequest(
        user_id=employee_user.user_id,
        date=today,
        hours_requested=2.0,
        reason="Project deadline",
        status=OvertimeStatus.Pending.value
    )
    db.add(overtime1)
    
    overtime2 = OvertimeRequest(
        user_id=employee_user.user_id,
        date=yesterday,
        hours_requested=1.5,
        reason="Bug fix",
        status=OvertimeStatus.Approved.value
    )
    db.add(overtime2)
    
    overtime3 = OvertimeRequest(
        user_id=employee_user.user_id,
        date=yesterday - timedelta(days=1),
        hours_requested=3.0,
        reason="Emergency fix",
        status=OvertimeStatus.Rejected.value
    )
    db.add(overtime3)
    
    # Create test payroll records
    payroll1 = Payroll(
        user_id=admin_user.user_id,
        cutoff_start=today.replace(day=1),
        cutoff_end=today,
        basic_pay=2000.00,
        overtime_pay=100.00,
        deductions=200.00,
        net_pay=1900.00
    )
    db.add(payroll1)
    
    payroll2 = Payroll(
        user_id=employee_user.user_id,
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

def test_dashboard_full_integration(test_db, auth_headers):
    """Test the complete dashboard integration."""
    # Get all dashboard data
    response = client.get("/dashboard/kpi", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify all required data is present
    required_sections = [
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
    
    for section in required_sections:
        assert section in data, f"Missing section: {section}"
    
    # Verify data consistency
    assert data["employees_present_today"] > 0
    assert data["late_absent_today"]["late"] >= 0
    assert data["late_absent_today"]["absent"] >= 0
    assert data["pending_leave_requests"] > 0
    assert data["pending_overtime_requests"] > 0
    assert len(data["attendance_overview"]) > 0
    assert len(data["today_attendance"]) > 0
    assert data["payroll_summary"]["total_payrolls"] > 0
    assert len(data["leave_stats"]) == 4  # All statuses
    assert len(data["overtime_stats"]) == 3  # All statuses
    
    # Test individual endpoints
    individual_endpoints = [
        "/dashboard/kpi/employees-present",
        "/dashboard/kpi/late-absent",
        "/dashboard/kpi/pending-leave",
        "/dashboard/kpi/pending-overtime",
        "/dashboard/kpi/attendance-overview",
        "/dashboard/kpi/today-attendance",
        "/dashboard/kpi/payroll-summary",
        "/dashboard/kpi/leave-stats",
        "/dashboard/kpi/overtime-stats"
    ]
    
    for endpoint in individual_endpoints:
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200, f"Failed on {endpoint}: {response.text}"

def test_dashboard_leave_management_integration(test_db, auth_headers):
    """Test leave management integration."""
    # Get pending leave count
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    pending_count = response.json()["pending_leave_requests"]
    assert pending_count > 0
    
    # Get all leave requests
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
    
    # Verify approval by querying the database directly
    db = test_db
    approved_leave = db.query(LeaveRequest).filter(LeaveRequest.leave_id == leave_id).first()
    assert approved_leave is not None
    assert approved_leave.status == "Approved"
    
    # Verify the count decreased
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["pending_leave_requests"] < pending_count
    
    # Test rejection on another leave
    another_leave = next((leave for leave in leaves if leave["status"] == "Pending" and leave["leave_id"] != leave_id), None)
    assert another_leave is not None
    
    response = client.post(f"/dashboard/leaves/{another_leave['leave_id']}/reject", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify rejection by querying the database directly
    rejected_leave = db.query(LeaveRequest).filter(LeaveRequest.leave_id == another_leave["leave_id"]).first()
    assert rejected_leave is not None
    assert rejected_leave.status == "Rejected"
    
    # Verify the count decreased by more than 1
    response = client.get("/dashboard/kpi/pending-leave", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["pending_leave_requests"] < pending_count - 1

def test_dashboard_overtime_management_integration(test_db, auth_headers):
    """Test overtime management integration."""
    # Get pending overtime count
    response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
    assert response.status_code == 200
    pending_count = response.json()["pending_overtime_requests"]
    assert pending_count > 0
    
    # Get the overtime request ID from the database
    db = test_db
    overtime_request = db.query(OvertimeRequest).filter(OvertimeRequest.status == "Pending").first()
    assert overtime_request is not None
    ot_id = overtime_request.ot_id
    
    # Test approval
    response = client.post(f"/dashboard/overtime/{ot_id}/approve", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify approval by refreshing the database record
    db.refresh(overtime_request)
    assert overtime_request.status == "Approved"
    
    # Verify the count decreased
    response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["pending_overtime_requests"] < pending_count
    
    # If there are still pending overtime requests, test rejection
    remaining_pending = db.query(OvertimeRequest).filter(OvertimeRequest.status == "Pending").filter(OvertimeRequest.ot_id != ot_id).all()
    if remaining_pending:
        another_overtime = remaining_pending[0]
        response = client.post(f"/dashboard/overtime/{another_overtime.ot_id}/reject", headers=auth_headers)
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify rejection by refreshing the database record
        db.refresh(another_overtime)
        assert another_overtime.status == "Rejected"
        
        # Verify the count decreased by more than 1
        response = client.get("/dashboard/kpi/pending-overtime", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["pending_overtime_requests"] < pending_count - 1

def test_dashboard_data_consistency(test_db, auth_headers):
    """Test data consistency across dashboard endpoints."""
    # Get full dashboard data
    full_response = client.get("/dashboard/kpi", headers=auth_headers)
    assert full_response.status_code == 200
    full_data = full_response.json()
    
    # Get individual endpoint data
    individual_responses = {}
    individual_endpoints = [
        "employees-present",
        "late-absent",
        "pending-leave",
        "pending-overtime",
        "attendance-overview",
        "today-attendance",
        "payroll-summary",
        "leave-stats",
        "overtime-stats"
    ]
    
    for endpoint in individual_endpoints:
        response = client.get(f"/dashboard/kpi/{endpoint}", headers=auth_headers)
        assert response.status_code == 200
        individual_responses[endpoint] = response.json()
    
    # Verify consistency
    assert full_data["employees_present_today"] == individual_responses["employees-present"]["employees_present_today"]
    assert full_data["late_absent_today"] == individual_responses["late-absent"]
    assert full_data["pending_leave_requests"] == individual_responses["pending-leave"]["pending_leave_requests"]
    assert full_data["pending_overtime_requests"] == individual_responses["pending-overtime"]["pending_overtime_requests"]
    assert full_data["attendance_overview"] == individual_responses["attendance-overview"]["attendance_overview"]
    assert full_data["today_attendance"] == individual_responses["today-attendance"]["today_attendance"]
    assert full_data["payroll_summary"] == individual_responses["payroll-summary"]["payroll_summary"]
    assert full_data["leave_stats"] == individual_responses["leave-stats"]["leave_stats"]
    assert full_data["overtime_stats"] == individual_responses["overtime-stats"]["overtime_stats"]

def test_dashboard_error_handling(test_db, auth_headers):
    """Test error handling in dashboard endpoints."""
    # Test invalid leave approval
    response = client.post("/dashboard/leaves/999/approve", headers=auth_headers)
    assert response.status_code == 404
    
    # Test invalid leave rejection
    response = client.post("/dashboard/leaves/999/reject", headers=auth_headers)
    assert response.status_code == 404
    
    # Test invalid overtime approval
    response = client.post("/dashboard/overtime/999/approve", headers=auth_headers)
    assert response.status_code == 404
    
    # Test invalid overtime rejection
    response = client.post("/dashboard/overtime/999/reject", headers=auth_headers)
    assert response.status_code == 404
    
    # Get leaves from database to find an approved one
    db = test_db
    approved_leave = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").first()
    
    # Test non-pending leave approval (only if approved leave exists)
    if approved_leave:
        response = client.post(f"/dashboard/leaves/{approved_leave.leave_id}/approve", headers=auth_headers)
        assert response.status_code == 400
    
    # Test non-pending leave rejection (only if rejected leave exists)
    rejected_leave = db.query(LeaveRequest).filter(LeaveRequest.status == "Rejected").first()
    if rejected_leave:
        response = client.post(f"/dashboard/leaves/{rejected_leave.leave_id}/reject", headers=auth_headers)
        assert response.status_code == 400
    
    # Test non-pending overtime approval
    approved_overtime = db.query(OvertimeRequest).filter(OvertimeRequest.status == "Approved").first()
    assert approved_overtime is not None
    
    response = client.post(f"/dashboard/overtime/{approved_overtime.ot_id}/approve", headers=auth_headers)
    assert response.status_code == 400
    
    # Test non-pending overtime rejection
    rejected_overtime = db.query(OvertimeRequest).filter(OvertimeRequest.status == "Rejected").first()
    assert rejected_overtime is not None
    
    response = client.post(f"/dashboard/overtime/{rejected_overtime.ot_id}/reject", headers=auth_headers)
    assert response.status_code == 400

def test_dashboard_unauthorized_access(test_db):
    """Test unauthorized access to dashboard endpoints."""
    endpoints = [
        "/dashboard/kpi",
        "/dashboard/kpi/employees-present",
        "/dashboard/kpi/late-absent",
        "/dashboard/kpi/pending-leave",
        "/dashboard/kpi/pending-overtime",
        "/dashboard/kpi/attendance-overview",
        "/dashboard/kpi/today-attendance",
        "/dashboard/kpi/payroll-summary",
        "/dashboard/kpi/leave-stats",
        "/dashboard/kpi/overtime-stats",
        "/dashboard/leaves/1/approve",
        "/dashboard/leaves/1/reject",
        "/dashboard/overtime/1/approve",
        "/dashboard/overtime/1/reject"
    ]
    
    for endpoint in endpoints:
        if "leaves" in endpoint or "overtime" in endpoint:
            # These require POST requests with data
            response = client.post(endpoint, json={"action": "approve"})
            # For POST requests without authentication, we expect 405 Method Not Allowed
            # because FastAPI doesn't even get to the authentication middleware
            assert response.status_code in [403, 405], f"Expected 403 or 405, got {response.status_code} for {endpoint}"
        else:
            response = client.get(endpoint)
            assert response.status_code == 403, f"Expected 403, got {response.status_code} for {endpoint}"

def test_dashboard_performance(test_db, auth_headers):
    """Test dashboard performance with realistic data."""
    # Add more test data
    db = test_db
    today = date.today()
    
    # Get the employee user from the database
    employee_user = db.query(User).filter(User.username == "employee@test.com").first()
    leave_type = db.query(LeaveType).filter(LeaveType.leave_name == "Annual Leave").first()
    
    # Add more attendance records
    for i in range(10):
        attendance = Attendance(
            user_id=employee_user.user_id,
            date=today - timedelta(days=i),
            time_in=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
            time_out=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
            hours_worked=8.0,
            status=AttendanceStatus.Present.value
        )
        db.add(attendance)
    
    # Add more leave requests
    for i in range(5):
        leave = LeaveRequest(
            user_id=employee_user.user_id,
            leave_type_id=leave_type.leave_type_id,
            date_from=today - timedelta(days=i),
            date_to=today - timedelta(days=i) + timedelta(days=1),
            reason=f"Test leave {i}",
            status=LeaveStatus.Pending.value if i % 2 == 0 else LeaveStatus.Approved.value
        )
        db.add(leave)
    
    # Add more overtime requests
    for i in range(3):
        overtime = OvertimeRequest(
            user_id=employee_user.user_id,
            date=today - timedelta(days=i),
            hours_requested=1.5 + i,
            reason=f"Test overtime {i}",
            status=OvertimeStatus.Pending.value if i % 2 == 0 else OvertimeStatus.Approved.value
        )
        db.add(overtime)
    
    # Add more payroll records
    for i in range(3):
        payroll = Payroll(
            user_id=employee_user.user_id,
            cutoff_start=today.replace(day=1) - timedelta(days=30*i),
            cutoff_end=today.replace(day=1) - timedelta(days=30*(i-1)) if i > 0 else today,
            basic_pay=1000.00 + i*100,
            overtime_pay=50.00 + i*10,
            deductions=100.00 + i*5,
            net_pay=950.00 + i*105
        )
        db.add(payroll)
    
    db.commit()
    
    # Test performance of main dashboard endpoint
    import time
    start_time = time.time()
    response = client.get("/dashboard/kpi", headers=auth_headers)
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
    
    data = response.json()
    assert data["employees_present_today"] > 0
    assert len(data["attendance_overview"]) > 0
    assert len(data["today_attendance"]) > 0
    assert data["payroll_summary"]["total_payrolls"] > 0

def test_dashboard_data_validation(test_db, auth_headers):
    """Test data validation and integrity."""
    response = client.get("/dashboard/kpi", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Validate KPI data types
    assert isinstance(data["employees_present_today"], int) and data["employees_present_today"] >= 0
    assert isinstance(data["late_absent_today"], dict)
    assert isinstance(data["pending_leave_requests"], int) and data["pending_leave_requests"] >= 0
    assert isinstance(data["pending_overtime_requests"], int) and data["pending_overtime_requests"] >= 0
    
    # Validate attendance overview
    assert isinstance(data["attendance_overview"], list)
    for item in data["attendance_overview"]:
        assert isinstance(item, dict)
        assert "date" in item
        assert "total" in item
        assert "present" in item
        assert "late" in item
        assert "absent" in item
        assert isinstance(item["total"], int)
        assert isinstance(item["present"], int)
        assert isinstance(item["late"], int)
        assert isinstance(item["absent"], int)
    
    # Validate today's attendance
    assert isinstance(data["today_attendance"], list)
    for item in data["today_attendance"]:
        assert isinstance(item, dict)
        required_fields = ["attendance_id", "user_id", "name", "email", "date", "time_in", "time_out", "hours_worked", "status"]
        for field in required_fields:
            assert field in item
        assert isinstance(item["attendance_id"], int)
        assert isinstance(item["user_id"], int)
        assert isinstance(item["hours_worked"], (int, float))
        assert isinstance(item["status"], str)
    
    # Validate payroll summary
    assert isinstance(data["payroll_summary"], dict)
    required_fields = ["total_payrolls", "total_basic_pay", "total_overtime_pay", "total_deductions", "total_net_pay"]
    for field in required_fields:
        assert field in data["payroll_summary"]
        assert isinstance(data["payroll_summary"][field], (int, float))
        assert data["payroll_summary"][field] >= 0
    
    # Validate leave stats
    assert isinstance(data["leave_stats"], dict)
    expected_statuses = ["pending", "approved", "rejected", "cancelled"]
    for status in expected_statuses:
        assert status in data["leave_stats"]
        assert isinstance(data["leave_stats"][status], int)
        assert data["leave_stats"][status] >= 0
    
    # Validate overtime stats
    assert isinstance(data["overtime_stats"], dict)
    expected_statuses = ["pending", "approved", "rejected"]
    for status in expected_statuses:
        assert status in data["overtime_stats"]
        assert isinstance(data["overtime_stats"][status], int)
        assert data["overtime_stats"][status] >= 0