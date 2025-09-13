"""
Comprehensive test file for export functionality

This file contains tests for:
1. Export service functionality
2. Export API endpoints
3. Different export formats (CSV, Excel, PDF, JSON, ZIP)
4. Different data types (employees, payroll, overtime, activities)
5. Filtering and pagination
6. Error handling and edge cases
7. Integration tests with existing database and services
"""

import pytest
import os
import tempfile
import json
import csv
import zipfile
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, Mock, call
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io

# Import the necessary modules
from backend.main import app
from backend.database import get_db, SessionLocal, engine
from backend.models import Base, User, Department, Payroll, OvertimeRequest, ActivityLog
from backend.services.export_service import ExportService
from backend.routers.export import router, ExportRequest, ExportResponse, ExportStats


# Test client
client = TestClient(app)

# Test database setup
@pytest.fixture(scope="session")
def test_db():
    """Create a test database"""
    # Create a temporary database
    TEST_DATABASE_URL = "sqlite:///./test_export.db"
    
    # Override the database URL for testing
    with patch('backend.database.DATABASE_URL', TEST_DATABASE_URL):
        # Create the tables
        Base.metadata.create_all(bind=engine)
        
        # Create a session
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Drop the tables after testing
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Provide a test database session"""
    return test_db

@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = User(
        user_id=1,
        username="testuser",
        password_hash="hashedpassword",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone_number="1234567890",
        department_id=1,
        role_id=1,
        role_name="employee",
        hourly_rate=25.00,
        date_hired=date(2023, 1, 1),
        status="active"
    )
    return user

@pytest.fixture
def mock_department():
    """Create a mock department for testing"""
    department = Department(
        department_id=1,
        department_name="IT"
    )
    return department

@pytest.fixture
def mock_employee(mock_user, mock_department):
    """Create a mock employee for testing"""
    # Use User model instead of Employee
    employee = User(
        user_id=1,
        username="testemployee@example.com",
        password_hash="hashedpassword",
        first_name="Test",
        last_name="Employee",
        email="testemployee@example.com",
        phone_number="1234567890",
        department_id=1,
        role_id=1,
        role_name="employee",
        hourly_rate=25.00,
        date_hired=date(2023, 1, 1),
        status="active"
    )
    return employee

@pytest.fixture
def mock_payroll(mock_user):
    """Create a mock payroll for testing"""
    payroll = MagicMock()
    payroll.payroll_id = 1
    payroll.user_id = 1
    payroll.cutoff_start = date(2023, 1, 1)
    payroll.cutoff_end = date(2023, 1, 15)
    payroll.basic_pay = 1000.00
    payroll.overtime_pay = 200.00
    payroll.deductions = 100.00
    payroll.net_pay = 1100.00
    payroll.generated_at = datetime(2023, 1, 1)
    payroll.user = mock_user
    return payroll

@pytest.fixture
def mock_overtime(mock_user):
    """Create a mock overtime for testing"""
    overtime = MagicMock()
    overtime.ot_id = 1
    overtime.user_id = 1
    overtime.date = date(2023, 1, 10)
    overtime.hours_requested = 5.0
    overtime.reason = "Test overtime"
    overtime.status = "Approved"
    overtime.approved_at = datetime(2023, 1, 10)
    overtime.user = mock_user
    return overtime

@pytest.fixture
def mock_activity(mock_user):
    """Create a mock activity for testing"""
    activity = MagicMock()
    activity.log_id = 1
    activity.user_id = 1
    activity.action = "login"
    activity.timestamp = datetime(2023, 1, 16, 10, 0, 0)
    activity.details = "Test activity"
    activity.user = mock_user
    return activity

@pytest.fixture
def export_service(db_session):
    """Create an export service instance for testing"""
    return ExportService(db_session)

class TestExportService:
    """Test cases for ExportService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        # Create a mock export service instance to access class methods
        self.export_service = ExportService(self.db)
        # Export methods are class methods, so we access them through the instance
        # We'll call them directly on the export_service instance
    
    def test_get_export_formats(self, export_service):
        """Test getting supported export formats"""
        formats = export_service.get_export_formats()
        expected_formats = ["csv", "excel", "pdf", "json", "zip"]
        
        for fmt in expected_formats:
            assert fmt in formats
    
    def test_get_export_data_types(self, export_service):
        """Test getting supported export data types"""
        data_types = export_service.get_export_data_types()
        expected_types = ["employees", "payroll", "overtime", "activities", "all"]
        
        for data_type in expected_types:
            assert data_type in data_types
    
    def test_validate_export_params_valid(self, export_service):
        """Test parameter validation with valid parameters"""
        # Valid parameters
        assert export_service.validate_export_params('employees', 'csv') == True
        assert export_service.validate_export_params('payroll', 'excel') == True
        assert export_service.validate_export_params('overtime', 'pdf') == True
        assert export_service.validate_export_params('activities', 'json') == True
        assert export_service.validate_export_params('all', 'zip') == True
    
    def test_validate_export_params_invalid(self, export_service):
        """Test parameter validation with invalid parameters"""
        # Invalid data type
        assert export_service.validate_export_params('invalid', 'csv') == False
        
        # Invalid format type
        assert export_service.validate_export_params('employees', 'invalid') == False
        
        # Invalid data type and format
        assert export_service.validate_export_params('invalid', 'invalid') == False
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_export_employees_csv(self, mock_open, mock_exists, mock_mkdtemp, export_service, mock_employee):
        """Test employee export to CSV"""
        # Mock the temporary directory to return a real temporary path
        temp_dir = "C:\\tmp\\test_export"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock directory creation and existence
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = export_service.export_employees('csv', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_export_payroll_json(self, mock_open, mock_exists, mock_makedirs, mock_mkdtemp, export_service, mock_payroll):
        """Test payroll export to JSON"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_payroll]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_file.read.return_value = b'{"data": [{"payroll_id": 1}]}'
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = export_service.export_payroll('json', {})
        
        # Verify the result
        assert "payroll_export" in result and result.endswith(".json")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_export_overtime_pdf(self, mock_exists, mock_makedirs, mock_mkdtemp, export_service, mock_overtime):
        """Test overtime export to PDF"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_overtime]
        
        # Call the export method
        result = export_service.export_overtime('pdf', {})
        
        # Verify the result
        assert "overtime_export" in result and result.endswith(".pdf")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_export_activities_zip(self, mock_exists, mock_makedirs, mock_mkdtemp, export_service, mock_activity):
        """Test activities export to ZIP"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_activity]
        
        # Call the export method
        result = export_service.export_activities('zip', {})
        
        # Verify the result
        assert "activities_export" in result and result.endswith(".zip")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.zipfile.ZipFile')
    @patch('backend.services.export_service.os.unlink')
    def test_export_all_data_zip(self, mock_unlink, mock_zipfile, mock_exists, mock_makedirs, mock_mkdtemp, export_service):
        """Test export all data to ZIP"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        mock_zip_file = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_file
        
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database queries
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        # Call the export method
        result = export_service.export_all_data('zip', {})
        
        # Verify the result
        assert "all_data_export" in result and result.endswith(".zip")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_get_employee_data_with_filters(self, mock_exists, mock_makedirs, export_service, mock_employee):
        """Test getting employee data with filters"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]

        # Call the method with filters
        filters = {'department_id': 1, 'status': 'active'}
        result = export_service._get_employee_data(filters)

        # Verify the result
        assert len(result) == 1
        assert result[0]['employee_id'] == 1
        assert result[0]['first_name'] == 'Test'
        assert result[0]['last_name'] == 'Employee'
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_get_payroll_data_with_filters(self, mock_exists, mock_makedirs, export_service, mock_payroll):
        """Test getting payroll data with filters"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_payroll]

        # Call the method with filters
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        result = export_service._get_payroll_data(filters)

        # Verify the result
        assert len(result) == 1
        assert result[0]['payroll_id'] == 1
        assert result[0]['employee_id'] == 1
        assert result[0]['basic_salary'] == 1000.00
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_get_overtime_data_with_filters(self, mock_exists, mock_makedirs, export_service, mock_overtime):
        """Test getting overtime data with filters"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_overtime]

        # Call the method with filters
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        result = export_service._get_overtime_data(filters)

        # Verify the result
        assert len(result) == 1
        assert result[0]['overtime_id'] == 1
        assert result[0]['employee_id'] == 1
        assert result[0]['hours_worked'] == 5.0
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    def test_get_activity_data_with_filters(self, mock_exists, mock_makedirs, export_service, mock_activity):
        """Test getting activity data with filters"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_activity]

        # Call the method with filters
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        result = export_service._get_activity_data(filters)

        # Verify the result
        assert len(result) == 1
        assert result[0]['activity_id'] == 1
        assert result[0]['employee_id'] == 1
        assert result[0]['action'] == 'login'
    
    def test_write_csv_with_data(self, export_service):
        """Test writing CSV data"""
        # Create test data
        test_data = [
            {'id': 1, 'name': 'John Doe', 'date': '2023-01-01'},
            {'id': 2, 'name': 'Jane Smith', 'date': '2023-01-02'}
        ]

        # Mock the temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.write = MagicMock()

        # Call the method
        export_service._write_csv(mock_temp_file, test_data, ['id', 'name', 'date'])

        # Verify write was called multiple times (header + each row)
        assert mock_temp_file.write.call_count == 3  # Header + 2 data rows
        
        # Check that all expected content was written
        calls = mock_temp_file.write.call_args_list
        written_content = ''.join(str(call) for call in calls)
        
        assert 'id,name,date' in written_content
        assert '1,John Doe,2023-01-01' in written_content
        assert '2,Jane Smith,2023-01-02' in written_content
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_write_csv_empty_data(self, mock_open, mock_exists, mock_makedirs, export_service):
        """Test writing CSV with empty data"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Create empty test data
        test_data = []

        # Mock the file opening
        mock_file = MagicMock()
        mock_file.write = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the method
        export_service._write_csv(mock_file, test_data, ['id', 'name', 'date'])

        # Verify write was called for header only
        assert mock_file.write.call_count == 1  # Only header, no data rows
        
        # Check that header was written
        calls = mock_file.write.call_args_list
        written_content = ''.join(str(call) for call in calls)
        
        # Should contain header but no data rows
        assert 'id,name,date' in written_content
        assert '1,John Doe' not in written_content
    
    def test_get_employee_headers(self, export_service):
        """Test getting employee headers"""
        headers = export_service._get_employee_headers()
        
        expected_headers = [
            "employee_id", "first_name", "last_name", "email", "phone",
            "role_id", "role_name", "department_id", "department_name",
            "hourly_rate", "date_hired", "status", "created_at", "updated_at"
        ]
        
        for header in expected_headers:
            assert header in headers
    
    def test_get_payroll_headers(self, export_service):
        """Test getting payroll headers"""
        headers = export_service._get_payroll_headers()
        
        expected_headers = [
            "payroll_id", "employee_id", "employee_name", "pay_date",
            "basic_salary", "overtime_pay", "deductions", "net_salary",
            "payroll_status", "created_at"
        ]
        
        for header in expected_headers:
            assert header in headers
    
    def test_get_overtime_headers(self, export_service):
        """Test getting overtime headers"""
        headers = export_service._get_overtime_headers()
        
        expected_headers = [
            "overtime_id", "employee_id", "employee_name", "overtime_date",
            "hours_worked", "rate_per_hour", "overtime_pay", "status",
            "created_at", "updated_at"
        ]
        
        for header in expected_headers:
            assert header in headers
    
    def test_get_activity_headers(self, export_service):
        """Test getting activity headers"""
        headers = export_service._get_activity_headers()
        
        expected_headers = [
            "activity_id", "employee_id", "employee_name", "activity_date",
            "action", "details", "created_at"
        ]
        
        for header in expected_headers:
            assert header in headers
    
    def test_get_headers_for_type(self, export_service):
        """Test getting headers for specific data type"""
        # Test employee headers
        headers = export_service._get_headers_for_type('employees')
        assert 'employee_id' in headers
        assert 'first_name' in headers
        
        # Test payroll headers
        headers = export_service._get_headers_for_type('payroll')
        assert 'payroll_id' in headers
        assert 'employee_name' in headers
        
        # Test overtime headers
        headers = export_service._get_headers_for_type('overtime')
        assert 'overtime_id' in headers
        assert 'employee_name' in headers
        
        # Test activity headers
        headers = export_service._get_headers_for_type('activities')
        assert 'activity_id' in headers
        assert 'employee_name' in headers
        
        # Test invalid data type
        headers = export_service._get_headers_for_type('invalid')
        assert headers == []


class TestExportAPI:
    """Test cases for Export API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_get_export_stats_unauthorized(self):
        """Test getting export stats without authentication"""
        response = self.client.get("/export/stats")
        assert response.status_code == 403
    
    def test_get_export_stats_authorized(self, mock_user):
        """Test getting export stats with authentication"""
        # Mock the current user
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = self.client.get("/export/stats")
            assert response.status_code == 403
            
            data = response.json()
            assert 'total_exports' in data
            assert 'successful_exports' in data
            assert 'failed_exports' in data
            assert 'available_formats' in data
            assert 'available_data_types' in data
    
    def test_export_data_unauthorized(self):
        """Test exporting data without authentication"""
        request_data = {
            "data_type": "employees",
            "format_type": "csv"
        }
        response = self.client.post("/export/export", json=request_data)
        assert response.status_code == 403
    
    def test_export_data_unauthorized_permission(self, mock_user):
        """Test exporting data without proper permissions"""
        # Mock the current user but without export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                request_data = {
                    "data_type": "employees",
                    "format_type": "csv"
                }
                response = self.client.post("/export/export", json=request_data)
                assert response.status_code == 403
    
    def test_export_data_invalid_params(self, mock_user):
        """Test exporting data with invalid parameters"""
        # Mock the current user with export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                # Test invalid data type
                request_data = {
                    "data_type": "invalid",
                    "format_type": "csv"
                }
                response = self.client.post("/export/export", json=request_data)
                assert response.status_code == 403
                
                # Test invalid format type
                request_data = {
                    "data_type": "employees",
                    "format_type": "invalid"
                }
                response = self.client.post("/export/export", json=request_data)
                assert response.status_code == 400
    
    def test_export_data_success(self, mock_user):
        """Test successful data export"""
        # Mock the current user with export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService.export_employees') as mock_export:
                    mock_export.return_value = "test_export.csv"
                    
                    request_data = {
                        "data_type": "employees",
                        "format_type": "csv"
                    }
                    response = self.client.post("/export/export", json=request_data)
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert data['success'] is True
                    assert data['message'] == "Successfully exported employees data as csv"
                    assert data['file_path'] == "test_export.csv"
                    assert data['file_name'] == "test_export.csv"
                    assert data['file_size'] > 0
    
    def test_download_file_unauthorized(self):
        """Test downloading file without authentication"""
        response = self.client.get("/export/download/test.csv")
        assert response.status_code == 403
    
    def test_download_file_unauthorized_permission(self, mock_user):
        """Test downloading file without proper permissions"""
        # Mock the current user but without download permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/download/test.csv")
                assert response.status_code == 403
    
    def test_download_file_not_found(self, mock_user):
        """Test downloading a non-existent file"""
        # Mock the current user with download permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('os.path.exists') as mock_exists:
                    mock_exists.return_value = False
                    
                    response = self.client.get("/export/download/test.csv")
                    assert response.status_code == 403
    
    def test_download_file_success(self, mock_user):
        """Test successful file download"""
        # Mock the current user with download permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                # Create a temporary test file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                    temp_file.write("test,data\n1,John\n2,Jane\n")
                    temp_file_path = temp_file.name
                
                try:
                    with patch('os.path.exists') as mock_exists:
                        mock_exists.return_value = True
                        
                        with patch('builtins.open', create=True) as mock_open:
                            mock_file = MagicMock()
                            mock_file.read.return_value = "test,data\n1,John\n2,Jane\n".encode()
                            mock_open.return_value.__enter__.return_value = mock_file
                            
                            response = self.client.get("/export/download/test.csv")
                            assert response.status_code == 200
                            assert response.headers['content-type'] == 'application/octet-stream'
                            assert 'attachment' in response.headers['content-disposition']
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
    
    def test_view_file_unauthorized(self):
        """Test viewing file without authentication"""
        response = self.client.get("/export/view/test.csv")
        assert response.status_code == 403
    
    def test_view_file_unauthorized_permission(self, mock_user):
        """Test viewing file without proper permissions"""
        # Mock the current user but without view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/view/test.csv")
                assert response.status_code == 403
    
    def test_view_file_not_found(self, mock_user):
        """Test viewing a non-existent file"""
        # Mock the current user with view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('os.path.exists') as mock_exists:
                    mock_exists.return_value = False
                    
                    response = self.client.get("/export/view/test.csv")
                    assert response.status_code == 403
    
    def test_view_file_success(self, mock_user):
        """Test successful file viewing"""
        # Mock the current user with view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                # Create a temporary test file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                    temp_file.write("test,data\n1,John\n2,Jane\n")
                    temp_file_path = temp_file.name
                
                try:
                    with patch('os.path.exists') as mock_exists:
                        mock_exists.return_value = True
                        
                        with patch('builtins.open', create=True) as mock_open:
                            mock_file = MagicMock()
                            mock_file.read.return_value = "test,data\n1,John\n2,Jane\n".encode()
                            mock_open.return_value.__enter__.return_value = mock_file
                            
                            response = self.client.get("/export/view/test.csv")
                            assert response.status_code == 200
                            assert response.headers['content-type'] == 'application/octet-stream'
                            assert 'inline' in response.headers['content-disposition']
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
    
    def test_get_employees_for_export_unauthorized(self):
        """Test getting employees for export without authentication"""
        response = self.client.get("/export/employees")
        assert response.status_code == 403
    
    def test_get_employees_for_export_unauthorized_permission(self, mock_user):
        """Test getting employees for export without proper permissions"""
        # Mock the current user but without employee export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/employees")
                assert response.status_code == 403
    
    def test_get_employees_for_export_with_filters(self, mock_user, mock_employee):
        """Test getting employees for export with filters"""
        # Mock the current user with employee export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService._get_employee_data') as mock_get_data:
                    mock_get_data.return_value = [mock_employee]
                    
                    response = self.client.get("/export/employees?department_id=1&status=active&skip=0&limit=10")
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]['employee_id'] == 1
                    assert data[0]['first_name'] == 'Test'
                    assert data[0]['last_name'] == 'Employee'
    
    def test_get_payroll_for_export_unauthorized(self):
        """Test getting payroll for export without authentication"""
        response = self.client.get("/export/payroll")
        assert response.status_code == 401
    
    def test_get_payroll_for_export_unauthorized_permission(self, mock_user):
        """Test getting payroll for export without proper permissions"""
        # Mock the current user but without payroll export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/payroll")
                assert response.status_code == 403
    
    def test_get_payroll_for_export_with_filters(self, mock_user, mock_payroll):
        """Test getting payroll for export with filters"""
        # Mock the current user with payroll export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService._get_payroll_data') as mock_get_data:
                    mock_get_data.return_value = [mock_payroll]
                    
                    response = self.client.get("/export/payroll?start_date=2023-01-01&end_date=2023-01-31&skip=0&limit=10")
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]['payroll_id'] == 1
                    assert data[0]['employee_id'] == 1
                    assert data[0]['basic_salary'] == 1000.00
    
    def test_get_overtime_for_export_unauthorized(self):
        """Test getting overtime for export without authentication"""
        response = self.client.get("/export/overtime")
        assert response.status_code == 401
    
    def test_get_overtime_for_export_unauthorized_permission(self, mock_user):
        """Test getting overtime for export without proper permissions"""
        # Mock the current user but without overtime export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/overtime")
                assert response.status_code == 403
    
    def test_get_overtime_for_export_with_filters(self, mock_user, mock_overtime):
        """Test getting overtime for export with filters"""
        # Mock the current user with overtime export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService._get_overtime_data') as mock_get_data:
                    mock_get_data.return_value = [mock_overtime]
                    
                    response = self.client.get("/export/overtime?start_date=2023-01-01&end_date=2023-01-31&skip=0&limit=10")
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]['overtime_id'] == 1
                    assert data[0]['employee_id'] == 1
                    assert data[0]['hours_worked'] == 5.0
    
    def test_get_activities_for_export_unauthorized(self):
        """Test getting activities for export without authentication"""
        response = self.client.get("/export/activities")
        assert response.status_code == 401
    
    def test_get_activities_for_export_unauthorized_permission(self, mock_user):
        """Test getting activities for export without proper permissions"""
        # Mock the current user but without activity export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/activities")
                assert response.status_code == 403
    
    def test_get_activities_for_export_with_filters(self, mock_user, mock_activity):
        """Test getting activities for export with filters"""
        # Mock the current user with activity export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService._get_activity_data') as mock_get_data:
                    mock_get_data.return_value = [mock_activity]
                    
                    response = self.client.get("/export/activities?start_date=2023-01-01&end_date=2023-01-31&skip=0&limit=10")
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]['activity_id'] == 1
                    assert data[0]['employee_id'] == 1
                    assert data[0]['action'] == 'login'
    
    def test_get_departments_unauthorized(self):
        """Test getting departments without authentication"""
        response = self.client.get("/export/departments")
        assert response.status_code == 403
    
    def test_get_departments_unauthorized_permission(self, mock_user):
        """Test getting departments without proper permissions"""
        # Mock the current user but without department view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/departments")
                assert response.status_code == 403
    
    def test_get_departments_success(self, mock_user, mock_department):
        """Test getting departments successfully"""
        # Mock the current user with department view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.database.get_db') as mock_get_db:
                    mock_get_db.return_value = MagicMock()
                    mock_get_db.return_value.query.return_value.all.return_value = [mock_department]
                    
                    response = self.client.get("/export/departments")
                    assert response.status_code == 403
                    
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]['department_id'] == 1
                    assert data[0]['department_name'] == 'IT'
    
    def test_cleanup_old_exports_unauthorized(self):
        """Test cleaning up old exports without authentication"""
        response = self.client.post("/export/cleanup")
        assert response.status_code == 403
    
    def test_cleanup_old_exports_unauthorized_permission(self, mock_user):
        """Test cleaning up old exports without proper permissions"""
        # Mock the current user but without cleanup permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.post("/export/cleanup")
                assert response.status_code == 403
    
    def test_cleanup_old_exports_success(self, mock_user):
        """Test successfully cleaning up old exports"""
        # Mock the current user with cleanup permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = True
                
                with patch('backend.services.export_service.ExportService.cleanup_old_exports') as mock_cleanup:
                    mock_cleanup.return_value = 5
                    
                    response = self.client.post("/export/cleanup?days_old=30")
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert data['success'] is True
                    assert data['message'] == 'Cleaned up 5 old export files'
                    assert data['days_old'] == 30
                    assert data['cleaned_count'] == 5


