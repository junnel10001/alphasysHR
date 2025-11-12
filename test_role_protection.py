#!/usr/bin/env python3
"""
Test script to verify role protection functionality
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_role_protection():
    """Test that super_admin and admin roles are protected from deletion"""
    
    print("🧪 Testing Role Protection Functionality")
    print("=" * 50)
    
    # First, let's get all roles to see what we have
    try:
        response = requests.get(f"{BASE_URL}/roles/")
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
                delete_response = requests.delete(f"{BASE_URL}/roles/{super_admin_role['role_id']}")
                print(f"   Status Code: {delete_response.status_code}")
                if delete_response.status_code == 403:
                    print("   ✅ super_admin role is protected from deletion")
                    print(f"   Response: {delete_response.json()}")
                else:
                    print("   ❌ super_admin role is NOT protected!")
            
            # Test deleting admin role (should fail)
            if admin_role:
                print(f"\n🧪 Attempting to delete admin role (ID: {admin_role['role_id']})")
                delete_response = requests.delete(f"{BASE_URL}/roles/{admin_role['role_id']}")
                print(f"   Status Code: {delete_response.status_code}")
                if delete_response.status_code == 403:
                    print("   ✅ admin role is protected from deletion")
                    print(f"   Response: {delete_response.json()}")
                else:
                    print("   ❌ admin role is NOT protected!")
            
            # Test deleting a non-protected role (if available)
            test_role = next((r for r in roles if r['role_name'] not in ['super_admin', 'admin']), None)
            if test_role:
                print(f"\n🧪 Testing non-protected role: {test_role['role_name']} (ID: {test_role['role_id']})")
                delete_response = requests.delete(f"{BASE_URL}/roles/{test_role['role_id']}")
                print(f"   Status Code: {delete_response.status_code}")
                if delete_response.status_code == 204:
                    print("   ✅ Non-protected role can be deleted (but we won't actually delete it)")
                else:
                    print(f"   Response: {delete_response.json()}")
            
        else:
            print(f"❌ Failed to retrieve roles. Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_permissions_endpoint():
    """Test the permissions endpoint"""
    print("\n🔐 Testing Permissions Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/permissions/")
        if response.status_code == 200:
            permissions = response.json()
            print(f"✅ Successfully retrieved {len(permissions)} permissions:")
            for perm in permissions[:5]:  # Show first 5
                print(f"   - {perm['permission_name']}: {perm['description']}")
            if len(permissions) > 5:
                print(f"   ... and {len(permissions) - 5} more")
        else:
            print(f"❌ Failed to retrieve permissions. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_role_protection()
    test_permissions_endpoint()
    print("\n🎉 Testing completed!")