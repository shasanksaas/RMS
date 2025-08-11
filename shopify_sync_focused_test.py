#!/usr/bin/env python3
"""
Focused Shopify Order Sync Test for tenant-rms34
Tests the fixed Shopify order sync functionality specifically for order #1001
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
BACKEND_URL = "https://35d12e52-b5b0-4c0d-8c1f-a01716e1ddd2.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ShopifySyncTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.order_1001_data = None
        
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
    
    async def test_backend_health(self):
        """Test backend health and connectivity"""
        print("\n🔧 Testing Backend Health...")
        
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if success:
            self.log_test("Backend Health Check", True, f"Backend is healthy - Status: {status}")
            return True
        else:
            self.log_test("Backend Health Check", False, f"Backend not accessible - Status: {status}", health_data)
            return False
    
    async def test_shopify_connectivity(self):
        """Test Shopify connectivity for tenant-rms34"""
        print("\n🔗 Testing Shopify Connectivity...")
        
        # Test Shopify quick connectivity test
        success, response_data, status = await self.make_request("GET", "/shopify-test/quick-test")
        if success:
            self.log_test("Shopify Connectivity Test", True, 
                         f"Connected to rms34.myshopify.com - Products found: {response_data.get('products_count', 0)}")
        else:
            self.log_test("Shopify Connectivity Test", False, 
                         f"Failed to connect to Shopify - Status: {status}", response_data)
            return False
        
        # Test if Order #1001 exists in Shopify using raw query
        query = """
        {
          orders(first: 10, query: "name:#1001") {
            edges {
              node {
                id
                name
                email
                createdAt
                totalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                customer {
                  id
                  email
                  firstName
                  lastName
                }
                lineItems(first: 10) {
                  edges {
                    node {
                      id
                      name
                      quantity
                      originalUnitPriceSet {
                        shopMoney {
                          amount
                          currencyCode
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        success, response_data, status = await self.make_request("POST", "/shopify-test/raw-query", 
                                                                data={"query": query})
        if success:
            orders = response_data.get("data", {}).get("orders", {}).get("edges", [])
            order_1001_found = any(order["node"]["name"] == "#1001" for order in orders)
            if order_1001_found:
                self.log_test("Shopify Order #1001 Verification", True, "Order #1001 exists in Shopify store")
                # Store order data for later verification
                for order in orders:
                    if order["node"]["name"] == "#1001":
                        self.order_1001_data = order["node"]
                        break
                print(f"   Order #1001 Details: ID={self.order_1001_data.get('id')}, Email={self.order_1001_data.get('email')}, Total={self.order_1001_data.get('totalPriceSet', {}).get('shopMoney', {}).get('amount')}")
            else:
                self.log_test("Shopify Order #1001 Verification", False, "Order #1001 not found in Shopify store")
        else:
            self.log_test("Shopify Order #1001 Verification", False, 
                         f"Failed to query Shopify orders - Status: {status}", response_data)
        
        return True
    
    async def test_current_orders_state(self):
        """Test current state of orders in database for tenant-rms34"""
        print("\n📊 Testing Current Orders State...")
        
        # Check current orders count
        success, response_data, status = await self.make_request("GET", "/orders?limit=100")
        if success:
            orders_count = len(response_data.get("items", []))
            self.log_test("Current Orders Count", True, 
                         f"Found {orders_count} orders in database for tenant-rms34")
            
            # Check if Order #1001 is in database
            order_1001_in_db = False
            for order in response_data.get("items", []):
                order_number = order.get("order_number", order.get("name", ""))
                if order_number in ["#1001", "1001"]:
                    order_1001_in_db = True
                    break
            
            if order_1001_in_db:
                self.log_test("Order #1001 Database Check", True, "Order #1001 found in database")
                return True
            else:
                self.log_test("Order #1001 Database Check", False, "Order #1001 NOT found in database - This is the core issue")
                return False
        else:
            self.log_test("Current Orders Count", False, 
                         f"Failed to retrieve orders - Status: {status}", response_data)
            return False
    
    async def test_integration_status(self):
        """Test integration status for tenant-rms34"""
        print("\n📊 Testing Integration Status...")
        
        success, response_data, status = await self.make_request("GET", "/integrations/shopify/status")
        if success:
            connected = response_data.get("connected", False)
            orders_count = response_data.get("orderCounts", {}).get("total", 0)
            last_sync = response_data.get("lastSyncAt")
            
            self.log_test("Integration Status Check", True, 
                         f"Connected: {connected}, Orders: {orders_count}, Last Sync: {last_sync}")
            
            if connected and orders_count > 0:
                self.log_test("Integration Health", True, "Integration is healthy with synced data")
            else:
                self.log_test("Integration Health", False, "Integration issues detected - no orders synced")
        else:
            self.log_test("Integration Status Check", False, 
                         f"Failed to get integration status - Status: {status}", response_data)
    
    async def test_manual_resync(self):
        """Test manual resync functionality"""
        print("\n🔄 Testing Manual Resync...")
        
        # Trigger manual resync using correct endpoint
        success, response_data, status = await self.make_request("POST", "/integrations/shopify/resync")
        if success:
            job_id = response_data.get('job_id')
            self.log_test("Manual Resync Trigger", True, 
                         f"Resync triggered successfully - Job ID: {job_id}")
            
            # Wait a moment for sync to process
            await asyncio.sleep(5)
            
            # Check sync jobs
            success, jobs_data, status_code = await self.make_request("GET", "/integrations/shopify/jobs?limit=5")
            if success and jobs_data:
                latest_job = jobs_data[0] if jobs_data else None
                if latest_job:
                    self.log_test("Sync Job Status Check", True, 
                                 f"Latest job status: {latest_job.get('status')} - Progress: {latest_job.get('progress', 0)}%")
                else:
                    self.log_test("Sync Job Status Check", False, "No sync jobs found")
            else:
                self.log_test("Sync Job Status Check", False, 
                             f"Failed to get sync jobs - Status: {status_code}", jobs_data)
        else:
            self.log_test("Manual Resync Trigger", False, 
                         f"Failed to trigger resync - Status: {status}", response_data)
            return False
        
        return True
    
    async def test_orders_after_sync(self):
        """Test orders state after sync"""
        print("\n📈 Testing Orders After Sync...")
        
        # Wait additional time for sync to complete
        await asyncio.sleep(10)
        
        # Check orders count again
        success, response_data, status = await self.make_request("GET", "/orders?limit=100")
        if success:
            orders_count = len(response_data.get("items", []))
            self.log_test("Orders Count After Sync", True, 
                         f"Found {orders_count} orders in database after sync")
            
            # Check if Order #1001 is now in database
            order_1001_in_db = False
            order_1001_data = None
            
            for order in response_data.get("items", []):
                order_number = order.get("order_number", order.get("name", ""))
                if order_number in ["#1001", "1001"]:
                    order_1001_in_db = True
                    order_1001_data = order
                    break
            
            if order_1001_in_db:
                self.log_test("Order #1001 After Sync", True, "Order #1001 now found in database!")
                
                # Verify order data structure
                await self.verify_order_data_structure(order_1001_data)
                return True
            else:
                self.log_test("Order #1001 After Sync", False, "Order #1001 still NOT found in database after sync")
                return False
        else:
            self.log_test("Orders Count After Sync", False, 
                         f"Failed to retrieve orders after sync - Status: {status}", response_data)
            return False
    
    async def verify_order_data_structure(self, order_data: Dict):
        """Verify order data structure matches frontend expectations"""
        print("\n🔍 Verifying Order Data Structure...")
        
        required_fields = [
            "order_id", "customer_name", "customer_email", 
            "financial_status", "fulfillment_status", "total_price", "currency_code"
        ]
        
        missing_fields = []
        present_fields = []
        
        for field in required_fields:
            # Check both snake_case and camelCase variants
            if (field in order_data or 
                field.replace("_", "") in order_data or
                field.replace("_", "").lower() in order_data):
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        if not missing_fields:
            self.log_test("Order Data Structure Verification", True, 
                         f"All required fields present: {', '.join(present_fields)}")
        else:
            self.log_test("Order Data Structure Verification", False, 
                         f"Missing fields: {', '.join(missing_fields)}, Present: {', '.join(present_fields)}")
        
        # Log actual order structure for debugging
        print(f"   Order #1001 Data Structure:")
        for key, value in order_data.items():
            print(f"     {key}: {value}")
    
    async def test_webhook_processing(self):
        """Test webhook processing with sample orders/create payload"""
        print("\n🎣 Testing Webhook Processing...")
        
        # Create sample orders/create webhook payload based on Shopify structure
        sample_payload = {
            "id": 5813364687034,
            "name": "#1002",
            "email": "test@example.com",
            "created_at": "2025-01-27T10:00:00Z",
            "updated_at": "2025-01-27T10:00:00Z",
            "total_price": "100.00",
            "currency": "USD",
            "financial_status": "paid",
            "fulfillment_status": "fulfilled",
            "customer": {
                "id": 123456,
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "Customer"
            },
            "line_items": [
                {
                    "id": 123,
                    "name": "Test Product",
                    "quantity": 1,
                    "price": "100.00",
                    "sku": "TEST-001"
                }
            ]
        }
        
        # Test webhook endpoint
        success, response_data, status = await self.make_request("POST", "/test/webhook", data=sample_payload)
        if success:
            self.log_test("Webhook Processing Test", True, 
                         f"Webhook processed successfully - Response: {response_data.get('message', 'N/A')}")
        else:
            self.log_test("Webhook Processing Test", False, 
                         f"Webhook processing failed - Status: {status}", response_data)
    
    async def run_all_tests(self):
        """Run all Shopify sync tests"""
        print("🚀 Starting Shopify Order Sync Tests for tenant-rms34")
        print("=" * 60)
        
        # Test sequence
        if not await self.test_backend_health():
            return
        
        await self.test_shopify_connectivity()
        await self.test_current_orders_state()
        await self.test_integration_status()
        await self.test_manual_resync()
        await self.test_orders_after_sync()
        await self.test_webhook_processing()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        order_in_shopify = any("Order #1001 exists in Shopify" in result["details"] for result in self.test_results if result["success"])
        order_in_db_before = any("Order #1001 found in database" in result["details"] for result in self.test_results if result["success"])
        order_in_db_after = any("Order #1001 now found in database" in result["details"] for result in self.test_results if result["success"])
        
        print(f"  • Order #1001 exists in Shopify: {'✅' if order_in_shopify else '❌'}")
        print(f"  • Order #1001 in DB before sync: {'✅' if order_in_db_before else '❌'}")
        print(f"  • Order #1001 in DB after sync: {'✅' if order_in_db_after else '❌'}")
        
        if order_in_shopify and not order_in_db_after:
            print("\n🚨 CRITICAL ISSUE: Order #1001 exists in Shopify but is not syncing to database!")
            print("   This confirms the sync service implementation issue.")
        elif order_in_db_after:
            print("\n✅ SUCCESS: Order #1001 sync issue has been resolved!")

async def main():
    """Main test execution"""
    async with ShopifySyncTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())