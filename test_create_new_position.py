import requests
import json

# Test creating a new position with a unique name
url = "http://localhost:8000/api/positions/"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Generate a unique position name using timestamp
import time
unique_name = f"Test Position {int(time.time())}"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# First, let's get available departments to pick from
dept_response = requests.get("http://localhost:8000/api/departments/", headers=headers)
print(f"Departments Status: {dept_response.status_code}")
if dept_response.status_code == 200:
    departments = dept_response.json()
    print(f"Available departments: {len(departments)}")
    
    # Use the first available department
    dept_id = departments[0]["department_id"] if departments else None
    
    # Now create the position with valid department_id
    data = {
        "position_name": unique_name,
        "description": "Test position description",
        "department_id": dept_id  # Use actual department ID
    }
    
    print(f"Creating position with department_id: {dept_id}")
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print("Failed to get departments")