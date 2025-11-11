import pytest
import os
import sys
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal, engine, get_db
from backend.models import Base, User, Role, Permission, RolePermission, Department, Attendance, Payroll, LeaveRequest, OvertimeRequest, ActivityLog, LeaveType
from backend.main import app

# Test database URL - using MySQL test database
TEST_DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/alpha_hr_test"

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL, echo=False, future=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables for test database
print("Creating test database tables...")
Base.metadata.create_all(bind=test_engine)
print("Test database tables created successfully!")

@pytest.fixture(scope="session")
def db_session():
    """Create a test database session."""
    # Create tables
    print("Creating test database tables...")
    Base.metadata.create_all(bind=test_engine)
    print("Test database tables created successfully!")
    
    # Use test session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after testing
        Base.metadata.drop_all(bind=test_engine)
        print("Test database tables dropped!")

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def admin_token(client):
    """Create admin user and return token."""
    # Create admin user directly in database
    db = TestingSessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "junnel@alphasys.com.au").first()
        if existing_admin:
            # Generate token for existing user
            from backend.main import create_access_token
            token = create_access_token(data={"sub": existing_admin.username, "role": existing_admin.role_name})
            return {"Authorization": f"Bearer {token}"}
        
        # Create admin role if not exists
        admin_role = db.query(Role).filter(Role.role_name == "admin").first()
        if not admin_role:
            admin_role = Role(role_name="admin", description="System administrator")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        
        # Create admin user
        admin_user = User(
            username="junnel@alphasys.com.au",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDrZiZ2kYZOjWPK",  # hashed "password"
            first_name="Admin",
            last_name="User",
            email="junnel@alphasys.com.au",
            role_name="admin",
            hourly_rate=0.0,
            date_hired=date(2025, 1, 1),
            status="active"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create default leave type
        leave_type = db.query(LeaveType).filter(LeaveType.leave_name == "Annual Leave").first()
        if not leave_type:
            leave_type = LeaveType(leave_name="Annual Leave", default_allocation=20)
            db.add(leave_type)
            db.commit()
            db.refresh(leave_type)
        
        # Create token
        from backend.main import create_access_token
        token = create_access_token(data={"sub": admin_user.username, "role": admin_user.role_name})
        
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()

def auth_headers(token: str):
    """Create authentication headers."""
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_fixture(admin_token):
    """Return authentication headers for admin."""
    # admin_token is already in the correct format {"Authorization": "Bearer <token>"}
    return admin_token

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Create employee role if not exists
    employee_role = db_session.query(Role).filter(Role.role_name == "employee").first()
    if not employee_role:
        employee_role = Role(role_name="employee", description="Regular employee")
        db_session.add(employee_role)
        db_session.commit()
        db_session.refresh(employee_role)
    
    # Create test department if not exists
    department = db_session.query(Department).filter(Department.department_name == "Test Department").first()
    if not department:
        department = Department(department_name="Test Department")
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)
    
    # Create test user
    test_user = User(
        username="testuser@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDrZiZ2kYZOjWPK",  # hashed "password"
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        role_name="employee",
        hourly_rate=25.0,
        date_hired=date(2025, 1, 1),
        status="active",
        department_id=department.department_id
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    
    return test_user

# Override the get_db dependency for testing
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the database dependency in the app
app.dependency_overrides[get_db] = override_get_db

# Set testing environment variable
import os
os.environ["TESTING"] = "true"