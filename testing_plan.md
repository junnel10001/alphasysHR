# Employee Invitation System Testing Plan

## Testing Strategy

This document outlines comprehensive testing procedures for the employee invitation feature to ensure reliability, security, and usability.

## Test Environment Setup

### Prerequisites
1. AlphaHR development environment running
2. Database with sample employees (without user accounts)
3. Email service configured (SMTP settings)
4. Admin/Manager user accounts for testing
5. Test browsers: Chrome, Firefox, Safari, Edge

### Test Data
```sql
-- Create test employees without user accounts
INSERT INTO employees (company_id, first_name, last_name, personal_email, department_id, role_id, employment_status, date_hired) VALUES
('EMP001', 'John', 'Doe', 'john.doe@company.com', 1, 1, 'Active', '2024-01-15'),
('EMP002', 'Jane', 'Smith', 'jane.smith@company.com', 2, 1, 'Active', '2024-02-01'),
('EMP003', 'Mike', 'Johnson', 'mike.johnson@company.com', 1, 2, 'Active', '2024-03-10');
```

## Unit Tests

### Backend Service Tests

#### Invitation Service Tests
```python
# tests/test_invitation_service.py
import pytest
from backend.services.invitation_service import InvitationService
from backend.schemas.invitation import InvitationCreate

def test_create_invitation_success(db_session, sample_employee, admin_user):
    """Test successful invitation creation"""
    invitation_data = InvitationCreate(
        employee_id=sample_employee.employee_id,
        username="johndoe",
        password="SecurePass123",
        role_id=1,
        send_email=False  # Don't send email in tests
    )
    
    invitation = InvitationService.create_invitation(
        db_session, invitation_data, admin_user.user_id
    )
    
    assert invitation.employee_id == sample_employee.employee_id
    assert invitation.username == "johndoe"
    assert invitation.status == "pending"
    assert invitation.invitation_token is not None
    assert invitation.expires_at is not None

def test_create_invitation_employee_with_user(db_session, employee_with_user):
    """Test invitation creation fails for employee with existing user"""
    invitation_data = InvitationCreate(
        employee_id=employee_with_user.employee_id,
        username="testuser",
        password="SecurePass123",
        role_id=1,
        send_email=False
    )
    
    with pytest.raises(ValueError, match="Employee already has a user account"):
        InvitationService.create_invitation(db_session, invitation_data, 1)

def test_create_invitation_duplicate_username(db_session, sample_employee, existing_user):
    """Test invitation creation fails with duplicate username"""
    invitation_data = InvitationCreate(
        employee_id=sample_employee.employee_id,
        username=existing_user.username,
        password="SecurePass123",
        role_id=1,
        send_email=False
    )
    
    with pytest.raises(ValueError, match="Username already exists"):
        InvitationService.create_invitation(db_session, invitation_data, 1)

def test_accept_invitation_success(db_session, pending_invitation):
    """Test successful invitation acceptance"""
    user = InvitationService.accept_invitation(db_session, pending_invitation.invitation_token)
    
    assert user.username == pending_invitation.username
    assert user.employee_id == pending_invitation.employee_id
    assert user.status == "active"
    
    # Check invitation status updated
    db_session.refresh(pending_invitation)
    assert pending_invitation.status == "accepted"
    assert pending_invitation.accepted_at is not None

def test_accept_invitation_expired(db_session, expired_invitation):
    """Test invitation acceptance fails for expired invitation"""
    with pytest.raises(ValueError, match="Invalid or expired invitation"):
        InvitationService.accept_invitation(db_session, expired_invitation.invitation_token)

def test_get_invitable_employees(db_session, mixed_employees):
    """Test getting employees without user accounts"""
    invitable = InvitationService.get_invitable_employees(db_session)
    
    # Should only return employees without user accounts
    employee_ids = [emp.employee_id for emp in invitable]
    assert mixed_employees['without_user'].employee_id in employee_ids
    assert mixed_employees['with_user'].employee_id not in employee_ids
```

