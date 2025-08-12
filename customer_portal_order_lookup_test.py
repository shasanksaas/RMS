#!/usr/bin/env python3
"""
Customer Portal Order Lookup Testing
Tests the simplified order lookup logic for tenant-rms34
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://returnportal.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class CustomerPortalOrderLookupTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.available_orders = []
        
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
    
    async def test_backend_health(self):
        """Test if backend is accessible"""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Backend Health Check", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_test("Backend Health Check", False, f"Status code: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def get_available_orders(self):
        """Get available orders for tenant-rms34 to test with"""
        try:
            async with self.session.get(f"{BACKEND_URL}/orders", headers=TEST_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get('items', [])
                    self.available_orders = orders
                    
                    order_numbers = [order.get('order_number', 'N/A') for order in orders]
                    self.log_test("Get Available Orders", True, 
                                f"Found {len(orders)} orders: {', '.join(order_numbers[:5])}")
                    
                    # Print detailed order info for testing
                    print("\n📋 AVAILABLE ORDERS FOR TESTING:")
                    for i, order in enumerate(orders[:10]):  # Show first 10 orders
                        print(f"   {i+1}. Order #{order.get('order_number', 'N/A')} - "
                              f"Customer: {order.get('customer_email', 'N/A')} - "
                              f"Total: ${order.get('total_price', 0)}")
                    
                    return True
                else:
                    self.log_test("Get Available Orders", False, f"Status code: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Get Available Orders", False, f"Error: {str(e)}")
            return False
    
    async def test_order_lookup_by_number_only(self, order_number: str):
        """Test order lookup with just order number (no email required)"""
        try:
            payload = {
                "order_number": order_number
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                headers=TEST_HEADERS,
                json=payload
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    success = data.get('success', False)
                    mode = data.get('mode', 'unknown')
                    order_data = data.get('order')
                    
                    if success and order_data:
                        self.log_test(f"Order Lookup by Number Only - {order_number}", True,
                                    f"Mode: {mode}, Found order with customer: {order_data.get('customer_email', 'N/A')}")
                    else:
                        self.log_test(f"Order Lookup by Number Only - {order_number}", False,
                                    f"Success: {success}, Message: {data.get('message', 'No message')}")
                else:
                    self.log_test(f"Order Lookup by Number Only - {order_number}", False,
                                f"Status: {response.status}, Response: {data}")
                
                return response.status == 200 and data.get('success', False)
                
        except Exception as e:
            self.log_test(f"Order Lookup by Number Only - {order_number}", False, f"Error: {str(e)}")
            return False
    
    async def test_order_lookup_with_email(self, order_number: str, email: str):
        """Test order lookup with both order number and email"""
        try:
            payload = {
                "order_number": order_number,
                "customer_email": email
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                headers=TEST_HEADERS,
                json=payload
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    success = data.get('success', False)
                    mode = data.get('mode', 'unknown')
                    order_data = data.get('order')
                    
                    if success and order_data:
                        self.log_test(f"Order Lookup with Email - {order_number}", True,
                                    f"Mode: {mode}, Verified customer: {order_data.get('customer_email', 'N/A')}")
                    else:
                        self.log_test(f"Order Lookup with Email - {order_number}", False,
                                    f"Success: {success}, Message: {data.get('message', 'No message')}")
                else:
                    self.log_test(f"Order Lookup with Email - {order_number}", False,
                                f"Status: {response.status}, Response: {data}")
                
                return response.status == 200 and data.get('success', False)
                
        except Exception as e:
            self.log_test(f"Order Lookup with Email - {order_number}", False, f"Error: {str(e)}")
            return False
    
    async def test_merchant_dashboard_orders(self):
        """Test that customer portal uses same data as merchant dashboard"""
        try:
            # Get orders from merchant dashboard endpoint
            async with self.session.get(f"{BACKEND_URL}/orders", headers=TEST_HEADERS) as response:
                if response.status == 200:
                    merchant_data = await response.json()
                    merchant_orders = merchant_data.get('items', [])
                    
                    self.log_test("Merchant Dashboard Orders Access", True,
                                f"Retrieved {len(merchant_orders)} orders from merchant dashboard")
                    
                    # Test that customer portal can find the same orders
                    found_orders = 0
                    for order in merchant_orders[:5]:  # Test first 5 orders
                        order_number = order.get('order_number')
                        if order_number:
                            lookup_success = await self.test_order_lookup_by_number_only(order_number)
                            if lookup_success:
                                found_orders += 1
                    
                    success_rate = (found_orders / min(5, len(merchant_orders))) * 100 if merchant_orders else 0
                    self.log_test("Data Source Consistency", success_rate >= 80,
                                f"Customer portal found {found_orders}/{min(5, len(merchant_orders))} orders ({success_rate:.1f}%)")
                    
                    return success_rate >= 80
                else:
                    self.log_test("Merchant Dashboard Orders Access", False, f"Status: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Data Source Consistency", False, f"Error: {str(e)}")
            return False
    
    async def test_specific_order_numbers(self):
        """Test specific order numbers mentioned in the request"""
        test_order_numbers = ["1001", "1002", "1003", "1004"]
        successful_lookups = 0
        
        for order_number in test_order_numbers:
            success = await self.test_order_lookup_by_number_only(order_number)
            if success:
                successful_lookups += 1
        
        success_rate = (successful_lookups / len(test_order_numbers)) * 100
        self.log_test("Specific Order Numbers Test", successful_lookups > 0,
                    f"Found {successful_lookups}/{len(test_order_numbers)} specific orders ({success_rate:.1f}%)")
        
        return successful_lookups > 0
    
    async def test_returns_endpoint_compatibility(self):
        """Test that returns endpoint works with tenant-rms34"""
        try:
            async with self.session.get(f"{BACKEND_URL}/returns", headers=TEST_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    returns = data.get('items', [])
                    
                    self.log_test("Returns Endpoint Compatibility", True,
                                f"Retrieved {len(returns)} returns for tenant-rms34")
                    return True
                else:
                    self.log_test("Returns Endpoint Compatibility", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Returns Endpoint Compatibility", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all customer portal order lookup tests"""
        print("🚀 CUSTOMER PORTAL ORDER LOOKUP TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Tenant: {TEST_TENANT_ID}")
        print("=" * 60)
        
        # Test 1: Backend Health
        if not await self.test_backend_health():
            print("❌ Backend not accessible, stopping tests")
            return
        
        # Test 2: Get available orders
        await self.get_available_orders()
        
        # Test 3: Test specific order numbers
        await self.test_specific_order_numbers()
        
        # Test 4: Test merchant dashboard consistency
        await self.test_merchant_dashboard_orders()
        
        # Test 5: Test returns endpoint compatibility
        await self.test_returns_endpoint_compatibility()
        
        # Test 6: Test with email verification (if we have orders)
        if self.available_orders:
            first_order = self.available_orders[0]
            order_number = first_order.get('order_number')
            customer_email = first_order.get('customer_email')
            
            if order_number and customer_email:
                await self.test_order_lookup_with_email(order_number, customer_email)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 CUSTOMER PORTAL ORDER LOOKUP TEST COMPLETE!")
        
        return success_rate >= 70  # 70% success rate threshold


async def main():
    """Main test execution"""
    async with CustomerPortalOrderLookupTestSuite() as test_suite:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())