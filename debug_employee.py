import requests
import json

# Test the employee creation endpoint
url = "http://localhost:8000/employees/"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqdW5uZWxAYWxwaGFzeXMuY29tLmF1Iiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzU3NDEwMzk2fQ.83JWbp9alAj3mKiFkoEuL15tKpKlDamjwvtodgb6p9M"
}

payload = {
    "username": "testuser@example.com",
    "password": "StrongPass123",
    "first_name": "Test",
    "last_name": "User",
    "email": "testuser@example.com",
    "hourly_rate": 25.0,
    "role": "employee",
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 201:
        print("Error details:")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print("No JSON error response")
except Exception as e:
    print(f"Request failed: {e}")