#### Email Service Tests
```python
# tests/test_email_service.py
import pytest
from unittest.mock import patch, MagicMock
from backend.services.email_service import EmailService

def test_send_invitation_email_success():
    """Test successful email sending"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        email_service = EmailService()
        result = email_service.send_invitation_email(
            "test@example.com",
            "John Doe",
            "johndoe",
            "SecurePass123",
            "Employee"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

def test_send_invitation_email_failure():
    """Test email sending failure handling"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP Error")
        
        email_service = EmailService()
        result = email_service.send_invitation_email(
            "test@example.com",
            "John Doe",
            "johndoe",
            "SecurePass123",
            "Employee"
        )
        
        assert result is False
```

#### API Endpoint Tests
```python
# tests/test_invitation_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_invitation_endpoint_success(admin_token, sample_employee):
    """Test POST /api/invitations/ endpoint success"""
    response = client.post(
        "/api/invitations/",
        json={
            "employee_id": sample_employee.employee_id,
            "username": "johndoe",
            "password": "SecurePass123",
            "role_id": 1,
            "send_email": False
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == sample_employee.employee_id
    assert data["username"] == "johndoe"
    assert data["status"] == "pending"

def test_create_invitation_unauthorized(employee_token):
    """Test unauthorized invitation creation"""
    response = client.post(
        "/api/invitations/",
        json={
            "employee_id": 1,
            "username": "testuser",
            "password": "SecurePass123",
            "role_id": 1
        },
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    
    assert response.status_code == 403

def test_get_invitable_employees_endpoint(admin_token):
    """Test GET /api/invitations/invitable endpoint"""
    response = client.get(
        "/api/invitations/invitable",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_accept_invitation_endpoint(pending_invitation_token):
    """Test POST /api/invitations/accept endpoint"""
    response = client.post(
        "/api/invitations/accept",
        json={"token": pending_invitation_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "username" in data
    assert data["message"] == "Invitation accepted successfully"
```

### Frontend Component Tests

#### Invitation Dialog Tests
```typescript
// frontend/src/components/__tests__/InvitationDialog.test.tsx
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { InvitationDialog } from '../InvitationDialog'

describe('InvitationDialog', () => {
  const mockEmployee = {
    employee_id: 1,
    first_name: 'John',
    last_name: 'Doe',
    personal_email: 'john.doe@company.com'
  }

  const mockOnClose = jest.fn()

  it('renders invitation form correctly', () => {
    render(<InvitationDialog employee={mockEmployee} onClose={mockOnClose} />)
    
    expect(screen.getByText(`Invite ${mockEmployee.first_name} ${mockEmployee.last_name}`)).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Send invitation email')).toBeInTheDocument()
  })

  it('validates password match', async () => {
    render(<InvitationDialog employee={mockEmployee} onClose={mockOnClose} />)
    
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'johndoe' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Password123' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Different123' } })
    
    fireEvent.click(screen.getByText('Send Invitation'))
    
    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const mockCreateInvitation = jest.fn().mockResolvedValue({})
    jest.mock('@/lib/api', () => ({
      invitationService: { createInvitation: mockCreateInvitation }
    }))

    render(<InvitationDialog employee={mockEmployee} onClose={mockOnClose} />)
    
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'johndoe' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'SecurePass123' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'SecurePass123' } })
    
    fireEvent.click(screen.getByText('Send Invitation'))
    
    await waitFor(() => {
      expect(mockCreateInvitation).toHaveBeenCalledWith({
        employee_id: mockEmployee.employee_id,
        username: 'johndoe',
        password: 'SecurePass123',
        role_id: 1,
        send_email: true
      })
    })
  })
})
```

## Integration Tests

### End-to-End Workflow Tests

