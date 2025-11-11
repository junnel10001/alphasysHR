#!/usr/bin/env python3
"""
Test script to verify invitation functionality
"""
import requests
import json
import random

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/token"
INVITATIONS_URL = f"{BASE_URL}/invitations"

def test_invitation_system():
    """Test the invitation system end-to-end"""
    
    print("🔧 Testing AlphaHR Invitation System...")
    
    # Step 1: Login as admin to get token
    print("\n1. Logging in as admin...")
    login_data = {
        "username": "junnel@alphasys.com.au",
        "password": "password"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Login successful!")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 2: Test creating an invitation
            print("\n2. Creating invitation...")
            invitation_data = {
                "email": "testinvitation@example.com",  # Fixed email for testing
                "role_id": 1,
                "department_id": 1,  # Human Resources department
                "expires_days": 7
            }
            
            create_response = requests.post(INVITATIONS_URL, json=invitation_data, headers=headers)
            if create_response.status_code == 201:
                invitation_result = create_response.json()
                print("✅ Invitation created successfully!")
                print(f"   Invitation ID: {invitation_result.get('invitation_id')}")
                print(f"   Email: {invitation_result.get('email')}")
                print(f"   Token: {invitation_result.get('token')}")
                
                # Step 3: Test listing invitations
                print("\n3. Listing invitations...")
                list_response = requests.get(INVITATIONS_URL, headers=headers)
                if list_response.status_code == 200:
                    invitations_list = list_response.json()
                    print(f"✅ Found {len(invitations_list.get('invitations', []))} invitations")
                    
                    # Step 4: Test validating the invitation token
                    print("\n4. Validating invitation token...")
                    token = invitation_result.get('token')
                    validate_response = requests.post(
                        f"{INVITATIONS_URL}/validate",
                        params={"token": token}
                    )
                    if validate_response.status_code == 200:
                        validation_result = validate_response.json()
                        if validation_result.get('is_valid'):
                            print("✅ Token validation successful!")
                            print(f"   Valid email: {validation_result.get('invitation_data', {}).get('email')}")
                        else:
                            print(f"❌ Token validation failed: {validation_result.get('error_message')}")
                    else:
                        print(f"❌ Token validation request failed: {validate_response.status_code}")
                
                else:
                    print(f"❌ Failed to list invitations: {list_response.status_code}")
            else:
                print(f"❌ Failed to create invitation: {create_response.status_code}")
                print(f"   Error: {create_response.text}")
                
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_invitation_system()