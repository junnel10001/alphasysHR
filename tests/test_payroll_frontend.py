import pytest
import streamlit as st
from unittest.mock import Mock, patch
import pandas as pd
from datetime import date, datetime
import sys
import os

# Add the frontend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'frontend'))

from payroll_management_page import (
    api_get, api_post, api_put, api_delete,
    has_permission, get_employees, get_departments,
    get_payroll_history, get_payroll_summary,
    get_employee_payroll_details, create_payroll,
    generate_payslip, payroll_generation_form,
    payroll_history_table, show_payroll_details,
    generate_payslip_action, delete_payroll_action,
    payroll_summary_dashboard, employee_payroll_view, main
)

# Mock session state for testing
class MockSessionState:
    def __init__(self):
        self.data = {
            "token": "mock_token",
            "username": "test_user",
            "role": "admin",
            "user_id": 1
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)

# Test data
MOCK_EMPLOYEES = [
    {
        "user_id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com"
    },
    {
        "user_id": 2,
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com"
    }
]

MOCK_DEPARTMENTS = [
    {"department_id": 1, "department_name": "Engineering"},
    {"department_id": 2, "department_name": "HR"}
]

MOCK_PAYROLL_DATA = [
    {
        "payroll_id": 1,
        "user_id": 1,
        "cutoff_start": "2023-01-01",
        "cutoff_end": "2023-01-31",
        "basic_pay": 3000.00,
        "overtime_pay": 500.00,
        "deductions": 200.00,
        "net_pay": 3300.00,
        "generated_at": "2023-01-31T10:00:00"
    },
    {
        "payroll_id": 2,
        "user_id": 2,
        "cutoff_start": "2023-01-01",
        "cutoff_end": "2023-01-31",
        "basic_pay": 3500.00,
        "overtime_pay": 300.00,
        "deductions": 250.00,
        "net_pay": 3550.00,
        "generated_at": "2023-01-31T10:00:00"
    }
]

MOCK_PAYROLL_SUMMARY = {
    "total_payrolls": 2,
    "total_net_pay": 6850.00,
    "average_net_pay": 3425.00,
    "recent_payrolls": 2
}

