#!/usr/bin/env python3
"""
Focused Unified Returns Testing - Quick verification of unified returns endpoints
Tests the specific functionality requested in the review
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://f4ede537-31b1-4ba8-b14e-a9ada50dbb28.preview.emergentagent.com"
TEST_TENANT_ID = "tenant-fashion-store"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class FocusedUnifiedReturnsTest:
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
    
    async def test_1_quick_health_check(self):
        """Test 1: Quick Health Check"""
        print("\n🏥 Test 1: Quick Health Check")
        
        # Test backend health
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if success:
            self.log_test("Health Check: Backend responsive", True, f"Backend is healthy")
        else:
            self.log_test("Health Check: Backend responsive", False, f"Backend not accessible: {status}")
            return False
        
        # Test unified returns endpoints availability
        endpoints_to_test = [
            ("/api/unified-returns/order/lookup", "POST", {"order_number": "test", "email": "test@example.com"}),
            ("/api/unified-returns/order/123/eligible-items", "GET", None),
            ("/api/unified-returns/policy-preview", "POST", {"items": [], "order_id": "test"}),
            ("/api/unified-returns/create", "POST", {"order_number": "test", "email": "test@example.com", "items": [], "preferred_outcome": "refund_original", "return_method": "prepaid_label", "channel": "portal"}),
            ("/api/unified-returns/upload-photos", "POST", None)
        ]
        
        available_endpoints = 0
        for endpoint, method, test_data in endpoints_to_test:
            success, response, status = await self.make_request(method, endpoint, test_data)
            endpoint_name = endpoint.split("/")[-1]
            
            if status == 404:
                self.log_test(f"Endpoint Availability: {endpoint_name}", False, "Endpoint not found")
            else:
                self.log_test(f"Endpoint Availability: {endpoint_name}", True, f"Endpoint available (status: {status})")
                available_endpoints += 1
        
        return available_endpoints == len(endpoints_to_test)
    
    async def test_2_order_lookup_flow(self):
        """Test 2: Order Lookup Flow with seeded data"""
        print("\n🔍 Test 2: Order Lookup Flow")
        
        # First get some orders from seeded data
        success, orders_data, status = await self.make_request("GET", "/api/orders?limit=5")
        
        if not success or not orders_data.get("items"):
            self.log_test("Order Lookup: Get seeded orders", False, f"No orders found. Status: {status}")
            return False
        
        self.test_order = orders_data["items"][0]
        self.log_test("Order Lookup: Get seeded orders", True, f"Found {len(orders_data['items'])} orders")
        
        # Test order lookup endpoint with real data
        lookup_data = {
            "order_number": self.test_order["order_number"],
            "email": self.test_order["customer_email"]
        }
        
        success, response, status = await self.make_request("POST", "/api/unified-returns/order/lookup", lookup_data)
        
        if success and response.get("success"):
            self.log_test("Order Lookup: Customer portal lookup", True, f"Successfully looked up order {self.test_order['order_number']}")
            
            # Verify response structure
            required_fields = ["order_id", "order_number", "customer_name", "eligible_items", "policy_preview"]
            if all(field in response for field in required_fields):
                self.log_test("Order Lookup: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Order Lookup: Response structure", False, f"Missing fields: {missing}")
            
            return True
        else:
            self.log_test("Order Lookup: Customer portal lookup", False, f"Status: {status}, Response: {response}")
            return False
    
    async def test_3_eligible_items_endpoint(self):
        """Test 3: Get eligible items for order"""
        print("\n📦 Test 3: Eligible Items Endpoint")
        
        if not self.test_order:
            self.log_test("Eligible Items: No test order", False, "Need order from previous test")
            return False
        
        order_id = self.test_order["id"]
        success, response, status = await self.make_request("GET", f"/api/unified-returns/order/{order_id}/eligible-items")
        
        if success and isinstance(response, list):
            self.log_test("Eligible Items: Get items for order", True, f"Retrieved {len(response)} eligible items")
            
            # Check item structure if items exist
            if response:
                item = response[0]
                required_fields = ["fulfillment_line_item_id", "title", "quantity_eligible", "price"]
                if all(field in item for field in required_fields):
                    self.log_test("Eligible Items: Item structure", True, "Item structure is correct")
                else:
                    missing = [f for f in required_fields if f not in item]
                    self.log_test("Eligible Items: Item structure", False, f"Missing fields: {missing}")
            
            return True
        else:
            self.log_test("Eligible Items: Get items for order", False, f"Status: {status}, Response: {response}")
            return False
    
    async def test_4_policy_preview(self):
        """Test 4: Policy Preview"""
        print("\n📋 Test 4: Policy Preview")
        
        if not self.test_order:
            self.log_test("Policy Preview: No test order", False, "Need order from previous test")
            return False
        
        # Get eligible items first
        order_id = self.test_order["id"]
        success, eligible_items, status = await self.make_request("GET", f"/api/unified-returns/order/{order_id}/eligible-items")
        
        if not success or not eligible_items:
            self.log_test("Policy Preview: Get eligible items", False, "Cannot get eligible items for preview")
            return False
        
        # Test policy preview with first eligible item
        preview_data = {
            "items": [
                {
                    "fulfillment_line_item_id": eligible_items[0]["fulfillment_line_item_id"],
                    "quantity": 1,
                    "reason": "damaged_defective",
                    "reason_note": "Item arrived damaged"
                }
            ],
            "order_id": order_id
        }
        
        success, response, status = await self.make_request("POST", "/api/unified-returns/policy-preview", preview_data)
        
        if success and "estimated_refund" in response:
            self.log_test("Policy Preview: Calculate preview", True, f"Estimated refund: ${response['estimated_refund']:.2f}")
            
            # Check response structure
            required_fields = ["estimated_refund", "fees", "auto_approve_eligible", "total_items"]
            if all(field in response for field in required_fields):
                self.log_test("Policy Preview: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Policy Preview: Response structure", False, f"Missing fields: {missing}")
            
            return True
        else:
            self.log_test("Policy Preview: Calculate preview", False, f"Status: {status}, Response: {response}")
            return False
    
    async def test_5_create_return_customer(self):
        """Test 5: Create Return - Customer Portal"""
        print("\n🛒 Test 5: Create Return - Customer Portal")
        
        if not self.test_order:
            self.log_test("Create Return (Customer): No test order", False, "Need order from previous test")
            return False
        
        # Get eligible items
        order_id = self.test_order["id"]
        success, eligible_items, status = await self.make_request("GET", f"/api/unified-returns/order/{order_id}/eligible-items")
        
        if not success or not eligible_items:
            self.log_test("Create Return (Customer): Get eligible items", False, "Cannot get eligible items")
            return False
        
        # Create return request
        return_data = {
            "order_number": self.test_order["order_number"],
            "email": self.test_order["customer_email"],
            "items": [
                {
                    "fulfillment_line_item_id": eligible_items[0]["fulfillment_line_item_id"],
                    "quantity": 1,
                    "reason": "damaged_defective",
                    "reason_note": "Item arrived damaged during shipping",
                    "photo_urls": []
                }
            ],
            "preferred_outcome": "refund_original",
            "return_method": "prepaid_label",
            "customer_note": "Please process refund to original payment method",
            "channel": "portal"
        }
        
        success, response, status = await self.make_request("POST", "/api/unified-returns/create", return_data)
        
        if success and response.get("success"):
            self.log_test("Create Return (Customer): Valid request", True, f"Created return {response['return_id']} with status {response['status']}")
            
            # Check response structure
            required_fields = ["return_id", "status", "decision", "estimated_refund"]
            if all(field in response for field in required_fields):
                self.log_test("Create Return (Customer): Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Create Return (Customer): Response structure", False, f"Missing fields: {missing}")
            
            return True
        else:
            self.log_test("Create Return (Customer): Valid request", False, f"Status: {status}, Response: {response}")
            return False
    
    async def test_6_create_return_admin(self):
        """Test 6: Create Return - Admin Portal"""
        print("\n👨‍💼 Test 6: Create Return - Admin Portal")
        
        if not self.test_order:
            self.log_test("Create Return (Admin): No test order", False, "Need order from previous test")
            return False
        
        # Get eligible items
        order_id = self.test_order["id"]
        success, eligible_items, status = await self.make_request("GET", f"/api/unified-returns/order/{order_id}/eligible-items")
        
        if not success or not eligible_items:
            self.log_test("Create Return (Admin): Get eligible items", False, "Cannot get eligible items")
            return False
        
        # Create admin return request with override
        admin_return_data = {
            "order_id": order_id,
            "items": [
                {
                    "fulfillment_line_item_id": eligible_items[0]["fulfillment_line_item_id"],
                    "quantity": 1,
                    "reason": "wrong_size",
                    "reason_note": "Customer ordered wrong size",
                    "photo_urls": []
                }
            ],
            "preferred_outcome": "exchange",
            "return_method": "prepaid_label",
            "customer_note": "Exchange for larger size",
            "channel": "admin",
            "admin_override_approve": True,
            "admin_override_note": "Approved by customer service manager",
            "internal_tags": ["priority", "vip_customer"]
        }
        
        success, response, status = await self.make_request("POST", "/api/unified-returns/create", admin_return_data)
        
        if success and response.get("success"):
            self.log_test("Create Return (Admin): Valid request with override", True, f"Created admin return {response['return_id']} with status {response['status']}")
            
            # Check if admin override was applied
            if response["status"] == "approved":
                self.log_test("Create Return (Admin): Admin override applied", True, "Return auto-approved via admin override")
            else:
                self.log_test("Create Return (Admin): Admin override applied", False, "Admin override not applied correctly")
            
            return True
        else:
            self.log_test("Create Return (Admin): Valid request with override", False, f"Status: {status}, Response: {response}")
            return False
    
    async def test_7_integration_verification(self):
        """Test 7: Integration Verification"""
        print("\n🔗 Test 7: Integration Verification")
        
        # Test ShopifyService integration (order data retrieval)
        success, orders_data, status = await self.make_request("GET", "/api/orders?limit=1")
        
        if success and orders_data.get("items"):
            self.log_test("Integration: ShopifyService order data", True, "Successfully retrieved order data from ShopifyService")
        else:
            self.log_test("Integration: ShopifyService order data", False, "Failed to retrieve order data")
        
        # Test tenant isolation
        wrong_tenant_headers = {**TEST_HEADERS, "X-Tenant-Id": "wrong-tenant-id"}
        success, response, status = await self.make_request("GET", "/api/orders", headers=wrong_tenant_headers)
        
        if not success or not response.get("items"):
            self.log_test("Integration: Tenant isolation", True, "Correctly isolated data by tenant")
        else:
            self.log_test("Integration: Tenant isolation", False, "Tenant isolation not working properly")
        
        # Test database persistence (check if returns are being saved)
        success, returns_data, status = await self.make_request("GET", "/api/returns?limit=1")
        
        if success and returns_data.get("items"):
            self.log_test("Integration: Database persistence", True, "Returns are being saved to database")
        else:
            self.log_test("Integration: Database persistence", False, "Returns not being saved properly")
        
        return True
    
    async def run_focused_tests(self):
        """Run focused unified returns tests"""
        print("🚀 Starting Focused Unified Returns Testing")
        print("=" * 60)
        
        # Run tests in sequence
        test_1_passed = await self.test_1_quick_health_check()
        test_2_passed = await self.test_2_order_lookup_flow()
        test_3_passed = await self.test_3_eligible_items_endpoint()
        test_4_passed = await self.test_4_policy_preview()
        test_5_passed = await self.test_5_create_return_customer()
        test_6_passed = await self.test_6_create_return_admin()
        test_7_passed = await self.test_7_integration_verification()
        
        # Summary
        self.print_summary()
        
        return {
            "health_check": test_1_passed,
            "order_lookup": test_2_passed,
            "eligible_items": test_3_passed,
            "policy_preview": test_4_passed,
            "create_return_customer": test_5_passed,
            "create_return_admin": test_6_passed,
            "integration": test_7_passed
        }
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED UNIFIED RETURNS TESTING SUMMARY")
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
        
        # Analyze results by test category
        categories = {
            "Health Check": [r for r in self.test_results if "Health Check:" in r["test"]],
            "Endpoint Availability": [r for r in self.test_results if "Endpoint Availability:" in r["test"]],
            "Order Lookup": [r for r in self.test_results if "Order Lookup:" in r["test"]],
            "Eligible Items": [r for r in self.test_results if "Eligible Items:" in r["test"]],
            "Policy Preview": [r for r in self.test_results if "Policy Preview:" in r["test"]],
            "Create Return (Customer)": [r for r in self.test_results if "Create Return (Customer):" in r["test"]],
            "Create Return (Admin)": [r for r in self.test_results if "Create Return (Admin):" in r["test"]],
            "Integration": [r for r in self.test_results if "Integration:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")

async def main():
    """Main test execution"""
    async with FocusedUnifiedReturnsTest() as test_suite:
        results = await test_suite.run_focused_tests()
        return results

if __name__ == "__main__":
    results = asyncio.run(main())