"""
Dashboard Frontend Tests

Tests for dashboard frontend components and functionality.
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.dashboard_page import (
    render_kpi_cards,
    render_attendance_overview,
    render_today_attendance_table,
    render_leave_management,
    render_overtime_management,
    render_payroll_summary,
    check_admin_access,
    api_get,
    api_post
)

@pytest.fixture
def mock_session_state():
    """Mock session state for testing."""
    with patch('streamlit.session_state') as mock_state:
        mock_state.get.return_value = "admin"
        yield mock_state

@pytest.fixture
def mock_st():
    """Mock Streamlit components."""
    with patch('streamlit.metric') as mock_metric, \
         patch('streamlit.bar_chart') as mock_bar_chart, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.write') as mock_write:
        
        yield {
            'metric': mock_metric,
            'bar_chart': mock_bar_chart,
            'dataframe': mock_dataframe,
            'warning': mock_warning,
            'info': mock_info,
            'error': mock_error,
            'expander': mock_expander,
            'button': mock_button,
            'success': mock_success,
            'subheader': mock_subheader,
            'write': mock_write
        }

def test_check_admin_access_admin():
    """Test admin access check for admin role."""
    with patch('frontend.dashboard_page.st') as mock_st:
        mock_st.session_state.get.return_value = "admin"
        assert check_admin_access() == True

def test_check_admin_access_employee():
    """Test admin access check for employee role."""
    with patch('frontend.dashboard_page.st') as mock_st:
        mock_st.session_state.get.return_value = "employee"
        assert check_admin_access() == False

def test_check_admin_access_no_role():
    """Test admin access check when no role is set."""
    with patch('frontend.dashboard_page.st') as mock_st:
        mock_st.session_state.get.return_value = None
        assert check_admin_access() == False

def test_render_kpi_cards(mock_st):
    """Test KPI cards rendering."""
    kpi_data = {
        "employees_present_today": 25,
        "late_absent_today": {"late": 2, "absent": 1},
        "pending_leave_requests": 3
    }
    
    render_kpi_cards(kpi_data)
    
    # Check that metrics were called
    assert mock_st.metric.call_count == 4

def test_render_kpi_cards_empty(mock_st):
    """Test KPI cards rendering with empty data."""
    kpi_data = {}
    
    render_kpi_cards(kpi_data)
    
    # Check that metrics were called
    assert mock_st.metric.call_count == 4

def test_render_attendance_overview(mock_st):
    """Test attendance overview rendering."""
    attendance_data = [
        {"date": "2025-01-09", "total": 30, "present": 25, "late": 2, "absent": 3},
        {"date": "2025-01-10", "total": 28, "present": 24, "late": 1, "absent": 3}
    ]
    
    render_attendance_overview(attendance_data)
    
    # Check that subheader and bar_chart were called
    mock_st.subheader.assert_called_once_with("Attendance Overview (Last 7 Days)")
    mock_st.bar_chart.assert_called_once()

def test_render_attendance_overview_empty(mock_st):
    """Test attendance overview rendering with empty data."""
    attendance_data = []
    
    render_attendance_overview(attendance_data)
    
    # Check that warning was called
    mock_st.warning.assert_called_once_with("No attendance data available for the last 7 days.")

def test_render_today_attendance_table(mock_st):
    """Test today's attendance table rendering."""
    attendance_data = [
        {
            "attendance_id": 1,
            "user_id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "date": "2025-01-09",
            "time_in": "09:00:00",
            "time_out": "17:00:00",
            "hours_worked": 8.0,
            "status": "Present"
        }
    ]
    
    render_today_attendance_table(attendance_data)
    
    # Check that subheader and dataframe were called
    mock_st.subheader.assert_called_once_with("Today's Attendance")
    mock_st.dataframe.assert_called_once()

def test_render_today_attendance_table_empty(mock_st):
    """Test today's attendance table rendering with empty data."""
    attendance_data = []
    
    render_today_attendance_table(attendance_data)
    
    # Check that warning was called
    mock_st.warning.assert_called_once_with("No attendance data available for today.")

def test_render_leave_management(mock_st):
    """Test leave management rendering."""
    leave_stats = {"pending": 2, "approved": 5, "rejected": 1, "cancelled": 0}
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "leave_id": 1,
            "user_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "leave_type_name": "Annual Leave",
            "date_from": "2025-01-10",
            "date_to": "2025-01-12",
            "reason": "Vacation",
            "status": "Pending"
        }
    ]
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_leave_management(leave_stats)
    
    # Check that subheader was called
    mock_st.subheader.assert_called_once_with("Leave Management")
    # Check that metrics were called
    assert mock_st.metric.call_count == 3

def test_render_leave_management_no_pending(mock_st):
    """Test leave management rendering with no pending requests."""
    leave_stats = {"pending": 0, "approved": 5, "rejected": 1, "cancelled": 0}
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_leave_management(leave_stats)
    
    # Check that info was called
    mock_st.info.assert_called_once_with("No pending leave requests.")

def test_render_leave_management_api_error(mock_st):
    """Test leave management rendering with API error."""
    leave_stats = {"pending": 2, "approved": 5, "rejected": 1, "cancelled": 0}
    
    # Mock the API response with error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_leave_management(leave_stats)
    
    # Check that error was called
    mock_st.error.assert_called_once_with("Failed to fetch leave requests.")

