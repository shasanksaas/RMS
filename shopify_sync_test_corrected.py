#!/usr/bin/env python3
"""
Corrected Shopify Data Sync Testing for tenant-rms34
Tests the correct Shopify integration endpoints and order sync functionality
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

class CorrectedShopifySyncTestSuite:
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
            connected = response_data.get('connected', False)
            shop = response_data.get('shop', 'N/A')
            order_counts = response_data.get('orderCounts', {})
            return_counts = response_data.get('returnCounts', {})
            last_sync = response_data.get('lastSyncAt', 'Never')
            
            self.log_test(
                "Shopify Integration Status",
                True,
                f"Integration status: Connected={connected}, Shop={shop}, Orders={order_counts.get('total', 0)}, Returns={return_counts.get('total', 0)}, Last Sync={last_sync}"
            )
        else:
            self.log_test(
                "Shopify Integration Status - Failed",
                False,
                f"Failed to get integration status. Status: {status_code}",
                response_data
            )

    async def test_manual_shopify_resync(self):
        """Test 3: Test manual resync endpoint (corrected endpoint)"""
        print("\n🔍 TEST 3: Testing manual Shopify resync...")
        
        success, response_data, status_code = await self.make_request("POST", "/integrations/shopify/resync")
        
        if success:
            job_id = response_data.get('job_id', 'N/A')
            message = response_data.get('message', 'N/A')
            status = response_data.get('status', 'N/A')
            
            self.log_test(
                "Manual Shopify Resync",
                True,
                f"Manual resync initiated successfully. Job ID: {job_id}, Status: {status}, Message: {message}"
            )
            
            # Wait a moment and check job status
            await asyncio.sleep(2)
            await self.check_sync_job_status()
            
        else:
            self.log_test(
                "Manual Shopify Resync - Failed",
                False,
                f"Manual resync failed. Status: {status_code}",
                response_data
            )

    async def check_sync_job_status(self):
        """Check the status of sync jobs"""
        print("\n🔍 Checking sync job status...")
        
        success, response_data, status_code = await self.make_request("GET", "/integrations/shopify/jobs")
        
        if success and isinstance(response_data, list) and len(response_data) > 0:
            latest_job = response_data[0]
            self.log_test(
                "Sync Job Status Check",
                True,
                f"Latest job: ID={latest_job.get('id', 'N/A')}, Type={latest_job.get('type', 'N/A')}, Status={latest_job.get('status', 'N/A')}, Progress={latest_job.get('progress', 0)}%"
            )
        else:
            self.log_test(
                "Sync Job Status Check - No Jobs",
                False,
                f"No sync jobs found or failed to retrieve. Status: {status_code}",
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

    async def test_shopify_connectivity_direct(self):
        """Test 5: Test direct Shopify connectivity"""
        print("\n🔍 TEST 5: Testing direct Shopify connectivity...")
        
        success, response_data, status_code = await self.make_request("GET", "/shopify-test/quick-test")
        
        if success:
            store_name = response_data.get('store_name', 'N/A')
            products_count = response_data.get('products_count', 0)
            self.log_test(
                "Direct Shopify Connectivity",
                True,
                f"Shopify connection successful. Store: {store_name}, Products found: {products_count}"
            )
        else:
            self.log_test(
                "Direct Shopify Connectivity - Failed",
                False,
                f"Shopify connectivity test failed. Status: {status_code}",
                response_data
            )

    async def test_shopify_raw_query(self):
        """Test 6: Test raw GraphQL query to Shopify"""
        print("\n🔍 TEST 6: Testing raw GraphQL query to Shopify...")
        
        # Test with a simple orders query
        query_data = {
            "query": """
            {
                orders(first: 10) {
                    edges {
                        node {
                            id
                            name
                            email
                            totalPrice
                            createdAt
                            lineItems(first: 5) {
                                edges {
                                    node {
                                        title
                                        quantity
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
        }
        
        success, response_data, status_code = await self.make_request("POST", "/shopify-test/raw-query", query_data)
        
        if success:
            orders_data = response_data.get('data', {}).get('orders', {}).get('edges', [])
            orders_count = len(orders_data)
            
            # Look for order #1001
            order_1001_found = False
            for edge in orders_data:
                order = edge.get('node', {})
                order_name = order.get('name', '')
                if order_name == '#1001' or order_name == '1001':
                    order_1001_found = True
                    self.log_test(
                        "Raw GraphQL Query - Order #1001 Found",
                        True,
                        f"Found order #1001 in Shopify! Name: {order_name}, Email: {order.get('email', 'N/A')}, Total: {order.get('totalPrice', 'N/A')}"
                    )
                    break
            
            if not order_1001_found:
                order_names = [edge.get('node', {}).get('name', 'N/A') for edge in orders_data[:5]]
                self.log_test(
                    "Raw GraphQL Query - Order #1001 Not Found",
                    False,
                    f"Order #1001 not found in Shopify GraphQL response. Found {orders_count} orders. Sample order names: {order_names}"
                )
            
        else:
            self.log_test(
                "Raw GraphQL Query - Failed",
                False,
                f"Raw GraphQL query failed. Status: {status_code}",
                response_data
            )

    async def test_orders_after_sync(self):
        """Test 7: Check orders again after sync attempt"""
        print("\n🔍 TEST 7: Checking orders again after sync attempt...")
        
        # Wait a bit more for sync to potentially complete
        await asyncio.sleep(3)
        
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
                    "Orders After Sync - Order #1001 Found",
                    True,
                    f"SUCCESS! Order #1001 now found after sync. Total orders: {order_count}. Customer: {order_1001.get('customer_name', 'N/A')}, Email: {order_1001.get('customer_email', 'N/A')}"
                )
            else:
                self.log_test(
                    "Orders After Sync - Order #1001 Still Missing",
                    False,
                    f"Order #1001 still not found after sync attempt. Total orders: {order_count}. This indicates a sync issue."
                )
        else:
            self.log_test(
                "Orders After Sync - Request Failed",
                False,
                f"Failed to retrieve orders after sync. Status: {status_code}",
                response_data
            )

    async def run_all_tests(self):
        """Run all corrected Shopify sync tests"""
        print("🚀 STARTING CORRECTED SHOPIFY DATA SYNC TESTS FOR TENANT-RMS34")
        print("=" * 70)
        
        # Run all tests in sequence
        await self.test_orders_endpoint_for_tenant_rms34()
        await self.test_shopify_integration_status()
        await self.test_shopify_connectivity_direct()
        await self.test_shopify_raw_query()
        await self.test_manual_shopify_resync()
        await self.test_webhook_health_endpoint()
        await self.test_orders_after_sync()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
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
        
        # Check if order #1001 was found in Shopify
        order_1001_in_shopify = any("Order #1001 Found" in result["test"] and "GraphQL" in result["test"] and result["success"] for result in self.test_results)
        if order_1001_in_shopify:
            print("  ✅ Order #1001 exists in Shopify store")
        else:
            print("  ❌ Order #1001 NOT found in Shopify store")
        
        # Check if order #1001 was found in database
        order_1001_in_db = any("Order #1001 Found" in result["test"] and "Orders" in result["test"] and result["success"] for result in self.test_results)
        if order_1001_in_db:
            print("  ✅ Order #1001 is synced to database")
        else:
            print("  ❌ Order #1001 is NOT synced to database - sync issue confirmed")
        
        # Check if sync was successful
        sync_successful = any("Manual Shopify Resync" in result["test"] and result["success"] for result in self.test_results)
        if sync_successful:
            print("  ✅ Manual sync can be triggered")
        else:
            print("  ❌ Manual sync failed - integration issue")
        
        # Check Shopify connectivity
        shopify_connected = any("Shopify Connectivity" in result["test"] and result["success"] for result in self.test_results)
        if shopify_connected:
            print("  ✅ Shopify connectivity is working")
        else:
            print("  ❌ Shopify connectivity issues detected")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if not order_1001_in_db and order_1001_in_shopify:
            print("  • Order exists in Shopify but not in database - sync process needs investigation")
        elif not order_1001_in_shopify:
            print("  • Order #1001 does not exist in the Shopify store - check order number")
        
        if not sync_successful:
            print("  • Manual sync is failing - check Shopify integration configuration")
        
        return passed == total

async def main():
    """Main test execution"""
    async with CorrectedShopifySyncTestSuite() as test_suite:
        success = await test_suite.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)