#!/usr/bin/env python3
"""
Enhanced Tenant Creation System Testing
Tests the complete tenant creation with user account system as requested in review
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import re

# Configuration
BACKEND_URL = "https://returnportal.preview.emergentagent.com/api"

# Admin credentials for testing
ADMIN_CREDENTIALS = {
    "email": "admin@returns-manager.com",
    "password": "AdminPassword123!",
    "tenant_id": "tenant-rms34"
}

class EnhancedTenantCreationTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.admin_token = None
        self.created_tenants = []
        self.created_users = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def authenticate_admin(self):
        """Authenticate as admin user to get access token"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": ADMIN_CREDENTIALS["tenant_id"]
            }
            
            login_data = {
                "email": ADMIN_CREDENTIALS["email"],
                "password": ADMIN_CREDENTIALS["password"],
                "tenant_id": ADMIN_CREDENTIALS["tenant_id"]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/users/login",
                headers=headers,
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    self.log_test("Admin Authentication", True, f"Admin authenticated successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Admin Authentication", False, f"Status: {response.status}", error_text)
                    return False
                    
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_admin_headers(self):
        """Get headers with admin authentication"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}",
            "X-Tenant-Id": ADMIN_CREDENTIALS["tenant_id"]
        }
    
    async def test_enhanced_tenant_creation_api(self):
        """Test 1: Enhanced Tenant Creation API with email/password/notes"""
        print("\n=== TEST 1: Enhanced Tenant Creation API ===")
        
        # Test valid tenant creation
        test_tenant_id = f"test-tenant-{int(datetime.now().timestamp())}"
        test_email = f"merchant-{int(datetime.now().timestamp())}@example.com"
        
        tenant_data = {
            "tenant_id": test_tenant_id,
            "name": "Test Merchant Store",
            "shop_domain": "test-store.myshopify.com",
            "email": test_email,
            "password": "SecurePassword123!",
            "notes": "Test tenant created for enhanced tenant creation testing"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=tenant_data
            ) as response:
                response_data = await response.json()
                
                if response.status == 201:
                    self.created_tenants.append(test_tenant_id)
                    self.created_users.append({
                        "email": test_email,
                        "password": "SecurePassword123!",
                        "tenant_id": test_tenant_id
                    })
                    
                    # Verify response structure
                    required_fields = ["tenant_id", "name", "shop_domain", "created_at", "stats"]
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        # Check if merchant_email is in stats
                        stats = response_data.get("stats", {})
                        if "merchant_email" in stats:
                            self.log_test("Enhanced Tenant Creation - Valid Data", True, 
                                        f"Tenant created with merchant account: {test_email}")
                        else:
                            self.log_test("Enhanced Tenant Creation - Valid Data", False, 
                                        "merchant_email not found in stats", response_data)
                    else:
                        self.log_test("Enhanced Tenant Creation - Valid Data", False, 
                                    f"Missing fields: {missing_fields}", response_data)
                else:
                    self.log_test("Enhanced Tenant Creation - Valid Data", False, 
                                f"Status: {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Enhanced Tenant Creation - Valid Data", False, f"Exception: {str(e)}")
        
        # Test email format validation
        invalid_tenant_data = tenant_data.copy()
        invalid_tenant_data["tenant_id"] = f"test-invalid-{int(datetime.now().timestamp())}"
        invalid_tenant_data["email"] = "invalid-email-format"
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=invalid_tenant_data
            ) as response:
                if response.status == 422:  # Validation error
                    self.log_test("Enhanced Tenant Creation - Email Validation", True, 
                                "Invalid email format correctly rejected")
                else:
                    response_data = await response.json()
                    self.log_test("Enhanced Tenant Creation - Email Validation", False, 
                                f"Expected 422, got {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Enhanced Tenant Creation - Email Validation", False, f"Exception: {str(e)}")
        
        # Test password strength validation
        weak_password_data = tenant_data.copy()
        weak_password_data["tenant_id"] = f"test-weak-{int(datetime.now().timestamp())}"
        weak_password_data["email"] = f"weak-{int(datetime.now().timestamp())}@example.com"
        weak_password_data["password"] = "123"  # Too weak
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=weak_password_data
            ) as response:
                if response.status == 422:  # Validation error
                    self.log_test("Enhanced Tenant Creation - Password Validation", True, 
                                "Weak password correctly rejected")
                else:
                    response_data = await response.json()
                    self.log_test("Enhanced Tenant Creation - Password Validation", False, 
                                f"Expected 422, got {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Enhanced Tenant Creation - Password Validation", False, f"Exception: {str(e)}")
        
        # Test duplicate tenant_id handling
        duplicate_data = tenant_data.copy()
        duplicate_data["email"] = f"duplicate-{int(datetime.now().timestamp())}@example.com"
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=duplicate_data
            ) as response:
                if response.status == 409:  # Conflict
                    self.log_test("Enhanced Tenant Creation - Duplicate Tenant ID", True, 
                                "Duplicate tenant_id correctly rejected")
                else:
                    response_data = await response.json()
                    self.log_test("Enhanced Tenant Creation - Duplicate Tenant ID", False, 
                                f"Expected 409, got {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Enhanced Tenant Creation - Duplicate Tenant ID", False, f"Exception: {str(e)}")
    
    async def test_user_account_login_verification(self):
        """Test 2: User Account Login Verification"""
        print("\n=== TEST 2: User Account Login Verification ===")
        
        if not self.created_users:
            self.log_test("User Account Login - No Test Data", False, "No users created in previous test")
            return
        
        for user_data in self.created_users:
            # Test login with created credentials
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"],
                "tenant_id": user_data["tenant_id"]
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": user_data["tenant_id"]
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/users/login",
                    headers=headers,
                    json=login_data
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        # Verify JWT token and role
                        token = response_data.get("access_token")
                        user_info = response_data.get("user", {})
                        
                        if token and user_info.get("role") == "merchant":
                            self.log_test(f"User Login - {user_data['email']}", True, 
                                        f"Login successful, role: {user_info.get('role')}")
                            
                            # Test accessing merchant dashboard (verify token works)
                            auth_headers = {
                                "Authorization": f"Bearer {token}",
                                "X-Tenant-Id": user_data["tenant_id"]
                            }
                            
                            async with self.session.get(
                                f"{BACKEND_URL}/users/me",
                                headers=auth_headers
                            ) as profile_response:
                                if profile_response.status == 200:
                                    self.log_test(f"Token Verification - {user_data['email']}", True, 
                                                "JWT token works for API access")
                                else:
                                    self.log_test(f"Token Verification - {user_data['email']}", False, 
                                                f"Token verification failed: {profile_response.status}")
                        else:
                            self.log_test(f"User Login - {user_data['email']}", False, 
                                        "Missing token or incorrect role", response_data)
                    else:
                        self.log_test(f"User Login - {user_data['email']}", False, 
                                    f"Login failed: {response.status}", response_data)
                        
            except Exception as e:
                self.log_test(f"User Login - {user_data['email']}", False, f"Exception: {str(e)}")
    
    async def test_tenant_isolation(self):
        """Test 3: Tenant Isolation"""
        print("\n=== TEST 3: Tenant Isolation ===")
        
        # Create two different tenants with different emails
        tenant1_id = f"isolation-test-1-{int(datetime.now().timestamp())}"
        tenant2_id = f"isolation-test-2-{int(datetime.now().timestamp())}"
        
        tenant1_email = f"merchant1-{int(datetime.now().timestamp())}@example.com"
        tenant2_email = f"merchant2-{int(datetime.now().timestamp())}@example.com"
        
        tenant1_data = {
            "tenant_id": tenant1_id,
            "name": "Isolation Test Store 1",
            "email": tenant1_email,
            "password": "SecurePassword123!",
            "notes": "Tenant isolation test 1"
        }
        
        tenant2_data = {
            "tenant_id": tenant2_id,
            "name": "Isolation Test Store 2", 
            "email": tenant2_email,
            "password": "SecurePassword123!",
            "notes": "Tenant isolation test 2"
        }
        
        # Create both tenants
        tenant1_created = False
        tenant2_created = False
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=tenant1_data
            ) as response:
                if response.status == 201:
                    tenant1_created = True
                    self.created_tenants.append(tenant1_id)
                    self.created_users.append({
                        "email": tenant1_email,
                        "password": "SecurePassword123!",
                        "tenant_id": tenant1_id
                    })
                    
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=tenant2_data
            ) as response:
                if response.status == 201:
                    tenant2_created = True
                    self.created_tenants.append(tenant2_id)
                    self.created_users.append({
                        "email": tenant2_email,
                        "password": "SecurePassword123!",
                        "tenant_id": tenant2_id
                    })
                    
        except Exception as e:
            self.log_test("Tenant Isolation - Setup", False, f"Exception: {str(e)}")
            return
        
        if not (tenant1_created and tenant2_created):
            self.log_test("Tenant Isolation - Setup", False, "Failed to create test tenants")
            return
        
        # Test cross-tenant login prevention
        # Try to login to tenant1 with tenant2 credentials
        cross_login_data = {
            "email": tenant2_email,
            "password": "SecurePassword123!",
            "tenant_id": tenant1_id  # Wrong tenant
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": tenant1_id
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/users/login",
                headers=headers,
                json=cross_login_data
            ) as response:
                if response.status in [401, 403, 404]:  # Should be rejected
                    self.log_test("Tenant Isolation - Cross-Tenant Login Prevention", True, 
                                "Cross-tenant login correctly prevented")
                else:
                    response_data = await response.json()
                    self.log_test("Tenant Isolation - Cross-Tenant Login Prevention", False, 
                                f"Cross-tenant login allowed: {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Tenant Isolation - Cross-Tenant Login Prevention", False, f"Exception: {str(e)}")
        
        # Test that each merchant can only login to their specific tenant
        for user_data in [
            {"email": tenant1_email, "password": "SecurePassword123!", "tenant_id": tenant1_id},
            {"email": tenant2_email, "password": "SecurePassword123!", "tenant_id": tenant2_id}
        ]:
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": user_data["tenant_id"]
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/users/login",
                    headers=headers,
                    json=user_data
                ) as response:
                    if response.status == 200:
                        self.log_test(f"Tenant Isolation - Correct Tenant Login ({user_data['tenant_id']})", True, 
                                    f"Merchant can login to their own tenant")
                    else:
                        response_data = await response.json()
                        self.log_test(f"Tenant Isolation - Correct Tenant Login ({user_data['tenant_id']})", False, 
                                    f"Login failed: {response.status}", response_data)
                        
            except Exception as e:
                self.log_test(f"Tenant Isolation - Correct Tenant Login ({user_data['tenant_id']})", False, f"Exception: {str(e)}")
    
    async def test_admin_dashboard_integration(self):
        """Test 4: Admin Dashboard Integration"""
        print("\n=== TEST 4: Admin Dashboard Integration ===")
        
        # Test tenant listing shows newly created tenants
        try:
            async with self.session.get(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers()
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    tenants = response_data.get("tenants", [])
                    total = response_data.get("total", 0)
                    
                    # Check if our created tenants are in the list
                    found_tenants = []
                    for tenant in tenants:
                        if tenant.get("tenant_id") in self.created_tenants:
                            found_tenants.append(tenant.get("tenant_id"))
                            
                            # Check if stats include merchant_email
                            stats = tenant.get("stats", {})
                            if "merchant_email" in stats:
                                self.log_test(f"Admin Dashboard - Tenant Stats ({tenant.get('tenant_id')})", True, 
                                            f"Tenant stats include merchant_email: {stats.get('merchant_email')}")
                            else:
                                self.log_test(f"Admin Dashboard - Tenant Stats ({tenant.get('tenant_id')})", False, 
                                            "merchant_email not found in tenant stats")
                    
                    if found_tenants:
                        self.log_test("Admin Dashboard - Tenant Listing", True, 
                                    f"Found {len(found_tenants)} created tenants in listing")
                    else:
                        self.log_test("Admin Dashboard - Tenant Listing", False, 
                                    "Created tenants not found in admin listing")
                else:
                    self.log_test("Admin Dashboard - Tenant Listing", False, 
                                f"Failed to get tenant list: {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Admin Dashboard - Tenant Listing", False, f"Exception: {str(e)}")
        
        # Test impersonation functionality (if we have created tenants)
        if self.created_tenants:
            test_tenant_id = self.created_tenants[0]
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/admin/tenants/{test_tenant_id}/impersonate",
                    headers=self.get_admin_headers()
                ) as response:
                    if response.status == 302:  # Redirect expected
                        self.log_test("Admin Dashboard - Impersonation", True, 
                                    "Impersonation endpoint works (redirect received)")
                    else:
                        response_data = await response.text()
                        self.log_test("Admin Dashboard - Impersonation", False, 
                                    f"Impersonation failed: {response.status}", response_data)
                        
            except Exception as e:
                self.log_test("Admin Dashboard - Impersonation", False, f"Exception: {str(e)}")
    
    async def test_error_handling(self):
        """Test 5: Error Handling"""
        print("\n=== TEST 5: Error Handling ===")
        
        # Test duplicate email for same tenant
        if self.created_users:
            existing_user = self.created_users[0]
            duplicate_email_data = {
                "tenant_id": f"new-tenant-{int(datetime.now().timestamp())}",
                "name": "Duplicate Email Test",
                "email": existing_user["email"],  # Same email
                "password": "SecurePassword123!",
                "notes": "Testing duplicate email handling"
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/admin/tenants",
                    headers=self.get_admin_headers(),
                    json=duplicate_email_data
                ) as response:
                    if response.status == 409:  # Conflict expected
                        self.log_test("Error Handling - Duplicate Email", True, 
                                    "Duplicate email correctly rejected")
                    else:
                        response_data = await response.json()
                        self.log_test("Error Handling - Duplicate Email", False, 
                                    f"Expected 409, got {response.status}", response_data)
                        
            except Exception as e:
                self.log_test("Error Handling - Duplicate Email", False, f"Exception: {str(e)}")
        
        # Test invalid tenant_id format
        invalid_tenant_data = {
            "tenant_id": "Invalid_Tenant_ID!",  # Invalid format
            "name": "Invalid Tenant ID Test",
            "email": f"invalid-{int(datetime.now().timestamp())}@example.com",
            "password": "SecurePassword123!",
            "notes": "Testing invalid tenant_id format"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=invalid_tenant_data
            ) as response:
                if response.status == 422:  # Validation error
                    self.log_test("Error Handling - Invalid Tenant ID Format", True, 
                                "Invalid tenant_id format correctly rejected")
                else:
                    response_data = await response.json()
                    self.log_test("Error Handling - Invalid Tenant ID Format", False, 
                                f"Expected 422, got {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Error Handling - Invalid Tenant ID Format", False, f"Exception: {str(e)}")
        
        # Test missing required fields
        incomplete_data = {
            "tenant_id": f"incomplete-{int(datetime.now().timestamp())}",
            "name": "Incomplete Test"
            # Missing email and password
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants",
                headers=self.get_admin_headers(),
                json=incomplete_data
            ) as response:
                if response.status == 422:  # Validation error
                    self.log_test("Error Handling - Missing Required Fields", True, 
                                "Missing required fields correctly rejected")
                else:
                    response_data = await response.json()
                    self.log_test("Error Handling - Missing Required Fields", False, 
                                f"Expected 422, got {response.status}", response_data)
                    
        except Exception as e:
            self.log_test("Error Handling - Missing Required Fields", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all enhanced tenant creation tests"""
        print("🚀 ENHANCED TENANT CREATION SYSTEM TESTING")
        print("=" * 60)
        
        # Authenticate as admin first
        if not await self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        await self.test_enhanced_tenant_creation_api()
        await self.test_user_account_login_verification()
        await self.test_tenant_isolation()
        await self.test_admin_dashboard_integration()
        await self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 CRITICAL SUCCESS CRITERIA:")
        
        # Check critical criteria
        criteria = {
            "Tenant creation creates both tenant record AND user account": any(
                "Enhanced Tenant Creation - Valid Data" in result["test"] and result["success"] 
                for result in self.test_results
            ),
            "Created user can login via /users/login": any(
                "User Login -" in result["test"] and result["success"] 
                for result in self.test_results
            ),
            "Each tenant is isolated with their own merchant account": any(
                "Tenant Isolation -" in result["test"] and result["success"] 
                for result in self.test_results
            ),
            "Admin can see and manage all created tenants": any(
                "Admin Dashboard - Tenant Listing" in result["test"] and result["success"] 
                for result in self.test_results
            ),
            "Proper validation and error handling": any(
                "Error Handling -" in result["test"] and result["success"] 
                for result in self.test_results
            )
        }
        
        for criterion, met in criteria.items():
            status = "✅" if met else "❌"
            print(f"{status} {criterion}")
        
        all_criteria_met = all(criteria.values())
        
        print(f"\n🏆 OVERALL RESULT: {'SUCCESS' if all_criteria_met and success_rate >= 80 else 'NEEDS ATTENTION'}")
        
        if self.created_tenants:
            print(f"\n📝 CREATED TEST TENANTS: {', '.join(self.created_tenants)}")
        if self.created_users:
            print(f"📝 CREATED TEST USERS: {len(self.created_users)} merchant accounts")

async def main():
    """Main test execution"""
    async with EnhancedTenantCreationTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())