def test_render_overtime_management(mock_st):
    """Test overtime management rendering."""
    overtime_stats = {"pending": 1, "approved": 3, "rejected": 0}
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "ot_id": 1,
            "user_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "date": "2025-01-09",
            "hours_requested": 2.0,
            "reason": "Project deadline",
            "status": "Pending"
        }
    ]
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_overtime_management(overtime_stats)
    
    # Check that subheader was called
    mock_st.subheader.assert_called_once_with("Overtime Management")
    # Check that metrics were called
    assert mock_st.metric.call_count == 3

def test_render_overtime_management_no_pending(mock_st):
    """Test overtime management rendering with no pending requests."""
    overtime_stats = {"pending": 0, "approved": 3, "rejected": 0}
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_overtime_management(overtime_stats)
    
    # Check that info was called
    mock_st.info.assert_called_once_with("No pending overtime requests.")

def test_render_overtime_management_api_error(mock_st):
    """Test overtime management rendering with API error."""
    overtime_stats = {"pending": 1, "approved": 3, "rejected": 0}
    
    # Mock the API response with error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    with patch('frontend.dashboard_page.api_get', return_value=mock_response):
        render_overtime_management(overtime_stats)
    
    # Check that error was called
    mock_st.error.assert_called_once_with("Failed to fetch overtime requests.")

def test_render_payroll_summary(mock_st):
    """Test payroll summary rendering."""
    payroll_data = {
        "total_payrolls": 10,
        "total_basic_pay": 15000.00,
        "total_overtime_pay": 2000.00,
        "total_deductions": 1500.00,
        "total_net_pay": 15500.00
    }
    
    render_payroll_summary(payroll_data)
    
    # Check that subheader was called
    mock_st.subheader.assert_called_once_with("Payroll Summary")
    # Check that metrics were called
    assert mock_st.metric.call_count == 3
    # Check that bar_chart was called
    mock_st.bar_chart.assert_called_once()

def test_render_payroll_summary_empty(mock_st):
    """Test payroll summary rendering with empty data."""
    payroll_data = {}
    
    render_payroll_summary(payroll_data)
    
    # Check that info was called
    mock_st.info.assert_called_once_with("No payroll data available for the current month.")

def test_api_get():
    """Test API GET function."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        with patch('frontend.dashboard_page.st') as mock_st:
            mock_st.session_state.get.return_value = "token"
            
            result = api_get("/test/endpoint")
            
            assert result.status_code == 200
            mock_get.assert_called_once_with("http://localhost:8000/test/endpoint", headers={"Authorization": "Bearer token"})

def test_api_post():
    """Test API POST function."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"message": "created"}
        mock_post.return_value = mock_response
        
        with patch('frontend.dashboard_page.st') as mock_st:
            mock_st.session_state.get.return_value = "token"
            
            result = api_post("/test/endpoint", {"test": "data"})
            
            assert result.status_code == 201
            mock_post.assert_called_once_with("http://localhost:8000/test/endpoint", json={"test": "data"}, headers={"Authorization": "Bearer token"})

def test_api_get_no_token():
    """Test API GET function without token."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        result = api_get("/test/endpoint")
        
        assert result.status_code == 200
        mock_get.assert_called_once_with("http://localhost:8000/test/endpoint", headers={"Authorization": "Bearer "})

def test_api_post_no_token():
    """Test API POST function without token."""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"message": "created"}
        mock_post.return_value = mock_response
        
        result = api_post("/test/endpoint", {"test": "data"})
        
        assert result.status_code == 201
        mock_post.assert_called_once_with("http://localhost:8000/test/endpoint", json={"test": "data"}, headers={"Authorization": "Bearer "})

def test_dashboard_rendering_no_access(mock_st):
    """Test dashboard rendering without admin access."""
    with patch('frontend.dashboard_page.check_admin_access', return_value=False):
        with patch('frontend.dashboard_page.api_get') as mock_api:
            render_dashboard = MagicMock()
            render_dashboard()
            
            # Check that error was called
            mock_st.error.assert_called_once_with("Access denied. Admin privileges required.")

def test_dashboard_rendering_with_access(mock_st):
    """Test dashboard rendering with admin access."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "employees_present_today": 25,
        "late_absent_today": {"late": 2, "absent": 1},
        "pending_leave_requests": 3,
        "pending_overtime_requests": 1,
        "attendance_overview": [],
        "today_attendance": [],
        "payroll_summary": {},
        "leave_stats": {"pending": 3, "approved": 5, "rejected": 1, "cancelled": 0},
        "overtime_stats": {"pending": 1, "approved": 3, "rejected": 0}
    }
    
    with patch('frontend.dashboard_page.check_admin_access', return_value=True):
        with patch('frontend.dashboard_page.api_get', return_value=mock_response):
            with patch('frontend.dashboard_page.render_kpi_cards') as mock_kpi, \
                 patch('frontend.dashboard_page.render_attendance_overview') as mock_attendance, \
                 patch('frontend.dashboard_page.render_today_attendance_table') as mock_today_attendance, \
                 patch('frontend.dashboard_page.render_leave_management') as mock_leave, \
                 patch('frontend.dashboard_page.render_overtime_management') as mock_overtime, \
                 patch('frontend.dashboard_page.render_payroll_summary') as mock_payroll:
                
                render_dashboard = MagicMock()
                render_dashboard()
                
                # Check that all rendering functions were called
                mock_kpi.assert_called_once()
                mock_attendance.assert_called_once()
                mock_today_attendance.assert_called_once()
                mock_leave.assert_called_once()
                mock_overtime.assert_called_once()
                mock_payroll.assert_called_once()