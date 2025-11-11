import requests

# First login
login_data = {
    "username": "junnel@alphasys.com.au", 
    "password": "password"
}

response = requests.post("http://localhost:8000/token", data=login_data)
if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get departments
    dept_response = requests.get("http://localhost:8000/lookup/departments", headers=headers)
    print("Departments:", dept_response.json())
    
    # Get roles
    role_response = requests.get("http://localhost:8000/lookup/roles", headers=headers)
    print("Roles:", role_response.json())
else:
    print("Login failed:", response.text)