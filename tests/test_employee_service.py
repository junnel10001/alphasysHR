import pytest
from unittest.mock import MagicMock

from backend.services.employee_service import list_employees_with_filters
from backend.models import User

@pytest.fixture
def mock_db():
    """Create a mock SQLAlchemy session."""
    db = MagicMock()
    # Mock the query chain used in the service
    query = db.query.return_value
    query.filter.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    # Return a list with a single dummy User instance
    dummy_user = User(
        user_id=1,
        username="testuser",
        password_hash="hashed",
        role_name="employee",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone_number="1234567890",
        department_id=1,
        role_id=1,
        hourly_rate=20.0,
        date_hired=None,
        status="active"
    )
    query.all.return_value = [dummy_user]
    return db

def test_list_employees_without_filters(mock_db):
    result = list_employees_with_filters(mock_db)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].username == "testuser"

def test_list_employees_with_department_filter(mock_db):
    result = list_employees_with_filters(mock_db, department_id=1)
    assert isinstance(result, list)
    assert result[0].department_id == 1

def test_list_employees_with_role_and_status_filters(mock_db):
    result = list_employees_with_filters(mock_db, role="admin", status="active")
    assert isinstance(result, list)
    # Mock does not enforce filter logic; just ensure call succeeds
    assert result[0].status == "active"