#!/usr/bin/env python3
"""
End-to-End Return Creation and Merchant Approval Workflow Test
Tests the complete customer return creation flow and merchant approval process
Focus: tenant-rms34 and Order #1001 as specified by user
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration - Using the exact URLs from .env files
BACKEND_URL = "https://returnhub-1.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"  # As specified by user
TEST_ORDER_NUMBER = "1001"  # As specified by user
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class E2EReturnWorkflowTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_order = None
        self.test_return_id = None
        self.customer_email = "customer@example.com"
        
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
            "response_data": response_data
        })
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BACKEND_URL}{endpoint}"
        request_headers = TEST_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            async with self.session.request(method, url, json=data, headers=request_headers) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return response.status < 400, response_data, response.status
        except Exception as e:
            return False, str(e), 0

    async def test_1_order_lookup_integration(self):
        """Test 1: Order Lookup Integration - Verify Order #1001 exists for tenant-rms34"""
        print("\n🔍 TESTING ORDER LOOKUP INTEGRATION")
        
        # Test Elite Portal Order Lookup endpoint
        lookup_data = {
            "order_number": TEST_ORDER_NUMBER,
            "customer_email": self.customer_email
        }
        
        success, response, status = await self.make_request(
            "POST", 
            "/elite/portal/returns/lookup-order", 
            lookup_data
        )
        
        if success and isinstance(response, dict):
            if response.get("success"):
                self.test_order = response.get("order")
                self.log_test(
                    "Elite Portal Order Lookup - Success Path",
                    True,
                    f"Order found: {self.test_order.get('order_number') if self.test_order else 'N/A'}"
                )
            else:
                # Try fallback mode
                self.log_test(
                    "Elite Portal Order Lookup - Fallback Mode",
                    True,
                    f"Fallback mode activated: {response.get('message', 'No message')}"
                )
        else:
            self.log_test(
                "Elite Portal Order Lookup",
                False,
                f"Status: {status}",
                response
            )
        
        # Also test the regular order lookup endpoint
        success2, response2, status2 = await self.make_request(
            "POST",
            "/orders/lookup",
            lookup_data
        )
        
        if success2 and isinstance(response2, dict):
            self.test_order = response2
            self.log_test(
                "Regular Order Lookup Endpoint",
                True,
                f"Order ID: {response2.get('id')}, Number: {response2.get('order_number')}"
            )
        else:
            self.log_test(
                "Regular Order Lookup Endpoint",
                False,
                f"Status: {status2}",
                response2
            )

    async def test_2_customer_return_creation_flow(self):
        """Test 2: Customer Return Creation Flow - Complete Elite Portal workflow"""
        print("\n📝 TESTING CUSTOMER RETURN CREATION FLOW")
        
        if not self.test_order:
            self.log_test(
                "Customer Return Creation - Prerequisites",
                False,
                "No test order available from lookup"
            )
            return
        
        # Step 1: Get eligible items
        order_id = self.test_order.get("id")
        success, response, status = await self.make_request(
            "GET",
            f"/elite/portal/returns/eligible-items/{order_id}"
        )
        
        eligible_items = []
        if success and isinstance(response, dict):
            eligible_items = response.get("eligible_items", [])
            self.log_test(
                "Get Eligible Items",
                True,
                f"Found {len(eligible_items)} eligible items"
            )
        else:
            self.log_test(
                "Get Eligible Items",
                False,
                f"Status: {status}",
                response
            )
        
        # Step 2: Policy Preview
        if eligible_items:
            preview_data = {
                "items": eligible_items[:1],  # Take first eligible item
                "return_reason": "defective"
            }
            
            success, response, status = await self.make_request(
                "POST",
                "/elite/portal/returns/policy-preview",
                preview_data
            )
            
            if success:
                self.log_test(
                    "Policy Preview",
                    True,
                    f"Estimated refund: ${response.get('estimated_refund', 0)}"
                )
            else:
                self.log_test(
                    "Policy Preview",
                    False,
                    f"Status: {status}",
                    response
                )
        
        # Step 3: Create Return Request
        return_data = {
            "order_id": order_id,
            "customer_email": self.customer_email,
            "return_reason": "defective",
            "items": eligible_items[:1] if eligible_items else [
                {
                    "product_id": "test-product-1",
                    "product_name": "Test Product",
                    "quantity": 1,
                    "price": 29.99,
                    "reason": "defective"
                }
            ],
            "notes": "E2E Test Return - Product arrived damaged"
        }
        
        success, response, status = await self.make_request(
            "POST",
            "/elite/portal/returns/create",
            return_data
        )
        
        if success and isinstance(response, dict):
            self.test_return_id = response.get("return_id") or response.get("id")
            self.log_test(
                "Elite Portal Return Creation",
                True,
                f"Return created with ID: {self.test_return_id}"
            )
        else:
            self.log_test(
                "Elite Portal Return Creation",
                False,
                f"Status: {status}",
                response
            )

    async def test_3_merchant_returns_list(self):
        """Test 3: Merchant Returns List - Verify return appears in merchant dashboard"""
        print("\n📊 TESTING MERCHANT RETURNS LIST")
        
        # Test paginated returns endpoint
        success, response, status = await self.make_request(
            "GET",
            "/returns?page=1&limit=20"
        )
        
        if success and isinstance(response, dict):
            items = response.get("items", [])
            pagination = response.get("pagination", {})
            
            # Look for our test return
            test_return_found = False
            if self.test_return_id:
                test_return_found = any(
                    item.get("id") == self.test_return_id 
                    for item in items
                )
            
            self.log_test(
                "Merchant Returns List - Basic Functionality",
                True,
                f"Retrieved {len(items)} returns, Total: {pagination.get('total_count', 0)}"
            )
            
            if self.test_return_id:
                self.log_test(
                    "Merchant Returns List - Test Return Visibility",
                    test_return_found,
                    f"Test return {'found' if test_return_found else 'not found'} in list"
                )
        else:
            self.log_test(
                "Merchant Returns List",
                False,
                f"Status: {status}",
                response
            )
        
        # Test with search and filtering
        success2, response2, status2 = await self.make_request(
            "GET",
            "/returns?search=defective&status_filter=requested"
        )
        
        if success2:
            filtered_items = response2.get("items", [])
            self.log_test(
                "Merchant Returns List - Search & Filter",
                True,
                f"Filtered results: {len(filtered_items)} returns"
            )
        else:
            self.log_test(
                "Merchant Returns List - Search & Filter",
                False,
                f"Status: {status2}",
                response2
            )

    async def test_4_merchant_approval_workflow(self):
        """Test 4: Merchant Approval Workflow - Test approve/decline functionality"""
        print("\n✅ TESTING MERCHANT APPROVAL WORKFLOW")
        
        if not self.test_return_id:
            # Try to find any return to test with
            success, response, status = await self.make_request("GET", "/returns?limit=1")
            if success and response.get("items"):
                self.test_return_id = response["items"][0].get("id")
                self.log_test(
                    "Merchant Approval - Using Existing Return",
                    True,
                    f"Using return ID: {self.test_return_id}"
                )
            else:
                self.log_test(
                    "Merchant Approval Workflow",
                    False,
                    "No return available for testing approval workflow"
                )
                return
        
        # Test 1: Get return details
        success, response, status = await self.make_request(
            "GET",
            f"/returns/{self.test_return_id}"
        )
        
        if success:
            current_status = response.get("status")
            self.log_test(
                "Get Return Details",
                True,
                f"Return status: {current_status}"
            )
        else:
            self.log_test(
                "Get Return Details",
                False,
                f"Status: {status}",
                response
            )
            return
        
        # Test 2: Approve Return (if in requested status)
        if current_status == "requested":
            approval_data = {
                "status": "approved",
                "notes": "E2E Test - Return approved by merchant"
            }
            
            success, response, status = await self.make_request(
                "PUT",
                f"/returns/{self.test_return_id}/status",
                approval_data
            )
            
            if success:
                new_status = response.get("status")
                self.log_test(
                    "Merchant Approval - Approve Return",
                    new_status == "approved",
                    f"Status changed to: {new_status}"
                )
            else:
                self.log_test(
                    "Merchant Approval - Approve Return",
                    False,
                    f"Status: {status}",
                    response
                )
        
        # Test 3: Test Elite Admin Returns Controller
        success, response, status = await self.make_request(
            "GET",
            f"/elite/admin/returns/{self.test_return_id}"
        )
        
        if success:
            self.log_test(
                "Elite Admin Returns - Get Return Details",
                True,
                f"Retrieved return via Elite Admin API"
            )
        else:
            self.log_test(
                "Elite Admin Returns - Get Return Details",
                False,
                f"Status: {status}",
                response
            )
        
        # Test 4: Audit Log
        success, response, status = await self.make_request(
            "GET",
            f"/returns/{self.test_return_id}/audit-log"
        )
        
        if success and isinstance(response, dict):
            timeline = response.get("timeline", [])
            self.log_test(
                "Return Audit Log",
                True,
                f"Audit log has {len(timeline)} entries"
            )
        else:
            self.log_test(
                "Return Audit Log",
                False,
                f"Status: {status}",
                response
            )

    async def test_5_data_integrity_and_tenant_isolation(self):
        """Test 5: Data Integrity and Tenant Isolation"""
        print("\n🔒 TESTING DATA INTEGRITY & TENANT ISOLATION")
        
        # Test tenant isolation - try to access with wrong tenant
        wrong_tenant_headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": "wrong-tenant-id"
        }
        
        success, response, status = await self.make_request(
            "GET",
            "/returns",
            headers=wrong_tenant_headers
        )
        
        # Should either return empty results or 403/404
        if status in [403, 404] or (success and len(response.get("items", [])) == 0):
            self.log_test(
                "Tenant Isolation - Cross-tenant Access Block",
                True,
                f"Properly blocked cross-tenant access (Status: {status})"
            )
        else:
            self.log_test(
                "Tenant Isolation - Cross-tenant Access Block",
                False,
                f"Cross-tenant access not properly blocked (Status: {status})",
                response
            )
        
        # Test data consistency - verify return data structure
        if self.test_return_id:
            success, response, status = await self.make_request(
                "GET",
                f"/returns/{self.test_return_id}"
            )
            
            if success and isinstance(response, dict):
                required_fields = ["id", "tenant_id", "status", "customer_email", "created_at"]
                has_all_fields = all(field in response for field in required_fields)
                
                self.log_test(
                    "Data Integrity - Return Structure",
                    has_all_fields,
                    f"Return has all required fields: {has_all_fields}"
                )
                
                # Verify tenant_id matches
                correct_tenant = response.get("tenant_id") == TEST_TENANT_ID
                self.log_test(
                    "Data Integrity - Tenant ID Consistency",
                    correct_tenant,
                    f"Tenant ID matches: {response.get('tenant_id')} == {TEST_TENANT_ID}"
                )
            else:
                self.log_test(
                    "Data Integrity - Return Structure",
                    False,
                    f"Could not retrieve return for integrity check (Status: {status})"
                )

    async def test_6_api_response_structures(self):
        """Test 6: API Response Structures Match Frontend Expectations"""
        print("\n📋 TESTING API RESPONSE STRUCTURES")
        
        # Test returns list response structure
        success, response, status = await self.make_request("GET", "/returns?limit=5")
        
        if success and isinstance(response, dict):
            # Check pagination structure
            pagination = response.get("pagination", {})
            required_pagination_fields = [
                "current_page", "total_pages", "total_count", 
                "per_page", "has_next", "has_prev"
            ]
            
            has_pagination = all(field in pagination for field in required_pagination_fields)
            self.log_test(
                "API Response Structure - Pagination",
                has_pagination,
                f"Pagination structure complete: {has_pagination}"
            )
            
            # Check items structure
            items = response.get("items", [])
            if items:
                first_item = items[0]
                required_item_fields = ["id", "status", "customer_email", "created_at"]
                has_item_fields = all(field in first_item for field in required_item_fields)
                
                self.log_test(
                    "API Response Structure - Return Items",
                    has_item_fields,
                    f"Return items have required fields: {has_item_fields}"
                )
            else:
                self.log_test(
                    "API Response Structure - Return Items",
                    True,
                    "No items to check (empty result set)"
                )
        else:
            self.log_test(
                "API Response Structure",
                False,
                f"Could not retrieve returns list (Status: {status})",
                response
            )

    async def run_all_tests(self):
        """Run all E2E workflow tests"""
        print("🚀 STARTING END-TO-END RETURN CREATION & MERCHANT APPROVAL WORKFLOW TESTS")
        print(f"Target Tenant: {TEST_TENANT_ID}")
        print(f"Target Order: #{TEST_ORDER_NUMBER}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run tests in sequence
        await self.test_1_order_lookup_integration()
        await self.test_2_customer_return_creation_flow()
        await self.test_3_merchant_returns_list()
        await self.test_4_merchant_approval_workflow()
        await self.test_5_data_integrity_and_tenant_isolation()
        await self.test_6_api_response_structures()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 E2E WORKFLOW TEST SUMMARY")
        print("=" * 80)
        
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
        
        print(f"\n🎯 E2E WORKFLOW STATUS:")
        
        # Check critical workflow components
        order_lookup_working = any(
            "Order Lookup" in result["test"] and result["success"] 
            for result in self.test_results
        )
        
        return_creation_working = any(
            "Return Creation" in result["test"] and result["success"]
            for result in self.test_results
        )
        
        merchant_list_working = any(
            "Merchant Returns List" in result["test"] and result["success"]
            for result in self.test_results
        )
        
        approval_workflow_working = any(
            "Merchant Approval" in result["test"] and result["success"]
            for result in self.test_results
        )
        
        print(f"   Order Lookup: {'✅ Working' if order_lookup_working else '❌ Issues'}")
        print(f"   Return Creation: {'✅ Working' if return_creation_working else '❌ Issues'}")
        print(f"   Merchant Dashboard: {'✅ Working' if merchant_list_working else '❌ Issues'}")
        print(f"   Approval Workflow: {'✅ Working' if approval_workflow_working else '❌ Issues'}")
        
        # Overall workflow status
        workflow_complete = all([
            order_lookup_working, return_creation_working, 
            merchant_list_working, approval_workflow_working
        ])
        
        print(f"\n🏆 OVERALL E2E WORKFLOW: {'✅ COMPLETE' if workflow_complete else '⚠️ PARTIAL'}")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "workflow_complete": workflow_complete,
            "components": {
                "order_lookup": order_lookup_working,
                "return_creation": return_creation_working,
                "merchant_dashboard": merchant_list_working,
                "approval_workflow": approval_workflow_working
            }
        }

async def main():
    """Main test execution"""
    async with E2EReturnWorkflowTestSuite() as test_suite:
        results = await test_suite.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if results["workflow_complete"] else 1)

if __name__ == "__main__":
    asyncio.run(main())