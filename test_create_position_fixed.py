import requests
import json

# Get auth token
auth_response = requests.post('http://localhost:8000/token', data={
    'username': 'junnel@alphasys.com.au',
    'password': 'password'
})

if auth_response.status_code == 200:
    token = auth_response.json()['access_token']
    
    # Test creating position with new name
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    data = {
        'position_name': 'Test Position New',
        'description': 'Test Description New',
        'department_id': 1
    }
    
    response = requests.post('http://localhost:8000/positions/', headers=headers, json=data)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')
    
    if response.status_code == 201:
        result = response.json()
        print(f'Created position: ID {result["position_id"]}, Name {result["position_name"]}')
else:
    print('Failed to create position')