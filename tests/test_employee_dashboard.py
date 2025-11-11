import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date

# Set environment variable for testing
os.environ["TESTING"] = "true"

from backend.main import app
from backend.database import get_db
from backend.models import Base, User, Role, LeaveType, LeaveRequest, OvertimeRequest, Attendance, Payroll, Payslip
from backend.services.employee_dashboard_service import EmployeeDashboardService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_employee_dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    # Create employee role if it doesn't exist
    role = db_session.query(Role).filter(Role.role_name == "employee").first()
    if not role:
        role = Role(role_name="employee", description="Regular employee")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    
    # Create test user
    user = User(
        username="testemployee@example.com",
        password_hash="hashedpassword",
        role_name="employee",
        role_id=role.role_id,
        first_name="Test",
        last_name="Employee",
        email="testemployee@example.com",
        hourly_rate=25.0,
        date_hired=date(2025, 1, 1),
        status="active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_leave_type(db_session):
    leave_type = LeaveType(
        leave_name="Annual Leave",
        default_allocation=20
    )
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)
    return leave_type

@pytest.fixture
def test_leave_request(db_session, test_user, test_leave_type):
    leave_request = LeaveRequest(
        user_id=test_user.user_id,
        leave_type_id=test_leave_type.leave_type_id,
        date_from=date(2025, 6, 1),
        date_to=date(2025, 6, 5),
        reason="Family vacation",
        status="Approved"
    )
    db_session.add(leave_request)
    db_session.commit()
    db_session.refresh(leave_request)
    return leave_request

@pytest.fixture
def test_overtime_request(db_session, test_user):
    overtime_request = OvertimeRequest(
        user_id=test_user.user_id,
        date=date(2025, 6, 10),
        hours_requested=3.5,
        reason="Project deadline",
        status="Approved"
    )
    db_session.add(overtime_request)
    db_session.commit()
    db_session.refresh(overtime_request)
    return overtime_request

@pytest.fixture
def test_attendance(db_session, test_user):
    attendance = Attendance(
        user_id=test_user.user_id,
        date=date(2025, 6, 15),
        time_in=datetime(2025, 6, 15, 9, 0, 0),
        time_out=datetime(2025, 6, 15, 17, 0, 0),
        hours_worked=8.0,
        status="Present"
    )
    db_session.add(attendance)
    db_session.commit()
    db_session.refresh(attendance)
    return attendance

@pytest.fixture
def test_payroll(db_session, test_user):
    payroll = Payroll(
        user_id=test_user.user_id,
        cutoff_start=date(2025, 6, 1),
        cutoff_end=date(2025, 6, 15),
        basic_pay=2000.00,
        overtime_pay=350.00,
        deductions=200.00,
        net_pay=2150.00
    )
    db_session.add(payroll)
    db_session.commit()
    db_session.refresh(payroll)
    return payroll

@pytest.fixture
def test_payslip(db_session, test_payroll):
    payslip = Payslip(
        payroll_id=test_payroll.payroll_id,
        file_path="/path/to/payslip.pdf"
    )
    db_session.add(payslip)
    db_session.commit()
    db_session.refresh(payslip)
    return payslip

def test_get_personal_kpi(test_user, test_leave_type, test_leave_request, test_overtime_request, test_attendance, test_payroll, test_payslip):
    """Test getting personal KPI metrics"""
    response = client.get("/employee-dashboard/kpi")
    assert response.status_code == 200
    
    data = response.json()
    assert "days_worked_this_month" in data
    assert "remaining_leave_balance" in data
    assert "total_overtime_hours_this_month" in data
    assert "latest_payslip" in data
    
    # Test days worked this month
    assert data["days_worked_this_month"] >= 0
    
    # Test remaining leave balance
    assert isinstance(data["remaining_leave_balance"], list)
    assert len(data["remaining_leave_balance"]) > 0
    
    # Test overtime hours
    assert data["total_overtime_hours_this_month"] >= 0
    
    # Test latest payslip
    assert data["latest_payslip"] is not None
    assert "payroll_id" in data["latest_payslip"]
    assert "net_pay" in data["latest_payslip"]

def test_get_attendance_summary_current_month(test_user, test_attendance):
    """Test getting attendance summary for current month"""
    response = client.get("/employee-dashboard/attendance-summary")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if data:  # May be empty if no attendance data
        for item in data:
            assert "date" in item
            assert "hours_worked" in item
            assert "status" in item

def test_get_personal_attendance_log(test_user, test_attendance):
    """Test getting personal attendance log"""
    response = client.get("/employee-dashboard/attendance-log")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if data:  # May be empty if no attendance data
        for item in data:
            assert "attendance_id" in item
            assert "date" in item
            assert "status" in item

