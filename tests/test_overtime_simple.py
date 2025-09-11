"""
Simple Tests for Overtime Management Functionality

Basic tests to verify overtime functionality without complex database setup.
"""

import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_overtime_router_import():
    """Test that the overtime router can be imported"""
    try:
        from backend.routers.overtime import router
        assert router is not None
        assert router.prefix == "/overtime"
    except ImportError as e:
        pytest.fail(f"Failed to import overtime router: {e}")

def test_overtime_models_import():
    """Test that the overtime models can be imported"""
    try:
        from backend.models import OvertimeRequest, OvertimeStatus
        assert OvertimeRequest is not None
        assert OvertimeStatus is not None
    except ImportError as e:
        pytest.fail(f"Failed to import overtime models: {e}")

def test_overtime_status_enum():
    """Test that the overtime status enum works correctly"""
    try:
        from backend.models import OvertimeStatus
        
        # Test that all status values are accessible
        assert hasattr(OvertimeStatus, 'Pending')
        assert hasattr(OvertimeStatus, 'Approved')
        assert hasattr(OvertimeStatus, 'Rejected')
        
        # Test that the values are correct
        assert OvertimeStatus.Pending.value == "Pending"
        assert OvertimeStatus.Approved.value == "Approved"
        assert OvertimeStatus.Rejected.value == "Rejected"
        
    except Exception as e:
        pytest.fail(f"Failed to test overtime status enum: {e}")

def test_overtime_request_form_validation():
    """Test that the overtime request form validation works"""
    try:
        from backend.routers.overtime import OvertimeRequestForm
        
        # Test valid form data
        valid_form = OvertimeRequestForm(
            date="2023-12-01",
            hours_requested=3.5,
            reason="Test overtime"
        )
        
        assert valid_form.date == "2023-12-01"
        assert valid_form.hours_requested == 3.5
        assert valid_form.reason == "Test overtime"
        
        # Test form with None reason
        form_none_reason = OvertimeRequestForm(
            date="2023-12-01",
            hours_requested=3.5,
            reason=None
        )
        
        assert form_none_reason.reason is None
        
    except Exception as e:
        pytest.fail(f"Failed to test overtime request form validation: {e}")

def test_overtime_filter_validation():
    """Test that the overtime filter validation works"""
    try:
        from backend.routers.overtime import OvertimeFilter
        
        # Test valid filter
        valid_filter = OvertimeFilter(
            start_date="2023-12-01",
            end_date="2023-12-31",
            status="Pending",
            user_id=1
        )
        
        assert valid_filter.start_date == "2023-12-01"
        assert valid_filter.end_date == "2023-12-31"
        assert valid_filter.status == "Pending"
        assert valid_filter.user_id == 1
        
        # Test filter with None values
        none_filter = OvertimeFilter()
        
        assert none_filter.start_date is None
        assert none_filter.end_date is None
        assert none_filter.status is None
        assert none_filter.user_id is None
        
    except Exception as e:
        pytest.fail(f"Failed to test overtime filter validation: {e}")

def test_overtime_update_form_validation():
    """Test that the overtime update form validation works"""
    try:
        from backend.routers.overtime import OvertimeUpdateForm
        
        # Test valid update form
        valid_update = OvertimeUpdateForm(status="Approved")
        
        assert valid_update.status == "Approved"
        
        # Test invalid status
        with pytest.raises(ValueError):
            invalid_update = OvertimeUpdateForm(status="InvalidStatus")
            
    except Exception as e:
        pytest.fail(f"Failed to test overtime update form validation: {e}")

def test_frontend_import():
    """Test that the frontend overtime management page can be imported"""
    try:
        import sys
        import os
        
        # Add the frontend directory to the path
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
        if frontend_path not in sys.path:
            sys.path.insert(0, frontend_path)
        
        # Test that the overtime management page can be imported
        from overtime_management_page import main
        assert callable(main)
        
    except ImportError as e:
        pytest.fail(f"Failed to import overtime management page: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])