#!/usr/bin/env python3
"""
Elite Portal Returns Create API Debug Test
Specifically tests the /api/elite/portal/returns/create endpoint with real data
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://35d12e52-b5b0-4c0d-8c1f-a01716e1ddd2.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ElitePortalDebugTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        
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
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
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
            
            print(f"\n🔍 Making {method} request to: {url}")
            if data:
                print(f"📤 Request data: {json.dumps(data, indent=2)}")
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    response_data = await response.json()
                    print(f"📥 Response status: {response.status}")
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    response_data = await response.json()
                    print(f"📥 Response status: {response.status}")
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            return False, {"error": str(e)}, 500
    
    async def test_backend_health(self):
        """Test backend health and connectivity"""
        print("\n🏥 Testing Backend Health...")
        
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if success:
            self.log_test("Backend Health Check", True, "Backend is accessible and healthy")
        else:
            self.log_test("Backend Health Check", False, f"Backend not accessible: {status}")
            return False
        return True
    
    async def test_tenant_setup(self):
        """Test tenant-rms34 setup and configuration"""
        print("\n🏢 Testing Tenant Setup...")
        
        # Check if tenant exists
        success, tenants_data, status = await self.make_request("GET", "/tenants")
        if success and isinstance(tenants_data, list):
            tenant_rms34 = next((t for t in tenants_data if t.get("id") == TEST_TENANT_ID), None)
            if tenant_rms34:
                self.log_test("Tenant RMS34 Exists", True, f"Found tenant: {tenant_rms34.get('name', 'Unknown')}")
            else:
                self.log_test("Tenant RMS34 Exists", False, f"Tenant {TEST_TENANT_ID} not found in {len(tenants_data)} tenants")
        else:
            self.log_test("Tenant RMS34 Exists", False, f"Failed to retrieve tenants: {status}")
    
    async def test_order_1001_lookup(self):
        """Test if Order #1001 exists and has TESTORDER item"""
        print("\n🔍 Testing Order #1001 Lookup...")
        
        # Try to find Order #1001 in the orders
        success, orders_data, status = await self.make_request("GET", "/orders?limit=50")
        
        if success and orders_data.get("items"):
            order_1001 = None
            for order in orders_data["items"]:
                if order.get("order_number") == "1001" or order.get("name") == "#1001":
                    order_1001 = order
                    break
            
            if order_1001:
                self.log_test("Order #1001 Found", True, f"Order found with customer: {order_1001.get('customer_email', 'Unknown')}")
                
                # Check for TESTORDER item
                line_items = order_1001.get("line_items", [])
                testorder_item = None
                for item in line_items:
                    if "TESTORDER" in item.get("title", "").upper() or "TESTORDER" in item.get("name", "").upper():
                        testorder_item = item
                        break
                
                if testorder_item:
                    self.log_test("TESTORDER Item Found", True, f"Found item: {testorder_item.get('title', 'Unknown')}")
                    return order_1001, testorder_item
                else:
                    self.log_test("TESTORDER Item Found", False, f"TESTORDER item not found in {len(line_items)} line items")
                    print(f"   Available items: {[item.get('title', 'Unknown') for item in line_items]}")
                    return order_1001, None
            else:
                self.log_test("Order #1001 Found", False, f"Order #1001 not found in {len(orders_data['items'])} orders")
                # Show available orders
                order_numbers = [order.get("order_number", order.get("name", "Unknown")) for order in orders_data["items"][:10]]
                print(f"   Available orders: {order_numbers}")
                return None, None
        else:
            self.log_test("Order #1001 Found", False, f"Failed to retrieve orders: {status}")
            return None, None
    
    async def test_elite_portal_health(self):
        """Test Elite Portal Returns API health"""
        print("\n🎯 Testing Elite Portal Returns API Health...")
        
        success, health_data, status = await self.make_request("GET", "/elite/portal/returns/health")
        if success:
            self.log_test("Elite Portal API Health", True, "Elite Portal Returns API is healthy")
            return True
        else:
            self.log_test("Elite Portal API Health", False, f"Elite Portal API not accessible: {status}")
            return False
    
    async def test_order_lookup_api(self, order_number: str, customer_email: str):
        """Test the order lookup API"""
        print(f"\n🔎 Testing Order Lookup API for Order #{order_number}...")
        
        lookup_data = {
            "order_number": order_number,
            "customer_email": customer_email
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/lookup-order", lookup_data)
        
        if success:
            self.log_test("Elite Portal Order Lookup", True, f"Mode: {response.get('mode', 'unknown')}")
            return response
        else:
            self.log_test("Elite Portal Order Lookup", False, f"Status: {status}")
            return None
    
    async def test_create_return_api(self, order_data: Dict, testorder_item: Dict):
        """Test the Elite Portal Returns Create API with real data"""
        print("\n🚀 Testing Elite Portal Returns Create API...")
        
        # Prepare the request data based on the sample structure provided
        create_return_data = {
            "order_id": order_data.get("order_id", order_data.get("id")),
            "customer_email": order_data.get("customer_email", order_data.get("email")),
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": testorder_item.get("id", "gid://shopify/LineItem/13851721105593"),
                "sku": testorder_item.get("sku", "N/A"),
                "title": testorder_item.get("title", testorder_item.get("name", "TESTORDER")),
                "variant_title": testorder_item.get("variant_title"),
                "quantity": 1,
                "unit_price": float(testorder_item.get("price", 400)),
                "reason": "wrong_size",
                "condition": "used",
                "photos": [],
                "notes": ""
            }],
            "customer_note": "Selected resolution: refund"
        }
        
        print(f"📤 Testing with data structure:")
        print(json.dumps(create_return_data, indent=2))
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", create_return_data)
        
        if success:
            self.log_test("Elite Portal Returns Create", True, "Return creation successful")
            return response
        else:
            self.log_test("Elite Portal Returns Create", False, f"Status: {status}")
            
            # Analyze the error
            if status == 422:
                print("🔍 Validation Error Analysis:")
                if "detail" in response:
                    if isinstance(response["detail"], list):
                        for error in response["detail"]:
                            print(f"   • Field: {error.get('loc', 'unknown')}, Error: {error.get('msg', 'unknown')}")
                    else:
                        print(f"   • Error: {response['detail']}")
            elif status == 500:
                print("🔍 Server Error Analysis:")
                print(f"   • This indicates an implementation issue in the API")
                print(f"   • Error: {response.get('detail', 'Unknown server error')}")
            
            return None
    
    async def test_alternative_data_structures(self, order_data: Dict):
        """Test with alternative data structures to identify the issue"""
        print("\n🧪 Testing Alternative Data Structures...")
        
        # Test 1: Minimal required fields only
        minimal_data = {
            "order_id": order_data.get("order_id", order_data.get("id")),
            "customer_email": order_data.get("customer_email", order_data.get("email")),
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "new"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", minimal_data)
        
        if success:
            self.log_test("Minimal Data Structure", True, "Minimal data structure works")
        else:
            self.log_test("Minimal Data Structure", False, f"Status: {status}")
        
        # Test 2: Check required field validation
        incomplete_data = {
            "customer_email": order_data.get("customer_email", order_data.get("email")),
            "return_method": "prepaid_label",
            "items": []
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", incomplete_data)
        
        if not success and status == 422:
            self.log_test("Required Field Validation", True, "API correctly validates required fields")
        else:
            self.log_test("Required Field Validation", False, "API should validate required fields")
    
    async def test_dependency_container(self):
        """Test if the dependency container is properly initialized"""
        print("\n🔧 Testing Dependency Container...")
        
        # Try to access any Elite Portal endpoint to see if dependency injection works
        success, response, status = await self.make_request("GET", "/elite/portal/returns/health")
        
        if success:
            self.log_test("Dependency Container", True, "Dependency injection working")
        else:
            self.log_test("Dependency Container", False, f"Dependency injection issues: {status}")
    
    async def run_debug_tests(self):
        """Run all debug tests for Elite Portal Returns Create API"""
        print("🚀 Starting Elite Portal Returns Create API Debug Test")
        print("=" * 70)
        
        # Step 1: Basic connectivity
        if not await self.test_backend_health():
            print("❌ Backend not accessible. Stopping tests.")
            return
        
        # Step 2: Tenant setup
        await self.test_tenant_setup()
        
        # Step 3: Elite Portal API health
        if not await self.test_elite_portal_health():
            print("⚠️ Elite Portal API not accessible. Continuing with other tests...")
        
        # Step 4: Dependency container test
        await self.test_dependency_container()
        
        # Step 5: Find Order #1001 and TESTORDER item
        order_data, testorder_item = await self.test_order_1001_lookup()
        
        if order_data:
            # Step 6: Test order lookup API
            customer_email = order_data.get("customer_email", order_data.get("email"))
            order_number = order_data.get("order_number", order_data.get("name", "1001"))
            
            if customer_email:
                lookup_result = await self.test_order_lookup_api(order_number, customer_email)
            
            # Step 7: Test create return API
            if testorder_item:
                await self.test_create_return_api(order_data, testorder_item)
            else:
                # Use first available item if TESTORDER not found
                line_items = order_data.get("line_items", [])
                if line_items:
                    print("⚠️ Using first available item instead of TESTORDER")
                    await self.test_create_return_api(order_data, line_items[0])
            
            # Step 8: Test alternative data structures
            await self.test_alternative_data_structures(order_data)
        else:
            print("⚠️ No suitable order found for testing. Testing with mock data...")
            
            # Create mock order data for testing
            mock_order = {
                "id": "mock-order-id",
                "order_id": "mock-order-id",
                "customer_email": "test@example.com",
                "order_number": "MOCK001"
            }
            
            mock_item = {
                "id": "mock-item-id",
                "title": "Mock Test Item",
                "sku": "MOCK-SKU",
                "price": "50.00"
            }
            
            await self.test_create_return_api(mock_order, mock_item)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 ELITE PORTAL RETURNS CREATE API DEBUG SUMMARY")
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
        
        # Check for specific issues
        create_test = next((r for r in self.test_results if "Elite Portal Returns Create" in r["test"]), None)
        if create_test and not create_test["success"]:
            print("   ❌ Elite Portal Returns Create API is failing")
            print("   🔍 Root Cause Analysis needed:")
            print("     - Check dependency container initialization")
            print("     - Verify CQRS handlers are properly registered")
            print("     - Check data validation and field mapping")
            print("     - Verify tenant-rms34 configuration")
        else:
            print("   ✅ Elite Portal Returns Create API is working")
        
        health_test = next((r for r in self.test_results if "Elite Portal API Health" in r["test"]), None)
        if health_test and not health_test["success"]:
            print("   ⚠️ Elite Portal API endpoints may not be properly registered")
        
        order_test = next((r for r in self.test_results if "Order #1001 Found" in r["test"]), None)
        if order_test and not order_test["success"]:
            print("   ⚠️ Order #1001 not found - using alternative test data")

async def main():
    """Main test execution"""
    async with ElitePortalDebugTest() as test_suite:
        await test_suite.run_debug_tests()

if __name__ == "__main__":
    asyncio.run(main())