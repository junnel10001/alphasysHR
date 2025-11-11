import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_employee_success():
    # Minimal required fields for a successful creation
    payload = {
        "company_id": "COMP-001",
        "first_name": "John",
        "last_name": "Doe",
        "job_title": "Software Engineer",
        "department_id": 1,
        "role_id": 1,
        "employment_status": "Regular",
        "date_hired": "2023-01-01",
        "office_id": 1,
        "line_manager_id": 1,
        "basic_salary": 50000,
        "pay_frequency": "Monthly",
        "payment_method": "ATM",
    }
    response = client.post("/employees", json=payload)
    assert response.status_code == 201
    data = response.json()
    # Verify that the response contains the created employee data
    assert data["company_id"] == payload["company_id"]
    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]
    assert data["basic_salary"] == payload["basic_salary"]

def test_create_employee_missing_required():
    # Omit required fields to trigger validation errors
    payload = {
        "company_id": "",
        "first_name": "",
        "last_name": "",
        "job_title": "",
        "department_id": None,
        "role_id": None,
        "employment_status": "",
        "date_hired": "",
        "office_id": None,
        "line_manager_id": None,
        "basic_salary": -100,
        "pay_frequency": "",
        "payment_method": "",
    }
    response = client.post("/employees", json=payload)
    # Expect a 422 Unprocessable Entity from FastAPI validation
    assert response.status_code == 422
    errors = response.json()
    # Ensure that errors contain messages for required fields
    assert any("Company ID" in err["msg"] for err in errors.get("detail", []))
    assert any("first name" in err["msg"] for err in errors.get("detail", []))
    assert any("basic salary" in err["msg"] for err in errors.get("detail", []))