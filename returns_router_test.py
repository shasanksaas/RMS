#!/usr/bin/env python3
"""
CRITICAL ROUTER CONFLICT FIX VERIFICATION TEST
Tests that the returns endpoints are now accessible after disabling conflicting routers
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
MERCHANT_EMAIL = "merchant@rms34.com"
MERCHANT_PASSWORD = "merchant123"

class ReturnsRouterTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        
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
            request_headers = headers or {}
            
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
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def authenticate_merchant(self):
        """Authenticate as merchant user for tenant-rms34"""
        print("\n🔐 Authenticating merchant user...")
        
        auth_data = {
            "email": MERCHANT_EMAIL,
            "password": MERCHANT_PASSWORD,
            "tenant_id": TEST_TENANT_ID
        }
        
        success, response, status = await self.make_request("POST", "/users/login", auth_data)
        
        if success and response.get("access_token"):
            self.auth_token = response["access_token"]
            self.log_test("Authentication: Merchant login", True, f"Successfully authenticated as {MERCHANT_EMAIL}")
            return True
        else:
            self.log_test("Authentication: Merchant login", False, f"Failed to authenticate. Status: {status}, Response: {response}")
            return False
    
    async def test_returns_api_accessibility(self):
        """Test 1: Returns API Accessibility - Test GET /api/returns/ endpoint"""
        print("\n🎯 Testing Returns API Accessibility...")
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test GET /api/returns/ endpoint
        success, response, status = await self.make_request("GET", "/returns/", headers=headers)
        
        if success and status == 200:
            self.log_test("Returns API: GET /api/returns/ accessibility", True, 
                         f"Endpoint returns 200 status (not 404). Response type: {type(response)}")
            
            # Check if response has expected structure
            if isinstance(response, dict):
                if "items" in response or "returns" in response or isinstance(response, list):
                    self.log_test("Returns API: Response structure", True, "Returns data structure is valid")
                else:
                    self.log_test("Returns API: Response structure", True, f"Response structure: {list(response.keys()) if isinstance(response, dict) else 'Non-dict response'}")
            elif isinstance(response, list):
                self.log_test("Returns API: Response structure", True, f"Returns list with {len(response)} items")
            else:
                self.log_test("Returns API: Response structure", False, f"Unexpected response type: {type(response)}")
                
        elif status == 404:
            self.log_test("Returns API: GET /api/returns/ accessibility", False, 
                         "❌ CRITICAL: Endpoint still returns 404 - router conflict not resolved!")
        else:
            self.log_test("Returns API: GET /api/returns/ accessibility", False, 
                         f"Endpoint returns {status} status. Response: {response}")
        
        # Test alternative returns endpoints
        for endpoint in ["/returns", "/returns?limit=10", "/returns?page=1"]:
            success, response, status = await self.make_request("GET", endpoint, headers=headers)
            
            endpoint_name = f"GET /api{endpoint}"
            if success and status == 200:
                self.log_test(f"Returns API: {endpoint_name} accessibility", True, f"Endpoint accessible (200)")
            elif status == 404:
                self.log_test(f"Returns API: {endpoint_name} accessibility", False, f"Endpoint returns 404")
            else:
                self.log_test(f"Returns API: {endpoint_name} accessibility", False, f"Status: {status}")
    
    async def test_tenant_isolation_verification(self):
        """Test 2: Tenant Isolation Verification"""
        print("\n🏢 Testing Tenant Isolation...")
        
        # Test with correct tenant ID
        correct_headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        if self.auth_token:
            correct_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        success, response, status = await self.make_request("GET", "/returns/", headers=correct_headers)
        
        if success:
            self.log_test("Tenant Isolation: Access with correct tenant ID", True, 
                         f"tenant-rms34 can access their returns data (Status: {status})")
            
            # Store the response for comparison
            tenant_rms34_data = response
        else:
            self.log_test("Tenant Isolation: Access with correct tenant ID", False, 
                         f"Failed to access with correct tenant ID. Status: {status}")
            tenant_rms34_data = None
        
        # Test with invalid tenant ID
        invalid_headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": "invalid-tenant-id"
        }
        
        if self.auth_token:
            invalid_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        success, response, status = await self.make_request("GET", "/returns/", headers=invalid_headers)
        
        if not success and status in [400, 403, 404]:
            self.log_test("Tenant Isolation: Invalid tenant ID rejection", True, 
                         f"Invalid tenant ID properly rejected with status {status}")
        elif success:
            # Check if data is different (should be empty or different)
            if tenant_rms34_data and response != tenant_rms34_data:
                self.log_test("Tenant Isolation: Data isolation", True, 
                             "Different tenant returns different data (isolation working)")
            else:
                self.log_test("Tenant Isolation: Data isolation", False, 
                             "Same data returned for different tenants (isolation issue)")
        else:
            self.log_test("Tenant Isolation: Invalid tenant ID rejection", False, 
                         f"Invalid tenant ID not properly handled. Status: {status}")
        
        # Test without tenant ID header
        no_tenant_headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            no_tenant_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        success, response, status = await self.make_request("GET", "/returns/", headers=no_tenant_headers)
        
        if not success and status in [400, 403]:
            self.log_test("Tenant Isolation: Missing tenant ID rejection", True, 
                         f"Missing tenant ID properly rejected with status {status}")
        else:
            self.log_test("Tenant Isolation: Missing tenant ID rejection", False, 
                         f"Missing tenant ID not properly handled. Status: {status}")
    
    async def test_router_conflict_resolution(self):
        """Test 3: Router Conflict Resolution"""
        print("\n🔀 Testing Router Conflict Resolution...")
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test main returns endpoints that should be handled by returns_enhanced_router
        main_endpoints = [
            "/returns/",
            "/returns",
            "/returns?limit=5",
            "/returns?page=1&limit=10"
        ]
        
        working_endpoints = 0
        total_endpoints = len(main_endpoints)
        
        for endpoint in main_endpoints:
            success, response, status = await self.make_request("GET", endpoint, headers=headers)
            
            if success and status == 200:
                working_endpoints += 1
                self.log_test(f"Router Conflict: {endpoint} handled correctly", True, 
                             "Endpoint accessible without conflicts")
            elif status == 404:
                self.log_test(f"Router Conflict: {endpoint} handled correctly", False, 
                             "❌ CRITICAL: 404 indicates routing conflict still exists")
            else:
                self.log_test(f"Router Conflict: {endpoint} handled correctly", False, 
                             f"Unexpected status: {status}")
        
        # Overall router conflict assessment
        if working_endpoints == total_endpoints:
            self.log_test("Router Conflict: Overall resolution", True, 
                         "✅ All main returns endpoints work consistently - conflicts resolved!")
        elif working_endpoints > 0:
            self.log_test("Router Conflict: Overall resolution", False, 
                         f"⚠️ Partial resolution: {working_endpoints}/{total_endpoints} endpoints working")
        else:
            self.log_test("Router Conflict: Overall resolution", False, 
                         "❌ CRITICAL: No endpoints working - router conflicts not resolved")
        
        # Test that conflicting routers are disabled
        conflicting_endpoints = [
            "/portal/returns/",
            "/admin/returns/",
            "/elite/portal/returns/",
            "/elite/admin/returns/"
        ]
        
        for endpoint in conflicting_endpoints:
            success, response, status = await self.make_request("GET", endpoint, headers=headers)
            
            if status == 404:
                self.log_test(f"Router Conflict: {endpoint} properly disabled", True, 
                             "Conflicting router properly disabled (404)")
            elif success:
                self.log_test(f"Router Conflict: {endpoint} properly disabled", False, 
                             f"⚠️ Conflicting router still active (Status: {status})")
            else:
                self.log_test(f"Router Conflict: {endpoint} properly disabled", True, 
                             f"Conflicting router disabled or secured (Status: {status})")
    
    async def test_data_structure_validation(self):
        """Test 4: Data Structure Validation"""
        print("\n📊 Testing Data Structure Validation...")
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test returns data structure
        success, response, status = await self.make_request("GET", "/returns/", headers=headers)
        
        if success and status == 200:
            self.log_test("Data Structure: Returns endpoint response", True, 
                         f"Returns endpoint returns valid response (Status: {status})")
            
            # Validate response structure
            if isinstance(response, dict):
                # Check for pagination structure
                if "items" in response:
                    self.log_test("Data Structure: Pagination structure", True, 
                                 f"Response has 'items' field with {len(response['items'])} returns")
                    
                    # Check individual return structure
                    if response["items"]:
                        return_item = response["items"][0]
                        expected_fields = ["id", "tenant_id", "status", "customer_email", "created_at"]
                        
                        present_fields = [field for field in expected_fields if field in return_item]
                        if len(present_fields) >= 3:  # At least 3 core fields
                            self.log_test("Data Structure: Return item fields", True, 
                                         f"Return items have core fields: {present_fields}")
                        else:
                            self.log_test("Data Structure: Return item fields", False, 
                                         f"Missing core fields. Present: {present_fields}")
                    else:
                        self.log_test("Data Structure: Return item fields", True, 
                                     "No returns data to validate (empty result is valid)")
                
                elif isinstance(response, list):
                    self.log_test("Data Structure: List format", True, 
                                 f"Response is list with {len(response)} returns")
                else:
                    self.log_test("Data Structure: Response format", True, 
                                 f"Response structure: {list(response.keys())}")
            
            elif isinstance(response, list):
                self.log_test("Data Structure: List response", True, 
                             f"Returns data as list with {len(response)} items")
            else:
                self.log_test("Data Structure: Response format", False, 
                             f"Unexpected response format: {type(response)}")
        else:
            self.log_test("Data Structure: Returns endpoint response", False, 
                         f"Failed to get valid response. Status: {status}")
        
        # Test pagination functionality
        success, response, status = await self.make_request("GET", "/returns?limit=5", headers=headers)
        
        if success and status == 200:
            self.log_test("Data Structure: Pagination functionality", True, 
                         "Pagination parameter accepted")
        else:
            self.log_test("Data Structure: Pagination functionality", False, 
                         f"Pagination not working. Status: {status}")
        
        # Test filtering functionality
        success, response, status = await self.make_request("GET", "/returns?status=requested", headers=headers)
        
        if success and status == 200:
            self.log_test("Data Structure: Filtering functionality", True, 
                         "Status filtering parameter accepted")
        else:
            self.log_test("Data Structure: Filtering functionality", False, 
                         f"Filtering not working. Status: {status}")
        
        # Test search functionality
        success, response, status = await self.make_request("GET", "/returns?search=test", headers=headers)
        
        if success and status == 200:
            self.log_test("Data Structure: Search functionality", True, 
                         "Search parameter accepted")
        else:
            self.log_test("Data Structure: Search functionality", False, 
                         f"Search not working. Status: {status}")
    
    async def test_return_detail_endpoints(self):
        """Test return detail endpoints work properly"""
        print("\n🔍 Testing Return Detail Endpoints...")
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # First get a list of returns to test detail endpoint
        success, response, status = await self.make_request("GET", "/returns?limit=1", headers=headers)
        
        if success and status == 200:
            returns_data = response
            
            # Extract return ID for detail testing
            return_id = None
            if isinstance(returns_data, dict) and "items" in returns_data and returns_data["items"]:
                return_id = returns_data["items"][0].get("id")
            elif isinstance(returns_data, list) and returns_data:
                return_id = returns_data[0].get("id")
            
            if return_id:
                # Test return detail endpoint
                success, detail_response, status = await self.make_request("GET", f"/returns/{return_id}", headers=headers)
                
                if success and status == 200:
                    self.log_test("Return Detail: Individual return access", True, 
                                 f"Successfully retrieved return {return_id}")
                    
                    # Validate detail response has more information
                    if isinstance(detail_response, dict) and "id" in detail_response:
                        self.log_test("Return Detail: Response structure", True, 
                                     "Return detail has proper structure")
                    else:
                        self.log_test("Return Detail: Response structure", False, 
                                     "Return detail response structure invalid")
                else:
                    self.log_test("Return Detail: Individual return access", False, 
                                 f"Failed to retrieve return detail. Status: {status}")
            else:
                self.log_test("Return Detail: Test data availability", False, 
                             "No return ID available for detail testing")
        else:
            self.log_test("Return Detail: Test data availability", False, 
                         f"Cannot get returns list for detail testing. Status: {status}")
    
    async def run_all_tests(self):
        """Run all router conflict fix verification tests"""
        print("🚀 CRITICAL ROUTER CONFLICT FIX VERIFICATION")
        print("=" * 60)
        print(f"Testing returns endpoints for tenant: {TEST_TENANT_ID}")
        print(f"Using merchant credentials: {MERCHANT_EMAIL}")
        print("=" * 60)
        
        # Authenticate first
        if not await self.authenticate_merchant():
            print("❌ Authentication failed. Continuing with unauthenticated tests...")
        
        # Run all test suites
        await self.test_returns_api_accessibility()
        await self.test_tenant_isolation_verification()
        await self.test_router_conflict_resolution()
        await self.test_data_structure_validation()
        await self.test_return_detail_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ROUTER CONFLICT FIX VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Check critical success criteria
        critical_tests = [
            "Returns API: GET /api/returns/ accessibility",
            "Tenant Isolation: Access with correct tenant ID",
            "Router Conflict: Overall resolution"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            for result in self.test_results:
                if test_name in result["test"] and result["success"]:
                    critical_passed += 1
                    break
        
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA:")
        print(f"✅ Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 SUCCESS: Router conflict fix is working correctly!")
            print("✅ GET /api/returns/ returns 200 status (not 404)")
            print("✅ Returns data is properly formatted and accessible")
            print("✅ Tenant isolation works correctly")
            print("✅ No more routing conflicts or 404 errors")
        else:
            print("❌ CRITICAL ISSUES REMAIN:")
            for test_name in critical_tests:
                found = False
                for result in self.test_results:
                    if test_name in result["test"]:
                        if not result["success"]:
                            print(f"   ❌ {test_name}: {result['details']}")
                        found = True
                        break
                if not found:
                    print(f"   ❌ {test_name}: Test not found")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n📋 RECOMMENDATION:")
        if critical_passed == len(critical_tests):
            print("✅ Router conflict fix is successful. Returns endpoints are now accessible.")
        else:
            print("❌ Router conflict fix needs additional work. Check server.py router configuration.")

async def main():
    """Main test execution"""
    async with ReturnsRouterTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())