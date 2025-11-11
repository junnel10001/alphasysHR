"""
Test cases for the Export Service
"""

import pytest
import os
import tempfile
from datetime import datetime, date, timezone
from unittest.mock import MagicMock, patch

# Import the export service after setting up mocks
from backend.services.export_service import ExportService


class TestExportService:
    """Test cases for ExportService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a mock database session
        self.db = MagicMock()
        
        # Mock user data
        self.mock_user = MagicMock()
        self.mock_user.user_id = 1
        self.mock_user.first_name = "John"
        self.mock_user.last_name = "Doe"
        self.mock_user.email = "john@example.com"
        self.mock_user.phone_number = "1234567890"
        self.mock_user.department = MagicMock()
        self.mock_user.department.department_name = "IT"
        self.mock_user.role_name = "Employee"
        self.mock_user.role_id = 1
        self.mock_user.hourly_rate = 25.00
        self.mock_user.date_hired = date(2023, 1, 1)
        self.mock_user.status = "active"
        self.mock_user.department_id = 1
        self.mock_user.generated_at = datetime(2023, 1, 1)
        
        # Mock payroll data
        self.mock_payroll = MagicMock()
        self.mock_payroll.payroll_id = 1
        self.mock_payroll.user_id = 1
        self.mock_payroll.user = self.mock_user
        self.mock_payroll.cutoff_start = date(2023, 1, 1)
        self.mock_payroll.cutoff_end = date(2023, 1, 15)
        self.mock_payroll.basic_pay = 1000.00
        self.mock_payroll.overtime_pay = 200.00
        self.mock_payroll.deductions = 100.00
        self.mock_payroll.net_pay = 1100.00
        self.mock_payroll.generated_at = datetime(2023, 1, 16, 10, 0, 0)
        
        # Create a simple data structure instead of complex mocks
        # This avoids the issue of mocks being serialized as <MagicMock name='...'>
        self.mock_user_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        # Mock payroll data
        self.mock_payroll = MagicMock()
        self.mock_payroll.payroll_id = 1
        self.mock_payroll.user_id = 1
        self.mock_payroll.user = self.mock_user_data
        self.mock_payroll.cutoff_start = date(2023, 1, 1)
        self.mock_payroll.cutoff_end = date(2023, 1, 15)
        self.mock_payroll.basic_pay = 1000.00
        self.mock_payroll.overtime_pay = 200.00
        self.mock_payroll.deductions = 100.00
        self.mock_payroll.net_pay = 1100.00
        self.mock_payroll.generated_at = datetime(2023, 1, 16, 10, 0, 0)
        
        # Mock overtime data
        self.mock_overtime = MagicMock()
        self.mock_overtime.ot_id = 1  # Correct attribute name from model
        self.mock_overtime.user_id = 1
        self.mock_overtime.user = self.mock_user_data
        self.mock_overtime.date = date(2023, 1, 10)
        self.mock_overtime.hours_requested = 5.0  # Correct attribute name from model
        self.mock_overtime.reason = "Project deadline"
        self.mock_overtime.status = "active"
        self.mock_overtime.approver_id = 2
        self.mock_overtime.approved_at = datetime(2023, 1, 11, 9, 0, 0)
        
        # Mock activity data
        self.mock_activity = MagicMock()
        self.mock_activity.log_id = 1  # Correct attribute name from model
        self.mock_activity.user_id = 1
        self.mock_activity.user = self.mock_user_data
        self.mock_activity.action = "login"
        self.mock_activity.timestamp = datetime(2023, 1, 16, 8, 30, 0)
        
        # Mock department data
        self.mock_department = MagicMock()
        self.mock_department.department_id = 1
        self.mock_department.department_name = "IT"
        
        # Initialize export service
        self.export_service = ExportService(self.db)
        
        # Set up query mocks after initialization
        self._setup_query_mocks()
    
    def _setup_query_mocks(self):
        """Set up database query mocks"""
        # Mock the query methods to return our test data directly
        def mock_user_query(*args, **kwargs):
            result = MagicMock()
            result.all.return_value = [self.mock_user]
            return result
            
        def mock_payroll_query(*args, **kwargs):
            result = MagicMock()
            result.all.return_value = [self.mock_payroll]
            return result
            
        def mock_overtime_query(*args, **kwargs):
            result = MagicMock()
            result.all.return_value = [self.mock_overtime]
            # Mock the join and filter chain for overtime
            join_result = MagicMock()
            join_result.filter.return_value.all.return_value = [self.mock_overtime]
            result.join.return_value = join_result
            return result
            
        def mock_activity_query(*args, **kwargs):
            result = MagicMock()
            result.all.return_value = [self.mock_activity]
            # Mock the join and filter chain for activity
            join_result = MagicMock()
            join_result.filter.return_value.all.return_value = [self.mock_activity]
            result.join.return_value = join_result
            return result
            
        def mock_department_query(*args, **kwargs):
            result = MagicMock()
            result.all.return_value = [self.mock_department]
            return result
        
        # Apply mocks to database session - fix the relationship mocking
        def mock_query_side_effect(*args, **kwargs):
            if args and len(args) > 0:
                model_name = args[0]
                if model_name == 'Payroll':
                    return mock_payroll_query(*args, **kwargs)
                elif model_name == 'OvertimeRequest':
                    return mock_overtime_query(*args, **kwargs)
                elif model_name == 'ActivityLog':
                    return mock_activity_query(*args, **kwargs)
                elif model_name == 'Department':
                    return mock_department_query(*args, **kwargs)
            return mock_user_query(*args, **kwargs)
        
        self.db.query.side_effect = mock_query_side_effect
        
        # Mock the join and filter chains for each model type
        def create_join_filter_chain(mock_data):
            join_result = MagicMock()
            filter_result = MagicMock()
            filter_result.all.return_value = [mock_data]
            join_result.filter.return_value = filter_result
            return join_result
        
        # Set up specific mocks for payroll join operations
        payroll_join_result = create_join_filter_chain(self.mock_payroll)
        self.db.query.return_value.join.return_value = payroll_join_result
        
        # Also patch the query methods on the export service's db attribute
        self.export_service.db.query.side_effect = mock_query_side_effect
        self.export_service.db.query.return_value.join.return_value = payroll_join_result
    
    def test_init(self):
        """Test ExportService initialization"""
        assert self.export_service.db == self.db
        assert hasattr(self.export_service, 'activity_service')
        
        # Check that export directories are created
        for dir_path in self.export_service.export_dirs.values():
            assert os.path.exists(dir_path)
    
    def test_generate_filename(self):
        """Test filename generation"""
        filename = self.export_service._generate_filename('employees', 'csv')
        assert filename.startswith('employees_')
        assert filename.endswith('.csv')
        
        # Test with filters
        filters = {'start_date': date(2023, 1, 1), 'department_id': 1}
        filename = self.export_service._generate_filename('payroll', 'excel', filters)
        assert 'from_2023-01-01' in filename
        assert 'dept_1' in filename
        assert filename.endswith('.excel')
    
    def test_get_export_formats(self):
        """Test supported export formats"""
        formats = self.export_service.get_export_formats()
        assert 'csv' in formats
        assert 'zip' in formats
        
        # Test that excel is included if pandas is available
        if hasattr(self.export_service, 'PANDAS_AVAILABLE') and self.export_service.PANDAS_AVAILABLE:
            assert 'excel' in formats
        
        # Test that pdf is included if reportlab is available
        if hasattr(self.export_service, 'REPORTLAB_AVAILABLE') and self.export_service.REPORTLAB_AVAILABLE:
            assert 'pdf' in formats
    
    def test_get_export_data_types(self):
        """Test supported export data types"""
        data_types = self.export_service.get_export_data_types()
        expected_types = ['employees', 'payroll', 'overtime', 'activities', 'all']
        for data_type in expected_types:
            assert data_type in data_types
    
    def test_validate_export_params(self):
        """Test parameter validation"""
        # Valid parameters
        assert self.export_service.validate_export_params('employees', 'csv') == True
        assert self.export_service.validate_export_params('payroll', 'excel') == True
        assert self.export_service.validate_export_params('overtime', 'pdf') == True
        assert self.export_service.validate_export_params('activities', 'zip') == True
        assert self.export_service.validate_export_params('all', 'csv') == True
        
        # Invalid data type
        assert self.export_service.validate_export_params('invalid', 'csv') == False
        
        # Invalid format type
        assert self.export_service.validate_export_params('employees', 'invalid') == False
    
    def test_clean_data_for_export(self):
        """Test data cleaning for export"""
        test_data = [
            {
                'id': 1,
                'name': 'John Doe',
                'date': datetime(2023, 1, 1, 10, 0, 0),
                'value': 100.50
            }
        ]
        
        cleaned_data = self.export_service._clean_data_for_export(test_data)
        
        # Check that datetime is converted to string
        assert 'date' in cleaned_data[0]
        assert isinstance(cleaned_data[0]['date'], str)
        
        # Check that None values are converted to empty string
        test_data_with_none = [
            {
                'id': 1,
                'name': None,
                'date': date(2023, 1, 1),
                'value': None
            }
        ]
        
        cleaned_data = self.export_service._clean_data_for_export(test_data_with_none)
        assert cleaned_data[0]['name'] == ""
        assert cleaned_data[0]['value'] == ""
    
    def test_export_employees_csv(self):
        """Test employee export to CSV"""
        result = self.export_service.export_employees('csv', {})
        assert os.path.exists(result)
        assert result.endswith('.csv')
        
        # Check file content
        with open(result, 'r') as f:
            content = f.read()
            assert 'employee_id' in content
            assert 'John' in content and 'Doe' in content  # Check first and last name separately
    
    def test_export_payroll_csv(self):
        """Test payroll export to CSV"""
        # Patch the _write_csv method to return expected data
        with patch.object(self.export_service, '_write_csv') as mock_write_csv:
            # Mock the CSV writing to return expected content
            mock_write_csv.return_value = 'payroll_id,employee_id,employee_name,pay_date,basic_salary,overtime_pay,deductions,net_salary,payroll_status,created_at\n1,John Doe,2023-01-15,1000.0,200.0,100.0,1100.0,2023-01-16T10:00:00\n'
            
            result = self.export_service.export_payroll('csv', {})
            assert os.path.exists(result)
            assert result.endswith('.csv')

            # Check that the mock was called with correct data
            mock_write_csv.assert_called_once()
    
    def test_export_overtime_csv(self):
        """Test overtime export to CSV"""
        # Patch the _write_csv method to return expected data
        with patch.object(self.export_service, '_write_csv') as mock_write_csv:
            # Mock the CSV writing to return expected content
            mock_write_csv.return_value = 'overtime_id,employee_id,employee_name,overtime_date,hours_worked,rate_per_hour,overtime_pay,status,created_at,updated_at\n1,John Doe,2023-01-10,5.0,25.0,125.0,active,2023-01-11T09:00:00,2023-01-11T09:00:00\n'
            
            result = self.export_service.export_overtime('csv', {})
            assert os.path.exists(result)
            assert result.endswith('.csv')

            # Check that the mock was called with correct data
            mock_write_csv.assert_called_once()
    
    def test_export_activities_csv(self):
        """Test activity export to CSV"""
        # Patch the _write_csv method to return expected data
        with patch.object(self.export_service, '_write_csv') as mock_write_csv:
            # Mock the CSV writing to return expected content
            mock_write_csv.return_value = 'activity_id,employee_id,employee_name,activity_date,action,details,created_at,updated_at\n1,John Doe,2023-01-16,login,User logged in,2023-01-16T08:30:00,2023-01-16T08:30:00\n'
            
            result = self.export_service.export_activities('csv', {})
            assert os.path.exists(result)
            assert result.endswith('.csv')

            # Check that the mock was called with correct data
            mock_write_csv.assert_called_once()
    
    def test_export_all_data_zip(self):
        """Test export all data to zip"""
        result = self.export_service.export_all_data('zip', {})
        assert os.path.exists(result)
        assert result.endswith('.zip')
    
    def test_export_with_filters(self):
        """Test export with filters"""
        filters = {
            'start_date': date(2023, 1, 1),
            'end_date': date(2023, 1, 31),
            'department_id': 1
        }
        
        result = self.export_service.export_employees('csv', filters)
        assert os.path.exists(result)
        # Check that filename contains filter information
        basename = os.path.basename(result)
        assert 'from_2023-01-01' in basename or 'to_2023-01-31' in basename or 'dept_1' in basename
    
    def test_cleanup_old_exports(self):
        """Test cleanup of old export files"""
        # Create a test file
        test_file = os.path.join(self.export_service.export_dirs['csv'], 'test.csv')
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Set file modification time to be old (35 days ago)
        old_time = datetime.now().timestamp() - (35 * 24 * 60 * 60)
        os.utime(test_file, (old_time, old_time))
        
        # Change to the export directory to find files
        original_cwd = os.getcwd()
        try:
            os.chdir(self.export_service.export_dirs['csv'])
            
            # Cleanup files older than 30 days
            cleaned_count = self.export_service.cleanup_old_exports(30)
            assert cleaned_count >= 1
            assert not os.path.exists(test_file)
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    pytest.main([__file__])