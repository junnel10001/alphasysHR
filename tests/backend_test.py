import pytest
from fastapi.testclient import TestClient
from backend.main import app
from datetime import date

client = TestClient(app)

@pytest.fixture
def admin_token():
    """Obtain JWT token for the seeded admin user."""
    response = client.post(
        "/token",
        data={"username": "junnel@alphasys.com.au", "password": "password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

def test_create_employee(admin_token):
    import uuid
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    unique_email = unique_username
    
    payload = {
        "username": unique_username,
        "password": "StrongPass123",
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "hourly_rate": 25.0,
        "role": "employee",
    }
    resp = client.post(
        "/employees/",
        json=payload,
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["hourly_rate"] == payload["hourly_rate"]

def test_list_employees(admin_token):
    resp = client.get("/employees/", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    employees = resp.json()
    assert isinstance(employees, list)

def test_create_leave_request(admin_token):
    # First, ensure a user exists (use the admin user)
    payload = {
        "user_id": 2,  # Use the seeded admin user with ID 2
        "leave_type_id": 1,
        "date_from": "2025-01-01",
        "date_to": "2025-01-05",
        "reason": "Vacation",
    }
    resp = client.post(
        "/leaves/",
        json=payload,
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    leave = resp.json()
    assert leave["user_id"] == payload["user_id"]
    assert leave["status"] == "Pending"

def test_create_attendance(admin_token):
    import uuid
    import datetime
    day = str(int(uuid.uuid4().hex[:2], 16) % 28 + 1)  # Ensure valid day (1-28)
    unique_date = f"2025-09-{day.zfill(2)}"
    
    payload = {
        "user_id": 2,  # Use the seeded admin user with ID 2
        "date": unique_date,  # Use the field name that matches the model
        "time_in": f"2025-09-{day.zfill(2)}T09:00:00",
        "time_out": f"2025-09-{day.zfill(2)}T17:00:00",
        "status": "Present",
    }
    resp = client.post(
"/attendance/",
        json=payload,
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 201
    att = resp.json()
    assert att["user_id"] == payload["user_id"]
    assert att["status"] == "Present"