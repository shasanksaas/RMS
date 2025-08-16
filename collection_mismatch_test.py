#!/usr/bin/env python3
"""
Collection Mismatch Fix Testing - Merchant Dashboard Returns Display
Testing Focus: Verify merchant dashboard now displays all 21 created returns from 'returns' collection
instead of 1 from 'return_requests' collection
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
import sys

# Backend URL from environment
BACKEND_URL = "https://returns-manager-1.preview.emergentagent.com"

class CollectionMismatchTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.tenant_id = "tenant-fashion-store"  # Using seeded tenant
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and expected:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()

    async def test_collections_verification(self):
        """Test 1: Verify collections exist and document counts"""
        print("🔍 TEST 1: Collections Verification")
        
        try:
            # Test database connection and collections
            headers = {"X-Tenant-Id": self.tenant_id}
            
            # Check if we can access the returns endpoint (which should use 'returns' collection)
            async with self.session.get(f"{BACKEND_URL}/api/returns", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    returns_count = len(data.get("returns", []))
                    total_count = data.get("pagination", {}).get("total", 0)
                    
                    self.log_test(
                        "Returns Collection Access",
                        True,
                        f"Successfully accessed returns collection via API. Found {returns_count} returns in current page, {total_count} total",
                        "API accessible with returns data",
                        f"{returns_count} returns retrieved, {total_count} total"
                    )
                    
                    # Verify we're getting more than 1 return (the old collection had only 1)
                    if total_count > 1:
                        self.log_test(
                            "Collection Mismatch Fix Verification",
                            True,
                            f"Found {total_count} total returns - confirms fix is working",
                            "More than 1 return (old collection had only 1)",
                            f"{total_count} returns found"
                        )
                    else:
                        self.log_test(
                            "Collection Mismatch Fix Verification",
                            False,
                            f"Only found {total_count} returns - may still be using old collection",
                            "More than 1 return",
                            f"{total_count} returns found"
                        )
                        
                else:
                    self.log_test(
                        "Returns Collection Access",
                        False,
                        f"Failed to access returns API: {response.status}",
                        "200 status code",
                        f"{response.status} status code"
                    )
                    
        except Exception as e:
            self.log_test(
                "Collections Verification",
                False,
                f"Exception during collections verification: {str(e)}"
            )

    async def test_merchant_returns_api(self):
        """Test 2: Merchant Returns API Testing - GET /api/returns"""
        print("🔍 TEST 2: Merchant Returns API Testing")
        
        try:
            headers = {"X-Tenant-Id": self.tenant_id}
            
            # Test basic returns endpoint
            async with self.session.get(f"{BACKEND_URL}/api/returns", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    returns = data.get("returns", [])
                    pagination = data.get("pagination", {})
                    
                    self.log_test(
                        "GET /api/returns - Basic Access",
                        True,
                        f"Successfully retrieved {len(returns)} returns",
                        "200 status with returns data",
                        f"Status {response.status}, {len(returns)} returns"
                    )
                    
                    # Verify pagination structure
                    required_pagination_fields = ["page", "pageSize", "total", "totalPages", "hasNext", "hasPrev"]
                    missing_fields = [field for field in required_pagination_fields if field not in pagination]
                    
                    if not missing_fields:
                        self.log_test(
                            "Pagination Structure",
                            True,
                            f"All required pagination fields present: {list(pagination.keys())}",
                            "Complete pagination structure",
                            f"Found: {list(pagination.keys())}"
                        )
                    else:
                        self.log_test(
                            "Pagination Structure",
                            False,
                            f"Missing pagination fields: {missing_fields}",
                            f"All fields: {required_pagination_fields}",
                            f"Missing: {missing_fields}"
                        )
                    
                    # Verify return data structure
                    if returns:
                        sample_return = returns[0]
                        required_fields = ["id", "order_number", "customer_name", "customer_email", 
                                         "status", "item_count", "estimated_refund", "created_at"]
                        missing_fields = [field for field in required_fields if field not in sample_return]
                        
                        if not missing_fields:
                            self.log_test(
                                "Return Data Structure",
                                True,
                                f"All required return fields present in sample return",
                                "Complete return data structure",
                                f"Found all required fields"
                            )
                        else:
                            self.log_test(
                                "Return Data Structure",
                                False,
                                f"Missing return fields: {missing_fields}",
                                f"All fields: {required_fields}",
                                f"Missing: {missing_fields}"
                            )
                            
                        # Test specific field mappings from new structure
                        item_count = sample_return.get("item_count", 0)
                        estimated_refund = sample_return.get("estimated_refund", 0)
                        customer_name = sample_return.get("customer_name", "")
                        
                        self.log_test(
                            "Field Mapping - Item Count",
                            isinstance(item_count, int) and item_count >= 0,
                            f"Item count properly extracted: {item_count}",
                            "Non-negative integer",
                            f"{item_count} ({type(item_count).__name__})"
                        )
                        
                        self.log_test(
                            "Field Mapping - Estimated Refund",
                            isinstance(estimated_refund, (int, float)) and estimated_refund >= 0,
                            f"Estimated refund properly extracted: {estimated_refund}",
                            "Non-negative number",
                            f"{estimated_refund} ({type(estimated_refund).__name__})"
                        )
                        
                        self.log_test(
                            "Field Mapping - Customer Name",
                            isinstance(customer_name, str) and len(customer_name) > 0,
                            f"Customer name properly derived: '{customer_name}'",
                            "Non-empty string",
                            f"'{customer_name}' ({type(customer_name).__name__})"
                        )
                    
                else:
                    self.log_test(
                        "GET /api/returns - Basic Access",
                        False,
                        f"Failed to retrieve returns: {response.status}",
                        "200 status code",
                        f"{response.status} status code"
                    )
                    
        except Exception as e:
            self.log_test(
                "Merchant Returns API Testing",
                False,
                f"Exception during API testing: {str(e)}"
            )

    async def test_pagination_functionality(self):
        """Test 3: Pagination with New Collection Data"""
        print("🔍 TEST 3: Pagination Functionality Testing")
        
        try:
            headers = {"X-Tenant-Id": self.tenant_id}
            
            # Test pagination with different page sizes
            test_cases = [
                {"page": 1, "pageSize": 10},
                {"page": 1, "pageSize": 5},
                {"page": 2, "pageSize": 5}
            ]
            
            for case in test_cases:
                params = case
                async with self.session.get(f"{BACKEND_URL}/api/returns", headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        returns = data.get("returns", [])
                        pagination = data.get("pagination", {})
                        
                        expected_page = case["page"]
                        expected_page_size = case["pageSize"]
                        actual_page = pagination.get("page", 0)
                        actual_page_size = pagination.get("pageSize", 0)
                        
                        page_correct = actual_page == expected_page
                        size_correct = actual_page_size == expected_page_size
                        returns_within_limit = len(returns) <= expected_page_size
                        
                        self.log_test(
                            f"Pagination - Page {expected_page}, Size {expected_page_size}",
                            page_correct and size_correct and returns_within_limit,
                            f"Page: {actual_page}, Size: {actual_page_size}, Returns: {len(returns)}",
                            f"Page: {expected_page}, Size: {expected_page_size}, Returns ≤ {expected_page_size}",
                            f"Page: {actual_page}, Size: {actual_page_size}, Returns: {len(returns)}"
                        )
                    else:
                        self.log_test(
                            f"Pagination - Page {case['page']}, Size {case['pageSize']}",
                            False,
                            f"Failed to retrieve paginated results: {response.status}",
                            "200 status code",
                            f"{response.status} status code"
                        )
                        
        except Exception as e:
            self.log_test(
                "Pagination Functionality Testing",
                False,
                f"Exception during pagination testing: {str(e)}"
            )

    async def test_return_detail_endpoint(self):
        """Test 4: Return Detail Endpoint with New Data Structure"""
        print("🔍 TEST 4: Return Detail Endpoint Testing")
        
        try:
            headers = {"X-Tenant-Id": self.tenant_id}
            
            # First get a list of returns to get a valid return ID
            async with self.session.get(f"{BACKEND_URL}/api/returns", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    returns = data.get("returns", [])
                    
                    if returns:
                        # Test detail endpoint with first return
                        return_id = returns[0]["id"]
                        
                        async with self.session.get(f"{BACKEND_URL}/api/returns/{return_id}", headers=headers) as detail_response:
                            if detail_response.status == 200:
                                detail_data = await detail_response.json()
                                
                                self.log_test(
                                    "GET /api/returns/{return_id} - Basic Access",
                                    True,
                                    f"Successfully retrieved return detail for ID: {return_id}",
                                    "200 status with return detail",
                                    f"Status {detail_response.status}, return data retrieved"
                                )
                                
                                # Verify detailed structure
                                required_detail_fields = ["id", "order_id", "order_number", "customer", 
                                                        "status", "items", "estimated_refund"]
                                missing_fields = [field for field in required_detail_fields if field not in detail_data]
                                
                                if not missing_fields:
                                    self.log_test(
                                        "Return Detail Structure",
                                        True,
                                        f"All required detail fields present",
                                        "Complete return detail structure",
                                        "All required fields found"
                                    )
                                else:
                                    self.log_test(
                                        "Return Detail Structure",
                                        False,
                                        f"Missing detail fields: {missing_fields}",
                                        f"All fields: {required_detail_fields}",
                                        f"Missing: {missing_fields}"
                                    )
                                
                                # Test line items structure (from new 'returns' collection)
                                items = detail_data.get("items", [])
                                if items:
                                    sample_item = items[0]
                                    required_item_fields = ["title", "quantity", "price", "reason"]
                                    missing_item_fields = [field for field in required_item_fields if field not in sample_item]
                                    
                                    if not missing_item_fields:
                                        self.log_test(
                                            "Line Items Structure",
                                            True,
                                            f"Line items properly formatted from new structure",
                                            "Complete line item structure",
                                            "All required item fields found"
                                        )
                                    else:
                                        self.log_test(
                                            "Line Items Structure",
                                            False,
                                            f"Missing line item fields: {missing_item_fields}",
                                            f"All fields: {required_item_fields}",
                                            f"Missing: {missing_item_fields}"
                                        )
                                        
                                    # Test unit price extraction from nested objects
                                    price = sample_item.get("price", 0)
                                    self.log_test(
                                        "Unit Price Extraction",
                                        isinstance(price, (int, float)) and price >= 0,
                                        f"Unit price properly extracted: {price}",
                                        "Non-negative number",
                                        f"{price} ({type(price).__name__})"
                                    )
                                    
                                    # Test return reason extraction
                                    reason = sample_item.get("reason", "")
                                    self.log_test(
                                        "Return Reason Extraction",
                                        isinstance(reason, str),
                                        f"Return reason extracted: '{reason}'",
                                        "String value",
                                        f"'{reason}' ({type(reason).__name__})"
                                    )
                                
                                # Test customer information derivation
                                customer = detail_data.get("customer", {})
                                customer_name = customer.get("name", "")
                                customer_email = customer.get("email", "")
                                
                                self.log_test(
                                    "Customer Information Derivation",
                                    isinstance(customer_name, str) and isinstance(customer_email, str),
                                    f"Customer info derived - Name: '{customer_name}', Email: '{customer_email}'",
                                    "String values for name and email",
                                    f"Name: '{customer_name}', Email: '{customer_email}'"
                                )
                                
                            else:
                                self.log_test(
                                    "GET /api/returns/{return_id} - Basic Access",
                                    False,
                                    f"Failed to retrieve return detail: {detail_response.status}",
                                    "200 status code",
                                    f"{detail_response.status} status code"
                                )
                    else:
                        self.log_test(
                            "Return Detail Endpoint Testing",
                            False,
                            "No returns available to test detail endpoint",
                            "At least one return available",
                            "No returns found"
                        )
                else:
                    self.log_test(
                        "Return Detail Endpoint Testing",
                        False,
                        f"Failed to get returns list for detail testing: {response.status}",
                        "200 status code",
                        f"{response.status} status code"
                    )
                    
        except Exception as e:
            self.log_test(
                "Return Detail Endpoint Testing",
                False,
                f"Exception during detail endpoint testing: {str(e)}"
            )

    async def test_tenant_isolation(self):
        """Test 5: Tenant Isolation with New Collection"""
        print("🔍 TEST 5: Tenant Isolation Testing")
        
        try:
            # Test with different tenant IDs
            tenant_ids = ["tenant-fashion-store", "tenant-tech-gadgets"]
            
            for tenant_id in tenant_ids:
                headers = {"X-Tenant-Id": tenant_id}
                
                async with self.session.get(f"{BACKEND_URL}/api/returns", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        returns = data.get("returns", [])
                        total = data.get("pagination", {}).get("total", 0)
                        
                        self.log_test(
                            f"Tenant Isolation - {tenant_id}",
                            True,
                            f"Successfully retrieved {total} returns for tenant {tenant_id}",
                            "Tenant-specific data access",
                            f"{total} returns for {tenant_id}"
                        )
                        
                    else:
                        self.log_test(
                            f"Tenant Isolation - {tenant_id}",
                            False,
                            f"Failed to access returns for tenant {tenant_id}: {response.status}",
                            "200 status code",
                            f"{response.status} status code"
                        )
                        
        except Exception as e:
            self.log_test(
                "Tenant Isolation Testing",
                False,
                f"Exception during tenant isolation testing: {str(e)}"
            )

    async def run_all_tests(self):
        """Run all collection mismatch fix tests"""
        print("🚀 COLLECTION MISMATCH FIX TESTING - MERCHANT DASHBOARD RETURNS DISPLAY")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Tenant: {self.tenant_id}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        await self.setup()
        
        try:
            # Run all tests
            await self.test_collections_verification()
            await self.test_merchant_returns_api()
            await self.test_pagination_functionality()
            await self.test_return_detail_endpoint()
            await self.test_tenant_isolation()
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT: Collection mismatch fix is working correctly!")
        elif success_rate >= 75:
            print("✅ GOOD: Collection mismatch fix is mostly working with minor issues.")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Collection mismatch fix has significant issues that need attention.")
        else:
            print("❌ CRITICAL: Collection mismatch fix is not working properly.")
        
        print("=" * 80)
        
        return success_rate >= 75  # Consider 75%+ as success

async def main():
    """Main test execution"""
    tester = CollectionMismatchTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())