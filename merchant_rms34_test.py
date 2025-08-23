#!/usr/bin/env python3
"""
Merchant User Creation and Login Test for tenant-rms34
Tests the specific requirement to create merchant@rms34.com user and verify login
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

# Test merchant credentials as specified in review request
MERCHANT_EMAIL = "merchant@rms34.com"
MERCHANT_PASSWORD = "merchant123"

class MerchantRMS34TestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.merchant_token = None
        
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
            request_headers = {**TEST_HEADERS, **(headers or {})}
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500

    async def test_backend_health(self):
        """Test backend health and user endpoints availability"""
        print("\n🏥 Testing Backend Health...")
        
        # Test 1: Backend health check
        success, response, status = await self.make_request("GET", "/health")
        self.log_test("Backend Health Check", success, 
                     f"Status: {status}, Response: {response}")
        
        # Test 2: User endpoints availability
        endpoints_to_check = [
            "/users/register",
            "/users/login"
        ]
        
        for endpoint in endpoints_to_check:
            # Use OPTIONS to check if endpoint exists
            try:
                url = f"{BACKEND_URL}{endpoint}"
                async with self.session.options(url, headers=TEST_HEADERS) as response:
                    endpoint_exists = response.status != 404
                    self.log_test(f"Endpoint availability: {endpoint}", endpoint_exists,
                                f"Status: {response.status}")
            except Exception as e:
                self.log_test(f"Endpoint availability: {endpoint}", False, f"Error: {str(e)}")

    async def test_tenant_rms34_exists(self):
        """Verify tenant-rms34 exists in the system"""
        print("\n🏢 Testing Tenant RMS34 Existence...")
        
        # Check if tenant exists by trying to get tenant info
        success, response, status = await self.make_request("GET", f"/tenants/{TEST_TENANT_ID}")
        
        if success:
            self.log_test("Tenant RMS34 Existence", True, 
                         f"Tenant found: {response.get('name', 'Unknown')}")
        else:
            # Try to create tenant if it doesn't exist
            tenant_data = {
                "name": "RMS Demo Store",
                "domain": "rms34.myshopify.com",
                "shopify_store_url": "https://rms34.myshopify.com"
            }
            
            create_success, create_response, create_status = await self.make_request("POST", "/tenants", tenant_data)
            
            if create_success:
                self.log_test("Tenant RMS34 Creation", True, 
                             f"Tenant created: {create_response.get('name', 'Unknown')}")
            else:
                self.log_test("Tenant RMS34 Existence/Creation", False, 
                             f"Failed to find or create tenant. Status: {status}, Create Status: {create_status}")

    async def test_merchant_user_creation(self):
        """Create merchant user for tenant-rms34"""
        print("\n👤 Testing Merchant User Creation...")
        
        # First check if user already exists by trying to login
        login_data = {
            "email": MERCHANT_EMAIL,
            "password": MERCHANT_PASSWORD,
            "tenant_id": TEST_TENANT_ID,
            "remember_me": False
        }
        
        login_success, login_response, login_status = await self.make_request("POST", "/users/login", login_data)
        
        if login_success:
            self.log_test("Merchant User Already Exists", True, 
                         f"User {MERCHANT_EMAIL} already exists and can login")
            self.merchant_token = login_response.get("access_token")
            return
        
        # User doesn't exist, create it
        merchant_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": MERCHANT_EMAIL,
            "password": MERCHANT_PASSWORD,
            "confirm_password": MERCHANT_PASSWORD,
            "role": "merchant",
            "auth_provider": "email",
            "first_name": "Merchant",
            "last_name": "RMS34",
            "is_active": True
        }
        
        success, response, status = await self.make_request("POST", "/users/register", merchant_data)
        
        if success:
            self.log_test("Merchant User Creation", True, 
                         f"Created user: {response.get('email')} with role: {response.get('role')}")
        else:
            self.log_test("Merchant User Creation", False, 
                         f"Failed to create user. Status: {status}, Response: {response}")

    async def test_merchant_login(self):
        """Test direct merchant login"""
        print("\n🔐 Testing Merchant Login...")
        
        login_data = {
            "email": MERCHANT_EMAIL,
            "password": MERCHANT_PASSWORD,
            "tenant_id": TEST_TENANT_ID,
            "remember_me": False
        }
        
        success, response, status = await self.make_request("POST", "/users/login", login_data)
        
        if success:
            self.merchant_token = response.get("access_token")
            user_info = response.get("user", {})
            
            # Verify user details
            correct_email = user_info.get("email") == MERCHANT_EMAIL
            correct_role = user_info.get("role") == "merchant"
            correct_tenant = user_info.get("tenant_id") == TEST_TENANT_ID
            has_token = bool(self.merchant_token)
            
            all_correct = correct_email and correct_role and correct_tenant and has_token
            
            details = f"Email: {user_info.get('email')}, Role: {user_info.get('role')}, Tenant: {user_info.get('tenant_id')}, Token: {'Yes' if has_token else 'No'}"
            
            self.log_test("Merchant Login Success", all_correct, details)
            
            if has_token:
                self.log_test("Access Token Generated", True, f"Token length: {len(self.merchant_token)}")
            else:
                self.log_test("Access Token Generated", False, "No access token in response")
                
        else:
            self.log_test("Merchant Login", False, 
                         f"Login failed. Status: {status}, Response: {response}")

    async def test_authenticated_access(self):
        """Test authenticated access to merchant dashboard endpoints"""
        print("\n🔑 Testing Authenticated Access...")
        
        if not self.merchant_token:
            self.log_test("Authenticated Access Test", False, "No access token available")
            return
        
        # Test authenticated endpoints
        auth_headers = {
            "Authorization": f"Bearer {self.merchant_token}",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Test 1: Get user profile
        success, response, status = await self.make_request("GET", "/users/profile", headers=auth_headers)
        self.log_test("Get User Profile", success, 
                     f"Status: {status}, User: {response.get('email', 'Unknown') if success else 'Failed'}")
        
        # Test 2: Get tenant settings (merchant should have access)
        success, response, status = await self.make_request("GET", f"/tenants/{TEST_TENANT_ID}/settings", headers=auth_headers)
        self.log_test("Get Tenant Settings", success, 
                     f"Status: {status}, Settings available: {'Yes' if success and 'settings' in response else 'No'}")
        
        # Test 3: Get returns (merchant should have access)
        success, response, status = await self.make_request("GET", "/returns/", headers=auth_headers)
        self.log_test("Get Returns List", success, 
                     f"Status: {status}, Returns count: {len(response.get('returns', [])) if success else 'Failed'}")

    async def test_shopify_connection_status(self):
        """Test Shopify connection status for tenant-rms34"""
        print("\n🛍️ Testing Shopify Connection Status...")
        
        if not self.merchant_token:
            self.log_test("Shopify Connection Test", False, "No access token available")
            return
        
        auth_headers = {
            "Authorization": f"Bearer {self.merchant_token}",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Test Shopify connection status
        success, response, status = await self.make_request("GET", "/auth/shopify/status", headers=auth_headers)
        
        if success:
            connection_status = response.get("status", "unknown")
            shop_domain = response.get("shop_domain", "unknown")
            
            self.log_test("Shopify Connection Status", True, 
                         f"Status: {connection_status}, Shop: {shop_domain}")
            
            # Check if connected
            if connection_status == "connected":
                self.log_test("Shopify Integration Active", True, 
                             f"Shop {shop_domain} is connected")
            else:
                self.log_test("Shopify Integration Active", False, 
                             f"Shop not connected. Status: {connection_status}")
        else:
            self.log_test("Shopify Connection Status", False, 
                         f"Failed to get status. Status: {status}, Response: {response}")

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Merchant RMS34 User Creation and Login Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Tenant ID: {TEST_TENANT_ID}")
        print(f"Merchant Email: {MERCHANT_EMAIL}")
        print("=" * 80)
        
        # Run tests in order
        await self.test_backend_health()
        await self.test_tenant_rms34_exists()
        await self.test_merchant_user_creation()
        await self.test_merchant_login()
        await self.test_authenticated_access()
        await self.test_shopify_connection_status()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 MERCHANT USER STATUS:")
        if self.merchant_token:
            print(f"✅ Merchant user {MERCHANT_EMAIL} is ready for tenant-rms34")
            print("✅ User can login directly without admin impersonation")
            print("✅ Access token generated successfully")
        else:
            print(f"❌ Merchant user {MERCHANT_EMAIL} is NOT ready")
            print("❌ Direct login failed")
        
        return success_rate >= 80  # Consider success if 80% or more tests pass


async def main():
    """Main test runner"""
    async with MerchantRMS34TestSuite() as test_suite:
        success = await test_suite.run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)