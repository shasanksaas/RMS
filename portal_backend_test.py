#!/usr/bin/env python3
"""
Customer Returns Portal Backend API Testing
Tests the new customer returns portal backend APIs as requested
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
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class PortalAPITestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_order = None
        
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
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    response_data = await response.json()
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def setup_test_data(self):
        """Setup test data for portal API testing"""
        print("\n🔧 Setting up test data...")
        
        # First check if backend is accessible
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if not success:
            self.log_test("Setup: Backend health check", False, f"Backend not accessible: {status}")
            return False
        
        self.log_test("Setup: Backend health check", True, "Backend is healthy")
        
        # Get existing orders from seeded data for tenant-rms34
        success, orders_data, status = await self.make_request("GET", "/orders?limit=10")
        
        if success and orders_data.get("items"):
            # Look for Order #1001 specifically or use first available order
            for order in orders_data["items"]:
                if order.get("order_number") == "1001" or order.get("name") == "#1001":
                    self.test_order = order
                    break
            
            if not self.test_order:
                self.test_order = orders_data["items"][0]
            
            self.log_test("Setup: Get test order from seeded data", True, 
                         f"Using order {self.test_order.get('order_number', self.test_order.get('name', 'Unknown'))} for testing")
            return True
        else:
            self.log_test("Setup: Get test order", False, f"No orders found for tenant {TEST_TENANT_ID}. Status: {status}, Response: {orders_data}")
            return False
    
    async def test_order_lookup_portal(self):
        """Test 1: Order lookup: POST /api/portal/returns/lookup-order"""
        print("\n🔍 Testing Order Lookup Portal API...")
        
        if not self.test_order:
            self.log_test("Portal Order Lookup: No test order available", False)
            return
        
        # Test 1: Valid order lookup
        lookup_data = {
            "orderNumber": self.test_order.get("order_number", self.test_order.get("name", "1001")),
            "email": self.test_order.get("customer_email", "customer@example.com")
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/lookup-order", lookup_data)
        
        if success:
            self.log_test("Portal Order Lookup: Valid lookup", True, 
                         f"Successfully found order {lookup_data['orderNumber']}")
            
            # Validate response structure
            required_fields = ["id", "order_number", "customer_name", "customer_email", "line_items"]
            if all(field in response for field in required_fields):
                self.log_test("Portal Order Lookup: Response structure", True, "All required fields present")
            else:
                missing_fields = [field for field in required_fields if field not in response]
                self.log_test("Portal Order Lookup: Response structure", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Portal Order Lookup: Valid lookup", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Invalid order number
        invalid_lookup = {
            "orderNumber": "INVALID-ORDER-999",
            "email": lookup_data["email"]
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/lookup-order", invalid_lookup)
        
        if not success and status == 404:
            self.log_test("Portal Order Lookup: Invalid order rejection", True, "Correctly rejected invalid order number")
        else:
            self.log_test("Portal Order Lookup: Invalid order rejection", False, "Should reject invalid order number")
        
        # Test 3: Invalid email
        invalid_email_lookup = {
            "orderNumber": lookup_data["orderNumber"],
            "email": "wrong@email.com"
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/lookup-order", invalid_email_lookup)
        
        if not success and status in [403, 404]:
            self.log_test("Portal Order Lookup: Invalid email rejection", True, "Correctly rejected invalid email")
        else:
            self.log_test("Portal Order Lookup: Invalid email rejection", False, "Should reject invalid email")
    
    async def test_policy_preview_portal(self):
        """Test 2: Policy preview: POST /api/portal/returns/policy-preview"""
        print("\n📋 Testing Policy Preview Portal API...")
        
        if not self.test_order:
            self.log_test("Portal Policy Preview: No test order available", False)
            return
        
        # Test 1: Valid policy preview request
        preview_data = {
            "items": [
                {
                    "line_item_id": "test-line-item-1",
                    "quantity": 1,
                    "reason": "damaged_defective",
                    "reason_note": "Item arrived damaged"
                }
            ],
            "order_id": self.test_order.get("id", self.test_order.get("order_id"))
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/policy-preview", preview_data)
        
        if success:
            self.log_test("Portal Policy Preview: Valid request", True, 
                         f"Policy preview generated successfully")
            
            # Validate response structure
            expected_fields = ["estimated_refund", "fees", "auto_approve_eligible"]
            if any(field in response for field in expected_fields):
                self.log_test("Portal Policy Preview: Response structure", True, "Policy preview fields present")
            else:
                self.log_test("Portal Policy Preview: Response structure", False, "Missing policy preview fields")
        else:
            self.log_test("Portal Policy Preview: Valid request", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Invalid order ID
        invalid_preview = {
            "items": preview_data["items"],
            "order_id": "invalid-order-id"
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/policy-preview", invalid_preview)
        
        if not success:
            self.log_test("Portal Policy Preview: Invalid order rejection", True, "Correctly rejected invalid order ID")
        else:
            self.log_test("Portal Policy Preview: Invalid order rejection", False, "Should reject invalid order ID")
    
    async def test_admin_returns_endpoint(self):
        """Test 3: Admin returns endpoints: GET /api/returns"""
        print("\n👨‍💼 Testing Admin Returns Endpoint...")
        
        # Test 1: Basic returns retrieval
        success, response, status = await self.make_request("GET", "/returns")
        
        if success:
            self.log_test("Admin Returns: Basic retrieval", True, 
                         f"Retrieved returns data successfully")
            
            # Validate response structure
            if "items" in response and "pagination" in response:
                self.log_test("Admin Returns: Response structure", True, "Proper pagination structure")
                
                # Check if we have returns data
                if response["items"]:
                    self.log_test("Admin Returns: Data availability", True, 
                                 f"Found {len(response['items'])} returns")
                else:
                    self.log_test("Admin Returns: Data availability", True, "No returns found (expected for new tenant)")
            else:
                self.log_test("Admin Returns: Response structure", False, "Missing pagination structure")
        else:
            self.log_test("Admin Returns: Basic retrieval", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Returns with pagination
        success, response, status = await self.make_request("GET", "/returns?page=1&limit=10")
        
        if success:
            self.log_test("Admin Returns: Pagination", True, "Pagination parameters accepted")
        else:
            self.log_test("Admin Returns: Pagination", False, "Pagination not working")
        
        # Test 3: Returns with search filter
        success, response, status = await self.make_request("GET", "/returns?search=customer")
        
        if success:
            self.log_test("Admin Returns: Search filter", True, "Search filter accepted")
        else:
            self.log_test("Admin Returns: Search filter", False, "Search filter not working")
        
        # Test 4: Returns with status filter
        success, response, status = await self.make_request("GET", "/returns?status_filter=requested")
        
        if success:
            self.log_test("Admin Returns: Status filter", True, "Status filter accepted")
        else:
            self.log_test("Admin Returns: Status filter", False, "Status filter not working")
    
    async def test_return_creation_portal(self):
        """Test 5: Return creation: POST /api/portal/returns/create"""
        print("\n🛒 Testing Return Creation Portal API...")
        
        if not self.test_order:
            self.log_test("Portal Return Creation: No test order available", False)
            return
        
        # Test 1: Valid return creation
        return_data = {
            "orderNumber": self.test_order.get("order_number", self.test_order.get("name", "1001")),
            "email": self.test_order.get("customer_email", "customer@example.com"),
            "items": [
                {
                    "line_item_id": "test-line-item-1",
                    "quantity": 1,
                    "reason": "damaged_defective",
                    "reason_note": "Item arrived damaged during shipping"
                }
            ],
            "preferred_outcome": "refund_original",
            "return_method": "prepaid_label",
            "customer_note": "Please process refund to original payment method"
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/create", return_data)
        
        if success:
            self.log_test("Portal Return Creation: Valid request", True, 
                         f"Return created successfully")
            
            # Validate response structure
            expected_fields = ["return_id", "status"]
            if any(field in response for field in expected_fields):
                self.log_test("Portal Return Creation: Response structure", True, "Return creation response valid")
                
                # Store return ID for further testing
                if "return_id" in response:
                    return_id = response["return_id"]
                    
                    # Test return retrieval
                    success, return_details, status = await self.make_request("GET", f"/returns/{return_id}")
                    if success:
                        self.log_test("Portal Return Creation: Return retrieval", True, "Created return can be retrieved")
                    else:
                        self.log_test("Portal Return Creation: Return retrieval", False, "Cannot retrieve created return")
            else:
                self.log_test("Portal Return Creation: Response structure", False, "Missing return creation fields")
        else:
            self.log_test("Portal Return Creation: Valid request", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Invalid email for return creation
        invalid_return = {
            **return_data,
            "email": "wrong@email.com"
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/create", invalid_return)
        
        if not success:
            self.log_test("Portal Return Creation: Invalid email rejection", True, "Correctly rejected invalid email")
        else:
            self.log_test("Portal Return Creation: Invalid email rejection", False, "Should reject invalid email")
        
        # Test 3: Missing required fields
        incomplete_return = {
            "orderNumber": return_data["orderNumber"]
            # Missing email and other required fields
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/create", incomplete_return)
        
        if not success and status in [400, 422]:
            self.log_test("Portal Return Creation: Missing fields rejection", True, "Correctly rejected incomplete data")
        else:
            self.log_test("Portal Return Creation: Missing fields rejection", False, "Should reject incomplete data")
    
    async def test_portal_api_data_structure(self):
        """Test 4: Check if portal APIs return proper data structure"""
        print("\n🏗️ Testing Portal API Data Structure...")
        
        if not self.test_order:
            self.log_test("Portal Data Structure: No test order available", False)
            return
        
        # Test order lookup data structure
        lookup_data = {
            "orderNumber": self.test_order.get("order_number", self.test_order.get("name", "1001")),
            "email": self.test_order.get("customer_email", "customer@example.com")
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/lookup-order", lookup_data)
        
        if success:
            # Check for customer portal specific fields
            customer_fields = ["id", "order_number", "customer_name", "customer_email", "total_price", "line_items"]
            present_fields = [field for field in customer_fields if field in response]
            
            if len(present_fields) >= 4:  # At least 4 out of 6 fields should be present
                self.log_test("Portal Data Structure: Order lookup fields", True, 
                             f"Order lookup has {len(present_fields)}/{len(customer_fields)} expected fields")
            else:
                self.log_test("Portal Data Structure: Order lookup fields", False, 
                             f"Order lookup missing key fields. Present: {present_fields}")
            
            # Check line items structure
            if "line_items" in response and isinstance(response["line_items"], list):
                self.log_test("Portal Data Structure: Line items format", True, "Line items in proper array format")
            else:
                self.log_test("Portal Data Structure: Line items format", False, "Line items not in proper format")
        
        # Test policy preview data structure
        preview_data = {
            "items": [
                {
                    "line_item_id": "test-line-item-1",
                    "quantity": 1,
                    "reason": "damaged_defective"
                }
            ],
            "order_id": self.test_order.get("id", self.test_order.get("order_id"))
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/policy-preview", preview_data)
        
        if success:
            # Check for policy preview specific fields
            policy_fields = ["estimated_refund", "fees", "auto_approve_eligible", "return_window_valid"]
            present_policy_fields = [field for field in policy_fields if field in response]
            
            if len(present_policy_fields) >= 2:  # At least 2 policy fields should be present
                self.log_test("Portal Data Structure: Policy preview fields", True, 
                             f"Policy preview has {len(present_policy_fields)}/{len(policy_fields)} expected fields")
            else:
                self.log_test("Portal Data Structure: Policy preview fields", False, 
                             f"Policy preview missing key fields. Present: {present_policy_fields}")
    
    async def test_tenant_isolation(self):
        """Test tenant isolation for portal APIs"""
        print("\n🔒 Testing Tenant Isolation...")
        
        # Test with wrong tenant ID
        wrong_tenant_headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": "wrong-tenant-id"
        }
        
        # Test order lookup with wrong tenant
        lookup_data = {
            "orderNumber": "1001",
            "email": "customer@example.com"
        }
        
        success, response, status = await self.make_request("POST", "/portal/returns/lookup-order", 
                                                          lookup_data, headers=wrong_tenant_headers)
        
        if not success and status in [403, 404]:
            self.log_test("Tenant Isolation: Order lookup", True, "Correctly blocked cross-tenant access")
        else:
            self.log_test("Tenant Isolation: Order lookup", False, "Cross-tenant access not properly blocked")
        
        # Test admin returns with wrong tenant
        success, response, status = await self.make_request("GET", "/returns", headers=wrong_tenant_headers)
        
        if not success or (success and not response.get("items")):
            self.log_test("Tenant Isolation: Admin returns", True, "Correctly isolated returns by tenant")
        else:
            self.log_test("Tenant Isolation: Admin returns", False, "Returns not properly isolated by tenant")
    
    async def run_all_tests(self):
        """Run all portal API tests"""
        print("🚀 Starting Customer Returns Portal Backend API Testing")
        print("=" * 70)
        print(f"Testing against: {BACKEND_URL}")
        print(f"Using tenant: {TEST_TENANT_ID}")
        print("=" * 70)
        
        # Setup
        if not await self.setup_test_data():
            print("❌ Failed to setup test data. Some tests may fail...")
        
        # Run all test suites
        await self.test_order_lookup_portal()
        await self.test_policy_preview_portal()
        await self.test_admin_returns_endpoint()
        await self.test_return_creation_portal()
        await self.test_portal_api_data_structure()
        await self.test_tenant_isolation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 CUSTOMER RETURNS PORTAL API TESTING SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        
        # Analyze results by API endpoint
        api_categories = {
            "Order Lookup Portal": [r for r in self.test_results if "Portal Order Lookup:" in r["test"]],
            "Policy Preview Portal": [r for r in self.test_results if "Portal Policy Preview:" in r["test"]],
            "Admin Returns": [r for r in self.test_results if "Admin Returns:" in r["test"]],
            "Return Creation Portal": [r for r in self.test_results if "Portal Return Creation:" in r["test"]],
            "Data Structure": [r for r in self.test_results if "Portal Data Structure:" in r["test"]],
            "Tenant Isolation": [r for r in self.test_results if "Tenant Isolation:" in r["test"]],
            "Setup": [r for r in self.test_results if "Setup:" in r["test"]]
        }
        
        for category, tests in api_categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")
        
        print("\n📋 SPECIFIC API ENDPOINT RESULTS:")
        print(f"   1. POST /api/portal/returns/lookup-order - {'✅ Working' if any(r['success'] for r in self.test_results if 'Portal Order Lookup: Valid lookup' in r['test']) else '❌ Issues'}")
        print(f"   2. POST /api/portal/returns/policy-preview - {'✅ Working' if any(r['success'] for r in self.test_results if 'Portal Policy Preview: Valid request' in r['test']) else '❌ Issues'}")
        print(f"   3. GET /api/returns - {'✅ Working' if any(r['success'] for r in self.test_results if 'Admin Returns: Basic retrieval' in r['test']) else '❌ Issues'}")
        print(f"   4. POST /api/portal/returns/create - {'✅ Working' if any(r['success'] for r in self.test_results if 'Portal Return Creation: Valid request' in r['test']) else '❌ Issues'}")
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if passed_tests / total_tests >= 0.8:
            print("   ✅ EXCELLENT - Portal APIs are working well")
        elif passed_tests / total_tests >= 0.6:
            print("   ⚠️ GOOD - Portal APIs mostly working with minor issues")
        elif passed_tests / total_tests >= 0.4:
            print("   ⚠️ FAIR - Portal APIs partially working, needs attention")
        else:
            print("   ❌ POOR - Portal APIs have significant issues")

async def main():
    """Main test execution"""
    async with PortalAPITestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())