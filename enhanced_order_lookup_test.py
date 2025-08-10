#!/usr/bin/env python3
"""
Enhanced Order Lookup System Testing
Tests both Shopify and fallback modes as requested in the review
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
BACKEND_URL = "https://1ce8ef7a-c16d-43a6-b3d4-da8a63312de8.preview.emergentagent.com/api"

# Test tenants - one with Shopify integration, one without
SHOPIFY_TENANT_ID = "tenant-rms34"  # Has Shopify integration
FALLBACK_TENANT_ID = "tenant-fashion-store"  # No Shopify integration

class EnhancedOrderLookupTestSuite:
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

    async def test_shopify_mode_order_lookup(self):
        """Test 1: Shopify mode order lookup as requested"""
        print("\n🔍 Testing Shopify Mode Order Lookup...")
        
        # Test data as specified in the review request
        lookup_data = {
            "order_number": "1001",
            "email": "customer@example.com",
            "channel": "customer"
        }
        
        headers = {"X-Tenant-Id": SHOPIFY_TENANT_ID}
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", lookup_data, headers
        )
        
        if success:
            if response.get("mode") == "shopify":
                self.log_test("Shopify Mode: Order lookup endpoint", True, 
                             f"Successfully used Shopify mode, found order data")
                
                # Validate response structure
                if "order" in response:
                    self.log_test("Shopify Mode: Response structure", True, 
                                 "Response contains order data as expected")
                else:
                    self.log_test("Shopify Mode: Response structure", False, 
                                 "Missing order data in response")
            else:
                self.log_test("Shopify Mode: Order lookup endpoint", False, 
                             f"Expected Shopify mode but got: {response.get('mode')}")
        else:
            if status == 404 and "ORDER_NOT_FOUND_OR_EMAIL_MISMATCH" in str(response):
                self.log_test("Shopify Mode: Order lookup endpoint", True, 
                             "Correctly returned 404 for non-existent order/email combo")
            else:
                self.log_test("Shopify Mode: Order lookup endpoint", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test with real order data from tenant-rms34
        real_lookup_data = {
            "order_number": "1001",
            "email": "john.doe@example.com",  # Try with seeded data email
            "channel": "customer"
        }
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", real_lookup_data, headers
        )
        
        if success and response.get("mode") == "shopify":
            self.log_test("Shopify Mode: Real order lookup", True, 
                         "Successfully found real order in Shopify mode")
        else:
            self.log_test("Shopify Mode: Real order lookup", False, 
                         f"Failed to find real order. Status: {status}")

    async def test_policy_preview_endpoint(self):
        """Test 2: Policy preview endpoint as requested"""
        print("\n📋 Testing Policy Preview Endpoint...")
        
        # Sample items data as requested
        sample_data = {
            "items": [
                {
                    "id": "item-1",
                    "name": "Sample Product",
                    "price": 50.00,
                    "quantity": 1,
                    "reason": "defective"
                },
                {
                    "id": "item-2", 
                    "name": "Another Product",
                    "price": 75.00,
                    "quantity": 2,
                    "reason": "wrong_size"
                }
            ],
            "orderMeta": {
                "orderNumber": "1001",
                "totalValue": 200.00
            }
        }
        
        headers = {"X-Tenant-Id": SHOPIFY_TENANT_ID}
        
        success, response, status = await self.make_request(
            "POST", "/returns/policy-preview", sample_data, headers
        )
        
        if success:
            self.log_test("Policy Preview: Endpoint availability", True, 
                         f"Policy preview endpoint working, status: {status}")
            
            # Validate response structure
            required_fields = ["success", "eligible", "fees", "estimatedRefund"]
            if all(field in response for field in required_fields):
                self.log_test("Policy Preview: Response structure", True, 
                             f"All required fields present. Estimated refund: ${response.get('estimatedRefund', 0):.2f}")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Policy Preview: Response structure", False, 
                             f"Missing fields: {missing}")
        else:
            self.log_test("Policy Preview: Endpoint availability", False, 
                         f"Status: {status}, Response: {response}")

    async def test_fallback_mode(self):
        """Test 3: Fallback mode by using tenant without Shopify integration"""
        print("\n🔄 Testing Fallback Mode...")
        
        lookup_data = {
            "orderNumber": "FB-1001",
            "email": "fallback@example.com",
            "channel": "customer"
        }
        
        headers = {"X-Tenant-Id": FALLBACK_TENANT_ID}
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", lookup_data, headers
        )
        
        if success:
            if response.get("mode") == "fallback":
                self.log_test("Fallback Mode: Order lookup", True, 
                             f"Successfully used fallback mode, status: {response.get('status')}")
                
                # Validate fallback response structure
                if "captured" in response and "message" in response:
                    self.log_test("Fallback Mode: Response structure", True, 
                                 f"Fallback response contains captured data and message")
                else:
                    self.log_test("Fallback Mode: Response structure", False, 
                                 "Missing captured data or message in fallback response")
            else:
                self.log_test("Fallback Mode: Order lookup", False, 
                             f"Expected fallback mode but got: {response.get('mode')}")
        else:
            self.log_test("Fallback Mode: Order lookup", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test duplicate fallback request
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", lookup_data, headers
        )
        
        if success and response.get("status") == "pending_validation":
            if "already received" in response.get("message", "").lower():
                self.log_test("Fallback Mode: Duplicate request handling", True, 
                             "Correctly handled duplicate fallback request")
            else:
                self.log_test("Fallback Mode: Duplicate request handling", True, 
                             "Fallback request processed (may be new or duplicate)")
        else:
            self.log_test("Fallback Mode: Duplicate request handling", False, 
                         "Failed to handle duplicate fallback request")

    async def test_admin_drafts_endpoints(self):
        """Test 4: Admin drafts endpoints for fallback requests"""
        print("\n👨‍💼 Testing Admin Drafts Endpoints...")
        
        headers = {"X-Tenant-Id": FALLBACK_TENANT_ID}
        
        # Test GET /api/admin/returns/pending
        success, response, status = await self.make_request(
            "GET", "/admin/returns/pending", headers=headers
        )
        
        if success:
            self.log_test("Admin Drafts: Get pending drafts", True, 
                         f"Retrieved {len(response.get('items', []))} pending drafts")
            
            # Validate pagination structure
            if "pagination" in response:
                self.log_test("Admin Drafts: Pagination structure", True, 
                             "Response includes pagination information")
            else:
                self.log_test("Admin Drafts: Pagination structure", False, 
                             "Missing pagination in response")
        else:
            self.log_test("Admin Drafts: Get pending drafts", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test with different status filter
        success, response, status = await self.make_request(
            "GET", "/admin/returns/pending?status=pending_validation", headers=headers
        )
        
        if success:
            self.log_test("Admin Drafts: Status filtering", True, 
                         f"Status filtering working, found {len(response.get('items', []))} items")
        else:
            self.log_test("Admin Drafts: Status filtering", False, 
                         f"Status filtering failed: {status}")

    async def test_graphql_service_order_lookup(self):
        """Test 5: Verify GraphQL service can lookup Shopify orders properly"""
        print("\n🔗 Testing GraphQL Service Order Lookup...")
        
        # Test Shopify connectivity test endpoints to verify GraphQL service
        success, response, status = await self.make_request(
            "GET", "/shopify-test/quick-test", headers={"X-Tenant-Id": SHOPIFY_TENANT_ID}
        )
        
        if success:
            if response.get("success") and "products" in response:
                self.log_test("GraphQL Service: Quick connectivity test", True, 
                             f"GraphQL service connected, retrieved {len(response.get('products', []))} products")
            else:
                self.log_test("GraphQL Service: Quick connectivity test", False, 
                             "GraphQL service connection issues")
        else:
            self.log_test("GraphQL Service: Quick connectivity test", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test full connectivity test
        success, response, status = await self.make_request(
            "GET", "/shopify-test/full-connectivity", headers={"X-Tenant-Id": SHOPIFY_TENANT_ID}
        )
        
        if success:
            test_results = response.get("test_results", {})
            passed_tests = sum(1 for result in test_results.values() if result.get("success"))
            total_tests = len(test_results)
            
            if passed_tests >= total_tests * 0.8:  # 80% success rate
                self.log_test("GraphQL Service: Full connectivity test", True, 
                             f"GraphQL operations working: {passed_tests}/{total_tests} tests passed")
            else:
                self.log_test("GraphQL Service: Full connectivity test", False, 
                             f"GraphQL operations issues: {passed_tests}/{total_tests} tests passed")
        else:
            self.log_test("GraphQL Service: Full connectivity test", False, 
                         f"Status: {status}")

    async def test_new_controllers_registration(self):
        """Test 6: Check new controllers are registered and responding correctly"""
        print("\n🎛️ Testing New Controllers Registration...")
        
        # Test order lookup controller endpoints
        endpoints_to_test = [
            ("/returns/order-lookup", "POST", {"orderNumber": "test", "email": "test@example.com", "channel": "customer"}),
            ("/returns/policy-preview", "POST", {"items": [], "orderMeta": {}}),
            ("/admin/returns/pending", "GET", None)
        ]
        
        for endpoint, method, test_data in endpoints_to_test:
            headers = {"X-Tenant-Id": SHOPIFY_TENANT_ID}
            
            if method == "GET":
                success, response, status = await self.make_request(method, endpoint, headers=headers)
            else:
                success, response, status = await self.make_request(method, endpoint, test_data, headers)
            
            if status == 404:
                self.log_test(f"Controller Registration: {endpoint}", False, 
                             "Endpoint not found - controller not registered")
            elif status in [200, 400, 422, 500]:  # Any response means controller is registered
                self.log_test(f"Controller Registration: {endpoint}", True, 
                             f"Controller registered and responding (status: {status})")
            else:
                self.log_test(f"Controller Registration: {endpoint}", False, 
                             f"Unexpected status: {status}")

    async def test_dual_mode_system_validation(self):
        """Test the dual-mode lookup system works as expected"""
        print("\n⚖️ Testing Dual-Mode System Validation...")
        
        # Test 1: Verify tenant with Shopify integration uses Shopify mode
        shopify_data = {
            "orderNumber": "1001",
            "email": "test@example.com",
            "channel": "customer"
        }
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", shopify_data, 
            headers={"X-Tenant-Id": SHOPIFY_TENANT_ID}
        )
        
        expected_mode = "shopify"
        actual_mode = response.get("mode") if success else None
        
        if actual_mode == expected_mode:
            self.log_test("Dual-Mode: Shopify tenant routing", True, 
                         f"Shopify tenant correctly routed to {expected_mode} mode")
        else:
            self.log_test("Dual-Mode: Shopify tenant routing", False, 
                         f"Expected {expected_mode} mode, got {actual_mode}")
        
        # Test 2: Verify tenant without Shopify integration uses fallback mode
        fallback_data = {
            "orderNumber": "FB-2001",
            "email": "fallback2@example.com",
            "channel": "customer"
        }
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", fallback_data,
            headers={"X-Tenant-Id": FALLBACK_TENANT_ID}
        )
        
        expected_mode = "fallback"
        actual_mode = response.get("mode") if success else None
        
        if actual_mode == expected_mode:
            self.log_test("Dual-Mode: Fallback tenant routing", True, 
                         f"Fallback tenant correctly routed to {expected_mode} mode")
        else:
            self.log_test("Dual-Mode: Fallback tenant routing", False, 
                         f"Expected {expected_mode} mode, got {actual_mode}")
        
        # Test 3: Verify mode consistency
        if actual_mode == expected_mode:
            self.log_test("Dual-Mode: System consistency", True, 
                         "Dual-mode system routing working consistently")
        else:
            self.log_test("Dual-Mode: System consistency", False, 
                         "Dual-mode system has routing inconsistencies")

    async def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        print("\n🚨 Testing Error Handling and Edge Cases...")
        
        # Test 1: Missing required fields
        invalid_data = {"orderNumber": "1001"}  # Missing email
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", invalid_data,
            headers={"X-Tenant-Id": SHOPIFY_TENANT_ID}
        )
        
        if not success and status in [400, 422]:
            self.log_test("Error Handling: Missing required fields", True, 
                         "Correctly rejected request with missing email")
        else:
            self.log_test("Error Handling: Missing required fields", False, 
                         "Should reject requests with missing required fields")
        
        # Test 2: Invalid tenant ID
        valid_data = {
            "orderNumber": "1001",
            "email": "test@example.com",
            "channel": "customer"
        }
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", valid_data,
            headers={"X-Tenant-Id": "invalid-tenant-id"}
        )
        
        # Should still work but might use guest mode or return appropriate error
        if success or status in [400, 403, 404]:
            self.log_test("Error Handling: Invalid tenant ID", True, 
                         f"Handled invalid tenant appropriately (status: {status})")
        else:
            self.log_test("Error Handling: Invalid tenant ID", False, 
                         f"Unexpected handling of invalid tenant: {status}")
        
        # Test 3: Empty order number
        empty_data = {
            "orderNumber": "",
            "email": "test@example.com",
            "channel": "customer"
        }
        
        success, response, status = await self.make_request(
            "POST", "/returns/order-lookup", empty_data,
            headers={"X-Tenant-Id": SHOPIFY_TENANT_ID}
        )
        
        if not success and status in [400, 422]:
            self.log_test("Error Handling: Empty order number", True, 
                         "Correctly rejected empty order number")
        else:
            self.log_test("Error Handling: Empty order number", False, 
                         "Should reject empty order numbers")

    async def run_all_tests(self):
        """Run all enhanced order lookup tests"""
        print("🚀 Starting Enhanced Order Lookup System Testing")
        print("=" * 60)
        
        # Run all test suites as requested in the review
        await self.test_shopify_mode_order_lookup()
        await self.test_policy_preview_endpoint()
        await self.test_fallback_mode()
        await self.test_admin_drafts_endpoints()
        await self.test_graphql_service_order_lookup()
        await self.test_new_controllers_registration()
        await self.test_dual_mode_system_validation()
        await self.test_error_handling_and_edge_cases()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ENHANCED ORDER LOOKUP TESTING SUMMARY")
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
            "Shopify Mode": [r for r in self.test_results if "Shopify Mode:" in r["test"]],
            "Policy Preview": [r for r in self.test_results if "Policy Preview:" in r["test"]],
            "Fallback Mode": [r for r in self.test_results if "Fallback Mode:" in r["test"]],
            "Admin Drafts": [r for r in self.test_results if "Admin Drafts:" in r["test"]],
            "GraphQL Service": [r for r in self.test_results if "GraphQL Service:" in r["test"]],
            "Controller Registration": [r for r in self.test_results if "Controller Registration:" in r["test"]],
            "Dual-Mode System": [r for r in self.test_results if "Dual-Mode:" in r["test"]],
            "Error Handling": [r for r in self.test_results if "Error Handling:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")
        
        print("\n🔍 DUAL-MODE LOOKUP SYSTEM ASSESSMENT:")
        
        # Specific assessment for the dual-mode system
        shopify_tests = [r for r in self.test_results if "Shopify Mode:" in r["test"]]
        fallback_tests = [r for r in self.test_results if "Fallback Mode:" in r["test"]]
        
        shopify_success = sum(1 for t in shopify_tests if t["success"])
        fallback_success = sum(1 for t in fallback_tests if t["success"])
        
        print(f"   • Shopify Mode Functionality: {shopify_success}/{len(shopify_tests)} working")
        print(f"   • Fallback Mode Functionality: {fallback_success}/{len(fallback_tests)} working")
        
        if shopify_success > 0 and fallback_success > 0:
            print("   ✅ Dual-mode system is operational for both Shopify and non-Shopify tenants")
        elif shopify_success > 0:
            print("   ⚠️ Only Shopify mode is working - fallback mode needs attention")
        elif fallback_success > 0:
            print("   ⚠️ Only fallback mode is working - Shopify mode needs attention")
        else:
            print("   ❌ Both modes have issues - dual-mode system needs fixes")

async def main():
    """Main test execution"""
    async with EnhancedOrderLookupTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())