"""
Test cases for the Export Service
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from unittest.mock import MagicMock, patch

# Mock the database and models before importing
mock_db = MagicMock()
mock_user = MagicMock()
mock_user.user_id = 1
mock_user.first_name = "John"
mock_user.last_name = "Doe"
mock_user.email = "john@example.com"
mock_user.phone_number = "1234567890"
mock_user.department = MagicMock()
mock_user.department.department_name = "IT"
mock_user.role_obj = MagicMock()
mock_user.role_obj.role_name = "Employee"
mock_user.hourly_rate = 25.00
mock_user.date_hired = date(2023, 1, 1)
mock_user.status = "active"

# Patch the database and models
with patch('backend.services.export_service.User') as mock_user_model, \
     patch('backend.services.export_service.Payroll') as mock_payroll_model, \
     patch('backend.services.export_service.OvertimeRequest') as mock_overtime_model, \
     patch('backend.services.export_service.ActivityLog') as mock_activity_model, \
     patch('backend.services.export_service.Department') as mock_department_model:
    
    mock_user_model.query.all.return_value = [mock_user]
    mock_user_model.query.filter.return_value.all.return_value = [mock_user]
    
    # Set up the mock relationships
    mock_user.department = MagicMock()
    mock_user.department.department_name = "IT"
    mock_user.role_obj = MagicMock()
    mock_user.role_obj.role_name = "Employee"
    
    # Mock payroll data
    mock_payroll = MagicMock()
    mock_payroll.payroll_id = 1
    mock_payroll.user_id = 1
    mock_payroll.user = mock_user
    mock_payroll.cutoff_start = date(2023, 1, 1)
    mock_payroll.cutoff_end = date(2023, 1, 15)
    mock_payroll.basic_pay = 1000.00
    mock_payroll.overtime_pay = 200.00
    mock_payroll.deductions = 100.00
    mock_payroll.net_pay = 1100.00
    mock_payroll.generated_at = datetime(2023, 1, 16, 10, 0, 0)
    
    mock_payroll_model.query.all.return_value = [mock_payroll]
    mock_payroll_model.query.join.return_value.filter.return_value.all.return_value = [mock_payroll]
    
    # Mock overtime data
    mock_overtime = MagicMock()
    mock_overtime.ot_id = 1
    mock_overtime.user_id = 1
    mock_overtime.user = mock_user
    mock_overtime.date = date(2023, 1, 10)
    mock_overtime.hours_requested = 5.0
    mock_overtime.reason = "Project deadline"
    mock_overtime.status = "Approved"
    mock_overtime.approver_id = 2
    mock_overtime.approved_at = datetime(2023, 1, 11, 9, 0, 0)
    
    mock_overtime_model.query.all.return_value = [mock_overtime]
    
    # Mock activity data
    mock_activity = MagicMock()
    mock_activity.log_id = 1
    mock_activity.user_id = 1
    mock_activity.user = mock_user
    mock_activity.action = "login"
    mock_activity.timestamp = datetime(2023, 1, 16, 8, 30, 0)
    
    mock_activity_model.query.all.return_value = [mock_activity]
    
    # Mock department
    mock_department = MagicMock()
    mock_department.department_id = 1
    mock_department.department_name = "IT"
    
    mock_department_model.query.all.return_value = [mock_department]
    
    # Now import the export service
    from backend.services.export_service import ExportService


class TestExportService:
    """Test cases for ExportService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = mock_db
        self.export_service = ExportService(self.db)
    
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
        filters = {'start_date': '2023-01-01', 'department_id': 1}
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
        if self.export_service._ExportService__dict__.get('PANDAS_AVAILABLE', False):
            assert 'excel' in formats
        
        # Test that pdf is included if reportlab is available
        if self.export_service._ExportService__dict__.get('REPORTLAB_AVAILABLE', False):
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
        result = self.export_service.export_employees('csv')
        assert os.path.exists(result)
        assert result.endswith('.csv')
        
        # Check file content
        with open(result, 'r') as f:
            content = f.read()
            assert 'Employee ID' in content
            assert 'John Doe' in content
    
    def test_export_payroll_csv(self):
        """Test payroll export to CSV"""
        result = self.export_service.export_payroll('csv')
        assert os.path.exists(result)
        assert result.endswith('.csv')
        
        # Check file content
        with open(result, 'r') as f:
            content = f.read()
            assert 'Payroll ID' in content
            assert 'John Doe' in content
    
    def test_export_overtime_csv(self):
        """Test overtime export to CSV"""
        result = self.export_service.export_overtime('csv')
        assert os.path.exists(result)
        assert result.endswith('.csv')
        
        # Check file content
        with open(result, 'r') as f:
            content = f.read()
            assert 'Overtime ID' in content
            assert 'John Doe' in content
    
    def test_export_activities_csv(self):
        """Test activity export to CSV"""
        result = self.export_service.export_activities('csv')
        assert os.path.exists(result)
        assert result.endswith('.csv')
        
        # Check file content
        with open(result, 'r') as f:
            content = f.read()
            assert 'Activity ID' in content
            assert 'John Doe' in content
    
    def test_export_all_data_zip(self):
        """Test export all data to zip"""
        result = self.export_service.export_all_data('zip')
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
        assert 'from_2023-01-01' in os.path.basename(result)
        assert 'to_2023-01-31' in os.path.basename(result)
        assert 'dept_1' in os.path.basename(result)
    
    def test_cleanup_old_exports(self):
        """Test cleanup of old export files"""
        # Create a test file
        test_file = os.path.join(self.export_service.export_dirs['csv'], 'test.csv')
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Set file modification time to be old
        old_time = datetime.now().timestamp() - (35 * 24 * 60 * 60)  # 35 days ago
        os.utime(test_file, (old_time, old_time))
        
        # Cleanup files older than 30 days
        cleaned_count = self.export_service.cleanup_old_exports(30)
        assert cleaned_count >= 1
        assert not os.path.exists(test_file)


if __name__ == '__main__':
    pytest.main([__file__])