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
    departments = dept_response.json()
    print("Departments API response:", departments)
    
    # Try to get specific department
    if departments:
        for dept in departments:
            print(f"Department ID {dept.get('department_id')}: {dept.get('department_name')}")
    else:
        print("No departments found in response")
        
    # Also test creating a department
    create_dept_response = requests.post("http://localhost:8000/departments/", 
                                    json={"department_name": "Test Department"}, 
                                    headers=headers)
    print("Create department response:", create_dept_response.status_code, create_dept_response.text)
else:
    print("Login failed:", response.text)