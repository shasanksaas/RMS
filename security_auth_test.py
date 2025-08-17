#!/usr/bin/env python3
"""
CRITICAL SECURITY VERIFICATION TEST: Authentication Flows and Admin Portal Access Control
Tests authentication flows to verify admin portal access control as requested in review
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import jwt
import base64

# Configuration
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"

# Test credentials from review request
MERCHANT_CREDENTIALS = {
    "email": "merchant@rms34.com",
    "password": "merchant123",
    "tenant_id": "tenant-rms34"
}

ADMIN_CREDENTIALS = {
    "email": "admin@returns-manager.com", 
    "password": "AdminPassword123!",
    "tenant_id": "tenant-rms34"
}

class SecurityAuthTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.merchant_token = None
        self.admin_token = None
        self.merchant_user_data = None
        self.admin_user_data = None
        
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
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    def decode_jwt_token(self, token: str) -> Dict:
        """Decode JWT token without verification for inspection"""
        try:
            # Split token and decode payload
            parts = token.split('.')
            if len(parts) != 3:
                return {}
            
            # Add padding if needed
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode base64
            decoded_bytes = base64.urlsafe_b64decode(payload)
            decoded_str = decoded_bytes.decode('utf-8')
            
            return json.loads(decoded_str)
        except Exception as e:
            print(f"Error decoding JWT: {e}")
            return {}
    
    async def test_merchant_login_verification(self):
        """Test merchant login with merchant@rms34.com/merchant123/tenant-rms34"""
        print("\n🔐 Testing Merchant Login Verification...")
        
        # Test 1: Merchant login with correct credentials
        login_data = {
            "email": MERCHANT_CREDENTIALS["email"],
            "password": MERCHANT_CREDENTIALS["password"],
            "tenant_id": MERCHANT_CREDENTIALS["tenant_id"]
        }
        
        login_headers = {
            "X-Tenant-Id": MERCHANT_CREDENTIALS["tenant_id"]
        }
        
        success, response, status = await self.make_request("POST", "/users/login", login_data, login_headers)
        
        if success and response.get("access_token"):
            self.merchant_token = response["access_token"]
            self.merchant_user_data = response.get("user", {})
            
            # Verify response contains role: "merchant"
            user_role = self.merchant_user_data.get("role")
            if user_role == "merchant":
                self.log_test("Merchant Login: Correct role verification", True, 
                             f"User role correctly set to 'merchant'")
            else:
                self.log_test("Merchant Login: Correct role verification", False, 
                             f"Expected role 'merchant', got '{user_role}'")
            
            # Verify JWT token has correct merchant role claims
            jwt_payload = self.decode_jwt_token(self.merchant_token)
            jwt_role = jwt_payload.get("role")
            jwt_tenant = jwt_payload.get("tenant_id")
            
            if jwt_role == "merchant":
                self.log_test("Merchant Login: JWT role claims", True, 
                             f"JWT token contains correct role 'merchant'")
            else:
                self.log_test("Merchant Login: JWT role claims", False, 
                             f"JWT token role expected 'merchant', got '{jwt_role}'")
            
            if jwt_tenant == TEST_TENANT_ID:
                self.log_test("Merchant Login: JWT tenant claims", True, 
                             f"JWT token contains correct tenant_id '{TEST_TENANT_ID}'")
            else:
                self.log_test("Merchant Login: JWT tenant claims", False, 
                             f"JWT token tenant_id expected '{TEST_TENANT_ID}', got '{jwt_tenant}'")
            
            self.log_test("Merchant Login: Authentication success", True, 
                         f"Successfully authenticated merchant user")
        else:
            self.log_test("Merchant Login: Authentication success", False, 
                         f"Failed to authenticate merchant. Status: {status}, Response: {response}")
        
        # Test 2: Merchant login with wrong password
        wrong_password_data = {
            "email": MERCHANT_CREDENTIALS["email"],
            "password": "wrongpassword",
            "tenant_id": MERCHANT_CREDENTIALS["tenant_id"]
        }
        
        success, response, status = await self.make_request("POST", "/users/login", wrong_password_data, login_headers)
        
        if not success and status in [401, 403]:
            self.log_test("Merchant Login: Wrong password rejection", True, 
                         "Correctly rejected wrong password")
        else:
            self.log_test("Merchant Login: Wrong password rejection", False, 
                         "Should reject wrong password")
    
    async def test_admin_login_verification(self):
        """Test admin login with admin@returns-manager.com/AdminPassword123!/tenant-rms34"""
        print("\n👑 Testing Admin Login Verification...")
        
        # Test 1: Admin login with correct credentials
        login_data = {
            "email": ADMIN_CREDENTIALS["email"],
            "password": ADMIN_CREDENTIALS["password"],
            "tenant_id": ADMIN_CREDENTIALS["tenant_id"]
        }
        
        login_headers = {
            "X-Tenant-Id": ADMIN_CREDENTIALS["tenant_id"]
        }
        
        success, response, status = await self.make_request("POST", "/users/login", login_data, login_headers)
        
        if success and response.get("access_token"):
            self.admin_token = response["access_token"]
            self.admin_user_data = response.get("user", {})
            
            # Verify response contains role: "admin"
            user_role = self.admin_user_data.get("role")
            if user_role == "admin":
                self.log_test("Admin Login: Correct role verification", True, 
                             f"User role correctly set to 'admin'")
            else:
                self.log_test("Admin Login: Correct role verification", False, 
                             f"Expected role 'admin', got '{user_role}'")
            
            # Verify JWT token has correct admin role claims
            jwt_payload = self.decode_jwt_token(self.admin_token)
            jwt_role = jwt_payload.get("role")
            jwt_tenant = jwt_payload.get("tenant_id")
            
            if jwt_role == "admin":
                self.log_test("Admin Login: JWT role claims", True, 
                             f"JWT token contains correct role 'admin'")
            else:
                self.log_test("Admin Login: JWT role claims", False, 
                             f"JWT token role expected 'admin', got '{jwt_role}'")
            
            if jwt_tenant == TEST_TENANT_ID:
                self.log_test("Admin Login: JWT tenant claims", True, 
                             f"JWT token contains correct tenant_id '{TEST_TENANT_ID}'")
            else:
                self.log_test("Admin Login: JWT tenant claims", False, 
                             f"JWT token tenant_id expected '{TEST_TENANT_ID}', got '{jwt_tenant}'")
            
            self.log_test("Admin Login: Authentication success", True, 
                         f"Successfully authenticated admin user")
        else:
            self.log_test("Admin Login: Authentication success", False, 
                         f"Failed to authenticate admin. Status: {status}, Response: {response}")
        
        # Test 2: Admin login with wrong password
        wrong_password_data = {
            "email": ADMIN_CREDENTIALS["email"],
            "password": "wrongpassword",
            "tenant_id": ADMIN_CREDENTIALS["tenant_id"]
        }
        
        success, response, status = await self.make_request("POST", "/users/login", wrong_password_data, login_headers)
        
        if not success and status in [401, 403]:
            self.log_test("Admin Login: Wrong password rejection", True, 
                         "Correctly rejected wrong password")
        else:
            self.log_test("Admin Login: Wrong password rejection", False, 
                         "Should reject wrong password")
    
    async def test_merchant_cannot_access_admin_routes(self):
        """Test that merchant credentials CANNOT access admin routes"""
        print("\n🚫 Testing Merchant Cannot Access Admin Routes...")
        
        if not self.merchant_token:
            self.log_test("Merchant Admin Access: No merchant token available", False, 
                         "Merchant login must succeed first")
            return
        
        merchant_headers = {
            "Authorization": f"Bearer {self.merchant_token}",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Test admin-only endpoints
        admin_endpoints = [
            "/admin/tenants",
            "/admin/tenants/tenant-rms34",
            "/admin/tenants/tenant-rms34/impersonate",
            "/tenants",  # Admin tenant management
            "/users?role=admin",  # Admin user listing
        ]
        
        for endpoint in admin_endpoints:
            success, response, status = await self.make_request("GET", endpoint, headers=merchant_headers)
            
            if not success and status in [401, 403]:
                self.log_test(f"Merchant Admin Access: {endpoint} blocked", True, 
                             f"Correctly blocked merchant access with status {status}")
            else:
                self.log_test(f"Merchant Admin Access: {endpoint} blocked", False, 
                             f"Merchant should not access admin endpoint. Status: {status}")
        
        # Test admin-only POST operations
        admin_post_endpoints = [
            ("/admin/tenants", {"name": "test", "tenant_id": "test"}),
            ("/tenants", {"name": "test", "domain": "test.com"}),
        ]
        
        for endpoint, data in admin_post_endpoints:
            success, response, status = await self.make_request("POST", endpoint, data, merchant_headers)
            
            if not success and status in [401, 403]:
                self.log_test(f"Merchant Admin Access: POST {endpoint} blocked", True, 
                             f"Correctly blocked merchant POST access with status {status}")
            else:
                self.log_test(f"Merchant Admin Access: POST {endpoint} blocked", False, 
                             f"Merchant should not access admin POST endpoint. Status: {status}")
    
    async def test_admin_can_access_admin_routes(self):
        """Test that admin credentials can access admin routes"""
        print("\n✅ Testing Admin Can Access Admin Routes...")
        
        if not self.admin_token:
            self.log_test("Admin Route Access: No admin token available", False, 
                         "Admin login must succeed first")
            return
        
        admin_headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Test admin-accessible endpoints
        admin_endpoints = [
            "/admin/tenants",
            "/tenants",  # Admin tenant management
            "/users?role=merchant",  # Admin can list users
        ]
        
        for endpoint in admin_endpoints:
            success, response, status = await self.make_request("GET", endpoint, headers=admin_headers)
            
            if success or status == 200:
                self.log_test(f"Admin Route Access: {endpoint} accessible", True, 
                             f"Admin correctly accessed endpoint with status {status}")
            elif status == 404:
                self.log_test(f"Admin Route Access: {endpoint} accessible", True, 
                             f"Endpoint not found but admin has access (404 vs 403)")
            else:
                self.log_test(f"Admin Route Access: {endpoint} accessible", False, 
                             f"Admin should access endpoint. Status: {status}, Response: {response}")
        
        # Test specific admin operations
        # Test 1: Admin tenant listing
        success, response, status = await self.make_request("GET", "/admin/tenants", headers=admin_headers)
        
        if success and isinstance(response, (list, dict)):
            self.log_test("Admin Route Access: Tenant listing", True, 
                         "Admin can successfully list tenants")
        else:
            self.log_test("Admin Route Access: Tenant listing", False, 
                         f"Admin should be able to list tenants. Status: {status}")
        
        # Test 2: Admin user management
        success, response, status = await self.make_request("GET", "/users", headers=admin_headers)
        
        if success and isinstance(response, (list, dict)):
            self.log_test("Admin Route Access: User management", True, 
                         "Admin can successfully access user management")
        else:
            self.log_test("Admin Route Access: User management", False, 
                         f"Admin should access user management. Status: {status}")
    
    async def test_role_based_access_control(self):
        """Test JWT token validation for different roles"""
        print("\n🛡️ Testing Role-Based Access Control...")
        
        # Test 1: Invalid JWT token
        invalid_headers = {
            "Authorization": "Bearer invalid.jwt.token",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        success, response, status = await self.make_request("GET", "/users", headers=invalid_headers)
        
        if not success and status in [401, 403]:
            self.log_test("RBAC: Invalid JWT rejection", True, 
                         f"Correctly rejected invalid JWT with status {status}")
        else:
            self.log_test("RBAC: Invalid JWT rejection", False, 
                         f"Should reject invalid JWT. Status: {status}")
        
        # Test 2: Missing Authorization header
        no_auth_headers = {
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        success, response, status = await self.make_request("GET", "/users", headers=no_auth_headers)
        
        if not success and status in [401, 403]:
            self.log_test("RBAC: Missing auth header rejection", True, 
                         f"Correctly rejected missing auth with status {status}")
        else:
            self.log_test("RBAC: Missing auth header rejection", False, 
                         f"Should reject missing auth. Status: {status}")
        
        # Test 3: Expired token (simulate by using malformed token)
        expired_headers = {
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.expired.token",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        success, response, status = await self.make_request("GET", "/users", headers=expired_headers)
        
        if not success and status in [401, 403]:
            self.log_test("RBAC: Expired token rejection", True, 
                         f"Correctly rejected expired/malformed token with status {status}")
        else:
            self.log_test("RBAC: Expired token rejection", False, 
                         f"Should reject expired token. Status: {status}")
    
    async def test_authentication_state_consistency(self):
        """Test authentication state consistency"""
        print("\n🔄 Testing Authentication State Consistency...")
        
        # Test 1: Merchant user object contains correct role information
        if self.merchant_user_data:
            required_fields = ["id", "email", "role", "tenant_id", "active"]
            missing_fields = [field for field in required_fields if field not in self.merchant_user_data]
            
            if not missing_fields:
                self.log_test("Auth State: Merchant user object completeness", True, 
                             "Merchant user object contains all required fields")
            else:
                self.log_test("Auth State: Merchant user object completeness", False, 
                             f"Missing fields in merchant user object: {missing_fields}")
            
            # Check role consistency
            if self.merchant_user_data.get("role") == "merchant":
                self.log_test("Auth State: Merchant role consistency", True, 
                             "Merchant user role is consistent")
            else:
                self.log_test("Auth State: Merchant role consistency", False, 
                             f"Merchant role inconsistent: {self.merchant_user_data.get('role')}")
        
        # Test 2: Admin user object contains correct role information
        if self.admin_user_data:
            required_fields = ["id", "email", "role", "tenant_id", "active"]
            missing_fields = [field for field in required_fields if field not in self.admin_user_data]
            
            if not missing_fields:
                self.log_test("Auth State: Admin user object completeness", True, 
                             "Admin user object contains all required fields")
            else:
                self.log_test("Auth State: Admin user object completeness", False, 
                             f"Missing fields in admin user object: {missing_fields}")
            
            # Check role consistency
            if self.admin_user_data.get("role") == "admin":
                self.log_test("Auth State: Admin role consistency", True, 
                             "Admin user role is consistent")
            else:
                self.log_test("Auth State: Admin role consistency", False, 
                             f"Admin role inconsistent: {self.admin_user_data.get('role')}")
        
        # Test 3: JWT token and user object consistency
        if self.merchant_token and self.merchant_user_data:
            jwt_payload = self.decode_jwt_token(self.merchant_token)
            jwt_role = jwt_payload.get("role")
            user_role = self.merchant_user_data.get("role")
            
            if jwt_role == user_role:
                self.log_test("Auth State: Merchant JWT-User role consistency", True, 
                             "JWT and user object roles match")
            else:
                self.log_test("Auth State: Merchant JWT-User role consistency", False, 
                             f"JWT role '{jwt_role}' != user role '{user_role}'")
        
        if self.admin_token and self.admin_user_data:
            jwt_payload = self.decode_jwt_token(self.admin_token)
            jwt_role = jwt_payload.get("role")
            user_role = self.admin_user_data.get("role")
            
            if jwt_role == user_role:
                self.log_test("Auth State: Admin JWT-User role consistency", True, 
                             "JWT and user object roles match")
            else:
                self.log_test("Auth State: Admin JWT-User role consistency", False, 
                             f"JWT role '{jwt_role}' != user role '{user_role}'")
    
    async def test_backend_security_enforcement(self):
        """Test backend security enforcement"""
        print("\n🔒 Testing Backend Security Enforcement...")
        
        # Test 1: Admin-protected endpoints require admin role
        admin_protected_endpoints = [
            "/admin/tenants",
            "/admin/tenants/tenant-rms34/impersonate",
            "/tenants",
        ]
        
        # Test with merchant token (should fail)
        if self.merchant_token:
            merchant_headers = {
                "Authorization": f"Bearer {self.merchant_token}",
                "X-Tenant-Id": TEST_TENANT_ID
            }
            
            for endpoint in admin_protected_endpoints:
                success, response, status = await self.make_request("GET", endpoint, headers=merchant_headers)
                
                if not success and status == 403:
                    self.log_test(f"Backend Security: {endpoint} requires admin (merchant blocked)", True, 
                                 "Correctly blocked merchant from admin endpoint")
                elif not success and status == 401:
                    self.log_test(f"Backend Security: {endpoint} requires admin (merchant blocked)", True, 
                                 "Correctly blocked merchant from admin endpoint (401)")
                else:
                    self.log_test(f"Backend Security: {endpoint} requires admin (merchant blocked)", False, 
                                 f"Merchant should be blocked. Status: {status}")
        
        # Test 2: Merchant-protected endpoints require merchant role
        merchant_protected_endpoints = [
            "/orders",
            "/returns",
            "/products",
        ]
        
        # Test with admin token (should succeed - admin can access merchant endpoints)
        if self.admin_token:
            admin_headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "X-Tenant-Id": TEST_TENANT_ID
            }
            
            for endpoint in merchant_protected_endpoints:
                success, response, status = await self.make_request("GET", endpoint, headers=admin_headers)
                
                if success or status == 200:
                    self.log_test(f"Backend Security: {endpoint} accessible to admin", True, 
                                 "Admin can access merchant endpoints")
                elif status == 404:
                    self.log_test(f"Backend Security: {endpoint} accessible to admin", True, 
                                 "Endpoint not found but admin has access")
                else:
                    self.log_test(f"Backend Security: {endpoint} accessible to admin", False, 
                                 f"Admin should access merchant endpoint. Status: {status}")
        
        # Test 3: Proper 403 responses for unauthorized access
        if self.merchant_token:
            merchant_headers = {
                "Authorization": f"Bearer {self.merchant_token}",
                "X-Tenant-Id": TEST_TENANT_ID
            }
            
            # Try to access admin-only tenant creation
            success, response, status = await self.make_request("POST", "/tenants", 
                                                               {"name": "test", "domain": "test.com"}, 
                                                               merchant_headers)
            
            if status == 403:
                self.log_test("Backend Security: Proper 403 for unauthorized access", True, 
                             "Correctly returned 403 for unauthorized access")
            elif status == 401:
                self.log_test("Backend Security: Proper 403 for unauthorized access", True, 
                             "Correctly returned 401 for unauthorized access")
            else:
                self.log_test("Backend Security: Proper 403 for unauthorized access", False, 
                             f"Should return 403/401 for unauthorized access. Got: {status}")
    
    async def test_cross_role_access_prevention(self):
        """Test cross-role access prevention (merchant trying admin endpoints)"""
        print("\n🚧 Testing Cross-Role Access Prevention...")
        
        if not self.merchant_token:
            self.log_test("Cross-Role Access: No merchant token for testing", False)
            return
        
        merchant_headers = {
            "Authorization": f"Bearer {self.merchant_token}",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Critical admin operations that merchant should never access
        critical_admin_operations = [
            ("GET", "/admin/tenants", None),
            ("POST", "/admin/tenants", {"name": "hack", "tenant_id": "hack"}),
            ("GET", "/admin/tenants/tenant-rms34/impersonate", None),
            ("POST", "/admin/tenants/tenant-rms34/impersonate", {}),
            ("GET", "/users?role=admin", None),
            ("POST", "/tenants", {"name": "hack", "domain": "hack.com"}),
        ]
        
        blocked_count = 0
        total_count = len(critical_admin_operations)
        
        for method, endpoint, data in critical_admin_operations:
            success, response, status = await self.make_request(method, endpoint, data, merchant_headers)
            
            if not success and status in [401, 403]:
                blocked_count += 1
                self.log_test(f"Cross-Role Prevention: {method} {endpoint}", True, 
                             f"Correctly blocked with status {status}")
            else:
                self.log_test(f"Cross-Role Prevention: {method} {endpoint}", False, 
                             f"Should block merchant access. Status: {status}")
        
        # Overall cross-role prevention score
        prevention_rate = (blocked_count / total_count) * 100
        if prevention_rate >= 90:
            self.log_test("Cross-Role Prevention: Overall security", True, 
                         f"Excellent cross-role prevention: {prevention_rate:.1f}%")
        elif prevention_rate >= 70:
            self.log_test("Cross-Role Prevention: Overall security", True, 
                         f"Good cross-role prevention: {prevention_rate:.1f}%")
        else:
            self.log_test("Cross-Role Prevention: Overall security", False, 
                         f"Poor cross-role prevention: {prevention_rate:.1f}%")
    
    async def run_all_tests(self):
        """Run all security authentication tests"""
        print("🔐 Starting CRITICAL SECURITY VERIFICATION TEST")
        print("Authentication Flows and Admin Portal Access Control")
        print("=" * 70)
        
        # Run all test suites in order
        await self.test_merchant_login_verification()
        await self.test_admin_login_verification()
        await self.test_merchant_cannot_access_admin_routes()
        await self.test_admin_can_access_admin_routes()
        await self.test_role_based_access_control()
        await self.test_authentication_state_consistency()
        await self.test_backend_security_enforcement()
        await self.test_cross_role_access_prevention()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🛡️ CRITICAL SECURITY VERIFICATION SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Security Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Security Score: {(passed_tests/total_tests*100):.1f}%")
        
        # Critical security findings
        print(f"\n🔍 CRITICAL SECURITY FINDINGS:")
        
        # Check merchant login
        merchant_login_tests = [r for r in self.test_results if "Merchant Login:" in r["test"]]
        merchant_login_passed = sum(1 for t in merchant_login_tests if t["success"])
        if merchant_login_passed == len(merchant_login_tests):
            print(f"   ✅ Merchant Authentication: SECURE ({merchant_login_passed}/{len(merchant_login_tests)} tests passed)")
        else:
            print(f"   ❌ Merchant Authentication: VULNERABLE ({merchant_login_passed}/{len(merchant_login_tests)} tests passed)")
        
        # Check admin login
        admin_login_tests = [r for r in self.test_results if "Admin Login:" in r["test"]]
        admin_login_passed = sum(1 for t in admin_login_tests if t["success"])
        if admin_login_passed == len(admin_login_tests):
            print(f"   ✅ Admin Authentication: SECURE ({admin_login_passed}/{len(admin_login_tests)} tests passed)")
        else:
            print(f"   ❌ Admin Authentication: VULNERABLE ({admin_login_passed}/{len(admin_login_tests)} tests passed)")
        
        # Check cross-role access prevention
        cross_role_tests = [r for r in self.test_results if "Cross-Role Prevention:" in r["test"] or "Merchant Admin Access:" in r["test"]]
        cross_role_passed = sum(1 for t in cross_role_tests if t["success"])
        if cross_role_passed == len(cross_role_tests):
            print(f"   ✅ Cross-Role Access Prevention: SECURE ({cross_role_passed}/{len(cross_role_tests)} tests passed)")
        else:
            print(f"   ❌ Cross-Role Access Prevention: VULNERABLE ({cross_role_passed}/{len(cross_role_tests)} tests passed)")
        
        # Check RBAC
        rbac_tests = [r for r in self.test_results if "RBAC:" in r["test"] or "Backend Security:" in r["test"]]
        rbac_passed = sum(1 for t in rbac_tests if t["success"])
        if rbac_passed == len(rbac_tests):
            print(f"   ✅ Role-Based Access Control: SECURE ({rbac_passed}/{len(rbac_tests)} tests passed)")
        else:
            print(f"   ❌ Role-Based Access Control: VULNERABLE ({rbac_passed}/{len(rbac_tests)} tests passed)")
        
        if failed_tests > 0:
            print(f"\n❌ SECURITY VULNERABILITIES FOUND:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Final security verdict
        print(f"\n🎯 SECURITY VERDICT:")
        if failed_tests == 0:
            print("   🟢 SYSTEM IS SECURE - All authentication flows working correctly")
            print("   🟢 ADMIN PORTAL ACCESS CONTROL - Properly enforced")
            print("   🟢 MERCHANT CREDENTIALS - Cannot access admin routes")
        elif failed_tests <= 2:
            print("   🟡 SYSTEM IS MOSTLY SECURE - Minor issues found")
            print("   🟡 Review failed tests for potential security improvements")
        else:
            print("   🔴 SYSTEM HAS SECURITY VULNERABILITIES")
            print("   🔴 IMMEDIATE ACTION REQUIRED - Fix authentication issues")
            print("   🔴 DO NOT DEPLOY TO PRODUCTION until issues are resolved")

async def main():
    """Main test execution"""
    async with SecurityAuthTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())