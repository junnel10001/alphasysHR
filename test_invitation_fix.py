#!/usr/bin/env python3
"""
Test script to verify invitation creation fix
"""

import requests
import json

def test_invitation_creation():
    """Test invitation creation endpoint"""
    
    # Login to get token
    login_data = {
        "username": "admin@test.com",
        "password": "password"
    }
    
    try:
        # Get token
        login_response = requests.post(
            "http://localhost:8000/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")
            return False
            
        token = login_response.json()["access_token"]
        print(f"✓ Login successful, got token")
        
        # Test invitation creation
        invitation_data = {
            "email": f"test{hash('random')}@example.com",
            "role_id": 1,
            "department_id": 1,
            "expires_days": 7
        }
        
        invitation_response = requests.post(
            "http://localhost:8000/invitations/",
            json=invitation_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Invitation creation response status: {invitation_response.status_code}")
        print(f"Response headers: {dict(invitation_response.headers)}")
        
        if invitation_response.status_code == 201:
            result = invitation_response.json()
            print(f"✓ Invitation created successfully!")
            print(f"Response structure: {json.dumps(result, indent=2, default=str)}")
            
            # Check if response has expected structure
            if 'invitation_id' in result:
                print("✓ Response has invitation_id field")
            else:
                print("✗ Response missing invitation_id field")
                
            return True
        else:
            print(f"✗ Invitation creation failed: {invitation_response.status_code}")
            print(f"Error response: {invitation_response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing invitation creation fix...")
    success = test_invitation_creation()
    
    if success:
        print("\n🎉 Test passed! The invitation creation issue is fixed.")
    else:
        print("\n❌ Test failed! The issue still exists.")