#### Complete Invitation Workflow
```python
# tests/test_e2e_invitation.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestInvitationWorkflow:
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_complete_invitation_flow(self, driver):
        """Test complete invitation flow from admin to employee login"""
        
        # 1. Admin logs in
        driver.get("http://localhost:3000/login")
        driver.find_element(By.ID, "username").send_keys("admin@company.com")
        driver.find_element(By.ID, "password").send_keys("adminpassword")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # 2. Navigate to employees page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Employees"))
        ).click()
        
        # 3. Find employee without user account and click invite
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Invite as User')]"))
        ).click()
        
        # 4. Fill invitation form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys("johndoe")
        
        driver.find_element(By.ID, "password").send_keys("SecurePass123")
        driver.find_element(By.ID, "confirmPassword").send_keys("SecurePass123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # 5. Verify invitation created (check for success message)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Invitation sent')]"))
        )
        
        # 6. Employee logs in with provided credentials
        driver.get("http://localhost:3000/login")
        driver.find_element(By.ID, "username").send_keys("johndoe")
        driver.find_element(By.ID, "password").send_keys("SecurePass123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # 7. Verify employee can access dashboard
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]"))
        )
```

### Email Integration Tests

#### Email Delivery Verification
```python
# tests/test_email_integration.py
import imaplib
import email
from email.header import decode_header
import pytest

class TestEmailIntegration:
    def test_invitation_email_delivery(self, test_email_account):
        """Test that invitation emails are actually delivered"""
        
        # Create invitation
        invitation_data = {
            "employee_id": 1,
            "username": "testuser",
            "password": "TestPass123",
            "role_id": 1,
            "send_email": True
        }
        
        # Send invitation via API
        response = client.post(
            "/api/invitations/",
            json=invitation_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        
        # Check email inbox
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(test_email_account["email"], test_email_account["password"])
        imap.select("INBOX")
        
        # Search for invitation email
        status, messages = imap.search(None, f'SUBJECT "Welcome to AlphaHR"')
        assert status == "OK"
        
        email_ids = messages[0].split()
        assert len(email_ids) > 0
        
        # Verify email content
        latest_email_id = email_ids[-1]
        status, msg_data = imap.fetch(latest_email_id, "(RFC822)")
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Check email headers
        assert "Welcome to AlphaHR" in msg["Subject"]
        assert test_email_account["email"] in msg["To"]
        
        # Check email body contains credentials
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
            
        assert "testuser" in body
        assert "TestPass123" in body
        assert "localhost:3000/login" in body
        
        imap.close()
        imap.logout()
```

## Performance Tests

### Load Testing
```python
# tests/test_invitation_performance.py
import pytest
import asyncio
import aiohttp
import time

class TestInvitationPerformance:
    async def test_concurrent_invitation_creation(self):
        """Test system handles multiple concurrent invitations"""
        
        base_url = "http://localhost:8000"
        token = "your-admin-token"
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Create 50 concurrent invitation requests
            for i in range(50):
                task = self.create_invitation_async(
                    session, base_url, token, i
                )
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Performance assertions
            assert end_time - start_time < 30  # Should complete within 30 seconds
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            assert success_count >= 45  # At least 90% success rate
    
    async def create_invitation_async(self, session, base_url, token, index):
        """Create single invitation asynchronously"""
        url = f"{base_url}/api/invitations/"
        headers = {"Authorization": f"Bearer {token}"}
        
        data = {
            "employee_id": index + 1,
            "username": f"testuser{index}",
            "password": "TestPass123",
            "role_id": 1,
            "send_email": False
        }
        
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()
```

## Security Tests