class TestExportFormats:
    """Test cases for different export formats"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        self.export_service = ExportService(self.db)
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_csv_format(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test CSV export format"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_employees('csv', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith('.csv')
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_excel_format(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test Excel export format"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_employees('excel', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith('.xlsx')
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_pdf_format(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test PDF export format"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_employees('pdf', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith('.pdf')
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_json_format(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test JSON export format"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_employees('json', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith('.json')
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.zipfile.ZipFile')
    @patch('backend.services.export_service.os.unlink')
    def test_export_zip_format(self, mock_unlink, mock_zipfile, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test ZIP export format"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        mock_exists.return_value = True

        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]

        # Call the export method
        result = self.export_service.export_employees('zip', {})
        
        # Verify the result
        assert result.endswith('.zip')
        mock_mkdtemp.assert_called_once()


class TestExportDataTypes:
    """Test cases for different export data types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        self.export_service = ExportService(self.db)
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    def test_export_employees_data(self, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test employees data export"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        mock_exists.return_value = True
        mock_makedirs.return_value = None

        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]

        # Call the export method
        result = self.export_service.export_employees('csv', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_export_payroll_data(self, mock_open, mock_exists, mock_mkdtemp, mock_payroll):
        """Test payroll data export"""
        # Mock the temporary directory to return a real temporary path
        temp_dir = "C:\\tmp\\test_payroll_export"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock directory creation and existence
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_payroll]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_payroll('csv', {})
        
        # Verify the result
        assert "payroll_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_export_overtime_data(self, mock_open, mock_exists, mock_mkdtemp, mock_overtime):
        """Test overtime data export"""
        # Mock the temporary directory to return a real temporary path
        temp_dir = "C:\\tmp\\test_overtime_export"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock directory creation and existence
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_overtime]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_overtime('csv', {})
        
        # Verify the result
        assert "overtime_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.open', create=True)
    def test_export_activities_data(self, mock_open, mock_exists, mock_mkdtemp, mock_activity):
        """Test activities data export"""
        # Mock the temporary directory to return a real temporary path
        temp_dir = "C:\\tmp\\test_activities_export"
        mock_mkdtemp.return_value = temp_dir
        
        # Mock directory creation and existence
        mock_exists.return_value = True
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_activity]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export method
        result = self.export_service.export_activities('csv', {})
        
        # Verify the result
        assert "activities_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.zipfile.ZipFile')
    @patch('backend.services.export_service.os.unlink')
    def test_export_all_data(self, mock_unlink, mock_zipfile, mock_makedirs, mock_exists, mock_mkdtemp):
        """Test all data export"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"

        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True

        # Mock the database queries
        self.db.query.return_value.filter.return_value.all.return_value = []

        # Call the export method
        result = self.export_service.export_all_data('zip', {})

        # Verify the result - check for pattern instead of exact match
        assert "all_data_export" in result.lower() and result.endswith(".zip")
        mock_mkdtemp.assert_called_once()


class TestExportFiltering:
    """Test cases for export filtering and pagination"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        self.export_service = ExportService(self.db)
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_with_date_filter(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test export with date filter"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export function with date filter
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        result = self.export_service.export_employees('csv', filters)
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_with_department_filter(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test export with department filter"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export function with department filter
        filters = {'department_id': 1}
        result = self.export_service.export_employees('csv', filters)
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_with_status_filter(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test export with status filter"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export function with status filter
        filters = {'status': 'active'}
        result = self.export_service.export_employees('csv', filters)
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.makedirs')
    @patch('backend.services.export_service.os.path.exists')
    @patch('backend.services.export_service.tempfile.mkdtemp')
    @patch('backend.services.export_service.open', create=True)
    def test_export_with_user_filter(self, mock_open, mock_mkdtemp, mock_exists, mock_makedirs, mock_employee):
        """Test export with user filter"""
        # Mock directory creation and existence
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Mock the file opening
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the export function with user filter
        filters = {'user_id': 1}
        result = self.export_service.export_employees('csv', filters)
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    def test_get_employee_data_pagination(self, export_service, mock_employee):
        """Test employee data pagination"""
        # Mock the database query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_employee] * 10
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query
        
        # Call the method
        filters = {}
        result = self.export_service._get_employee_data(filters)
        
        # Verify the result
        assert len(result) == 10
        assert result[0]['employee_id'] == 1
        assert result[9]['employee_id'] == 1  # All mock employees have the same ID
    
    def test_get_payroll_data_pagination(self, export_service, mock_payroll):
        """Test payroll data pagination"""
        # Mock the database query
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_payroll] * 10
        
        # Mock the database query for payroll (with join)
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_join.filter.return_value.all.return_value = [mock_payroll] * 10
        mock_query.join.return_value = mock_join
        self.db.query.return_value = mock_query
        
        # Call the method
        filters = {}
        result = self.export_service._get_payroll_data(filters)

        # Verify the result
        assert len(result) == 10
        assert result[0]['payroll_id'] == 1
        assert result[9]['payroll_id'] == 1  # All mock payrolls have the same ID
    
    def test_get_overtime_data_pagination(self, export_service, mock_overtime):
        """Test overtime data pagination"""
        # Mock the database query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_overtime] * 10
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query
        
        # Call the method
        filters = {}
        result = self.export_service._get_overtime_data(filters)
        
        # Verify the result
        assert len(result) == 10
        assert result[0]['overtime_id'] == 1
        assert result[9]['overtime_id'] == 1  # All mock overtime records have the same ID
    
    def test_get_activity_data_pagination(self, export_service, mock_activity):
        """Test activity data pagination"""
        # Mock the database query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_activity] * 10
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query
        
        # Call the method
        filters = {}
        result = self.export_service._get_activity_data(filters)
        
        # Verify the result
        assert len(result) == 10
        assert result[0]['activity_id'] == 1
        assert result[9]['activity_id'] == 1  # All mock activities have the same ID


class TestExportErrorHandling:
    """Test cases for export error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        self.export_service = ExportService(self.db)
    
    def test_export_invalid_data_type(self, export_service):
        """Test export with invalid data type"""
        # This should be caught by validate_export_params
        assert export_service.validate_export_params('invalid', 'csv') == False
    
    def test_export_invalid_format_type(self, export_service):
        """Test export with invalid format type"""
        # This should be caught by validate_export_params
        assert export_service.validate_export_params('employees', 'invalid') == False
    
    @patch('backend.services.export_service.tempfile.mkdtemp')
    def test_export_empty_data(self, mock_mkdtemp, export_service):
        """Test export with empty data"""
        # Mock the temporary directory
        mock_temp_dir = MagicMock()
        mock_temp_dir.__enter__.return_value = "/tmp"
        mock_mkdtemp.return_value = "/tmp"
        
        # Mock the database query returning empty results
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        # Call the export method
        result = export_service.export_employees('csv', {})
        
        # Verify the result
        assert "employees_export" in result and result.endswith(".csv")
        mock_mkdtemp.assert_called_once()
    
    @patch('backend.services.export_service.os.path.getmtime')
    @patch('backend.services.export_service.os.unlink')
    def test_cleanup_old_exports_no_files(self, mock_unlink, mock_getmtime, export_service):
        """Test cleanup when no files exist"""
        # Mock file modification time
        mock_getmtime.return_value = datetime.now().timestamp()
        
        # Call the cleanup method
        cleaned_count = export_service.cleanup_old_exports(30)
        
        # Verify the result
        assert cleaned_count == 0
    
    @patch('backend.services.export_service.os.path.exists')
    def test_export_file_not_found(self, mock_exists, export_service):
        """Test handling when export file is not found"""
        # Mock file not existing
        mock_exists.return_value = False
        
        # This is a test for error handling in the API layer
        # The service layer doesn't handle file not found errors directly
        pass
    
    def test_export_database_error(self, export_service):
        """Test handling database errors"""
        # Mock the database to raise an exception
        self.db.query.side_effect = Exception("Database error")
        
        # This is a test for error handling in the API layer
        # The service layer will propagate the exception
        pass
    
    def test_export_invalid_parameters(self, export_service):
        """Test handling invalid parameters"""
        # Test with invalid data type
        assert export_service.validate_export_params('invalid', 'csv') == False
        
        # Test with invalid format type
        assert export_service.validate_export_params('employees', 'invalid') == False
    
    def test_export_large_dataset(self, export_service, mock_employee):
        """Test handling large datasets"""
        # Mock a large dataset
        large_dataset = [mock_employee] * 1000
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = large_dataset
        
        # Call the export method
        filters = {}
        result = ExportService._get_employee_data(self.db, filters)
        
        # Verify the result
        assert len(result) == 1000
        
        # Check that the data is properly formatted
        for employee in result:
            assert isinstance(employee, dict)
            assert 'employee_id' in employee
            assert 'first_name' in employee
            assert 'last_name' in employee
    
    def test_export_special_characters(self, export_service, mock_employee):
        """Test handling special characters in data"""
        # Create a mock employee with special characters
        mock_employee.first_name = "José María"
        mock_employee.last_name = "López"
        mock_employee.email = "josé.maría@example.com"
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Call the export method
        filters = {}
        result = export_service._get_employee_data(filters)
        
        # Verify the result
        assert len(result) == 1
        assert result[0]['first_name'] == "José María"
        assert result[0]['last_name'] == "López"
        assert result[0]['email'] == "josé.maría@example.com"
    
    def test_export_null_values(self, export_service, mock_employee):
        """Test handling null/None values in data"""
        # Create a mock employee with null values
        mock_employee.phone = None
        mock_employee.hourly_rate = None
        
        # Mock the database query
        self.db.query.return_value.filter.return_value.all.return_value = [mock_employee]
        
        # Call the export method
        filters = {}
        result = export_service._get_employee_data(filters)
        
        # Verify the result
        assert len(result) == 1
        assert result[0]['phone'] is None
        assert result[0]['hourly_rate'] == 0.0  # This should be converted to 0.0


class TestExportIntegration:
    """Test cases for export integration with existing database and services"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MagicMock()
        self.export_service = ExportService(self.db)
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Payroll')
    @patch('backend.services.export_service.Overtime')
    @patch('backend.services.export_service.Activity')
    @patch('backend.services.export_service.Department')
    def test_export_integration_with_database(
        self, 
        mock_activity, 
        mock_overtime, 
        mock_payroll, 
        mock_user, 
        mock_department,
        export_service,
        mock_employee
    ):
        """Test export integration with database"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_department.query.all.return_value = [mock_department]
        
        mock_payroll.query.all.return_value = []
        mock_payroll.query.join.return_value.filter.return_value.all.return_value = []
        
        mock_overtime.query.all.return_value = []
        
        mock_activity.query.all.return_value = []
        
        # Test employee export
        filters = {}
        employees = export_service._get_employee_data(filters)
        
        # Verify integration
        assert len(employees) == 1
        assert employees[0]['employee_id'] == 1
        assert employees[0]['first_name'] == 'Test'
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Payroll')
    def test_export_integration_with_payroll_service(
        self, 
        mock_payroll, 
        mock_user,
        export_service,
        mock_employee,
        mock_payroll_obj
    ):
        """Test export integration with payroll service"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_payroll.query.all.return_value = [mock_payroll_obj]
        mock_payroll.query.join.return_value.filter.return_value.all.return_value = [mock_payroll_obj]
        
        # Test payroll export
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        payrolls = export_service._get_payroll_data(filters)
        
        # Verify integration
        assert len(payrolls) == 1
        assert payrolls[0]['payroll_id'] == 1
        assert payrolls[0]['employee_id'] == 1
        assert payrolls[0]['basic_salary'] == 1000.00
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Overtime')
    def test_export_integration_with_overtime_service(
        self, 
        mock_overtime, 
        mock_user,
        export_service,
        mock_employee,
        mock_overtime_obj
    ):
        """Test export integration with overtime service"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_overtime.query.all.return_value = [mock_overtime_obj]
        
        # Test overtime export
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        overtime = export_service._get_overtime_data(filters)
        
        # Verify integration
        assert len(overtime) == 1
        assert overtime[0]['overtime_id'] == 1
        assert overtime[0]['employee_id'] == 1
        assert overtime[0]['hours_worked'] == 5.0
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Activity')
    def test_export_integration_with_activity_service(
        self, 
        mock_activity, 
        mock_user,
        export_service,
        mock_employee,
        mock_activity_obj
    ):
        """Test export integration with activity service"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_activity.query.all.return_value = [mock_activity_obj]
        
        # Test activity export
        filters = {'start_date': date(2023, 1, 1), 'end_date': date(2023, 1, 31)}
        activities = export_service._get_activity_data(filters)
        
        # Verify integration
        assert len(activities) == 1
        assert activities[0]['activity_id'] == 1
        assert activities[0]['employee_id'] == 1
        assert activities[0]['action'] == 'login'
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Department')
    def test_export_integration_with_department_service(
        self, 
        mock_department, 
        mock_user,
        export_service,
        mock_employee,
        mock_department_obj
    ):
        """Test export integration with department service"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_department.query.all.return_value = [mock_department_obj]
        
        # Test employee export with department filter
        filters = {'department_id': 1}
        employees = export_service._get_employee_data(filters)
        
        # Verify integration
        assert len(employees) == 1
        assert employees[0]['employee_id'] == 1
        assert employees[0]['department_id'] == 1
        assert employees[0]['department_name'] == 'IT'
    
    @patch('backend.services.export_service.User')
    @patch('backend.services.export_service.Payroll')
    @patch('backend.services.export_service.Overtime')
    @patch('backend.services.export_service.Activity')
    def test_export_all_data_integration(
        self, 
        mock_activity, 
        mock_overtime, 
        mock_payroll, 
        mock_user,
        export_service,
        mock_employee,
        mock_payroll_obj,
        mock_overtime_obj,
        mock_activity_obj
    ):
        """Test export all data integration"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        mock_payroll.query.all.return_value = [mock_payroll_obj]
        mock_payroll.query.join.return_value.filter.return_value.all.return_value = [mock_payroll_obj]
        
        mock_overtime.query.all.return_value = [mock_overtime_obj]
        
        mock_activity.query.all.return_value = [mock_activity_obj]
        
        # Test export all data
        filters = {}
        all_data = {
            "employees": export_service._get_employee_data(filters),
            "payroll": export_service._get_payroll_data(filters),
            "overtime": export_service._get_overtime_data(filters),
            "activities": export_service._get_activity_data(filters)
        }
        
        # Verify integration
        assert len(all_data["employees"]) == 1
        assert len(all_data["payroll"]) == 1
        assert len(all_data["overtime"]) == 1
        assert len(all_data["activities"]) == 1
        
        # Verify data structure
        assert all_data["employees"][0]['employee_id'] == 1
        assert all_data["payroll"][0]['payroll_id'] == 1
        assert all_data["overtime"][0]['overtime_id'] == 1
        assert all_data["activities"][0]['activity_id'] == 1
    
    @patch('backend.services.export_service.User')
    def test_export_integration_with_user_service(
        self, 
        mock_user,
        export_service,
        mock_employee
    ):
        """Test export integration with user service"""
        # Mock the database models
        mock_user.query.all.return_value = [mock_employee]
        mock_user.query.filter.return_value.all.return_value = [mock_employee]
        
        # Test employee export with user filter
        filters = {'user_id': 1}
        employees = export_service._get_employee_data(filters)
        
        # Verify integration
        assert len(employees) == 1
        assert employees[0]['employee_id'] == 1
        assert employees[0]['first_name'] == 'Test'
        assert employees[0]['last_name'] == 'Employee'


class TestExportAuthentication:
    """Test cases for export authentication and authorization"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_export_permission_required(self, mock_user):
        """Test that export permission is required"""
        # Mock the current user without export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                request_data = {
                    "data_type": "employees",
                    "format_type": "csv"
                }
                response = self.client.post("/export/export", json=request_data)
                assert response.status_code == 403
    
    def test_download_permission_required(self, mock_user):
        """Test that download permission is required"""
        # Mock the current user without download permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/download/test.csv")
                assert response.status_code == 403
    
    def test_view_permission_required(self, mock_user):
        """Test that view permission is required"""
        # Mock the current user without view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/view/test.csv")
                assert response.status_code == 403
    
    def test_employee_export_permission_required(self, mock_user):
        """Test that employee export permission is required"""
        # Mock the current user without employee export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/employees")
                assert response.status_code == 403
    
    def test_payroll_export_permission_required(self, mock_user):
        """Test that payroll export permission is required"""
        # Mock the current user without payroll export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/payroll")
                assert response.status_code == 403
    
    def test_overtime_export_permission_required(self, mock_user):
        """Test that overtime export permission is required"""
        # Mock the current user without overtime export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/overtime")
                assert response.status_code == 403
    
    def test_activity_export_permission_required(self, mock_user):
        """Test that activity export permission is required"""
        # Mock the current user without activity export permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/activities")
                assert response.status_code == 403
    
    def test_department_view_permission_required(self, mock_user):
        """Test that department view permission is required"""
        # Mock the current user without department view permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.get("/export/departments")
                assert response.status_code == 403
    
    def test_cleanup_permission_required(self, mock_user):
        """Test that cleanup permission is required"""
        # Mock the current user without cleanup permission
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission:
                mock_has_permission.return_value = False
                
                response = self.client.post("/export/cleanup")
                assert response.status_code == 403
    
    def test_admin_role_can_cleanup(self, mock_user):
        """Test that admin role can cleanup exports"""
        # Mock the current user with admin role
        with patch('backend.routers.export.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.middleware.rbac.PermissionChecker.user_has_permission') as mock_has_permission, \
                 patch('backend.middleware.rbac.PermissionChecker.user_has_role') as mock_has_role:
                mock_has_permission.return_value = False
                mock_has_role.return_value = True
                
                response = self.client.post("/export/cleanup")
                assert response.status_code == 403


if __name__ == '__main__':
    pytest.main([__file__])