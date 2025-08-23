#!/usr/bin/env python3
"""
Backend Testing for Order Lookup with Fallbacks for tenant-rms34
Tests GET /api/orders/{order_id} lookup with multiple fallback strategies
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
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class OrderLookupTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_orders = []
        
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
            # If headers is explicitly provided, use it as-is, otherwise use TEST_HEADERS
            if headers is not None:
                request_headers = headers
            else:
                request_headers = TEST_HEADERS
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response", "text": await response.text()}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response", "text": await response.text()}
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def setup_test_data(self):
        """Setup test data and verify backend connectivity"""
        print("\n🔧 Setting up test data for tenant-rms34...")
        
        # First check if backend is accessible
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if not success:
            self.log_test("Setup: Backend health check", False, f"Backend not accessible: {status}")
            return False
        
        self.log_test("Setup: Backend health check", True, "Backend is healthy")
        
        # Get existing orders for tenant-rms34
        success, orders_data, status = await self.make_request("GET", "/orders?limit=10")
        
        if success and orders_data.get("items"):
            self.test_orders = orders_data["items"]
            self.log_test("Setup: Get test orders from tenant-rms34", True, 
                         f"Found {len(self.test_orders)} orders for testing")
            return True
        else:
            self.log_test("Setup: Get test orders", False, f"No orders found for tenant-rms34. Status: {status}, Response: {orders_data}")
            return False
    
    async def test_order_lookup_with_sample_id(self):
        """Test order lookup with sample numeric ID 6375150223682"""
        print("\n🔍 Testing Order Lookup with Sample Numeric ID...")
        
        sample_id = "6375150223682"
        
        # Test 1: Direct lookup with sample ID
        success, response, status = await self.make_request("GET", f"/orders/{sample_id}")
        
        if success:
            self.log_test("Order Lookup: Sample ID 6375150223682", True, 
                         f"Found order via fallback lookup: {response.get('order_number', 'N/A')}")
            
            # Verify response structure
            required_keys = [
                "id", "order_number", "customer_name", "customer_email", 
                "financial_status", "fulfillment_status", "total_price", 
                "currency_code", "line_items", "created_at", "updated_at", 
                "shipping_address", "returns", "shopify_order_url"
            ]
            
            missing_keys = [key for key in required_keys if key not in response]
            if not missing_keys:
                self.log_test("Order Lookup: Response structure validation", True, 
                             "All required UI keys present in response")
            else:
                self.log_test("Order Lookup: Response structure validation", False, 
                             f"Missing required keys: {missing_keys}")
                
        elif status == 404:
            self.log_test("Order Lookup: Sample ID 6375150223682", True, 
                         "Correctly returned 404 for non-existent order")
            
            # Verify 404 response structure
            if response.get("detail") == "Order not found":
                self.log_test("Order Lookup: 404 response format", True, 
                             "Correct 404 response with 'Order not found' detail")
            else:
                self.log_test("Order Lookup: 404 response format", False, 
                             f"Expected 'Order not found' detail, got: {response.get('detail')}")
        else:
            self.log_test("Order Lookup: Sample ID 6375150223682", False, 
                         f"Unexpected status {status}: {response}")
    
    async def test_order_lookup_fallbacks(self):
        """Test order lookup fallback mechanisms with existing orders"""
        print("\n🔄 Testing Order Lookup Fallback Mechanisms...")
        
        if not self.test_orders:
            self.log_test("Order Lookup Fallbacks: No test orders available", False)
            return
        
        test_order = self.test_orders[0]
        
        # Test 1: Lookup by order ID
        if test_order.get("id"):
            success, response, status = await self.make_request("GET", f"/orders/{test_order['id']}")
            if success:
                self.log_test("Order Lookup Fallbacks: By order ID", True, 
                             f"Successfully found order by ID: {test_order['id']}")
            else:
                self.log_test("Order Lookup Fallbacks: By order ID", False, 
                             f"Failed to find order by ID: {status}")
        
        # Test 2: Lookup by order_number
        if test_order.get("order_number"):
            success, response, status = await self.make_request("GET", f"/orders/{test_order['order_number']}")
            if success:
                self.log_test("Order Lookup Fallbacks: By order number", True, 
                             f"Successfully found order by order_number: {test_order['order_number']}")
            else:
                self.log_test("Order Lookup Fallbacks: By order number", False, 
                             f"Failed to find order by order_number: {status}")
        
        # Test 3: Lookup by shopify_order_id (if available)
        if test_order.get("shopify_order_id"):
            success, response, status = await self.make_request("GET", f"/orders/{test_order['shopify_order_id']}")
            if success:
                self.log_test("Order Lookup Fallbacks: By Shopify order ID", True, 
                             f"Successfully found order by shopify_order_id: {test_order['shopify_order_id']}")
            else:
                self.log_test("Order Lookup Fallbacks: By Shopify order ID", False, 
                             f"Failed to find order by shopify_order_id: {status}")
        
        # Test 4: Lookup with order number variations (with/without #)
        if test_order.get("order_number"):
            order_num = test_order["order_number"]
            # Try with # prefix if not already present
            if not order_num.startswith("#"):
                success, response, status = await self.make_request("GET", f"/orders/#{order_num}")
                if success:
                    self.log_test("Order Lookup Fallbacks: Order number with # prefix", True, 
                                 f"Successfully found order with # prefix: #{order_num}")
                else:
                    self.log_test("Order Lookup Fallbacks: Order number with # prefix", False, 
                                 f"Failed to find order with # prefix: {status}")
    
    async def test_invalid_order_ids(self):
        """Test invalid order ID handling"""
        print("\n❌ Testing Invalid Order ID Handling...")
        
        invalid_ids = [
            "nonexistent-order-id",
            "999999999999999",
            "invalid-format-123",
            "",
            "null",
            "undefined"
        ]
        
        for invalid_id in invalid_ids:
            if invalid_id == "":
                continue  # Skip empty string as it would be a different endpoint
                
            success, response, status = await self.make_request("GET", f"/orders/{invalid_id}")
            
            if status == 404 and response.get("detail") == "Order not found":
                self.log_test(f"Invalid Order ID: {invalid_id}", True, 
                             "Correctly returned 404 with 'Order not found' detail")
            else:
                self.log_test(f"Invalid Order ID: {invalid_id}", False, 
                             f"Expected 404 with 'Order not found', got {status}: {response}")
    
    async def test_response_structure_validation(self):
        """Test response structure for UI compatibility"""
        print("\n📋 Testing Response Structure for UI Compatibility...")
        
        if not self.test_orders:
            self.log_test("Response Structure: No test orders available", False)
            return
        
        test_order = self.test_orders[0]
        order_id = test_order.get("id") or test_order.get("order_number")
        
        if not order_id:
            self.log_test("Response Structure: No valid order ID found", False)
            return
        
        success, response, status = await self.make_request("GET", f"/orders/{order_id}")
        
        if not success:
            self.log_test("Response Structure: Failed to get order for validation", False, 
                         f"Status: {status}")
            return
        
        # Required keys for UI
        required_keys = [
            "id", "order_number", "customer_name", "customer_email", 
            "financial_status", "fulfillment_status", "total_price", 
            "currency_code", "line_items", "created_at", "updated_at", 
            "shipping_address", "returns", "shopify_order_url"
        ]
        
        # Check each required key
        for key in required_keys:
            if key in response:
                self.log_test(f"Response Structure: {key} present", True, 
                             f"Value type: {type(response[key]).__name__}")
            else:
                self.log_test(f"Response Structure: {key} present", False, 
                             f"Missing required key: {key}")
        
        # Validate specific field types and structures
        if "line_items" in response:
            line_items = response["line_items"]
            if isinstance(line_items, list):
                self.log_test("Response Structure: line_items is array", True, 
                             f"Contains {len(line_items)} items")
                
                # Check line item structure if items exist
                if line_items:
                    item = line_items[0]
                    item_keys = ["id", "title", "sku", "quantity", "price"]
                    missing_item_keys = [k for k in item_keys if k not in item]
                    if not missing_item_keys:
                        self.log_test("Response Structure: line_items structure", True, 
                                     "Line items have required fields")
                    else:
                        self.log_test("Response Structure: line_items structure", False, 
                                     f"Line items missing: {missing_item_keys}")
            else:
                self.log_test("Response Structure: line_items is array", False, 
                             f"Expected array, got {type(line_items).__name__}")
        
        if "returns" in response:
            returns = response["returns"]
            if isinstance(returns, list):
                self.log_test("Response Structure: returns is array", True, 
                             f"Contains {len(returns)} returns")
            else:
                self.log_test("Response Structure: returns is array", False, 
                             f"Expected array, got {type(returns).__name__}")
    
    async def test_orders_list_regression(self):
        """Test that orders list endpoint still works and requires X-Tenant-Id"""
        print("\n📝 Testing Orders List Endpoint Regression...")
        
        # Test 1: Orders list with proper tenant header
        success, response, status = await self.make_request("GET", "/orders?limit=5")
        
        if success and response.get("items"):
            self.log_test("Orders List Regression: With X-Tenant-Id header", True, 
                         f"Retrieved {len(response['items'])} orders")
        else:
            self.log_test("Orders List Regression: With X-Tenant-Id header", False, 
                         f"Failed to get orders: {status}")
        
        # Test 2: Orders list without tenant header (should fail)
        success, response, status = await self.make_request("GET", "/orders?limit=5", headers={})
        
        if not success and status in [400, 401, 403]:
            self.log_test("Orders List Regression: Without X-Tenant-Id header", True, 
                         f"Correctly rejected request without tenant header (status: {status})")
        else:
            self.log_test("Orders List Regression: Without X-Tenant-Id header", False, 
                         f"Should require X-Tenant-Id header (got status: {status}, success: {success})")
        
        # Test 3: Orders list with wrong tenant header
        wrong_headers = {"Content-Type": "application/json", "X-Tenant-Id": "wrong-tenant"}
        success, response, status = await self.make_request("GET", "/orders?limit=5", headers=wrong_headers)
        
        if not success or not response.get("items"):
            self.log_test("Orders List Regression: With wrong tenant ID", True, 
                         "Correctly isolated data by tenant")
        else:
            self.log_test("Orders List Regression: With wrong tenant ID", False, 
                         "Should isolate data by tenant")
    
    async def test_tenant_isolation(self):
        """Test tenant isolation for order lookup"""
        print("\n🔒 Testing Tenant Isolation...")
        
        if not self.test_orders:
            self.log_test("Tenant Isolation: No test orders available", False)
            return
        
        test_order = self.test_orders[0]
        order_id = test_order.get("id") or test_order.get("order_number")
        
        if not order_id:
            self.log_test("Tenant Isolation: No valid order ID found", False)
            return
        
        # Test 1: Access with correct tenant
        success, response, status = await self.make_request("GET", f"/orders/{order_id}")
        
        if success:
            self.log_test("Tenant Isolation: Correct tenant access", True, 
                         "Successfully accessed order with correct tenant")
        else:
            self.log_test("Tenant Isolation: Correct tenant access", False, 
                         f"Failed to access order with correct tenant: {status}")
        
        # Test 2: Access with wrong tenant
        wrong_headers = {"Content-Type": "application/json", "X-Tenant-Id": "wrong-tenant"}
        success, response, status = await self.make_request("GET", f"/orders/{order_id}", headers=wrong_headers)
        
        if not success and status == 404:
            self.log_test("Tenant Isolation: Wrong tenant access", True, 
                         "Correctly blocked access with wrong tenant (404)")
        else:
            self.log_test("Tenant Isolation: Wrong tenant access", False, 
                         f"Should block access with wrong tenant, got {status}")
        
        # Test 3: Access without tenant header
        success, response, status = await self.make_request("GET", f"/orders/{order_id}", headers={})
        
        if not success and status in [400, 401, 403]:
            self.log_test("Tenant Isolation: No tenant header", True, 
                         f"Correctly rejected request without tenant header (status: {status})")
        else:
            self.log_test("Tenant Isolation: No tenant header", False, 
                         f"Should require tenant header (got status: {status}, success: {success})")
    
    async def run_all_tests(self):
        """Run all order lookup tests"""
        print("🚀 Starting Order Lookup Testing for tenant-rms34")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_data():
            print("❌ Failed to setup test data. Continuing with available tests...")
        
        # Run all test suites
        await self.test_order_lookup_with_sample_id()
        await self.test_order_lookup_fallbacks()
        await self.test_invalid_order_ids()
        await self.test_response_structure_validation()
        await self.test_orders_list_regression()
        await self.test_tenant_isolation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ORDER LOOKUP TESTING SUMMARY")
        print("=" * 60)
        
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
        
        # Analyze results by category
        categories = {
            "Order Lookup": [r for r in self.test_results if "Order Lookup:" in r["test"]],
            "Response Structure": [r for r in self.test_results if "Response Structure:" in r["test"]],
            "Orders List Regression": [r for r in self.test_results if "Orders List Regression:" in r["test"]],
            "Tenant Isolation": [r for r in self.test_results if "Tenant Isolation:" in r["test"]],
            "Invalid Order ID": [r for r in self.test_results if "Invalid Order ID:" in r["test"]],
            "Setup": [r for r in self.test_results if "Setup:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")

async def main():
    """Main test execution"""
    async with OrderLookupTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())