### Security Validation Tests
```python
# tests/test_invitation_security.py
import pytest

class TestInvitationSecurity:
    def test_sql_injection_prevention(self, admin_token):
        """Test SQL injection attempts are prevented"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/invitations/",
                json={
                    "employee_id": 1,
                    "username": malicious_input,
                    "password": "ValidPass123",
                    "role_id": 1
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            # Should either succeed with sanitized input or fail validation
            assert response.status_code in [201, 400, 422]
            
            if response.status_code == 201:
                # Verify no SQL injection occurred
                data = response.json()
                assert malicious_input not in data["username"]

    def test_weak_password_rejection(self, admin_token):
        """Test weak passwords are rejected"""
        weak_passwords = [
            "123",           # Too short
            "password",      # Common password
            "qwerty",        # Keyboard sequence
            "12345678",      # Numeric sequence
        ]
        
        for weak_password in weak_passwords:
            response = client.post(
                "/api/invitations/",
                json={
                    "employee_id": 1,
                    "username": "testuser",
                    "password": weak_password,
                    "role_id": 1
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 400
            assert "password" in response.json()["detail"].lower()

    def test_authorization_bypass_prevention(self, employee_token):
        """Test regular users cannot create invitations"""
        response = client.post(
            "/api/invitations/",
            json={
                "employee_id": 1,
                "username": "testuser",
                "password": "ValidPass123",
                "role_id": 1
            },
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 403
```

## Regression Tests

### Existing Functionality Tests
```python
# tests/test_invitation_regression.py
import pytest

class TestInvitationRegression:
    def test_existing_user_login_still_works(self):
        """Test existing users can still login after invitation system added"""
        response = client.post(
            "/token",
            data={
                "username": "existinguser",
                "password": "existingpassword"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_existing_employee_management_still_works(self, admin_token):
        """Test existing employee management functionality still works"""
        # Test employee listing
        response = client.get(
            "/employees/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # Test employee creation
        response = client.post(
            "/employees/",
            json={
                "company_id": "EMP999",
                "first_name": "Test",
                "last_name": "User",
                "email": "test.user@company.com"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
```

## Test Automation

### CI/CD Pipeline Integration
```yaml
# .github/workflows/invitation-tests.yml
name: Invitation System Tests

on:
  push:
    paths:
      - 'backend/services/invitation_service.py'
      - 'backend/routers/invitations.py'
      - 'frontend/src/components/InvitationDialog.tsx'
  pull_request:
    paths:
      - 'backend/services/invitation_service.py'
      - 'backend/routers/invitations.py'
      - 'frontend/src/components/InvitationDialog.tsx'

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_alphahr
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run unit tests
      run: |
        pytest tests/test_invitation_service.py -v
        pytest tests/test_invitation_api.py -v
    
    - name: Run integration tests
      run: |
        pytest tests/test_e2e_invitation.py -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '16'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm install
    
    - name: Run component tests
      run: |
        cd frontend
        npm test -- --testPathPattern=InvitationDialog
```

## Manual Testing Checklist

### User Acceptance Testing

#### Admin/Manager Testing
- [ ] Can view list of employees without user accounts
- [ ] Can send invitations with valid credentials
- [ ] Can specify roles for invited users
- [ ] Receives confirmation when invitation is sent
- [ ] Can resend invitations
- [ ] Can revoke pending invitations
- [ ] Can view invitation history and status

#### Employee Testing
- [ ] Receives invitation email with correct credentials
- [ ] Can login with provided credentials
- [ ] Can access appropriate system features based on role
- [ ] Can change password after first login

#### Error Scenarios
- [ ] Proper error messages for invalid email formats
- [ ] Proper error messages for duplicate usernames
- [ ] Proper error messages for expired invitations
- [ ] Proper error messages for unauthorized access attempts

### Browser Compatibility Testing
- [ ] Chrome (latest version)
- [ ] Firefox (latest version)
- [ ] Safari (latest version)
- [ ] Edge (latest version)
- [ ] Mobile responsiveness testing

### Performance Testing
- [ ] Page load times under 3 seconds
- [ ] Form submission responses under 2 seconds
- [ ] Email delivery within 5 minutes
- [ ] Database query performance with 1000+ employees

This comprehensive testing plan ensures the invitation system is reliable, secure, and user-friendly across all scenarios.