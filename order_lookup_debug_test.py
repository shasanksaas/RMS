#!/usr/bin/env python3
"""
Order Lookup Debug Test for Customer Return Portal
Focuses on debugging the disconnect between merchant dashboard orders and customer portal lookup
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://08371864-d592-4183-9894-6a29b3c874f2.preview.emergentagent.com/api"
TARGET_TENANT_ID = "tenant-rms34"  # Focus on tenant-rms34 as requested
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TARGET_TENANT_ID
}

class OrderLookupDebugSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.merchant_orders = []
        self.portal_lookup_results = []
        
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
            "response_data": response_data
        })
    
    async def test_merchant_dashboard_orders(self):
        """Test 1: Get orders from merchant dashboard endpoint"""
        print(f"\n🔍 Testing Merchant Dashboard Orders for {TARGET_TENANT_ID}")
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/orders",
                headers=TEST_HEADERS
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.merchant_orders = data.get("items", [])
                    
                    self.log_test(
                        "Merchant Dashboard Orders Access",
                        True,
                        f"Retrieved {len(self.merchant_orders)} orders"
                    )
                    
                    # Log order details for debugging
                    print(f"\n📋 MERCHANT DASHBOARD ORDERS ({len(self.merchant_orders)} found):")
                    for i, order in enumerate(self.merchant_orders[:5]):  # Show first 5
                        print(f"   Order {i+1}:")
                        print(f"     - ID: {order.get('id', 'N/A')}")
                        print(f"     - Order Number: {order.get('order_number', 'N/A')}")
                        print(f"     - Customer Email: {order.get('customer_email', 'N/A')}")
                        print(f"     - Customer Name: {order.get('customer_name', 'N/A')}")
                        print(f"     - Total Price: {order.get('total_price', 'N/A')}")
                        print(f"     - Created At: {order.get('created_at', 'N/A')}")
                        print(f"     - Line Items: {len(order.get('line_items', []))} items")
                    
                    return True
                else:
                    error_data = await response.text()
                    self.log_test(
                        "Merchant Dashboard Orders Access",
                        False,
                        f"HTTP {response.status}",
                        error_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Merchant Dashboard Orders Access",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_customer_portal_lookup_endpoints(self):
        """Test 2: Test customer portal lookup endpoints"""
        print(f"\n🔍 Testing Customer Portal Lookup Endpoints")
        
        # Test the Elite portal lookup endpoint
        await self.test_elite_portal_lookup()
        
        # Test the regular portal lookup endpoint
        await self.test_regular_portal_lookup()
        
        # Test the unified returns lookup endpoint
        await self.test_unified_returns_lookup()
    
    async def test_elite_portal_lookup(self):
        """Test Elite Portal Returns Lookup"""
        print(f"\n🎯 Testing Elite Portal Returns Lookup")
        
        if not self.merchant_orders:
            self.log_test(
                "Elite Portal Lookup - No Orders",
                False,
                "No merchant orders available for testing"
            )
            return
        
        # Test with the first available order
        test_order = self.merchant_orders[0]
        order_number = test_order.get('order_number', test_order.get('name', ''))
        customer_email = test_order.get('customer_email', test_order.get('email', ''))
        
        if not order_number or not customer_email:
            self.log_test(
                "Elite Portal Lookup - Missing Data",
                False,
                f"Order missing required data: order_number={order_number}, email={customer_email}"
            )
            return
        
        lookup_data = {
            "order_number": order_number,
            "customer_email": customer_email
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                headers=TEST_HEADERS,
                json=lookup_data
            ) as response:
                
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Elite Portal Lookup - Success",
                        True,
                        f"Found order {order_number} for {customer_email}"
                    )
                    
                    # Store result for comparison
                    self.portal_lookup_results.append({
                        "endpoint": "elite_portal",
                        "success": True,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data
                    })
                    
                else:
                    self.log_test(
                        "Elite Portal Lookup - Failed",
                        False,
                        f"HTTP {response.status} for order {order_number}, email {customer_email}",
                        response_data
                    )
                    
                    self.portal_lookup_results.append({
                        "endpoint": "elite_portal",
                        "success": False,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data,
                        "status": response.status
                    })
                    
        except Exception as e:
            self.log_test(
                "Elite Portal Lookup - Exception",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_regular_portal_lookup(self):
        """Test Regular Portal Returns Lookup"""
        print(f"\n🎯 Testing Regular Portal Returns Lookup")
        
        if not self.merchant_orders:
            return
        
        test_order = self.merchant_orders[0]
        order_number = test_order.get('order_number', test_order.get('name', ''))
        customer_email = test_order.get('customer_email', test_order.get('email', ''))
        
        if not order_number or not customer_email:
            return
        
        lookup_data = {
            "order_number": order_number,
            "email": customer_email  # Note: different field name
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/orders/lookup",
                headers=TEST_HEADERS,
                json=lookup_data
            ) as response:
                
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Regular Portal Lookup - Success",
                        True,
                        f"Found order {order_number} for {customer_email}"
                    )
                    
                    self.portal_lookup_results.append({
                        "endpoint": "regular_portal",
                        "success": True,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data
                    })
                    
                else:
                    self.log_test(
                        "Regular Portal Lookup - Failed",
                        False,
                        f"HTTP {response.status} for order {order_number}, email {customer_email}",
                        response_data
                    )
                    
                    self.portal_lookup_results.append({
                        "endpoint": "regular_portal",
                        "success": False,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data,
                        "status": response.status
                    })
                    
        except Exception as e:
            self.log_test(
                "Regular Portal Lookup - Exception",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_unified_returns_lookup(self):
        """Test Unified Returns Lookup"""
        print(f"\n🎯 Testing Unified Returns Lookup")
        
        if not self.merchant_orders:
            return
        
        test_order = self.merchant_orders[0]
        order_number = test_order.get('order_number', test_order.get('name', ''))
        customer_email = test_order.get('customer_email', test_order.get('email', ''))
        
        if not order_number or not customer_email:
            return
        
        lookup_data = {
            "order_number": order_number,
            "customer_email": customer_email
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/returns/order-lookup",
                headers=TEST_HEADERS,
                json=lookup_data
            ) as response:
                
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Unified Returns Lookup - Success",
                        True,
                        f"Found order {order_number} for {customer_email}"
                    )
                    
                    self.portal_lookup_results.append({
                        "endpoint": "unified_returns",
                        "success": True,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data
                    })
                    
                else:
                    self.log_test(
                        "Unified Returns Lookup - Failed",
                        False,
                        f"HTTP {response.status} for order {order_number}, email {customer_email}",
                        response_data
                    )
                    
                    self.portal_lookup_results.append({
                        "endpoint": "unified_returns",
                        "success": False,
                        "order_number": order_number,
                        "customer_email": customer_email,
                        "response": response_data,
                        "status": response.status
                    })
                    
        except Exception as e:
            self.log_test(
                "Unified Returns Lookup - Exception",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_multiple_orders_lookup(self):
        """Test 3: Test lookup with multiple orders to find patterns"""
        print(f"\n🔍 Testing Multiple Orders Lookup Patterns")
        
        if len(self.merchant_orders) < 2:
            self.log_test(
                "Multiple Orders Test",
                False,
                "Need at least 2 orders for pattern testing"
            )
            return
        
        successful_lookups = 0
        failed_lookups = 0
        
        # Test up to 5 orders
        for i, order in enumerate(self.merchant_orders[:5]):
            order_number = order.get('order_number', order.get('name', ''))
            customer_email = order.get('customer_email', order.get('email', ''))
            
            if not order_number or not customer_email:
                print(f"   Order {i+1}: Missing data (order_number={order_number}, email={customer_email})")
                continue
            
            # Test with Elite portal endpoint
            lookup_data = {
                "order_number": order_number,
                "customer_email": customer_email
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/elite/portal/returns/lookup-order",
                    headers=TEST_HEADERS,
                    json=lookup_data
                ) as response:
                    
                    if response.status == 200:
                        successful_lookups += 1
                        print(f"   Order {i+1}: ✅ SUCCESS - {order_number} ({customer_email})")
                    else:
                        failed_lookups += 1
                        response_data = await response.json()
                        print(f"   Order {i+1}: ❌ FAILED - {order_number} ({customer_email}) - {response.status}")
                        print(f"     Error: {response_data.get('detail', 'Unknown error')}")
                        
            except Exception as e:
                failed_lookups += 1
                print(f"   Order {i+1}: ❌ EXCEPTION - {order_number} ({customer_email}) - {str(e)}")
        
        success_rate = (successful_lookups / (successful_lookups + failed_lookups)) * 100 if (successful_lookups + failed_lookups) > 0 else 0
        
        self.log_test(
            "Multiple Orders Lookup Pattern",
            success_rate > 0,
            f"Success rate: {success_rate:.1f}% ({successful_lookups}/{successful_lookups + failed_lookups})"
        )
    
    async def analyze_data_structure_differences(self):
        """Test 4: Analyze data structure differences between endpoints"""
        print(f"\n🔍 Analyzing Data Structure Differences")
        
        if not self.merchant_orders:
            self.log_test(
                "Data Structure Analysis",
                False,
                "No merchant orders available for analysis"
            )
            return
        
        # Analyze merchant order structure
        sample_order = self.merchant_orders[0]
        merchant_fields = set(sample_order.keys())
        
        print(f"\n📊 MERCHANT ORDER FIELDS ({len(merchant_fields)}):")
        for field in sorted(merchant_fields):
            value = sample_order.get(field)
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"   - {field}: {value}")
        
        # Check for email field variations
        email_fields = [field for field in merchant_fields if 'email' in field.lower()]
        print(f"\n📧 EMAIL FIELDS FOUND: {email_fields}")
        
        # Check for order number field variations
        order_num_fields = [field for field in merchant_fields if any(term in field.lower() for term in ['order', 'number', 'name'])]
        print(f"\n🔢 ORDER NUMBER FIELDS FOUND: {order_num_fields}")
        
        # Analyze portal lookup results if available
        if self.portal_lookup_results:
            print(f"\n📋 PORTAL LOOKUP RESULTS ANALYSIS:")
            for result in self.portal_lookup_results:
                print(f"   - {result['endpoint']}: {'SUCCESS' if result['success'] else 'FAILED'}")
                if not result['success'] and 'response' in result:
                    error_detail = result['response'].get('detail', 'Unknown error')
                    print(f"     Error: {error_detail}")
        
        self.log_test(
            "Data Structure Analysis",
            True,
            f"Analyzed {len(merchant_fields)} fields, found {len(email_fields)} email fields, {len(order_num_fields)} order number fields"
        )
    
    async def test_database_consistency(self):
        """Test 5: Check database consistency between endpoints"""
        print(f"\n🔍 Testing Database Consistency")
        
        if not self.merchant_orders:
            return
        
        # Get order count from merchant endpoint
        merchant_count = len(self.merchant_orders)
        
        # Try to get orders from different endpoints to compare
        endpoints_to_test = [
            "/orders",
            "/elite/admin/returns/orders",  # If this exists
        ]
        
        consistency_results = []
        
        for endpoint in endpoints_to_test:
            try:
                async with self.session.get(
                    f"{BACKEND_URL}{endpoint}",
                    headers=TEST_HEADERS
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        count = len(data.get("items", data if isinstance(data, list) else []))
                        consistency_results.append({
                            "endpoint": endpoint,
                            "count": count,
                            "success": True
                        })
                        print(f"   {endpoint}: {count} orders")
                    else:
                        consistency_results.append({
                            "endpoint": endpoint,
                            "count": 0,
                            "success": False,
                            "status": response.status
                        })
                        print(f"   {endpoint}: HTTP {response.status}")
                        
            except Exception as e:
                consistency_results.append({
                    "endpoint": endpoint,
                    "count": 0,
                    "success": False,
                    "error": str(e)
                })
                print(f"   {endpoint}: Exception - {str(e)}")
        
        # Check consistency
        successful_endpoints = [r for r in consistency_results if r['success']]
        if len(successful_endpoints) > 1:
            counts = [r['count'] for r in successful_endpoints]
            is_consistent = len(set(counts)) == 1
            
            self.log_test(
                "Database Consistency Check",
                is_consistent,
                f"Order counts: {counts} - {'Consistent' if is_consistent else 'Inconsistent'}"
            )
        else:
            self.log_test(
                "Database Consistency Check",
                False,
                "Not enough successful endpoints to compare"
            )
    
    async def run_comprehensive_debug(self):
        """Run all debug tests"""
        print(f"🚀 STARTING ORDER LOOKUP DEBUG FOR {TARGET_TENANT_ID}")
        print("=" * 80)
        
        # Test 1: Get merchant dashboard orders
        await self.test_merchant_dashboard_orders()
        
        # Test 2: Test customer portal lookup endpoints
        await self.test_customer_portal_lookup_endpoints()
        
        # Test 3: Test multiple orders for patterns
        await self.test_multiple_orders_lookup()
        
        # Test 4: Analyze data structure differences
        await self.analyze_data_structure_differences()
        
        # Test 5: Test database consistency
        await self.test_database_consistency()
        
        # Summary
        await self.print_debug_summary()
    
    async def print_debug_summary(self):
        """Print comprehensive debug summary"""
        print("\n" + "=" * 80)
        print("🎯 ORDER LOOKUP DEBUG SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n📋 KEY FINDINGS:")
        print(f"   - Merchant Dashboard Orders: {len(self.merchant_orders)} found")
        print(f"   - Portal Lookup Tests: {len(self.portal_lookup_results)} attempted")
        
        successful_portal_lookups = len([r for r in self.portal_lookup_results if r['success']])
        if self.portal_lookup_results:
            print(f"   - Portal Lookup Success Rate: {(successful_portal_lookups/len(self.portal_lookup_results))*100:.1f}%")
        
        if self.merchant_orders and len(self.merchant_orders) > 0:
            sample_order = self.merchant_orders[0]
            print(f"\n🔍 SAMPLE ORDER DATA:")
            print(f"   - Order Number: {sample_order.get('order_number', 'N/A')}")
            print(f"   - Customer Email: {sample_order.get('customer_email', 'N/A')}")
            print(f"   - Customer Name: {sample_order.get('customer_name', 'N/A')}")
            print(f"   - Total Price: {sample_order.get('total_price', 'N/A')}")
            print(f"   - Line Items: {len(sample_order.get('line_items', []))}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if failed_tests > 0:
            print(f"   - Investigate failed portal lookup endpoints")
            print(f"   - Check email field mapping consistency")
            print(f"   - Verify order number format matching")
            print(f"   - Ensure database query consistency across endpoints")
        else:
            print(f"   - All tests passed! Order lookup system appears to be working correctly.")

async def main():
    """Main test execution"""
    async with OrderLookupDebugSuite() as test_suite:
        await test_suite.run_comprehensive_debug()

if __name__ == "__main__":
    asyncio.run(main())