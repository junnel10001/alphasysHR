import requests
import json

# Test creating a new position with proper authentication
url = "http://localhost:8000/positions/"

# First, login to get a valid token using the correct endpoint
login_data = {
    "username": "junnel@alphasys.com.au",
    "password": "password"
}

print("Logging in...")
login_response = requests.post("http://localhost:8000/token", data=login_data)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data.get("access_token")
    print(f"Token received: {token[:20] if token else 'None'}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, get available departments
    dept_response = requests.get("http://localhost:8000/departments/", headers=headers)
    print(f"\nDepartments Status: {dept_response.status_code}")
    
    if dept_response.status_code == 200:
        departments = dept_response.json()
        print(f"Available departments: {len(departments)}")
        
        # Use the first available department
        dept_id = departments[0]["department_id"] if departments else None
        dept_name = departments[0]["department_name"] if departments else None
        
        # Generate a unique position name
        import time
        unique_name = f"Test Position {int(time.time())}"
        
        # Now create the position with valid department_id
        data = {
            "position_name": unique_name,
            "description": "Test position description",
            "department_id": dept_id  # Use actual department ID
        }
        
        print(f"\nCreating position:")
        print(f"  Name: {unique_name}")
        print(f"  Department ID: {dept_id} ({dept_name})")
        print(f"  Description: {data['description']}")
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\nCreate Position Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Position created successfully!")
            position_data = response.json()
            print(f"Position ID: {position_data.get('position_id')}")
        else:
            print(f"\n❌ Failed to create position: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error detail: {error_detail}")
            except:
                pass
    else:
        print(f"Failed to get departments: {dept_response.status_code}")
        print(f"Response: {dept_response.text}")
else:
    print(f"Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")