#!/usr/bin/env python3
"""
Focused Exchange Feature Backend API Testing
Re-tests the Exchange Feature Backend APIs after return policy fix
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
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_MERCHANT_EMAIL = "merchant@rms34.com"
TEST_MERCHANT_PASSWORD = "merchant123"

class ExchangeFocusedTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.auth_token = None
        self.test_order = None
        self.test_exchange_id = None
        
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
            request_headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": TEST_TENANT_ID
            }
            
            # Add auth token if available
            if self.auth_token:
                request_headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Merge additional headers
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
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def authenticate_merchant(self):
        """Authenticate as merchant user for tenant-rms34"""
        print("\n🔐 Authenticating merchant user...")
        
        auth_data = {
            "email": TEST_MERCHANT_EMAIL,
            "password": TEST_MERCHANT_PASSWORD,
            "tenant_id": TEST_TENANT_ID
        }
        
        # Include X-Tenant-Id header for authentication
        success, response, status = await self.make_request("POST", "/users/login", auth_data)
        
        if success and response.get("access_token"):
            self.auth_token = response["access_token"]
            self.log_test("Authentication: Merchant login", True, f"Successfully authenticated as {TEST_MERCHANT_EMAIL}")
            return True
        else:
            self.log_test("Authentication: Merchant login", False, f"Failed to authenticate. Status: {status}, Response: {response}")
            return False
    
    async def verify_return_policy(self):
        """Verify return policy with exchange functionality exists"""
        print("\n🔍 Verifying return policy...")
        
        success, response, status = await self.make_request("GET", "/policies/")
        
        if success and response.get("policies"):
            policies = response["policies"]
            exchange_enabled_policies = [p for p in policies if p.get("exchange_settings", {}).get("enabled", False)]
            
            if exchange_enabled_policies:
                policy = exchange_enabled_policies[0]
                self.log_test("Return Policy: Exchange enabled policy exists", True, 
                             f"Found policy '{policy.get('name')}' with exchange enabled")
                return True
            else:
                self.log_test("Return Policy: Exchange enabled policy exists", False, 
                             f"No exchange-enabled policies found among {len(policies)} policies")
                return False
        else:
            self.log_test("Return Policy: Exchange enabled policy exists", False, 
                         f"Failed to get policies. Status: {status}")
            return False
    
    async def setup_test_data(self):
        """Setup test data for exchange testing"""
        print("\n🔧 Setting up test data...")
        
        # Get existing orders from tenant-rms34
        success, orders_data, status = await self.make_request("GET", "/orders?limit=5")
        
        if success and orders_data.get("items"):
            # Use first order from tenant data
            self.test_order = orders_data["items"][0]
            order_id = self.test_order.get('id', self.test_order.get('order_id'))
            self.log_test("Setup: Get test order", True, 
                         f"Using order {order_id} for testing")
            
            # Check if order has line items with product/variant IDs
            line_items = self.test_order.get("line_items", [])
            if line_items and line_items[0].get("product_id"):
                self.log_test("Setup: Order has product data", True, 
                             f"Order has {len(line_items)} line items with product data")
                return True
            else:
                self.log_test("Setup: Order has product data", False, 
                             "Order line items missing product_id/variant_id data")
                return False
        else:
            self.log_test("Setup: Get test order", False, f"No orders found for tenant-rms34. Status: {status}, Response: {orders_data}")
            return False
    
    async def test_exchange_create_request_fixed(self):
        """Test POST /api/exchange/create with the return policy fix"""
        print("\n📝 Testing Exchange Request Creation (Fixed)...")
        
        if not self.test_order:
            self.log_test("Exchange Create (Fixed): No test order", False)
            return
        
        line_items = self.test_order.get("line_items", [])
        if not line_items:
            self.log_test("Exchange Create (Fixed): No line items", False)
            return
        
        # Test 1: Valid exchange request (should now work with return policy)
        exchange_data = {
            "order_id": self.test_order.get("id", self.test_order.get("order_id")),
            "customer_email": self.test_order.get("customer_email", "test@example.com"),
            "items": [
                {
                    "original_line_item_id": str(line_items[0].get("id")),
                    "original_quantity": 1,
                    "reason": "wrong_size",
                    "notes": "Need larger size"
                }
            ],
            "customer_note": "Please process exchange quickly"
        }
        
        success, response, status = await self.make_request("POST", "/exchange/create", exchange_data)
        
        if success and response.get("success"):
            exchange_request = response.get("exchange_request", {})
            self.test_exchange_id = exchange_request.get("id")
            self.log_test("Exchange Create (Fixed): Valid request", True, 
                         f"Created exchange {self.test_exchange_id} - Return policy fix working!")
            
            # Validate response structure
            required_fields = ["id", "status", "message"]
            if all(field in exchange_request for field in required_fields):
                self.log_test("Exchange Create (Fixed): Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in exchange_request]
                self.log_test("Exchange Create (Fixed): Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Create (Fixed): Valid request", False, 
                         f"Status: {status}, Response: {response}")
            
            # Check if it's still the "No active return policy found" error
            if "No active return policy found" in str(response):
                self.log_test("Exchange Create (Fixed): Return policy issue", False, 
                             "Still getting 'No active return policy found' error - policy not properly created")
            elif "Exchanges are not enabled" in str(response):
                self.log_test("Exchange Create (Fixed): Exchange settings issue", False, 
                             "Return policy exists but exchange_settings.enabled is false")
    
    async def test_exchange_browse_products_with_real_data(self):
        """Test POST /api/exchange/browse-products with real Shopify data"""
        print("\n🛍️ Testing Exchange Browse Products (Real Data)...")
        
        # Test 1: Basic product search
        search_data = {
            "query": "",
            "limit": 10
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", search_data)
        
        if success and response.get("success"):
            products = response.get("products", [])
            self.log_test("Exchange Browse Products (Real): Basic search", True, 
                         f"Retrieved {len(products)} products from Shopify")
            
            if products:
                product = products[0]
                required_fields = ["id", "title", "variants", "available"]
                if all(field in product for field in required_fields):
                    self.log_test("Exchange Browse Products (Real): Response structure", True, 
                                 f"Product structure valid - {product.get('title', 'Unknown')}")
                    
                    # Check if variants have proper data
                    variants = product.get("variants", [])
                    if variants and variants[0].get("id"):
                        self.log_test("Exchange Browse Products (Real): Variant data", True, 
                                     f"Variants have proper IDs - {len(variants)} variants")
                    else:
                        self.log_test("Exchange Browse Products (Real): Variant data", False, 
                                     "Variants missing ID data")
                else:
                    missing = [f for f in required_fields if f not in product]
                    self.log_test("Exchange Browse Products (Real): Response structure", False, f"Missing fields: {missing}")
            else:
                self.log_test("Exchange Browse Products (Real): No products", False, 
                             "No products returned - check Shopify connection")
        else:
            self.log_test("Exchange Browse Products (Real): Basic search", False, 
                         f"Status: {status}, Response: {response}")
    
    async def test_exchange_status_tracking_fixed(self):
        """Test GET /api/exchange/{exchange_id}/status after successful creation"""
        print("\n📊 Testing Exchange Status Tracking (Fixed)...")
        
        if not self.test_exchange_id:
            self.log_test("Exchange Status (Fixed): No exchange ID", False, "Need to create exchange first")
            return
        
        # Test 1: Valid status request
        success, response, status = await self.make_request("GET", f"/exchange/{self.test_exchange_id}/status")
        
        if success and response.get("success"):
            exchange_request = response.get("exchange_request", {})
            self.log_test("Exchange Status (Fixed): Valid request", True, 
                         f"Retrieved status: {exchange_request.get('status')} for exchange {self.test_exchange_id}")
            
            # Validate response structure
            required_fields = ["id", "status", "tenant_id", "order_id", "customer_email", "created_at"]
            if all(field in exchange_request for field in required_fields):
                self.log_test("Exchange Status (Fixed): Response structure", True, "All required fields present")
                
                # Verify data integrity
                if (exchange_request.get("tenant_id") == TEST_TENANT_ID and 
                    exchange_request.get("id") == self.test_exchange_id):
                    self.log_test("Exchange Status (Fixed): Data integrity", True, "Exchange data is correct")
                else:
                    self.log_test("Exchange Status (Fixed): Data integrity", False, "Exchange data mismatch")
            else:
                missing = [f for f in required_fields if f not in exchange_request]
                self.log_test("Exchange Status (Fixed): Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Status (Fixed): Valid request", False, 
                         f"Status: {status}, Response: {response}")
    
    async def test_exchange_merchant_dashboard(self):
        """Test GET /api/exchange/ for merchant dashboard"""
        print("\n📋 Testing Exchange Merchant Dashboard...")
        
        success, response, status = await self.make_request("GET", "/exchange/")
        
        if success:
            exchanges = response.get("exchanges", [])
            self.log_test("Exchange Dashboard: List exchanges", True, 
                         f"Retrieved {len(exchanges)} exchanges")
            
            # If we have exchanges, validate structure
            if exchanges:
                exchange = exchanges[0]
                required_fields = ["id", "status", "order_id", "customer_email", "created_at"]
                if all(field in exchange for field in required_fields):
                    self.log_test("Exchange Dashboard: Response structure", True, "All required fields present")
                    
                    # Check pagination
                    pagination = response.get("pagination", {})
                    if pagination and "total" in pagination:
                        self.log_test("Exchange Dashboard: Pagination", True, 
                                     f"Pagination working - {pagination.get('total')} total exchanges")
                    else:
                        self.log_test("Exchange Dashboard: Pagination", False, "Pagination data missing")
                else:
                    missing = [f for f in required_fields if f not in exchange]
                    self.log_test("Exchange Dashboard: Response structure", False, f"Missing fields: {missing}")
            else:
                self.log_test("Exchange Dashboard: No exchanges", True, "No exchanges found (expected for new tenant)")
        else:
            self.log_test("Exchange Dashboard: List exchanges", False, 
                         f"Status: {status}, Response: {response}")
    
    async def test_database_integration_fixed(self):
        """Test database integration and data persistence after fixes"""
        print("\n🗄️ Testing Database Integration (Fixed)...")
        
        if not self.test_exchange_id:
            self.log_test("Database Integration (Fixed): No exchange to test", False)
            return
        
        # Test 1: Data persistence - retrieve created exchange
        success, response, status = await self.make_request("GET", f"/exchange/{self.test_exchange_id}/status")
        
        if success and response.get("success"):
            exchange_data = response.get("exchange_request", {})
            
            # Verify data integrity
            if (exchange_data.get("tenant_id") == TEST_TENANT_ID and 
                exchange_data.get("id") == self.test_exchange_id):
                self.log_test("Database Integration (Fixed): Data persistence", True, "Exchange data persisted correctly")
            else:
                self.log_test("Database Integration (Fixed): Data persistence", False, "Exchange data integrity issues")
            
            # Verify tenant isolation in database
            if exchange_data.get("tenant_id") == TEST_TENANT_ID:
                self.log_test("Database Integration (Fixed): Tenant isolation", True, "Tenant isolation maintained in database")
            else:
                self.log_test("Database Integration (Fixed): Tenant isolation", False, "Tenant isolation not maintained")
            
            # Verify exchange collection structure
            required_db_fields = ["id", "tenant_id", "order_id", "customer_email", "items", "status", "created_at"]
            if all(field in exchange_data for field in required_db_fields):
                self.log_test("Database Integration (Fixed): Collection structure", True, "Exchange collection has all required fields")
            else:
                missing = [f for f in required_db_fields if f not in exchange_data]
                self.log_test("Database Integration (Fixed): Collection structure", False, f"Missing DB fields: {missing}")
        else:
            self.log_test("Database Integration (Fixed): Data persistence", False, "Failed to retrieve persisted exchange")
    
    async def run_focused_tests(self):
        """Run focused exchange feature tests after return policy fix"""
        print("🚀 Starting Focused Exchange Feature Backend API Testing")
        print("🎯 Focus: Testing after return policy with exchange functionality created")
        print("=" * 70)
        
        # Authentication
        if not await self.authenticate_merchant():
            print("❌ Failed to authenticate. Cannot proceed with tests.")
            return
        
        # Verify return policy
        await self.verify_return_policy()
        
        # Setup
        if not await self.setup_test_data():
            print("❌ Failed to setup test data. Some tests may fail.")
        
        # Run focused test suites
        await self.test_exchange_create_request_fixed()
        await self.test_exchange_status_tracking_fixed()
        await self.test_exchange_browse_products_with_real_data()
        await self.test_exchange_merchant_dashboard()
        await self.test_database_integration_fixed()
        
        # Summary
        self.print_focused_summary()
    
    def print_focused_summary(self):
        """Print focused test summary"""
        print("\n" + "=" * 70)
        print("📊 FOCUSED EXCHANGE FEATURE TESTING SUMMARY")
        print("🎯 After Return Policy Fix")
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
        
        print("\n🎯 KEY IMPROVEMENTS:")
        
        # Check for critical improvements
        exchange_create_tests = [r for r in self.test_results if "Exchange Create (Fixed)" in r["test"]]
        if exchange_create_tests and all(t["success"] for t in exchange_create_tests):
            print("   ✅ Exchange creation now working - Return policy fix successful!")
        elif exchange_create_tests:
            print("   ❌ Exchange creation still failing - Return policy fix incomplete")
        
        # Check for return policy verification
        policy_tests = [r for r in self.test_results if "Return Policy" in r["test"]]
        if policy_tests and all(t["success"] for t in policy_tests):
            print("   ✅ Return policy with exchange functionality verified")
        elif policy_tests:
            print("   ❌ Return policy issues detected")
        
        # Check for database integration
        db_tests = [r for r in self.test_results if "Database Integration (Fixed)" in r["test"]]
        if db_tests and all(t["success"] for t in db_tests):
            print("   ✅ Database integration working correctly")
        elif db_tests:
            print("   ⚠️ Some database integration issues")
        
        print(f"\n🏁 CONCLUSION:")
        if passed_tests / total_tests >= 0.9:
            print("   🎉 Exchange feature is now fully functional after return policy fix!")
        elif passed_tests / total_tests >= 0.7:
            print("   ⚠️ Exchange feature significantly improved but needs minor fixes")
        else:
            print("   ❌ Exchange feature still needs work despite return policy fix")
        
        # Compare with previous results
        print(f"\n📈 IMPROVEMENT ANALYSIS:")
        print("   Previous success rate: ~50% (mentioned in review request)")
        print(f"   Current success rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests / total_tests > 0.5:
            improvement = (passed_tests/total_tests - 0.5) * 100
            print(f"   📈 Improvement: +{improvement:.1f}% success rate")
        else:
            decline = (0.5 - passed_tests/total_tests) * 100
            print(f"   📉 Decline: -{decline:.1f}% success rate")


async def main():
    """Main test runner"""
    async with ExchangeFocusedTestSuite() as test_suite:
        await test_suite.run_focused_tests()


if __name__ == "__main__":
    asyncio.run(main())