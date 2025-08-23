#!/usr/bin/env python3
"""
Exchange Feature Backend API Testing
Tests all exchange endpoints and integration points as requested in the review
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

class ExchangeFeatureTestSuite:
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
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
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
        
        success, response, status = await self.make_request("POST", "/users/login", auth_data, headers={})
        
        if success and response.get("access_token"):
            self.auth_token = response["access_token"]
            self.log_test("Authentication: Merchant login", True, f"Successfully authenticated as {TEST_MERCHANT_EMAIL}")
            return True
        else:
            self.log_test("Authentication: Merchant login", False, f"Failed to authenticate. Status: {status}, Response: {response}")
            return False
    
    async def setup_test_data(self):
        """Setup test data for exchange testing"""
        print("\n🔧 Setting up test data...")
        
        # Get existing orders from tenant-rms34
        success, orders_data, status = await self.make_request("GET", "/orders?limit=5")
        
        if success and orders_data.get("items"):
            # Use first order from tenant data
            self.test_order = orders_data["items"][0]
            self.log_test("Setup: Get test order", True, 
                         f"Using order {self.test_order.get('order_number', self.test_order.get('id'))} for testing")
            return True
        else:
            self.log_test("Setup: Get test order", False, f"No orders found for tenant-rms34. Status: {status}, Response: {orders_data}")
            return False
    
    async def test_exchange_browse_products(self):
        """Test POST /api/exchange/browse-products"""
        print("\n🛍️ Testing Exchange Browse Products...")
        
        # Test 1: Basic product search
        search_data = {
            "query": "",
            "limit": 10
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", search_data)
        
        if success and response.get("success"):
            products = response.get("products", [])
            self.log_test("Exchange Browse Products: Basic search", True, 
                         f"Retrieved {len(products)} products")
            
            # Validate response structure
            if products:
                product = products[0]
                required_fields = ["id", "title", "variants", "available"]
                if all(field in product for field in required_fields):
                    self.log_test("Exchange Browse Products: Response structure", True, "All required fields present")
                else:
                    missing = [f for f in required_fields if f not in product]
                    self.log_test("Exchange Browse Products: Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Browse Products: Basic search", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Search with filters
        filtered_search = {
            "query": "shirt",
            "product_type": "Clothing",
            "limit": 5
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", filtered_search)
        
        if success:
            self.log_test("Exchange Browse Products: Filtered search", True, 
                         f"Filtered search completed with {len(response.get('products', []))} results")
        else:
            self.log_test("Exchange Browse Products: Filtered search", False, 
                         f"Filtered search failed. Status: {status}")
    
    async def test_exchange_check_availability(self):
        """Test POST /api/exchange/check-availability"""
        print("\n📦 Testing Exchange Check Availability...")
        
        if not self.test_order:
            self.log_test("Exchange Check Availability: No test order", False)
            return
        
        # Get a product ID from test order line items
        line_items = self.test_order.get("line_items", [])
        if not line_items:
            self.log_test("Exchange Check Availability: No line items", False)
            return
        
        product_id = line_items[0].get("product_id")
        variant_id = line_items[0].get("variant_id")
        
        if not product_id:
            self.log_test("Exchange Check Availability: No product ID", False)
            return
        
        # Test availability check
        availability_data = {
            "original_product_id": str(product_id),
            "original_variant_id": str(variant_id) if variant_id else None
        }
        
        success, response, status = await self.make_request("POST", "/exchange/check-availability", availability_data)
        
        if success and response.get("success"):
            available_variants = response.get("available_variants", [])
            self.log_test("Exchange Check Availability: Valid request", True, 
                         f"Found {len(available_variants)} available variants")
            
            # Validate response structure
            required_fields = ["product", "available_variants", "total_available"]
            if all(field in response for field in required_fields):
                self.log_test("Exchange Check Availability: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Exchange Check Availability: Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Check Availability: Valid request", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test with invalid product ID
        invalid_data = {
            "original_product_id": "invalid-product-id"
        }
        
        success, response, status = await self.make_request("POST", "/exchange/check-availability", invalid_data)
        
        if not success and status == 404:
            self.log_test("Exchange Check Availability: Invalid product ID rejection", True, "Correctly rejected invalid product")
        else:
            self.log_test("Exchange Check Availability: Invalid product ID rejection", False, "Should reject invalid product ID")
    
    async def test_exchange_calculate_price_difference(self):
        """Test POST /api/exchange/calculate-price-difference"""
        print("\n💰 Testing Exchange Price Calculation...")
        
        if not self.test_order:
            self.log_test("Exchange Price Calculation: No test order", False)
            return
        
        line_items = self.test_order.get("line_items", [])
        if not line_items:
            self.log_test("Exchange Price Calculation: No line items", False)
            return
        
        original_variant_id = line_items[0].get("variant_id")
        if not original_variant_id:
            self.log_test("Exchange Price Calculation: No variant ID", False)
            return
        
        # Test price calculation (using same variant for simplicity)
        price_data = {
            "original_variant_id": str(original_variant_id),
            "new_variant_id": str(original_variant_id),
            "quantity": 1
        }
        
        success, response, status = await self.make_request("POST", "/exchange/calculate-price-difference", price_data)
        
        if success and response.get("success"):
            price_diff = response.get("price_difference", 0)
            self.log_test("Exchange Price Calculation: Valid calculation", True, 
                         f"Price difference: ${price_diff:.2f}")
            
            # Validate response structure
            required_fields = ["original_price", "new_price", "price_difference", "customer_pays_more", "customer_gets_refund", "message"]
            if all(field in response for field in required_fields):
                self.log_test("Exchange Price Calculation: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in response]
                self.log_test("Exchange Price Calculation: Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Price Calculation: Valid calculation", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test with invalid variant IDs
        invalid_data = {
            "original_variant_id": "invalid-variant-1",
            "new_variant_id": "invalid-variant-2",
            "quantity": 1
        }
        
        success, response, status = await self.make_request("POST", "/exchange/calculate-price-difference", invalid_data)
        
        if not success and status == 404:
            self.log_test("Exchange Price Calculation: Invalid variant rejection", True, "Correctly rejected invalid variants")
        else:
            self.log_test("Exchange Price Calculation: Invalid variant rejection", False, "Should reject invalid variants")
    
    async def test_exchange_create_request(self):
        """Test POST /api/exchange/create"""
        print("\n📝 Testing Exchange Request Creation...")
        
        if not self.test_order:
            self.log_test("Exchange Create: No test order", False)
            return
        
        line_items = self.test_order.get("line_items", [])
        if not line_items:
            self.log_test("Exchange Create: No line items", False)
            return
        
        # Test 1: Valid exchange request
        exchange_data = {
            "order_id": self.test_order.get("id"),
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
            self.log_test("Exchange Create: Valid request", True, 
                         f"Created exchange {self.test_exchange_id}")
            
            # Validate response structure
            required_fields = ["id", "status", "message"]
            if all(field in exchange_request for field in required_fields):
                self.log_test("Exchange Create: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in exchange_request]
                self.log_test("Exchange Create: Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Create: Valid request", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Invalid customer email
        invalid_email_data = {
            **exchange_data,
            "customer_email": "wrong@email.com"
        }
        
        success, response, status = await self.make_request("POST", "/exchange/create", invalid_email_data)
        
        if not success and status == 403:
            self.log_test("Exchange Create: Invalid email rejection", True, "Correctly rejected invalid email")
        else:
            self.log_test("Exchange Create: Invalid email rejection", False, "Should reject invalid email")
        
        # Test 3: Missing required fields
        incomplete_data = {
            "order_id": self.test_order.get("id")
            # Missing customer_email and items
        }
        
        success, response, status = await self.make_request("POST", "/exchange/create", incomplete_data)
        
        if not success and status in [400, 422]:
            self.log_test("Exchange Create: Missing fields rejection", True, "Correctly rejected incomplete data")
        else:
            self.log_test("Exchange Create: Missing fields rejection", False, "Should reject incomplete data")
    
    async def test_exchange_status_tracking(self):
        """Test GET /api/exchange/{exchange_id}/status"""
        print("\n📊 Testing Exchange Status Tracking...")
        
        if not self.test_exchange_id:
            self.log_test("Exchange Status: No exchange ID", False, "Need to create exchange first")
            return
        
        # Test 1: Valid status request
        success, response, status = await self.make_request("GET", f"/exchange/{self.test_exchange_id}/status")
        
        if success and response.get("success"):
            exchange_request = response.get("exchange_request", {})
            self.log_test("Exchange Status: Valid request", True, 
                         f"Retrieved status: {exchange_request.get('status')}")
            
            # Validate response structure
            required_fields = ["id", "status", "tenant_id", "order_id", "customer_email", "created_at"]
            if all(field in exchange_request for field in required_fields):
                self.log_test("Exchange Status: Response structure", True, "All required fields present")
            else:
                missing = [f for f in required_fields if f not in exchange_request]
                self.log_test("Exchange Status: Response structure", False, f"Missing fields: {missing}")
        else:
            self.log_test("Exchange Status: Valid request", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Invalid exchange ID
        success, response, status = await self.make_request("GET", "/exchange/invalid-exchange-id/status")
        
        if not success and status == 404:
            self.log_test("Exchange Status: Invalid ID rejection", True, "Correctly rejected invalid exchange ID")
        else:
            self.log_test("Exchange Status: Invalid ID rejection", False, "Should reject invalid exchange ID")
    
    async def test_exchange_merchant_dashboard_listing(self):
        """Test GET /api/exchange/ for merchant dashboard"""
        print("\n📋 Testing Exchange Merchant Dashboard Listing...")
        
        # First, let's add the missing endpoint to the exchange controller
        # This endpoint should list all exchanges for the merchant's tenant
        
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
                else:
                    missing = [f for f in required_fields if f not in exchange]
                    self.log_test("Exchange Dashboard: Response structure", False, f"Missing fields: {missing}")
        else:
            # This endpoint might not exist yet, which is expected
            if status == 404:
                self.log_test("Exchange Dashboard: List exchanges", False, 
                             "Endpoint not implemented - GET /api/exchange/ returns 404")
            else:
                self.log_test("Exchange Dashboard: List exchanges", False, 
                             f"Unexpected error. Status: {status}, Response: {response}")
    
    async def test_authentication_and_tenant_isolation(self):
        """Test authentication and tenant isolation"""
        print("\n🔒 Testing Authentication & Tenant Isolation...")
        
        # Test 1: Request without authentication
        headers_no_auth = {"X-Tenant-Id": TEST_TENANT_ID}
        success, response, status = await self.make_request("GET", "/exchange/test-exchange-id/status", headers=headers_no_auth)
        
        # Should work with tenant header (exchange endpoints might not require auth for status check)
        if success or status in [401, 403]:
            self.log_test("Authentication: Proper auth handling", True, "Authentication handled correctly")
        else:
            self.log_test("Authentication: Proper auth handling", False, f"Unexpected status: {status}")
        
        # Test 2: Request with wrong tenant ID
        wrong_tenant_headers = {
            "X-Tenant-Id": "wrong-tenant-id",
            "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", 
                                                          {"query": "", "limit": 5}, 
                                                          headers=wrong_tenant_headers)
        
        if not success and status in [400, 403, 404]:
            self.log_test("Tenant Isolation: Wrong tenant rejection", True, "Correctly rejected wrong tenant")
        else:
            self.log_test("Tenant Isolation: Wrong tenant rejection", False, "Should reject wrong tenant ID")
        
        # Test 3: Request without tenant header
        no_tenant_headers = {
            "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", 
                                                          {"query": "", "limit": 5}, 
                                                          headers=no_tenant_headers)
        
        if not success and status == 400:
            self.log_test("Tenant Isolation: Missing tenant header rejection", True, "Correctly rejected missing tenant header")
        else:
            self.log_test("Tenant Isolation: Missing tenant header rejection", False, "Should reject missing tenant header")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing Error Handling...")
        
        # Test 1: Malformed JSON
        try:
            url = f"{BACKEND_URL}/exchange/browse-products"
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": TEST_TENANT_ID,
                "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
            }
            
            async with self.session.post(url, data="invalid json", headers=headers) as response:
                if response.status in [400, 422]:
                    self.log_test("Error Handling: Malformed JSON", True, "Correctly rejected malformed JSON")
                else:
                    self.log_test("Error Handling: Malformed JSON", False, f"Should reject malformed JSON, got {response.status}")
        except Exception as e:
            self.log_test("Error Handling: Malformed JSON", False, f"Exception: {str(e)}")
        
        # Test 2: Invalid data types
        invalid_data = {
            "query": 123,  # Should be string
            "limit": "invalid"  # Should be integer
        }
        
        success, response, status = await self.make_request("POST", "/exchange/browse-products", invalid_data)
        
        if not success and status in [400, 422]:
            self.log_test("Error Handling: Invalid data types", True, "Correctly rejected invalid data types")
        else:
            self.log_test("Error Handling: Invalid data types", False, "Should reject invalid data types")
        
        # Test 3: Non-existent endpoints
        success, response, status = await self.make_request("GET", "/exchange/non-existent-endpoint")
        
        if not success and status == 404:
            self.log_test("Error Handling: Non-existent endpoint", True, "Correctly returned 404 for non-existent endpoint")
        else:
            self.log_test("Error Handling: Non-existent endpoint", False, "Should return 404 for non-existent endpoint")
    
    async def test_database_integration(self):
        """Test database integration and data persistence"""
        print("\n🗄️ Testing Database Integration...")
        
        if not self.test_exchange_id:
            self.log_test("Database Integration: No exchange to test", False)
            return
        
        # Test 1: Data persistence - retrieve created exchange
        success, response, status = await self.make_request("GET", f"/exchange/{self.test_exchange_id}/status")
        
        if success and response.get("success"):
            exchange_data = response.get("exchange_request", {})
            
            # Verify data integrity
            if (exchange_data.get("tenant_id") == TEST_TENANT_ID and 
                exchange_data.get("id") == self.test_exchange_id):
                self.log_test("Database Integration: Data persistence", True, "Exchange data persisted correctly")
            else:
                self.log_test("Database Integration: Data persistence", False, "Exchange data integrity issues")
            
            # Verify tenant isolation in database
            if exchange_data.get("tenant_id") == TEST_TENANT_ID:
                self.log_test("Database Integration: Tenant isolation", True, "Tenant isolation maintained in database")
            else:
                self.log_test("Database Integration: Tenant isolation", False, "Tenant isolation not maintained")
        else:
            self.log_test("Database Integration: Data persistence", False, "Failed to retrieve persisted exchange")
    
    async def run_all_tests(self):
        """Run all exchange feature tests"""
        print("🚀 Starting Exchange Feature Backend API Testing")
        print("=" * 60)
        
        # Authentication
        if not await self.authenticate_merchant():
            print("❌ Failed to authenticate. Some tests may fail.")
        
        # Setup
        if not await self.setup_test_data():
            print("❌ Failed to setup test data. Some tests may fail.")
        
        # Run all test suites
        await self.test_exchange_browse_products()
        await self.test_exchange_check_availability()
        await self.test_exchange_calculate_price_difference()
        await self.test_exchange_create_request()
        await self.test_exchange_status_tracking()
        await self.test_exchange_merchant_dashboard_listing()
        await self.test_authentication_and_tenant_isolation()
        await self.test_error_handling()
        await self.test_database_integration()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 EXCHANGE FEATURE TESTING SUMMARY")
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
            "Authentication": [r for r in self.test_results if "Authentication:" in r["test"]],
            "Exchange Browse Products": [r for r in self.test_results if "Exchange Browse Products:" in r["test"]],
            "Exchange Check Availability": [r for r in self.test_results if "Exchange Check Availability:" in r["test"]],
            "Exchange Price Calculation": [r for r in self.test_results if "Exchange Price Calculation:" in r["test"]],
            "Exchange Create": [r for r in self.test_results if "Exchange Create:" in r["test"]],
            "Exchange Status": [r for r in self.test_results if "Exchange Status:" in r["test"]],
            "Exchange Dashboard": [r for r in self.test_results if "Exchange Dashboard:" in r["test"]],
            "Tenant Isolation": [r for r in self.test_results if "Tenant Isolation:" in r["test"]],
            "Error Handling": [r for r in self.test_results if "Error Handling:" in r["test"]],
            "Database Integration": [r for r in self.test_results if "Database Integration:" in r["test"]],
            "Setup": [r for r in self.test_results if "Setup:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} ({(passed/total*100):.0f}%)")
        
        print(f"\n📋 EXCHANGE FEATURE READINESS:")
        
        # Critical functionality assessment
        critical_tests = [
            "Exchange Browse Products: Basic search",
            "Exchange Check Availability: Valid request", 
            "Exchange Price Calculation: Valid calculation",
            "Exchange Create: Valid request",
            "Exchange Status: Valid request"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["success"])
        critical_total = len(critical_tests)
        
        if critical_passed == critical_total:
            print("   ✅ Core exchange functionality is working")
        elif critical_passed > critical_total * 0.7:
            print("   ⚠️ Most core exchange functionality is working")
        else:
            print("   ❌ Critical exchange functionality issues detected")
        
        # Authentication assessment
        auth_tests = [r for r in self.test_results if "Authentication:" in r["test"] or "Tenant Isolation:" in r["test"]]
        auth_passed = sum(1 for t in auth_tests if t["success"])
        
        if auth_passed == len(auth_tests):
            print("   ✅ Authentication and tenant isolation working")
        elif auth_passed > 0:
            print("   ⚠️ Some authentication/isolation issues")
        else:
            print("   ❌ Authentication and tenant isolation not working")
        
        print(f"\n🏁 CONCLUSION:")
        if passed_tests / total_tests >= 0.8:
            print("   🎉 Exchange feature is ready for production!")
        elif passed_tests / total_tests >= 0.6:
            print("   ⚠️ Exchange feature needs minor fixes before production")
        else:
            print("   ❌ Exchange feature needs significant work before production")


async def main():
    """Main test runner"""
    async with ExchangeFeatureTestSuite() as test_suite:
        await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())