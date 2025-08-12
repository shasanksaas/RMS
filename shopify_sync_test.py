#!/usr/bin/env python3
"""
Shopify Data Sync Testing for tenant-rms34
Tests Shopify integration endpoints and order sync functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://returnhub-1.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ShopifySyncTestSuite:
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
                response_data = await response.json()
                return response.status < 400, response_data, response.status
        except Exception as e:
            return False, {"error": str(e)}, 500

    async def test_orders_endpoint_for_tenant_rms34(self):
        """Test 1: Check orders endpoint for tenant-rms34 to see if Shopify orders exist"""
        print("\n🔍 TEST 1: Checking orders endpoint for tenant-rms34...")
        
        success, response_data, status_code = await self.make_request("GET", "/orders")
        
        if success:
            orders = response_data.get("items", []) if isinstance(response_data, dict) else response_data
            order_count = len(orders) if isinstance(orders, list) else 0
            
            # Look for order #1001 specifically
            order_1001 = None
            for order in orders if isinstance(orders, list) else []:
                order_number = order.get("order_number", order.get("name", ""))
                if order_number == "1001" or order_number == "#1001":
                    order_1001 = order
                    break
            
            if order_1001:
                self.log_test(
                    "Orders Endpoint - Order #1001 Found",
                    True,
                    f"Found order #1001 for tenant-rms34. Total orders: {order_count}. Order details: Customer={order_1001.get('customer_name', 'N/A')}, Email={order_1001.get('customer_email', 'N/A')}, Total=${order_1001.get('total_price', 'N/A')}"
                )
            else:
                self.log_test(
                    "Orders Endpoint - Order #1001 Missing",
                    False,
                    f"Order #1001 NOT found for tenant-rms34. Total orders found: {order_count}. Available order numbers: {[order.get('order_number', order.get('name', 'N/A')) for order in orders[:5] if isinstance(orders, list)]}"
                )
        else:
            self.log_test(
                "Orders Endpoint - Request Failed",
                False,
                f"Failed to retrieve orders for tenant-rms34. Status: {status_code}",
                response_data
            )

    async def test_shopify_integration_status(self):
        """Test 2: Check Shopify integration status for tenant-rms34"""
        print("\n🔍 TEST 2: Checking Shopify integration status...")
        
        success, response_data, status_code = await self.make_request("GET", "/integrations/shopify/status")
        
        if success:
            self.log_test(
                "Shopify Integration Status",
                True,
                f"Integration status retrieved successfully. Status: {response_data.get('status', 'unknown')}, Connected: {response_data.get('connected', False)}, Store: {response_data.get('store_url', 'N/A')}"
            )
        else:
            self.log_test(
                "Shopify Integration Status - Failed",
                False,
                f"Failed to get integration status. Status: {status_code}",
                response_data
            )

    async def test_manual_shopify_sync(self):
        """Test 3: Test manual sync endpoint"""
        print("\n🔍 TEST 3: Testing manual Shopify sync...")
        
        sync_data = {
            "sync_type": "manual",
            "include_orders": True,
            "include_products": True,
            "days_back": 30
        }
        
        success, response_data, status_code = await self.make_request("POST", "/integrations/shopify/sync", sync_data)
        
        if success:
            self.log_test(
                "Manual Shopify Sync",
                True,
                f"Manual sync initiated successfully. Sync ID: {response_data.get('sync_id', 'N/A')}, Status: {response_data.get('status', 'N/A')}"
            )
        else:
            self.log_test(
                "Manual Shopify Sync - Failed",
                False,
                f"Manual sync failed. Status: {status_code}",
                response_data
            )

    async def test_webhook_health_endpoint(self):
        """Test 4: Verify webhook endpoints are working for real-time sync"""
        print("\n🔍 TEST 4: Testing webhook health endpoint...")
        
        success, response_data, status_code = await self.make_request("GET", "/test/health")
        
        if success:
            webhook_status = response_data.get('webhook_service', {})
            self.log_test(
                "Webhook Health Check",
                True,
                f"Webhook service health: {webhook_status.get('status', 'unknown')}, Supported topics: {webhook_status.get('supported_topics', [])}"
            )
        else:
            self.log_test(
                "Webhook Health Check - Failed",
                False,
                f"Webhook health check failed. Status: {status_code}",
                response_data
            )

    async def test_order_lookup_for_1001(self):
        """Test 5: Specific lookup for order #1001 using order lookup endpoint"""
        print("\n🔍 TEST 5: Testing order lookup for order #1001...")
        
        # Try different lookup methods
        lookup_methods = [
            {"order_number": "1001", "email": "customer@example.com"},
            {"order_number": "#1001", "email": "customer@example.com"},
            {"order_number": "1001", "email": "test@rms34.com"},
            {"order_number": "#1001", "email": "test@rms34.com"}
        ]
        
        found_order = False
        for i, lookup_data in enumerate(lookup_methods):
            success, response_data, status_code = await self.make_request("POST", "/orders/lookup", lookup_data)
            
            if success:
                found_order = True
                self.log_test(
                    f"Order Lookup Method {i+1} - Success",
                    True,
                    f"Found order #1001 using {lookup_data}. Customer: {response_data.get('customer_name', 'N/A')}, Total: ${response_data.get('total_price', 'N/A')}"
                )
                break
            else:
                self.log_test(
                    f"Order Lookup Method {i+1} - Failed",
                    False,
                    f"Order lookup failed with {lookup_data}. Status: {status_code}",
                    response_data
                )
        
        if not found_order:
            self.log_test(
                "Order #1001 Lookup - All Methods Failed",
                False,
                "Could not find order #1001 using any lookup method. Order may not be synced from Shopify."
            )

    async def test_tenant_rms34_existence(self):
        """Test 6: Verify tenant-rms34 exists in the system"""
        print("\n🔍 TEST 6: Verifying tenant-rms34 exists...")
        
        success, response_data, status_code = await self.make_request("GET", "/tenants")
        
        if success:
            tenants = response_data if isinstance(response_data, list) else []
            rms34_tenant = None
            
            for tenant in tenants:
                if tenant.get("id") == "tenant-rms34" or "rms34" in tenant.get("domain", "").lower():
                    rms34_tenant = tenant
                    break
            
            if rms34_tenant:
                self.log_test(
                    "Tenant RMS34 Verification",
                    True,
                    f"Found tenant-rms34. Name: {rms34_tenant.get('name', 'N/A')}, Domain: {rms34_tenant.get('domain', 'N/A')}, Shopify Store: {rms34_tenant.get('shopify_store_url', 'N/A')}"
                )
            else:
                self.log_test(
                    "Tenant RMS34 Verification - Not Found",
                    False,
                    f"tenant-rms34 not found. Available tenants: {[t.get('id', 'N/A') for t in tenants[:5]]}"
                )
        else:
            self.log_test(
                "Tenant RMS34 Verification - Request Failed",
                False,
                f"Failed to retrieve tenants. Status: {status_code}",
                response_data
            )

    async def test_shopify_connectivity(self):
        """Test 7: Test Shopify connectivity for rms34 store"""
        print("\n🔍 TEST 7: Testing Shopify connectivity...")
        
        # Test the Shopify connectivity endpoint
        success, response_data, status_code = await self.make_request("GET", "/shopify-test/quick-test")
        
        if success:
            self.log_test(
                "Shopify Connectivity Test",
                True,
                f"Shopify connection successful. Store: {response_data.get('store_name', 'N/A')}, Products found: {response_data.get('products_count', 0)}"
            )
        else:
            self.log_test(
                "Shopify Connectivity Test - Failed",
                False,
                f"Shopify connectivity test failed. Status: {status_code}",
                response_data
            )

    async def run_all_tests(self):
        """Run all Shopify sync tests"""
        print("🚀 STARTING SHOPIFY DATA SYNC TESTS FOR TENANT-RMS34")
        print("=" * 60)
        
        # Run all tests
        await self.test_tenant_rms34_existence()
        await self.test_shopify_connectivity()
        await self.test_orders_endpoint_for_tenant_rms34()
        await self.test_shopify_integration_status()
        await self.test_manual_shopify_sync()
        await self.test_webhook_health_endpoint()
        await self.test_order_lookup_for_1001()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check if order #1001 was found
        order_1001_found = any("Order #1001 Found" in result["test"] and result["success"] for result in self.test_results)
        if order_1001_found:
            print("  ✅ Order #1001 is present in the database")
        else:
            print("  ❌ Order #1001 is NOT found in the database - sync issue likely")
        
        # Check if tenant exists
        tenant_exists = any("Tenant RMS34 Verification" in result["test"] and result["success"] for result in self.test_results)
        if tenant_exists:
            print("  ✅ Tenant-rms34 exists in the system")
        else:
            print("  ❌ Tenant-rms34 does not exist - setup issue")
        
        # Check Shopify connectivity
        shopify_connected = any("Shopify Connectivity" in result["test"] and result["success"] for result in self.test_results)
        if shopify_connected:
            print("  ✅ Shopify connectivity is working")
        else:
            print("  ❌ Shopify connectivity issues detected")
        
        return passed == total

async def main():
    """Main test execution"""
    async with ShopifySyncTestSuite() as test_suite:
        success = await test_suite.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)