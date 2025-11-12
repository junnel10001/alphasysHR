"""
Test script to verify that the user_id is properly populated 
in the employee record when an invitation is accepted.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_invitation_user_id_fix():
    """Test that user_id is populated when accepting an invitation linked to an employee."""
    
    # First, login as admin
    login_response = requests.post(
        f"{BASE_URL}/token",
        data={
            "username": "junnel@alphasys.com.au",
            "password": "password"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Step 1: Get a list of employees to find one without a user account
        print("\n1. Getting employees without user accounts...")
        employees_response = requests.get(
            f"{BASE_URL}/employees/",
            headers=headers
        )
        
        if employees_response.status_code != 200:
            print(f"❌ Failed to get employees: {employees_response.status_code}")
            return False
        
        employees = employees_response.json()
        
        # Always create a new test employee to ensure we have a clean test case
        target_employee = None
        print("⚠️ Creating a new test employee for clean test case...")
            
        # Get departments and roles for creating an employee
        dept_response = requests.get(f"{BASE_URL}/lookup/departments", headers=headers)
        role_response = requests.get(f"{BASE_URL}/roles/", headers=headers)
        office_response = requests.get(f"{BASE_URL}/lookup/offices", headers=headers)
            
        if dept_response.status_code != 200 or role_response.status_code != 200:
            print("❌ Failed to get departments or roles")
            return False
        
        departments = dept_response.json()
        roles = role_response.json()
        offices = office_response.json() if office_response.status_code == 200 else []
        
        # Create a test employee
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        employee_data = {
            "company_id": f"TEST{timestamp}",
            "first_name": "Test",
            "last_name": "Employee",
            "personal_email": f"testemployee-{timestamp}@example.com",
            "department_id": departments[0]["department_id"] if departments else 1,
            "role_id": roles[0]["role_id"] if roles else 1,
            "office_id": offices[0]["office_id"] if offices else 1,
            "basic_salary": 50000.00,
            "date_hired": datetime.now().date().isoformat()
        }
        
        create_emp_response = requests.post(
            f"{BASE_URL}/employees/",
            json=employee_data,
            headers=headers
        )
        
        if create_emp_response.status_code != 201:
            print(f"❌ Failed to create test employee: {create_emp_response.text}")
            return False
        
        target_employee = create_emp_response.json()
        print(f"✓ Created test employee: {target_employee['first_name']} {target_employee['last_name']}")
        
        print(f"✓ Found/created employee: {target_employee['first_name']} {target_employee['last_name']} (ID: {target_employee['employee_id']})")
        
        # Step 2: Create an invitation for this employee
        print("\n2. Creating invitation for the employee...")
        invitation_data = {
            "email": target_employee.get("personal_email") or f"invite-{target_employee['employee_id']}@example.com",
            "role_id": target_employee.get("role_id", 1),
            "department_id": target_employee.get("department_id"),
            "employee_profile_id": target_employee["employee_id"],
            "expires_days": 7
        }
        
        invite_response = requests.post(
            f"{BASE_URL}/invitations/",
            json=invitation_data,
            headers=headers
        )
        
        if invite_response.status_code != 201:
            print(f"❌ Failed to create invitation: {invite_response.text}")
            return False
        
        invitation = invite_response.json()
        print(f"✓ Created invitation with token: {invitation['token'][:20]}...")
        
        # Step 3: Validate the invitation token
        print("\n3. Validating invitation token...")
        validate_response = requests.post(
            f"{BASE_URL}/invitations/validate",
            params={"token": invitation["token"]}
        )
        
        if validate_response.status_code != 200:
            print(f"❌ Token validation failed: {validate_response.text}")
            return False
        
        validation = validate_response.json()
        if not validation["is_valid"]:
            print(f"❌ Invitation is not valid: {validation.get('error_message')}")
            return False
        
        print("✓ Token is valid")
        
        # Step 4: Accept the invitation (simulate user registration)
        print("\n4. Accepting invitation...")
        accept_data = {
            "token": invitation["token"],
            "username": f"user_{target_employee['employee_id']}",
            "password": "password123",
            "first_name": target_employee["first_name"],
            "last_name": target_employee["last_name"],
            "phone_number": "1234567890"
        }
        
        accept_response = requests.post(
            f"{BASE_URL}/invitations/accept",
            json=accept_data
        )
        
        if accept_response.status_code != 200:
            print(f"❌ Failed to accept invitation: {accept_response.text}")
            return False
        
        accept_result = accept_response.json()
        if not accept_result["success"]:
            print(f"❌ Invitation acceptance failed: {accept_result.get('message')}")
            return False
        
        print(f"✓ Invitation accepted successfully for user: {accept_result.get('user_id')}")
        
        # Step 5: Verify that the employee now has a user_id
        print("\n5. Verifying employee user_id is populated...")
        verify_response = requests.get(
            f"{BASE_URL}/employees/{target_employee['employee_id']}",
            headers=headers
        )
        
        if verify_response.status_code != 200:
            print(f"❌ Failed to verify employee: {verify_response.text}")
            return False
        
        updated_employee = verify_response.json()
        
        if updated_employee.get("user_id"):
            print(f"✅ SUCCESS: Employee {updated_employee['employee_id']} now has user_id: {updated_employee['user_id']}")
            return True
        else:
            print(f"❌ FAILURE: Employee {updated_employee['employee_id']} still has no user_id")
            print(f"Employee data: {json.dumps(updated_employee, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing invitation user_id population fix...")
    success = test_invitation_user_id_fix()
    
    if success:
        print("\n🎉 Test passed! The user_id is properly populated when an employee accepts an invitation.")
    else:
        print("\n💥 Test failed! The issue still exists.")