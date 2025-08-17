#!/usr/bin/env python3
"""
Elite Portal Returns Create API Fixed Test
Tests with corrected data format based on validation errors found
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ElitePortalFixedTest:
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
        if response_data and not success:
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
                    
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def test_with_valid_email(self):
        """Test Elite Portal Returns Create API with valid email"""
        print("\n🚀 Testing Elite Portal Returns Create API with Valid Email...")
        
        # Fixed data structure based on validation errors found
        create_return_data = {
            "order_id": "5813364687033",
            "customer_email": "shashankshekharofficial15@gmail.com",  # Valid email from the sample
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "gid://shopify/LineItem/13851721105593",  # String format
                "sku": "N/A",  # String instead of null
                "title": "TESTORDER",
                "variant_title": None,
                "quantity": 1,
                "unit_price": 400.0,
                "reason": "wrong_size",
                "condition": "used",
                "photos": [],
                "notes": ""
            }],
            "customer_note": "Selected resolution: refund"
        }
        
        print(f"📤 Testing with corrected data structure:")
        print(json.dumps(create_return_data, indent=2))
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", create_return_data)
        
        if success:
            self.log_test("Elite Portal Returns Create (Fixed)", True, "Return creation successful!")
            return response
        else:
            self.log_test("Elite Portal Returns Create (Fixed)", False, f"Status: {status}")
            
            # Analyze the error
            if status == 422:
                print("🔍 Validation Error Analysis:")
                if "detail" in response:
                    if isinstance(response["detail"], list):
                        for error in response["detail"]:
                            print(f"   • Field: {error.get('loc', 'unknown')}, Error: {error.get('msg', 'unknown')}")
                    else:
                        print(f"   • Error: {response['detail']}")
            elif status == 500:
                print("🔍 Server Error Analysis:")
                print(f"   • This indicates an implementation issue in the API")
                print(f"   • Error: {response.get('detail', 'Unknown server error')}")
            
            return None
    
    async def test_with_minimal_valid_data(self):
        """Test with minimal valid data structure"""
        print("\n🧪 Testing with Minimal Valid Data...")
        
        minimal_data = {
            "order_id": "5813364687033",
            "customer_email": "test@example.com",
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "new"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", minimal_data)
        
        if success:
            self.log_test("Minimal Valid Data Test", True, "Minimal data structure works")
        else:
            self.log_test("Minimal Valid Data Test", False, f"Status: {status}")
            if status == 500:
                print("🔍 Server Error - likely implementation issue in CQRS handlers")
    
    async def test_field_validation_edge_cases(self):
        """Test various field validation edge cases"""
        print("\n🔬 Testing Field Validation Edge Cases...")
        
        # Test 1: Invalid email format
        invalid_email_data = {
            "order_id": "5813364687033",
            "customer_email": "invalid-email",
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "new"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", invalid_email_data)
        
        if not success and status == 422:
            self.log_test("Invalid Email Validation", True, "Correctly rejected invalid email")
        else:
            self.log_test("Invalid Email Validation", False, "Should reject invalid email")
        
        # Test 2: Invalid return method
        invalid_method_data = {
            "order_id": "5813364687033",
            "customer_email": "test@example.com",
            "return_method": "invalid_method",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "new"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", invalid_method_data)
        
        if not success and status == 422:
            self.log_test("Invalid Return Method Validation", True, "Correctly rejected invalid return method")
        else:
            self.log_test("Invalid Return Method Validation", False, "Should reject invalid return method")
        
        # Test 3: Invalid condition
        invalid_condition_data = {
            "order_id": "5813364687033",
            "customer_email": "test@example.com",
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "invalid_condition"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", invalid_condition_data)
        
        if not success and status == 422:
            self.log_test("Invalid Condition Validation", True, "Correctly rejected invalid condition")
        else:
            self.log_test("Invalid Condition Validation", False, "Should reject invalid condition")
    
    async def test_missing_required_fields(self):
        """Test missing required fields"""
        print("\n📋 Testing Missing Required Fields...")
        
        # Test 1: Missing order_id
        missing_order_id = {
            "customer_email": "test@example.com",
            "return_method": "prepaid_label",
            "items": [{
                "line_item_id": "test-line-item-id",
                "sku": "TEST-SKU",
                "title": "Test Product",
                "quantity": 1,
                "unit_price": 100.0,
                "reason": "defective",
                "condition": "new"
            }]
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", missing_order_id)
        
        if not success and status == 422:
            self.log_test("Missing Order ID Validation", True, "Correctly rejected missing order_id")
        else:
            self.log_test("Missing Order ID Validation", False, "Should reject missing order_id")
        
        # Test 2: Empty items array
        empty_items = {
            "order_id": "5813364687033",
            "customer_email": "test@example.com",
            "return_method": "prepaid_label",
            "items": []
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/create", empty_items)
        
        if not success:
            self.log_test("Empty Items Validation", True, "Correctly rejected empty items")
        else:
            self.log_test("Empty Items Validation", False, "Should reject empty items")
    
    async def test_order_lookup_integration(self):
        """Test order lookup integration"""
        print("\n🔍 Testing Order Lookup Integration...")
        
        # Test the order lookup endpoint first
        lookup_data = {
            "order_number": "1001",
            "customer_email": "shashankshekharofficial15@gmail.com"
        }
        
        success, response, status = await self.make_request("POST", "/elite/portal/returns/lookup-order", lookup_data)
        
        if success:
            self.log_test("Order Lookup Integration", True, f"Mode: {response.get('mode', 'unknown')}")
            
            # If order lookup works, try to use the returned order data
            if response.get("order"):
                order_data = response["order"]
                print(f"   Found order: {order_data.get('order_number', 'Unknown')}")
        else:
            self.log_test("Order Lookup Integration", False, f"Status: {status}")
    
    async def run_fixed_tests(self):
        """Run all fixed tests for Elite Portal Returns Create API"""
        print("🚀 Starting Elite Portal Returns Create API Fixed Test")
        print("=" * 70)
        
        # Test with corrected data format
        await self.test_with_valid_email()
        
        # Test with minimal valid data
        await self.test_with_minimal_valid_data()
        
        # Test field validation
        await self.test_field_validation_edge_cases()
        
        # Test missing required fields
        await self.test_missing_required_fields()
        
        # Test order lookup integration
        await self.test_order_lookup_integration()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 ELITE PORTAL RETURNS CREATE API FIXED TEST SUMMARY")
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
        
        # Check for specific issues
        create_test = next((r for r in self.test_results if "Elite Portal Returns Create (Fixed)" in r["test"]), None)
        if create_test and create_test["success"]:
            print("   ✅ Elite Portal Returns Create API is working with correct data format")
        elif create_test:
            print("   ❌ Elite Portal Returns Create API still failing after data format fixes")
            print("   🔍 This indicates deeper implementation issues in CQRS handlers")
        
        validation_tests = [r for r in self.test_results if "Validation" in r["test"]]
        passed_validation = sum(1 for t in validation_tests if t["success"])
        
        if passed_validation == len(validation_tests):
            print("   ✅ All field validation is working correctly")
        else:
            print(f"   ⚠️ Some validation issues: {passed_validation}/{len(validation_tests)} passed")
        
        print("\n🔧 RECOMMENDATIONS:")
        if create_test and not create_test["success"]:
            print("   1. Check CQRS command handlers implementation")
            print("   2. Verify dependency container initialization")
            print("   3. Check domain entity validation")
            print("   4. Verify database connection and tenant isolation")
        else:
            print("   1. API is working correctly with proper data format")
            print("   2. Frontend should use the corrected data structure")

async def main():
    """Main test execution"""
    async with ElitePortalFixedTest() as test_suite:
        await test_suite.run_fixed_tests()

if __name__ == "__main__":
    asyncio.run(main())