def test_get_personal_leave_request_history(test_user, test_leave_request):
    """Test getting personal leave request history"""
    response = client.get("/employee-dashboard/leave-history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if data:  # May be empty if no leave data
        for item in data:
            assert "leave_id" in item
            assert "leave_type" in item
            assert "date_from" in item
            assert "date_to" in item
            assert "status" in item
            assert "approver" in item

def test_get_personal_overtime_request_history(test_user, test_overtime_request):
    """Test getting personal overtime request history"""
    response = client.get("/employee-dashboard/overtime-history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if data:  # May be empty if no overtime data
        for item in data:
            assert "ot_id" in item
            assert "date" in item
            assert "hours_requested" in item
            assert "status" in item
            assert "approver" in item

def test_get_personal_payroll_history(test_user, test_payroll):
    """Test getting personal payroll history"""
    response = client.get("/employee-dashboard/payroll-history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    if data:  # May be empty if no payroll data
        for item in data:
            assert "payroll_id" in item
            assert "cutoff_start" in item
            assert "cutoff_end" in item
            assert "basic_pay" in item
            assert "net_pay" in item
            assert "generated_at" in item

def test_create_leave_request(test_user, test_leave_type):
    """Test creating a new leave request"""
    payload = {
        "leave_type_id": test_leave_type.leave_type_id,
        "date_from": "2025-06-20",
        "date_to": "2025-06-22",
        "reason": "Personal day off"
    }
    
    response = client.post("/employee-dashboard/leave-requests", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "leave_id" in data

def test_create_overtime_request(test_user):
    """Test creating a new overtime request"""
    payload = {
        "date": "2025-06-18",
        "hours_requested": 2.0,
        "reason": "Extra work for project completion"
    }
    
    response = client.post("/employee-dashboard/overtime-requests", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "ot_id" in data

def test_employee_dashboard_service_methods(test_user, test_leave_type, test_leave_request, test_overtime_request, test_attendance, test_payroll, test_payslip):
    """Test EmployeeDashboardService methods directly"""
    db = TestingSessionLocal()
    
    try:
        # Test get_days_worked_this_month
        days_worked = EmployeeDashboardService.get_days_worked_this_month(db, test_user.user_id)
        assert isinstance(days_worked, int)
        assert days_worked >= 0
        
        # Test get_remaining_leave_balance
        leave_balance = EmployeeDashboardService.get_remaining_leave_balance(db, test_user.user_id)
        assert isinstance(leave_balance, dict)
        assert len(leave_balance) > 0
        
        # Test get_total_overtime_hours_this_month
        overtime_hours = EmployeeDashboardService.get_total_overtime_hours_this_month(db, test_user.user_id)
        assert isinstance(overtime_hours, float)
        assert overtime_hours >= 0
        
        # Test get_latest_payslip
        latest_payslip = EmployeeDashboardService.get_latest_payslip(db, test_user.user_id)
        assert latest_payslip is not None
        assert "payroll_id" in latest_payslip
        assert "net_pay" in latest_payslip
        
        # Test get_attendance_summary_current_month
        attendance_summary = EmployeeDashboardService.get_attendance_summary_current_month(db, test_user.user_id)
        assert isinstance(attendance_summary, list)
        
        # Test get_personal_attendance_log
        attendance_log = EmployeeDashboardService.get_personal_attendance_log(db, test_user.user_id)
        assert isinstance(attendance_log, list)
        
        # Test get_personal_leave_request_history
        leave_history = EmployeeDashboardService.get_personal_leave_request_history(db, test_user.user_id)
        assert isinstance(leave_history, list)
        
        # Test get_personal_overtime_request_history
        overtime_history = EmployeeDashboardService.get_personal_overtime_request_history(db, test_user.user_id)
        assert isinstance(overtime_history, list)
        
        # Test get_personal_payroll_history
        payroll_history = EmployeeDashboardService.get_personal_payroll_history(db, test_user.user_id)
        assert isinstance(payroll_history, list)
        
    finally:
        db.close()

def test_unauthorized_access():
    """Test that unauthorized access is blocked"""
    response = client.get("/employee-dashboard/kpi")
    assert response.status_code == 401

def test_invalid_date_format():
    """Test creating leave request with invalid date format"""
    payload = {
        "leave_type_id": 1,
        "date_from": "invalid-date",
        "date_to": "2025-06-22",
        "reason": "Test reason"
    }
    
    response = client.post("/employee-dashboard/leave-requests", json=payload)
    assert response.status_code == 422

def test_invalid_hours_format():
    """Test creating overtime request with invalid hours format"""
    payload = {
        "date": "2025-06-18",
        "hours_requested": "invalid-hours",
        "reason": "Test reason"
    }
    
    response = client.post("/employee-dashboard/overtime-requests", json=payload)
    assert response.status_code == 422