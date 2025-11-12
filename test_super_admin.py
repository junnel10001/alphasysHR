#!/usr/bin/env python3
"""
Test Super-Admin Access

This script tests if the super_admin user can access the system properly.
"""

import requests
import json

def test_login():
    """Test login with super_admin credentials."""
    login_url = "http://localhost:8000/token"
    
    # Login credentials (using admin@test.com which should now have super_admin role)
    credentials = {
        "username": "admin@test.com",
        "password": "password"
    }
    
    try:
        print("🔐 Testing login...")
        response = requests.post(
            login_url,
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Login successful! Token received: {token[:20]}...")
            
            # Test accessing protected endpoint
            test_protected_endpoint(token)
            
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")

def test_protected_endpoint(token):
    """Test accessing a protected endpoint."""
    api_url = "http://localhost:8000/users/me"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🔒 Testing protected endpoint access...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Protected endpoint access successful!")
            print(f"User ID: {user_data.get('id')}")
            print(f"Username: {user_data.get('username')}")
            print(f"Role: {user_data.get('role')}")
            
            # Test permissions endpoint
            test_permissions_endpoint(token)
            
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error accessing protected endpoint: {str(e)}")

def test_permissions_endpoint(token):
    """Test the permissions endpoint."""
    perms_url = "http://localhost:8000/me/permissions"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🔐 Testing permissions endpoint...")
        response = requests.get(perms_url, headers=headers)
        
        if response.status_code == 200:
            perms_data = response.json()
            print(f"✅ Permissions endpoint access successful!")
            print(f"User role: {perms_data.get('role')}")
            print(f"Permission count: {len(perms_data.get('permissions', []))}")
            
            # Check for admin_access permission
            permissions = perms_data.get('permissions', [])
            if 'admin_access' in permissions:
                print("✅ User has admin_access permission!")
            else:
                print("⚠️  User does not have admin_access permission")
                print(f"Available permissions: {permissions}")
            
        else:
            print(f"❌ Permissions endpoint access failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error accessing permissions endpoint: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing Super-Admin Access Configuration")
    print("=" * 50)
    
    test_login()
    print("=" * 50)