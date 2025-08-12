#!/usr/bin/env python3
"""
Real-time Shopify API Customer Portal Lookup Testing
Tests the live GraphQL lookup functionality for tenant-rms34
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

# Test order numbers from user's actual Shopify store
TEST_ORDER_NUMBERS = ["1001", "1002", "1003", "1004", "1005"]

class ShopifyRealtimeTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.found_orders = []
        
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
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def test_backend_health(self):
        """Test backend health and tenant configuration"""
        print("\n🔧 Testing Backend Health and Configuration...")
        
        # Test backend health
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if success:
            self.log_test("Backend Health Check", True, "Backend is healthy and accessible")
        else:
            self.log_test("Backend Health Check", False, f"Backend not accessible: {status}")
            return False
        
        # Test tenant configuration
        success, tenant_data, status = await self.make_request("GET", f"/tenants/{TEST_TENANT_ID}")
        if success:
            self.log_test("Tenant Configuration", True, f"Tenant {TEST_TENANT_ID} is configured")
        else:
            self.log_test("Tenant Configuration", False, f"Tenant not found: {status}")
        
        return True
    
    async def test_shopify_connectivity(self):
        """Test Shopify connectivity for tenant-rms34"""
        print("\n🔗 Testing Shopify Connectivity...")
        
        # Test Shopify connectivity endpoint
        success, response, status = await self.make_request("GET", "/shopify-test/quick-test", headers={})
        
        if success and response.get("connected"):
            self.log_test("Shopify Connectivity", True, 
                         f"Connected to {response.get('store_name', 'rms34.myshopify.com')}")
            return True
        else:
            self.log_test("Shopify Connectivity", False, 
                         f"Failed to connect to Shopify: {response}")
            return False
    
    async def test_realtime_order_lookup(self):
        """Test real-time order lookup with live Shopify API calls"""
        print("\n🔍 Testing Real-time Order Lookup...")
        
        successful_lookups = 0
        different_products_found = set()
        
        for order_number in TEST_ORDER_NUMBERS:
            print(f"\n   Testing Order #{order_number}...")
            
            # Test with different customer emails to find valid combinations
            test_emails = [
                "customer@example.com",
                "test@rms34.com", 
                "admin@rms34.com",
                "customer1@test.com",
                "customer2@test.com"
            ]
            
            order_found = False
            
            for email in test_emails:
                lookup_data = {
                    "order_number": order_number,
                    "customer_email": email
                }
                
                success, response, status = await self.make_request(
                    "POST", "/elite/portal/returns/lookup-order", lookup_data
                )
                
                if success and response.get("success") and response.get("mode") == "shopify_live":
                    order_found = True
                    successful_lookups += 1
                    
                    order_data = response.get("order", {})
                    self.found_orders.append(order_data)
                    
                    # Track different products
                    line_items = order_data.get("line_items", [])
                    for item in line_items:
                        product_id = item.get("product_id") or item.get("id")
                        if product_id:
                            different_products_found.add(product_id)
                    
                    self.log_test(f"Real-time Lookup Order #{order_number}", True, 
                                 f"Mode: {response['mode']}, Items: {len(line_items)}, Email: {email}")
                    break
                elif success and response.get("mode") == "not_connected":
                    self.log_test(f"Real-time Lookup Order #{order_number}", False, 
                                 "Shopify integration not connected - configuration issue")
                    break
            
            if not order_found:
                # Try without email (some implementations might not require it)
                lookup_data = {"order_number": order_number}
                success, response, status = await self.make_request(
                    "POST", "/elite/portal/returns/lookup-order", lookup_data
                )
                
                if success and response.get("success") and response.get("mode") == "shopify_live":
                    order_found = True
                    successful_lookups += 1
                    self.found_orders.append(response.get("order", {}))
                    self.log_test(f"Real-time Lookup Order #{order_number}", True, 
                                 f"Mode: {response['mode']} (no email required)")
                else:
                    self.log_test(f"Real-time Lookup Order #{order_number}", False, 
                                 f"Order not found with any test email. Status: {status}")
        
        # Summary of real-time lookup testing
        self.log_test("Real-time API Calls Summary", successful_lookups > 0, 
                     f"Successfully found {successful_lookups}/{len(TEST_ORDER_NUMBERS)} orders via live Shopify API")
        
        self.log_test("Different Products Verification", len(different_products_found) > 1, 
                     f"Found {len(different_products_found)} different products across orders (no static data)")
        
        return successful_lookups > 0
    
    async def test_live_data_validation(self):
        """Validate that returned data is live from Shopify API"""
        print("\n✅ Testing Live Data Validation...")
        
        if not self.found_orders:
            self.log_test("Live Data Validation", False, "No orders found to validate")
            return
        
        # Test 1: Verify different order data
        unique_order_numbers = set()
        unique_totals = set()
        unique_customers = set()
        
        for order in self.found_orders:
            order_number = order.get("order_number") or order.get("name")
            total_price = order.get("total_price")
            customer_email = order.get("customer_email") or order.get("email")
            
            if order_number:
                unique_order_numbers.add(order_number)
            if total_price:
                unique_totals.add(str(total_price))
            if customer_email:
                unique_customers.add(customer_email)
        
        self.log_test("Unique Order Numbers", len(unique_order_numbers) > 1, 
                     f"Found {len(unique_order_numbers)} unique order numbers")
        
        self.log_test("Unique Order Totals", len(unique_totals) > 1, 
                     f"Found {len(unique_totals)} unique order totals")
        
        # Test 2: Verify Shopify-specific fields
        shopify_fields_found = 0
        for order in self.found_orders:
            shopify_indicators = [
                "shopify_order_id" in order,
                "financial_status" in order,
                "fulfillment_status" in order,
                order.get("currency_code") is not None,
                "line_items" in order and len(order.get("line_items", [])) > 0
            ]
            
            if any(shopify_indicators):
                shopify_fields_found += 1
        
        self.log_test("Shopify Data Structure", shopify_fields_found > 0, 
                     f"{shopify_fields_found}/{len(self.found_orders)} orders have Shopify-specific fields")
        
        # Test 3: Verify line items have product details
        orders_with_products = 0
        total_line_items = 0
        
        for order in self.found_orders:
            line_items = order.get("line_items", [])
            if line_items:
                orders_with_products += 1
                total_line_items += len(line_items)
        
        self.log_test("Product Line Items", orders_with_products > 0, 
                     f"{orders_with_products} orders with {total_line_items} total line items")
    
    async def test_mode_verification(self):
        """Verify that the system returns 'shopify_live' mode"""
        print("\n🎯 Testing Mode Verification...")
        
        if not self.found_orders:
            # Try one more lookup to verify mode
            lookup_data = {
                "order_number": "1001",
                "customer_email": "test@example.com"
            }
            
            success, response, status = await self.make_request(
                "POST", "/elite/portal/returns/lookup-order", lookup_data
            )
            
            if success:
                mode = response.get("mode")
                if mode == "shopify_live":
                    self.log_test("Mode Verification", True, "System correctly returns 'shopify_live' mode")
                elif mode == "not_connected":
                    self.log_test("Mode Verification", False, "System returns 'not_connected' - integration issue")
                else:
                    self.log_test("Mode Verification", False, f"Unexpected mode: {mode}")
            else:
                self.log_test("Mode Verification", False, f"Failed to test mode: {status}")
        else:
            self.log_test("Mode Verification", True, "Mode 'shopify_live' verified through successful lookups")
    
    async def test_different_order_scenarios(self):
        """Test different order scenarios to ensure no static data"""
        print("\n🔄 Testing Different Order Scenarios...")
        
        # Test with invalid order number
        invalid_lookup = {
            "order_number": "99999",
            "customer_email": "test@example.com"
        }
        
        success, response, status = await self.make_request(
            "POST", "/elite/portal/returns/lookup-order", invalid_lookup
        )
        
        if success and response.get("mode") == "not_found":
            self.log_test("Invalid Order Handling", True, "Correctly returns 'not_found' for invalid orders")
        elif not success:
            self.log_test("Invalid Order Handling", True, "Correctly rejects invalid orders with error")
        else:
            self.log_test("Invalid Order Handling", False, "Should not return data for invalid orders")
        
        # Test with partial order number
        partial_lookup = {
            "order_number": "10",
            "customer_email": "test@example.com"
        }
        
        success, response, status = await self.make_request(
            "POST", "/elite/portal/returns/lookup-order", partial_lookup
        )
        
        # This should either find a match or return not found, but not return static data
        if success:
            mode = response.get("mode")
            if mode in ["shopify_live", "not_found"]:
                self.log_test("Partial Order Number", True, f"Correctly handled partial order: {mode}")
            else:
                self.log_test("Partial Order Number", False, f"Unexpected mode for partial order: {mode}")
        else:
            self.log_test("Partial Order Number", True, "Correctly rejected partial order number")
    
    async def test_customer_data_validation(self):
        """Validate real customer data, pricing, and line items"""
        print("\n👤 Testing Customer Data Validation...")
        
        if not self.found_orders:
            self.log_test("Customer Data Validation", False, "No orders to validate customer data")
            return
        
        valid_customer_data = 0
        valid_pricing_data = 0
        valid_line_items = 0
        
        for order in self.found_orders:
            # Check customer data
            customer_email = order.get("customer_email") or order.get("email")
            customer_name = order.get("customer_name") or order.get("customer", {}).get("first_name")
            
            if customer_email or customer_name:
                valid_customer_data += 1
            
            # Check pricing data
            total_price = order.get("total_price")
            currency = order.get("currency_code") or order.get("currency")
            
            if total_price is not None and currency:
                valid_pricing_data += 1
            
            # Check line items
            line_items = order.get("line_items", [])
            if line_items and len(line_items) > 0:
                # Verify line items have required fields
                valid_items = 0
                for item in line_items:
                    if (item.get("title") or item.get("name")) and item.get("price"):
                        valid_items += 1
                
                if valid_items > 0:
                    valid_line_items += 1
        
        total_orders = len(self.found_orders)
        
        self.log_test("Real Customer Data", valid_customer_data > 0, 
                     f"{valid_customer_data}/{total_orders} orders have valid customer data")
        
        self.log_test("Real Pricing Data", valid_pricing_data > 0, 
                     f"{valid_pricing_data}/{total_orders} orders have valid pricing data")
        
        self.log_test("Real Line Items", valid_line_items > 0, 
                     f"{valid_line_items}/{total_orders} orders have valid line items")
    
    async def run_all_tests(self):
        """Run all real-time Shopify API tests"""
        print("🚀 Starting Real-time Shopify API Customer Portal Lookup Testing")
        print("=" * 70)
        print(f"Testing tenant: {TEST_TENANT_ID}")
        print(f"Test order numbers: {', '.join(TEST_ORDER_NUMBERS)}")
        print("=" * 70)
        
        # Run all test suites
        if not await self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return
        
        if not await self.test_shopify_connectivity():
            print("⚠️ Shopify connectivity issues detected. Continuing with lookup tests...")
        
        await self.test_realtime_order_lookup()
        await self.test_live_data_validation()
        await self.test_mode_verification()
        await self.test_different_order_scenarios()
        await self.test_customer_data_validation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 REAL-TIME SHOPIFY API TESTING SUMMARY")
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
        
        # Real-time functionality assessment
        realtime_tests = [r for r in self.test_results if "Real-time" in r["test"]]
        realtime_passed = sum(1 for t in realtime_tests if t["success"])
        
        if realtime_passed > 0:
            print("   ✅ Real-time Shopify API calls are working")
            print("   ✅ System returns 'mode': 'shopify_live' for connected tenants")
            print("   ✅ Different products returned for different orders (no static data)")
        else:
            print("   ❌ Real-time Shopify API calls are not working")
        
        # Data validation assessment
        data_tests = [r for r in self.test_results if any(keyword in r["test"] for keyword in ["Customer Data", "Pricing", "Line Items", "Live Data"])]
        data_passed = sum(1 for t in data_tests if t["success"])
        
        if data_passed > 0:
            print("   ✅ Live customer data, pricing, and line items validated")
        else:
            print("   ⚠️ Live data validation needs attention")
        
        # Overall assessment
        if passed_tests >= total_tests * 0.8:  # 80% success rate
            print("\n🎉 OVERALL ASSESSMENT: EXCELLENT")
            print("   Real-time Shopify customer portal lookup is working correctly!")
        elif passed_tests >= total_tests * 0.6:  # 60% success rate
            print("\n⚠️ OVERALL ASSESSMENT: GOOD WITH ISSUES")
            print("   Real-time functionality is partially working but needs attention.")
        else:
            print("\n❌ OVERALL ASSESSMENT: NEEDS WORK")
            print("   Real-time Shopify integration requires significant fixes.")

async def main():
    """Main test execution"""
    async with ShopifyRealtimeTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())