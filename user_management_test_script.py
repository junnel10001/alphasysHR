#!/usr/bin/env python3
"""
Comprehensive User Management Testing Script
Tests all user management functionality to ensure everything works correctly
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class UserManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log a test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    def login(self):
        """Login as admin and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data=ADMIN_CREDENTIALS,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.log_test("Admin Login", True, f"Token acquired successfully")
                return True
            else:
                self.log_test("Admin Login", False, f"Failed to login: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
            
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
        
    def test_list_users(self):
        """Test user listing endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/user-management/users",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                users = response.json()
                self.log_test("List Users", True, f"Retrieved {len(users)} users")
                # Verify data structure
                if users and len(users) > 0:
                    user = users[0]
                    required_fields = ['user_id', 'username', 'full_name', 'email', 'role_name', 'status', 'date_hired']
                    missing_fields = [field for field in required_fields if field not in user]
                    if missing_fields:
                        self.log_test("User Data Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("User Data Structure", True, "All required fields present")
                return True
            else:
                self.log_test("List Users", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("List Users", False, f"Exception: {str(e)}")
            return False
            
    def test_roles_summary(self):
        """Test roles summary endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/user-management/roles/summary",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                roles = response.json()
                self.log_test("Roles Summary", True, f"Retrieved {len(roles)} roles")
                # Verify role data structure
                if roles and len(roles) > 0:
                    role = roles[0]
                    required_fields = ['role_id', 'role_name', 'description', 'user_count', 'permissions_count']
                    missing_fields = [field for field in required_fields if field not in role]
                    if missing_fields:
                        self.log_test("Role Data Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Role Data Structure", True, "All required fields present")
                return True
            else:
                self.log_test("Roles Summary", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Roles Summary", False, f"Exception: {str(e)}")
            return False
            
    def test_user_search(self):
        """Test user search functionality"""
        try:
            # Test search by name
            response = requests.get(
                f"{self.base_url}/user-management/users?search=employee1",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                users = response.json()
                found_users = [u for u in users if "employee1" in u['full_name'].lower()]
                self.log_test("User Search", True, f"Search returned {len(found_users)} matching users")
                return len(found_users) > 0
            else:
                self.log_test("User Search", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Search", False, f"Exception: {str(e)}")
            return False
            
    def test_user_filters(self):
        """Test user filtering functionality"""
        try:
            # Test status filter
            response = requests.get(
                f"{self.base_url}/user-management/users?status_filter=active",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                users = response.json()
                active_users = [u for u in users if u['status'] == 'active']
                self.log_test("Status Filter", True, f"Active filter returned {len(active_users)} users")
            else:
                self.log_test("Status Filter", False, f"HTTP {response.status_code}")
                return False
                
            # Test role filter
            response = requests.get(
                f"{self.base_url}/user-management/users?role_filter=employee",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                users = response.json()
                employee_users = [u for u in users if u['role_name'] == 'employee']
                self.log_test("Role Filter", True, f"Employee filter returned {len(employee_users)} users")
                return True
            else:
                self.log_test("Role Filter", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Filters", False, f"Exception: {str(e)}")
            return False
            
    def test_role_assignment(self):
        """Test role assignment functionality"""
        try:
            # Get first employee user for testing
            response = requests.get(
                f"{self.base_url}/user-management/users?role_filter=employee",
                headers=self.get_headers()
            )
            if response.status_code != 200:
                self.log_test("Role Assignment Setup", False, "Failed to get test user")
                return False
                
            users = response.json()
            if not users:
                self.log_test("Role Assignment Setup", False, "No employee users found")
                return False
                
            test_user = users[0]
            original_role = test_user['role_name']
            
            # Assign manager role
            assignment_data = {
                "user_id": test_user['user_id'],
                "role_ids": [2]  # Manager role ID
            }
            response = requests.post(
                f"{self.base_url}/user-management/users/assign-roles",
                json=assignment_data,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                self.log_test("Role Assignment", True, f"Assigned manager role to user {test_user['user_id']}")
                
                # Verify role change
                response = requests.get(
                    f"{self.base_url}/user-management/users",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    users = response.json()
                    updated_user = next((u for u in users if u['user_id'] == test_user['user_id']), None)
                    if updated_user and updated_user['role_name'] == 'manager':
                        self.log_test("Role Assignment Verification", True, "Role change verified")
                    else:
                        self.log_test("Role Assignment Verification", False, "Role change not reflected")
                
                # Restore original role
                original_role_id = 3 if original_role == 'employee' else 1
                restore_data = {
                    "user_id": test_user['user_id'],
                    "role_ids": [original_role_id]
                }
                requests.post(
                    f"{self.base_url}/user-management/users/assign-roles",
                    json=restore_data,
                    headers=self.get_headers()
                )
                return True
            else:
                self.log_test("Role Assignment", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Role Assignment", False, f"Exception: {str(e)}")
            return False
            
    def test_user_deactivation(self):
        """Test user deactivation functionality"""
        try:
            # Get first employee user for testing
            response = requests.get(
                f"{self.base_url}/user-management/users?role_filter=employee",
                headers=self.get_headers()
            )
            if response.status_code != 200:
                self.log_test("Deactivation Setup", False, "Failed to get test user")
                return False
                
            users = response.json()
            if not users:
                self.log_test("Deactivation Setup", False, "No employee users found")
                return False
                
            test_user = users[0]
            
            # Deactivate user
            deactivation_data = {
                "user_id": test_user['user_id'],
                "reason": "Testing deactivation functionality"
            }
            response = requests.post(
                f"{self.base_url}/user-management/users/deactivate",
                json=deactivation_data,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                self.log_test("User Deactivation", True, f"Deactivated user {test_user['user_id']}")
                
                # Verify deactivation
                response = requests.get(
                    f"{self.base_url}/user-management/users",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    users = response.json()
                    deactivated_user = next((u for u in users if u['user_id'] == test_user['user_id']), None)
                    if deactivated_user and deactivated_user['status'] == 'inactive':
                        self.log_test("Deactivation Verification", True, "User status changed to inactive")
                    else:
                        self.log_test("Deactivation Verification", False, "User status not updated")
                
                # Reactivate user
                response = requests.post(
                    f"{self.base_url}/user-management/users/{test_user['user_id']}/activate",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    self.log_test("User Reactivation", True, f"Reactivated user {test_user['user_id']}")
                else:
                    self.log_test("User Reactivation", False, f"Failed to reactivate: {response.status_code}")
                
                return True
            else:
                self.log_test("User Deactivation", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Deactivation", False, f"Exception: {str(e)}")
            return False
            
    def test_permission_protection(self):
        """Test permission-based access control"""
        try:
            # Test without token (should fail)
            response = requests.get(f"{self.base_url}/user-management/users")
            if response.status_code == 401:
                self.log_test("Unauthorized Access", True, "Correctly blocked without token")
            else:
                self.log_test("Unauthorized Access", False, f"Expected 401, got {response.status_code}")
                
            return True
        except Exception as e:
            self.log_test("Permission Protection", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("Starting User Management Testing...")
        print("=" * 50)
        
        if not self.login():
            print("Cannot proceed without login")
            return
            
        # Run all test categories
        self.test_list_users()
        self.test_roles_summary()
        self.test_user_search()
        self.test_user_filters()
        self.test_role_assignment()
        self.test_user_deactivation()
        self.test_permission_protection()
        
        # Generate summary
        self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("TEST SUMMARY REPORT")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            print(f"[{result['status']}] {result['test']}: {result['details']}")
            
        # Save to file
        with open('user_management_test_report.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results
            }, f, indent=2)
        print(f"\nDetailed report saved to: user_management_test_report.json")

if __name__ == "__main__":
    tester = UserManagementTester()
    tester.run_all_tests()