import importlib
import sys

def test_frontend_imports():
    """
    Verify that the Streamlit frontend can be imported without errors.
    This ensures that all required modules are available and the file
    syntax is correct.
    """
    try:
        # Import the frontend app module
        frontend = importlib.import_module("frontend.app")
    except Exception as e:
        assert False, f"Importing frontend.app failed: {e}"

    # Verify that the expected attributes exist
    assert hasattr(frontend, "login"), "login function missing in frontend.app"
    assert hasattr(frontend, "backend_url"), "backend_url variable missing in frontend.app"

# ----------------------------------------------------------------------
# Employee Management UI Tests (React Testing Library)
# ----------------------------------------------------------------------
import pytest
from unittest import mock
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_filter_toolbar_filters_employee_list(mocker):
    """
    Verify that the filter toolbar component correctly filters the employee list
    based on a search query.
    """
    # Mock the API call that fetches employees
    mock_response = [
        {"id": 1, "username": "alice@example.com"},
        {"id": 2, "username": "bob@example.com"},
    ]
    mocker.patch("frontend.src.lib.api.get_employees", return_value=mock_response)

    # Import the component (placeholder import – adjust to actual component path)
    from frontend.src.components.employee_management import EmployeeList

    # Render component with a filter term
    rendered = EmployeeList(filter_term="alice")
    # The component should only display the matching employee
    assert len(rendered.displayed_employees) == 1
    assert rendered.displayed_employees[0]["username"] == "alice@example.com"

def test_pagination_controls_navigate_pages(mocker):
    """
    Ensure pagination controls correctly navigate between pages and display total count.
    """
    # Mock paginated API response
    page1 = {"items": [{"id": i} for i in range(1, 11)], "total": 25}
    page2 = {"items": [{"id": i} for i in range(11, 21)], "total": 25}
    mocker.patch("frontend.src.lib.api.get_employees_page", side_effect=[page1, page2])

    from frontend.src.components.employee_management import EmployeeList

    # Render first page
    rendered = EmployeeList(page=1, page_size=10)
    assert rendered.total_count == 25
    assert len(rendered.displayed_employees) == 10

    # Simulate clicking "next page"
    rendered.go_to_page(2)
    assert len(rendered.displayed_employees) == 10
    assert rendered.displayed_employees[0]["id"] == 11

def test_add_employee_modal_creates_employee(mocker, client):
    """
    Verify that clicking the “Add Employee” button opens the modal and submitting
    the form creates a new employee via the mocked API.
    """
    # Mock the POST request for creating an employee
    mocker.patch("frontend.src.lib.api.create_employee", return_value={"id": 99, "username": "newuser@example.com"})

    from frontend.src.components.employee_management import EmployeeManagementPage

    page = EmployeeManagementPage()
    # Simulate button click
    page.click_add_employee()
    assert page.is_add_modal_open

    # Fill form data
    form_data = {
        "username": "newuser@example.com",
        "password": "StrongPass123",
        "first_name": "New",
        "last_name": "User",
        "email": "newuser@example.com",
        "hourly_rate": 30,
        "role": "employee",
    }
    page.submit_add_employee(form_data)

    # Ensure the mock API was called and the UI updated
    page.refresh_employee_list()
    assert any(emp["username"] == "newuser@example.com" for emp in page.displayed_employees)

def test_edit_and_delete_employee_actions(mocker, client):
    """
    Verify that edit and delete icons trigger the appropriate modals and API calls.
    """
    # Mock existing employee list
    mocker.patch("frontend.src.lib.api.get_employees", return_value=[{"id": 1, "username": "alice@example.com"}])
    # Mock update and delete API calls
    mocker.patch("frontend.src.lib.api.update_employee", return_value={"id": 1, "username": "alice_updated@example.com"})
    mocker.patch("frontend.src.lib.api.delete_employee", return_value=None)

    from frontend.src.components.employee_management import EmployeeManagementPage

    page = EmployeeManagementPage()
    page.load_employees()
    # Simulate edit action
    page.click_edit_employee(1)
    assert page.is_edit_modal_open
    page.submit_edit_employee(1, {"first_name": "AliceUpdated"})
    # Verify update reflected
    assert any(emp["username"] == "alice_updated@example.com" for emp in page.displayed_employees)

    # Simulate delete action
    page.click_delete_employee(1)
    assert page.is_delete_modal_open
    page.confirm_delete_employee(1)
    # Verify employee removed
    assert not any(emp["id"] == 1 for emp in page.displayed_employees)