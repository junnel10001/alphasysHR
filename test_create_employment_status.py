import requests
import json

# Test creating a new employment status
url = "http://localhost:8000/employment-statuses/"

# First, login to get a valid token
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
    
    # Generate a unique employment status name
    import time
    unique_name = f"Test Status {int(time.time())}"
    
    # Create employment status data
    data = {
        "status_name": unique_name,
        "description": "Test employment status description",
        "is_active": True
    }
    
    print(f"\nCreating employment status:")
    print(f"  Name: {unique_name}")
    print(f"  Description: {data['description']}")
    print(f"  Active: {data['is_active']}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"\nCreate Employment Status Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("\n✅ Employment status created successfully!")
        status_data = response.json()
        print(f"Status ID: {status_data.get('employment_status_id')}")
    else:
        print(f"\n❌ Failed to create employment status: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error detail: {error_detail}")
        except:
            pass
else:
    print(f"Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")