#!/usr/bin/env python3
"""
Focused test for the fixed orders endpoint
Tests GET /api/orders with tenant-rms34 to verify frontend API compatibility fix
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://1ce8ef7a-c16d-43a6-b3d4-da8a63312de8.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class OrdersEndpointTest:
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
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_orders_endpoint_basic(self):
        """Test basic GET /api/orders endpoint functionality"""
        try:
            async with self.session.get(f"{BACKEND_URL}/orders", headers=TEST_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Orders Endpoint Basic Access", 
                        True, 
                        f"Status: {response.status}, Response type: {type(data)}"
                    )
                    return data
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Orders Endpoint Basic Access", 
                        False, 
                        f"Status: {response.status}, Error: {error_text}"
                    )
                    return None
        except Exception as e:
            self.log_test("Orders Endpoint Basic Access", False, f"Exception: {str(e)}")
            return None
    
    async def test_orders_response_structure(self, orders_data):
        """Test that response has proper pagination structure with 'items' array"""
        if not orders_data:
            self.log_test("Orders Response Structure", False, "No orders data to test")
            return False
        
        # Check for 'items' array
        has_items = 'items' in orders_data
        if not has_items:
            self.log_test(
                "Orders Response Structure - Items Array", 
                False, 
                f"Missing 'items' array. Keys found: {list(orders_data.keys())}"
            )
            return False
        
        # Check for pagination structure
        has_pagination = 'pagination' in orders_data
        if not has_pagination:
            self.log_test(
                "Orders Response Structure - Pagination", 
                False, 
                f"Missing 'pagination' object. Keys found: {list(orders_data.keys())}"
            )
            return False
        
        pagination = orders_data['pagination']
        required_pagination_fields = ['current_page', 'total_pages', 'total_count', 'per_page', 'has_next', 'has_prev']
        missing_fields = [field for field in required_pagination_fields if field not in pagination]
        
        if missing_fields:
            self.log_test(
                "Orders Response Structure - Pagination Fields", 
                False, 
                f"Missing pagination fields: {missing_fields}"
            )
            return False
        
        self.log_test(
            "Orders Response Structure", 
            True, 
            f"Has items array with {len(orders_data['items'])} orders, complete pagination structure"
        )
        return True
    
    async def test_order_1001_presence(self, orders_data):
        """Test if order #1001 is included in the response"""
        if not orders_data or 'items' not in orders_data:
            self.log_test("Order #1001 Presence", False, "No orders data to search")
            return False
        
        orders = orders_data['items']
        order_1001_found = False
        order_1001_data = None
        
        # Search for order #1001 by order_number or name
        for order in orders:
            order_number = order.get('order_number', order.get('name', ''))
            if order_number == '1001' or order_number == '#1001':
                order_1001_found = True
                order_1001_data = order
                break
        
        if order_1001_found:
            self.log_test(
                "Order #1001 Presence", 
                True, 
                f"Order #1001 found with ID: {order_1001_data.get('id', 'N/A')}"
            )
            return order_1001_data
        else:
            # List available order numbers for debugging
            available_orders = [order.get('order_number', order.get('name', 'N/A')) for order in orders]
            self.log_test(
                "Order #1001 Presence", 
                False, 
                f"Order #1001 not found. Available orders: {available_orders[:10]}"  # Show first 10
            )
            return None
    
    async def test_required_fields_presence(self, orders_data):
        """Test that all required fields are present in order objects"""
        if not orders_data or 'items' not in orders_data:
            self.log_test("Required Fields Presence", False, "No orders data to test")
            return False
        
        orders = orders_data['items']
        if not orders:
            self.log_test("Required Fields Presence", False, "No orders in items array")
            return False
        
        # Required fields for frontend compatibility
        required_fields = [
            'id',  # or order_id
            'customer_name', 
            'financial_status', 
            'order_number',  # or name
            'customer_email',  # or email
            'total_price',
            'created_at'
        ]
        
        # Test first order for required fields
        test_order = orders[0]
        missing_fields = []
        present_fields = []
        
        for field in required_fields:
            # Check for alternative field names
            if field == 'id' and ('id' in test_order or 'order_id' in test_order):
                present_fields.append(field)
            elif field == 'order_number' and ('order_number' in test_order or 'name' in test_order):
                present_fields.append(field)
            elif field == 'customer_email' and ('customer_email' in test_order or 'email' in test_order):
                present_fields.append(field)
            elif field in test_order:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        if missing_fields:
            available_fields = list(test_order.keys())
            self.log_test(
                "Required Fields Presence", 
                False, 
                f"Missing fields: {missing_fields}. Available fields: {available_fields}"
            )
            return False
        else:
            self.log_test(
                "Required Fields Presence", 
                True, 
                f"All required fields present: {present_fields}"
            )
            return True
    
    async def test_order_data_quality(self, orders_data):
        """Test the quality and validity of order data"""
        if not orders_data or 'items' not in orders_data:
            self.log_test("Order Data Quality", False, "No orders data to test")
            return False
        
        orders = orders_data['items']
        if not orders:
            self.log_test("Order Data Quality", False, "No orders in items array")
            return False
        
        # Test data quality on first few orders
        test_orders = orders[:3]  # Test first 3 orders
        quality_issues = []
        
        for i, order in enumerate(test_orders):
            # Check for non-empty customer_name
            customer_name = order.get('customer_name', '')
            if not customer_name or customer_name.strip() == '':
                quality_issues.append(f"Order {i+1}: Empty customer_name")
            
            # Check for valid financial_status
            financial_status = order.get('financial_status', '')
            valid_statuses = ['paid', 'pending', 'authorized', 'partially_paid', 'refunded', 'voided']
            if financial_status not in valid_statuses:
                quality_issues.append(f"Order {i+1}: Invalid financial_status '{financial_status}'")
            
            # Check for valid total_price
            total_price = order.get('total_price')
            if total_price is None or (isinstance(total_price, str) and not total_price.replace('.', '').isdigit()):
                quality_issues.append(f"Order {i+1}: Invalid total_price '{total_price}'")
        
        if quality_issues:
            self.log_test(
                "Order Data Quality", 
                False, 
                f"Data quality issues found: {quality_issues}"
            )
            return False
        else:
            self.log_test(
                "Order Data Quality", 
                True, 
                f"Data quality good for {len(test_orders)} tested orders"
            )
            return True
    
    async def run_all_tests(self):
        """Run all tests for the orders endpoint"""
        print(f"\n🚀 TESTING ORDERS ENDPOINT FIX FOR TENANT: {TEST_TENANT_ID}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test 1: Basic endpoint access
        orders_data = await self.test_orders_endpoint_basic()
        
        if orders_data:
            # Test 2: Response structure
            await self.test_orders_response_structure(orders_data)
            
            # Test 3: Order #1001 presence
            await self.test_order_1001_presence(orders_data)
            
            # Test 4: Required fields presence
            await self.test_required_fields_presence(orders_data)
            
            # Test 5: Data quality
            await self.test_order_data_quality(orders_data)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed_tests == total_tests

async def main():
    """Main test execution"""
    async with OrdersEndpointTest() as test_suite:
        success = await test_suite.run_all_tests()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)