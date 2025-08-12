#!/usr/bin/env python3
"""
Admin Authentication Testing
Tests admin user credentials and login endpoint functionality
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration from environment
BACKEND_URL = "https://returnhub-1.preview.emergentagent.com/api"
EXPECTED_ADMIN_EMAIL = "admin@returns-manager.com"
EXPECTED_ADMIN_PASSWORD = "AdminPassword123!"
EXPECTED_TENANT_ID = "tenant-rms34"
EXPECTED_ADMIN_ROLE = "admin"

class AdminAuthTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.admin_token = None
        
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
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_database_connection(self):
        """Test if backend is accessible"""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Backend Health Check", True, f"Backend is accessible: {data.get('status')}")
                    return True
                else:
                    self.log_test("Backend Health Check", False, f"Backend returned status {response.status}")
                    return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def test_admin_user_exists_in_database(self):
        """Test if admin user exists in the database by attempting login"""
        try:
            login_data = {
                "tenant_id": EXPECTED_TENANT_ID,
                "email": EXPECTED_ADMIN_EMAIL,
                "password": EXPECTED_ADMIN_PASSWORD
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": EXPECTED_TENANT_ID
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/users/login", 
                json=login_data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Check if user data indicates admin exists
                    user_data = response_data.get("user", {})
                    if user_data.get("email") == EXPECTED_ADMIN_EMAIL:
                        self.log_test(
                            "Admin User Exists in Database", 
                            True, 
                            f"Admin user {EXPECTED_ADMIN_EMAIL} found in database"
                        )
                        return True, response_data
                    else:
                        self.log_test(
                            "Admin User Exists in Database", 
                            False, 
                            f"Login successful but user email mismatch: {user_data.get('email')}"
                        )
                        return False, response_data
                elif response.status == 401:
                    # Invalid credentials - user might not exist or password wrong
                    error_msg = response_data.get("detail", "Invalid credentials")
                    self.log_test(
                        "Admin User Exists in Database", 
                        False, 
                        f"Admin user authentication failed: {error_msg}",
                        response_data
                    )
                    return False, response_data
                else:
                    self.log_test(
                        "Admin User Exists in Database", 
                        False, 
                        f"Unexpected response status {response.status}",
                        response_data
                    )
                    return False, response_data
                    
        except Exception as e:
            self.log_test("Admin User Exists in Database", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_admin_login_endpoint(self):
        """Test the /api/users/login endpoint with admin credentials"""
        try:
            login_data = {
                "tenant_id": EXPECTED_TENANT_ID,
                "email": EXPECTED_ADMIN_EMAIL,
                "password": EXPECTED_ADMIN_PASSWORD
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": EXPECTED_TENANT_ID
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/users/login", 
                json=login_data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Admin Login Endpoint", 
                        True, 
                        f"Login successful with status {response.status}"
                    )
                    return True, response_data
                else:
                    error_msg = response_data.get("detail", "Unknown error")
                    self.log_test(
                        "Admin Login Endpoint", 
                        False, 
                        f"Login failed with status {response.status}: {error_msg}",
                        response_data
                    )
                    return False, response_data
                    
        except Exception as e:
            self.log_test("Admin Login Endpoint", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_admin_role_verification(self, login_response: Dict[str, Any]):
        """Verify the user has 'admin' role"""
        try:
            user_data = login_response.get("user", {})
            user_role = user_data.get("role")
            
            if user_role == EXPECTED_ADMIN_ROLE:
                self.log_test(
                    "Admin Role Verification", 
                    True, 
                    f"User has correct admin role: {user_role}"
                )
                return True
            else:
                self.log_test(
                    "Admin Role Verification", 
                    False, 
                    f"User role mismatch. Expected: {EXPECTED_ADMIN_ROLE}, Got: {user_role}",
                    user_data
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Role Verification", False, f"Error checking role: {str(e)}")
            return False
    
    async def test_tenant_id_verification(self, login_response: Dict[str, Any]):
        """Test with tenant_id 'tenant-rms34'"""
        try:
            user_data = login_response.get("user", {})
            user_tenant = user_data.get("tenant_id")
            
            if user_tenant == EXPECTED_TENANT_ID:
                self.log_test(
                    "Tenant ID Verification", 
                    True, 
                    f"User has correct tenant ID: {user_tenant}"
                )
                return True
            else:
                self.log_test(
                    "Tenant ID Verification", 
                    False, 
                    f"Tenant ID mismatch. Expected: {EXPECTED_TENANT_ID}, Got: {user_tenant}",
                    user_data
                )
                return False
                
        except Exception as e:
            self.log_test("Tenant ID Verification", False, f"Error checking tenant ID: {str(e)}")
            return False
    
    async def test_jwt_token_and_user_info(self, login_response: Dict[str, Any]):
        """Check if the API response includes proper JWT token and user info"""
        try:
            # Check for JWT token
            token = login_response.get("access_token") or login_response.get("token")
            if not token:
                self.log_test(
                    "JWT Token Verification", 
                    False, 
                    "No JWT token found in response",
                    login_response
                )
                return False
            
            # Basic JWT format check (should have 3 parts separated by dots)
            token_parts = token.split('.')
            if len(token_parts) != 3:
                self.log_test(
                    "JWT Token Verification", 
                    False, 
                    f"Invalid JWT format. Expected 3 parts, got {len(token_parts)}"
                )
                return False
            
            # Check for user info
            user_data = login_response.get("user", {})
            required_user_fields = ["email", "role", "tenant_id"]
            missing_fields = [field for field in required_user_fields if not user_data.get(field)]
            
            if missing_fields:
                self.log_test(
                    "User Info Verification", 
                    False, 
                    f"Missing required user fields: {missing_fields}",
                    user_data
                )
                return False
            
            self.log_test(
                "JWT Token and User Info", 
                True, 
                f"Valid JWT token and complete user info provided. Token length: {len(token)}"
            )
            
            # Store token for potential future tests
            self.admin_token = token
            return True
            
        except Exception as e:
            self.log_test("JWT Token and User Info", False, f"Error verifying token/user info: {str(e)}")
            return False
    
    async def test_token_validation(self):
        """Test if the JWT token can be used for authenticated requests"""
        if not self.admin_token:
            self.log_test("Token Validation", False, "No admin token available for testing")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json",
                "X-Tenant-Id": EXPECTED_TENANT_ID
            }
            
            # Try to access a protected endpoint (like user profile)
            async with self.session.get(
                f"{BACKEND_URL}/users/profile", 
                headers=headers
            ) as response:
                
                if response.status == 200:
                    self.log_test(
                        "Token Validation", 
                        True, 
                        "JWT token successfully validated for authenticated requests"
                    )
                    return True
                elif response.status == 401:
                    response_data = await response.json()
                    self.log_test(
                        "Token Validation", 
                        False, 
                        "JWT token rejected by server",
                        response_data
                    )
                    return False
                else:
                    response_data = await response.json()
                    self.log_test(
                        "Token Validation", 
                        False, 
                        f"Unexpected response status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Token Validation", False, f"Error validating token: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all admin authentication tests"""
        print("🎯 ADMIN AUTHENTICATION TESTING STARTED")
        print(f"Testing admin credentials: {EXPECTED_ADMIN_EMAIL}")
        print(f"Expected tenant: {EXPECTED_TENANT_ID}")
        print(f"Expected role: {EXPECTED_ADMIN_ROLE}")
        print("-" * 60)
        
        # Skip health check and proceed directly to admin tests
        print("ℹ️  Skipping health check - proceeding directly to admin authentication tests")
        
        # Test 1: Admin user exists and login works
        user_exists, login_response = await self.test_admin_user_exists_in_database()
        
        if not user_exists or not login_response:
            print("❌ Admin user authentication failed. Cannot proceed with further tests.")
            await self.print_summary()
            return
        
        # Test 3: Login endpoint functionality
        login_ok, login_data = await self.test_admin_login_endpoint()
        if login_ok and login_data:
            login_response = login_data  # Use the fresh login data
        
        # Test 4: Role verification
        await self.test_admin_role_verification(login_response)
        
        # Test 5: Tenant ID verification
        await self.test_tenant_id_verification(login_response)
        
        # Test 6: JWT token and user info
        await self.test_jwt_token_and_user_info(login_response)
        
        # Test 7: Token validation
        await self.test_token_validation()
        
        # Print summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 ADMIN AUTHENTICATION TEST SUMMARY")
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
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n🎯 CRITICAL FINDINGS:")
        
        # Check if admin user exists
        admin_exists = any(r["success"] for r in self.test_results if "Admin User Exists" in r["test"])
        if admin_exists:
            print("✅ Admin user exists in database and can authenticate")
        else:
            print("❌ Admin user does not exist or cannot authenticate")
            print("   RECOMMENDATION: Create admin user with proper credentials")
        
        # Check if login endpoint works
        login_works = any(r["success"] for r in self.test_results if "Login Endpoint" in r["test"])
        if login_works:
            print("✅ Admin login endpoint is functional")
        else:
            print("❌ Admin login endpoint has issues")
        
        # Check role and tenant
        role_ok = any(r["success"] for r in self.test_results if "Role Verification" in r["test"])
        tenant_ok = any(r["success"] for r in self.test_results if "Tenant ID Verification" in r["test"])
        
        if role_ok and tenant_ok:
            print("✅ Admin user has correct role and tenant assignment")
        else:
            print("❌ Admin user role or tenant assignment issues detected")
        
        # Check JWT functionality
        jwt_ok = any(r["success"] for r in self.test_results if "JWT Token" in r["test"])
        if jwt_ok:
            print("✅ JWT token generation and user info response working")
        else:
            print("❌ JWT token or user info response issues detected")

async def main():
    """Main test execution"""
    async with AdminAuthTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())