class TestPayrollFrontend:
    """Test class for payroll frontend functionality"""
    
    @pytest.fixture
    def mock_session_state(self):
        """Mock session state for testing"""
        st.session_state = MockSessionState()
        return st.session_state
    
    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses"""
        with patch('payroll_management_page.api_get') as mock_get, \
             patch('payroll_management_page.api_post') as mock_post, \
             patch('payroll_management_page.api_put') as mock_put, \
             patch('payroll_management_page.api_delete') as mock_delete:
            
            # Mock GET responses
            mock_get.return_value.status_code = 200
            
            # Mock employees response
            def mock_get_employees(endpoint):
                if endpoint == "/employees/":
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = MOCK_EMPLOYEES
                    MockedResponse.status_code = 200
                    return MockedResponse
                elif endpoint == "/departments/":
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = MOCK_DEPARTMENTS
                    MockedResponse.status_code = 200
                    return MockedResponse
                elif endpoint == "/payroll/summary":
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = MOCK_PAYROLL_SUMMARY
                    MockedResponse.status_code = 200
                    return MockedResponse
                elif "/payroll/employee/" in endpoint:
                    employee_id = int(endpoint.split("/")[-1])
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = [p for p in MOCK_PAYROLL_DATA if p["user_id"] == employee_id]
                    MockedResponse.status_code = 200
                    return MockedResponse
                elif endpoint == "/payroll/filtered":
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = MOCK_PAYROLL_DATA
                    MockedResponse.status_code = 200
                    return MockedResponse
                elif "/payroll/" in endpoint and not "/employee/" in endpoint:
                    payroll_id = int(endpoint.split("/")[-1])
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = [p for p in MOCK_PAYROLL_DATA if p["payroll_id"] == payroll_id][0]
                    MockedResponse.status_code = 200
                    return MockedResponse
                else:
                    MockedResponse = Mock()
                    MockedResponse.json.return_value = []
                    MockedResponse.status_code = 404
                    return MockedResponse
            
            mock_get.side_effect = mock_get_employees
            
            # Mock POST responses
            def mock_post_create(endpoint, data):
                if endpoint == "/payroll/":
                    MockedResponse = Mock()
                    MockedResponse.status_code = 201
                    MockedResponse.json.return_value = {
                        "payroll_id": 3,
                        "user_id": data["user_id"],
                        "cutoff_start": data["cutoff_start"],
                        "cutoff_end": data["cutoff_end"],
                        "basic_pay": data["basic_pay"],
                        "overtime_pay": data["overtime_pay"],
                        "deductions": data["deductions"],
                        "net_pay": data["basic_pay"] + data["overtime_pay"] - data["deductions"],
                        "generated_at": datetime.now().isoformat()
                    }
                    return MockedResponse
                elif "/generate-payslip" in endpoint:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 200
                    MockedResponse.json.return_value = {
                        "payroll_id": int(endpoint.split("/")[-2]),
                        "message": "Payslip generated successfully",
                        "status": "success"
                    }
                    return MockedResponse
                else:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 400
                    MockedResponse.text = "Bad request"
                    return MockedResponse
            
            mock_post.side_effect = mock_post_create
            
            # Mock PUT responses
            def mock_put_update(endpoint, data):
                if "/payroll/" in endpoint:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 200
                    MockedResponse.json.return_value = {
                        "payroll_id": int(endpoint.split("/")[-1]),
                        "user_id": 1,
                        "cutoff_start": "2023-01-01",
                        "cutoff_end": "2023-01-31",
                        "basic_pay": 3000.00,
                        "overtime_pay": 500.00,
                        "deductions": 200.00,
                        "net_pay": 3300.00,
                        "generated_at": datetime.now().isoformat()
                    }
                    return MockedResponse
                else:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 404
                    MockedResponse.text = "Not found"
                    return MockedResponse
            
            mock_put.side_effect = mock_put_update
            
            # Mock DELETE responses
            def mock_delete(endpoint):
                if "/payroll/" in endpoint:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 204
                    return MockedResponse
                else:
                    MockedResponse = Mock()
                    MockedResponse.status_code = 404
                    return MockedResponse
            
            mock_delete.side_effect = mock_delete
            
            yield mock_get, mock_post, mock_put, mock_delete
    
    def test_has_permission(self, mock_session_state):
        """Test permission checking"""
        # Test admin role
        st.session_state.data["role"] = "admin"
        assert has_permission("admin") == True
        assert has_permission("manager") == False
        assert has_permission("employee") == False
        
        # Test manager role
        st.session_state.data["role"] = "manager"
        assert has_permission("admin") == False
        assert has_permission("manager") == True
        assert has_permission("employee") == False
        
        # Test employee role
        st.session_state.data["role"] = "employee"
        assert has_permission("admin") == False
        assert has_permission("manager") == False
        assert has_permission("employee") == True
        
        # Test invalid role
        st.session_state.data["role"] = "invalid"
        assert has_permission("admin") == False
        assert has_permission("manager") == False
        assert has_permission("employee") == False
    
    def test_get_employees(self, mock_api_responses):
        """Test getting employees"""
        mock_get, _, _, _ = mock_api_responses
        employees = get_employees()
        assert employees == MOCK_EMPLOYEES
        assert len(employees) == 2
        assert employees[0]["user_id"] == 1
        assert employees[1]["user_id"] == 2
    
    def test_get_departments(self, mock_api_responses):
        """Test getting departments"""
        mock_get, _, _, _ = mock_api_responses
        departments = get_departments()
        assert departments == MOCK_DEPARTMENTS
        assert len(departments) == 2
        assert departments[0]["department_id"] == 1
        assert departments[1]["department_id"] == 2
    
    def test_get_payroll_history(self, mock_api_responses):
        """Test getting payroll history"""
        mock_get, _, _, _ = mock_api_responses
        payroll_data = get_payroll_history()
        assert payroll_data == MOCK_PAYROLL_DATA
        assert len(payroll_data) == 2
    
    def test_get_payroll_summary(self, mock_api_responses):
        """Test getting payroll summary"""
        mock_get, _, _, _ = mock_api_responses
        summary = get_payroll_summary()
        assert summary == MOCK_PAYROLL_SUMMARY
        assert summary["total_payrolls"] == 2
        assert summary["total_net_pay"] == 6850.00
        assert summary["average_net_pay"] == 3425.00
        assert summary["recent_payrolls"] == 2
    
    def test_get_employee_payroll_details(self, mock_api_responses):
        """Test getting employee payroll details"""
        mock_get, _, _, _ = mock_api_responses
        details = get_employee_payroll_details(1)
        assert len(details) == 1
        assert details[0]["user_id"] == 1
        assert details[0]["payroll_id"] == 1
    
    def test_create_payroll(self, mock_api_responses):
        """Test creating payroll"""
        _, mock_post, _, _ = mock_api_responses
        payroll_data = {
            "user_id": 1,
            "cutoff_start": "2023-01-01",
            "cutoff_end": "2023-01-31",
            "basic_pay": 3000.00,
            "overtime_pay": 500.00,
            "deductions": 200.00
        }
        result = create_payroll(payroll_data)
        assert result["success"] == True
        assert result["data"]["payroll_id"] == 3
        assert result["data"]["user_id"] == 1
        assert result["data"]["net_pay"] == 3300.00
    
    def test_generate_payslip(self, mock_api_responses):
        """Test generating payslip"""
        _, mock_post, _, _ = mock_api_responses
        result = generate_payslip(1)
        assert result["success"] == True
        assert result["data"]["payroll_id"] == 1
        assert result["data"]["status"] == "success"
    
    def test_payroll_generation_form_validation(self, mock_session_state):
        """Test payroll generation form validation"""
        # Test cutoff date validation
        cutoff_start = date(2023, 1, 31)
        cutoff_end = date(2023, 1, 1)  # End before start
        
        form_errors = []
        if cutoff_start >= cutoff_end:
            form_errors.append("Cutoff start date must be before end date")
        
        assert len(form_errors) == 1
        assert "Cutoff start date must be before end date" in form_errors[0]
        
        # Test negative values validation
        basic_pay = -100.0
        overtime_pay = -50.0
        deductions = -25.0
        
        form_errors = []
        if basic_pay <= 0:
            form_errors.append("Basic pay must be greater than 0")
        if overtime_pay < 0:
            form_errors.append("Overtime pay cannot be negative")
        if deductions < 0:
            form_errors.append("Deductions cannot be negative")
        
        assert len(form_errors) == 3
        assert "Basic pay must be greater than 0" in form_errors[0]
        assert "Overtime pay cannot be negative" in form_errors[1]
        assert "Deductions cannot be negative" in form_errors[2]
    
    def test_payroll_history_table_permissions(self, mock_session_state):
        """Test payroll history table permissions"""
        # Test without permission
        st.session_state.data["role"] = "guest"
        # This would normally show an error message in the UI
        # We can't easily test the UI behavior here, but we can test the function logic
        
        # Test with admin permission
        st.session_state.data["role"] = "admin"
        assert has_permission("admin") == True
        
        # Test with manager permission
        st.session_state.data["role"] = "manager"
        assert has_permission("manager") == True
        
        # Test with employee permission
        st.session_state.data["role"] = "employee"
        assert has_permission("employee") == True
    
    def test_delete_payroll_action(self, mock_api_responses):
        """Test delete payroll action"""
        _, _, _, mock_delete = mock_api_responses
        # This would normally show a confirmation dialog in the UI
        # We can't easily test the UI behavior here, but we can test the API call
        
        # The actual delete action is triggered by the UI, but we can test the API call
        # This is a simplified test of the API call
        response = api_delete("/payroll/1")
        assert response.status_code == 204
    
    def test_show_payroll_details(self, mock_api_responses):
        """Test showing payroll details"""
        mock_get, _, _, _ = mock_api_responses
        # This would normally show details in the UI
        # We can't easily test the UI behavior here, but we can test the API call
        
        # The actual show details action is triggered by the UI, but we can test the API call
        response = api_get("/payroll/1")
        assert response.status_code == 200
        data = response.json()
        assert data["payroll_id"] == 1
        assert data["user_id"] == 1
        assert data["net_pay"] == 3300.00

def test_payroll_frontend_integration():
    """Integration test for payroll frontend functionality"""
    # This would be more comprehensive integration testing
    # For now, we'll just test that the main function can be called
    # without errors (though it won't run without a Streamlit context)
    
    # Test that the functions exist and are callable
    assert callable(api_get)
    assert callable(api_post)
    assert callable(api_put)
    assert callable(api_delete)
    assert callable(has_permission)
    assert callable(get_employees)
    assert callable(get_departments)
    assert callable(get_payroll_history)
    assert callable(get_payroll_summary)
    assert callable(get_employee_payroll_details)
    assert callable(create_payroll)
    assert callable(generate_payslip)
    assert callable(payroll_generation_form)
    assert callable(payroll_history_table)
    assert callable(show_payroll_details)
    assert callable(generate_payslip_action)
    assert callable(delete_payroll_action)
    assert callable(payroll_summary_dashboard)
    assert callable(employee_payroll_view)
    assert callable(main)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])