#!/usr/bin/env python3
"""
Test script to verify role protection functionality with authentication
"""

import requests
import json
import jwt
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "http://localhost:8000"

# JWT Secret (should match backend.config)
JWT_SECRET = "your-secret-key-here"
JWT_ALGORITHM = "HS256"

def get_auth_token(username="admin", password="admin123"):
    """Get authentication token by logging in"""
    try:
        # Use OAuth2PasswordRequestForm format (application/x-www-form-urlencoded)
        login_data = {
            "username": username,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/token", data=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_role_protection():
    """Test that super_admin and admin roles are protected from deletion"""
    
    print("🧪 Testing Role Protection Functionality with Authentication")
    print("=" * 60)
    
    # Get auth token with correct credentials
    token = get_auth_token(username="junnel@alphasys.com.au", password="password")
    if not token:
        print("❌ Could not authenticate. Skipping tests.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, let's get all roles to see what we have
    try:
        response = requests.get(f"{BASE_URL}/roles/", headers=headers)
        if response.status_code == 200:
            roles = response.json()
            print("✅ Successfully retrieved roles:")
            for role in roles:
                print(f"   - {role['role_name']} (ID: {role['role_id']})")
            
            # Find super_admin and admin roles
            super_admin_role = next((r for r in roles if r['role_name'] == 'super_admin'), None)
            admin_role = next((r for r in roles if r['role_name'] == 'admin'), None)
            
            print(f"\n🔒 Testing deletion protection...")
            
            # Test deleting super_admin role (should fail)
            if super_admin_role:
                print(f"\n🧪 Attempting to delete super_admin role (ID: {super_admin_role['role_id']})")
                delete_response = requests.delete(f"{BASE_URL}/roles/{super_admin_role['role_id']}", headers=headers)
                print(f"   Status Code: {delete_response.status_code}")
                if delete_response.status_code == 403:
                    print("   ✅ super_admin role is protected from deletion")
                    if delete_response.headers.get('content-type', '').startswith('application/json'):
                        print(f"   Response: {delete_response.json()}")
                else:
                    print("   ❌ super_admin role is NOT protected!")
            
            # Test deleting admin role (should fail)
            if admin_role:
                print(f"\n🧪 Attempting to delete admin role (ID: {admin_role['role_id']})")
                delete_response = requests.delete(f"{BASE_URL}/roles/{admin_role['role_id']}", headers=headers)
                print(f"   Status Code: {delete_response.status_code}")
                if delete_response.status_code == 403:
                    print("   ✅ admin role is protected from deletion")
                    if delete_response.headers.get('content-type', '').startswith('application/json'):
                        print(f"   Response: {delete_response.json()}")
                else:
                    print("   ❌ admin role is NOT protected!")
            
        else:
            print(f"❌ Failed to retrieve roles. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_permissions_endpoint():
    """Test the permissions endpoint"""
    print("\n🔐 Testing Permissions Endpoint")
    print("=" * 60)
    
    # Get auth token with correct credentials
    token = get_auth_token(username="junnel@alphasys.com.au", password="password")
    if not token:
        print("❌ Could not authenticate. Skipping tests.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/permissions/", headers=headers)
        if response.status_code == 200:
            permissions = response.json()
            print(f"✅ Successfully retrieved {len(permissions)} permissions:")
            for perm in permissions[:5]:  # Show first 5
                print(f"   - {perm['permission_name']}: {perm['description']}")
            if len(permissions) > 5:
                print(f"   ... and {len(permissions) - 5} more")
        else:
            print(f"❌ Failed to retrieve permissions. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_role_permission_assignment():
    """Test assigning permissions to roles"""
    print("\n🔧 Testing Role Permission Assignment")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Could not authenticate. Skipping tests.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get roles and permissions
        roles_response = requests.get(f"{BASE_URL}/roles/", headers=headers)
        permissions_response = requests.get(f"{BASE_URL}/permissions/", headers=headers)
        
        if roles_response.status_code == 200 and permissions_response.status_code == 200:
            roles = roles_response.json()
            permissions = permissions_response.json()
            
            # Find a test role (not super_admin or admin)
            test_role = next((r for r in roles if r['role_name'] not in ['super_admin', 'admin']), None)
            
            if test_role:
                print(f"🧪 Testing permission assignment for role: {test_role['role_name']}")
                
                # Get first 3 permissions for testing
                test_permissions = [p['permission_id'] for p in permissions[:3]]
                
                # Assign permissions
                assign_data = {"permission_ids": test_permissions}
                assign_response = requests.post(
                    f"{BASE_URL}/roles/{test_role['role_id']}/permissions",
                    json=assign_data,
                    headers=headers
                )
                
                print(f"   Assignment Status: {assign_response.status_code}")
                if assign_response.status_code == 200:
                    print("   ✅ Successfully assigned permissions to role")
                    print(f"   Response: {assign_response.json()}")
                else:
                    print(f"   ❌ Failed to assign permissions")
                    print(f"   Response: {assign_response.text}")
            else:
                print("   ℹ️  No suitable test role found (need a role other than super_admin/admin)")
        else:
            print("   ❌ Failed to retrieve roles or permissions")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_role_protection()
    test_permissions_endpoint()
    test_role_permission_assignment()
    print("\n🎉 Testing completed!")