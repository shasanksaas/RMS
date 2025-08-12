#!/usr/bin/env python3
"""
URGENT DUPLICATE INVESTIGATION - Backend Testing
Tests the /api/returns/ endpoint for tenant-rms34 to identify duplicate entries
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import Counter
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
BACKEND_URL = "https://returnportal.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "returns_management"

class DuplicateReturnsInvestigation:
    def __init__(self):
        self.session = None
        self.mongo_client = None
        self.db = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.mongo_client:
            self.mongo_client.close()
    
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log investigation result"""
        status = "✅ CLEAN" if success else "🚨 ISSUE FOUND"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if data and not success:
            print(f"   Data: {data}")
        
        self.test_results.append({
            "test": test_name,
            "clean": success,
            "details": details,
            "data": data
        })
    
    async def make_api_request(self, endpoint: str, headers: Dict = None, params: Dict = None) -> tuple:
        """Make API request and return (success, response_data, status_code)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            request_headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": TEST_TENANT_ID,
                **(headers or {})
            }
            
            async with self.session.get(url, headers=request_headers, params=params) as response:
                response_data = await response.json()
                return response.status < 400, response_data, response.status
                
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def test_api_returns_endpoint_duplicates(self):
        """Test /api/returns/ endpoint for duplicate entries"""
        print("\n🔍 TESTING API ENDPOINT FOR DUPLICATES")
        print("=" * 50)
        
        # Test 1: Basic returns endpoint
        success, response, status = await self.make_api_request("/returns")
        
        if not success:
            self.log_result("API Endpoint Accessibility", False, f"Failed to access /api/returns - Status: {status}")
            return
        
        self.log_result("API Endpoint Accessibility", True, f"Successfully accessed /api/returns - Status: {status}")
        
        # Test 2: Check response structure
        if not isinstance(response, dict) or 'returns' not in response:
            self.log_result("API Response Structure", False, f"Unexpected response structure: {type(response)}")
            return
        
        returns_list = response.get('returns', [])
        total_count = response.get('total', 0)
        
        print(f"   📊 API Response Summary:")
        print(f"      Total returns reported: {total_count}")
        print(f"      Returns in array: {len(returns_list)}")
        print(f"      Response has pagination: {'pagination' in response}")
        
        # Test 3: Check for duplicate IDs in API response
        return_ids = [ret.get('id') for ret in returns_list if ret.get('id')]
        duplicate_ids = [id for id, count in Counter(return_ids).items() if count > 1]
        
        if duplicate_ids:
            self.log_result("API Response - Duplicate IDs", False, 
                          f"Found {len(duplicate_ids)} duplicate return IDs", duplicate_ids)
        else:
            self.log_result("API Response - Duplicate IDs", True, 
                          f"No duplicate IDs found in {len(return_ids)} returns")
        
        # Test 4: Check for duplicate return numbers
        return_numbers = [ret.get('return_number') for ret in returns_list if ret.get('return_number')]
        duplicate_numbers = [num for num, count in Counter(return_numbers).items() if count > 1]
        
        if duplicate_numbers:
            self.log_result("API Response - Duplicate Return Numbers", False,
                          f"Found {len(duplicate_numbers)} duplicate return numbers", duplicate_numbers)
        else:
            self.log_result("API Response - Duplicate Return Numbers", True,
                          f"No duplicate return numbers found")
        
        # Test 5: Check for identical return objects
        return_hashes = []
        for ret in returns_list:
            # Create a hash of key fields to identify identical returns
            key_fields = {
                'customer_email': ret.get('customer_email'),
                'order_id': ret.get('order_id'),
                'status': ret.get('status'),
                'created_at': ret.get('created_at'),
                'refund_amount': ret.get('refund_amount')
            }
            return_hashes.append(str(sorted(key_fields.items())))
        
        duplicate_hashes = [hash for hash, count in Counter(return_hashes).items() if count > 1]
        
        if duplicate_hashes:
            self.log_result("API Response - Identical Returns", False,
                          f"Found {len(duplicate_hashes)} sets of identical returns")
            # Show details of first duplicate set
            for i, ret in enumerate(returns_list):
                ret_hash = return_hashes[i]
                if ret_hash in duplicate_hashes:
                    print(f"      Duplicate return: ID={ret.get('id')}, Email={ret.get('customer_email')}, Order={ret.get('order_id')}")
                    break
        else:
            self.log_result("API Response - Identical Returns", True,
                          "No identical returns found")
        
        return returns_list
    
    async def test_api_with_different_parameters(self):
        """Test API with different pagination and filter parameters"""
        print("\n🔍 TESTING API WITH DIFFERENT PARAMETERS")
        print("=" * 50)
        
        test_params = [
            {"page": 1, "limit": 10},
            {"page": 1, "limit": 20},
            {"page": 2, "limit": 10},
            {"search": ""},
            {"status": "requested"},
            {"status": "approved"}
        ]
        
        all_returns_by_params = {}
        
        for params in test_params:
            success, response, status = await self.make_api_request("/returns", params=params)
            
            if success and 'returns' in response:
                returns_list = response.get('returns', [])
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                all_returns_by_params[param_str] = returns_list
                
                print(f"   📊 Params {param_str}: {len(returns_list)} returns")
                
                # Check for duplicates within this parameter set
                return_ids = [ret.get('id') for ret in returns_list if ret.get('id')]
                duplicate_ids = [id for id, count in Counter(return_ids).items() if count > 1]
                
                if duplicate_ids:
                    self.log_result(f"Parameter Test - {param_str}", False,
                                  f"Duplicates found with params {param_str}", duplicate_ids)
                else:
                    self.log_result(f"Parameter Test - {param_str}", True,
                                  f"No duplicates with params {param_str}")
        
        # Test cross-parameter consistency
        if len(all_returns_by_params) > 1:
            all_ids_seen = set()
            for param_str, returns_list in all_returns_by_params.items():
                for ret in returns_list:
                    ret_id = ret.get('id')
                    if ret_id in all_ids_seen:
                        self.log_result("Cross-Parameter Consistency", False,
                                      f"Return ID {ret_id} appears in multiple parameter sets")
                        break
                    all_ids_seen.add(ret_id)
            else:
                self.log_result("Cross-Parameter Consistency", True,
                              "No return appears in multiple parameter result sets")
    
    async def test_mongodb_collection_directly(self):
        """Query MongoDB 'returns' collection directly for duplicates"""
        print("\n🔍 TESTING MONGODB COLLECTION DIRECTLY")
        print("=" * 50)
        
        try:
            # Test 1: Check if returns collection exists and has data
            returns_count = await self.db.returns.count_documents({"tenant_id": TEST_TENANT_ID})
            
            if returns_count == 0:
                self.log_result("MongoDB Collection - Data Exists", False,
                              f"No returns found for tenant {TEST_TENANT_ID}")
                return
            
            self.log_result("MongoDB Collection - Data Exists", True,
                          f"Found {returns_count} returns for tenant {TEST_TENANT_ID}")
            
            # Test 2: Check for duplicate _id fields (should be impossible)
            pipeline = [
                {"$match": {"tenant_id": TEST_TENANT_ID}},
                {"$group": {"_id": "$_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicate_object_ids = await self.db.returns.aggregate(pipeline).to_list(length=100)
            
            if duplicate_object_ids:
                self.log_result("MongoDB - Duplicate ObjectIds", False,
                              f"Found {len(duplicate_object_ids)} duplicate ObjectIds (impossible!)")
            else:
                self.log_result("MongoDB - Duplicate ObjectIds", True,
                              "No duplicate ObjectIds (as expected)")
            
            # Test 3: Check for duplicate return IDs (business logic IDs)
            pipeline = [
                {"$match": {"tenant_id": TEST_TENANT_ID}},
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "docs": {"$push": "$$ROOT"}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicate_return_ids = await self.db.returns.aggregate(pipeline).to_list(length=100)
            
            if duplicate_return_ids:
                self.log_result("MongoDB - Duplicate Return IDs", False,
                              f"Found {len(duplicate_return_ids)} duplicate return IDs")
                for dup in duplicate_return_ids[:3]:  # Show first 3
                    print(f"      Duplicate ID: {dup['_id']} appears {dup['count']} times")
            else:
                self.log_result("MongoDB - Duplicate Return IDs", True,
                              "No duplicate return IDs found")
            
            # Test 4: Check for duplicate return numbers
            pipeline = [
                {"$match": {"tenant_id": TEST_TENANT_ID, "return_number": {"$exists": True}}},
                {"$group": {"_id": "$return_number", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicate_return_numbers = await self.db.returns.aggregate(pipeline).to_list(length=100)
            
            if duplicate_return_numbers:
                self.log_result("MongoDB - Duplicate Return Numbers", False,
                              f"Found {len(duplicate_return_numbers)} duplicate return numbers")
            else:
                self.log_result("MongoDB - Duplicate Return Numbers", True,
                              "No duplicate return numbers found")
            
            # Test 5: Check for identical returns (same customer, order, items)
            pipeline = [
                {"$match": {"tenant_id": TEST_TENANT_ID}},
                {"$group": {
                    "_id": {
                        "customer_email": "$customer_email",
                        "order_id": "$order_id",
                        "status": "$status",
                        "refund_amount": "$refund_amount"
                    },
                    "count": {"$sum": 1},
                    "return_ids": {"$push": "$id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            identical_returns = await self.db.returns.aggregate(pipeline).to_list(length=100)
            
            if identical_returns:
                self.log_result("MongoDB - Identical Returns", False,
                              f"Found {len(identical_returns)} sets of identical returns")
                for ident in identical_returns[:3]:  # Show first 3
                    print(f"      Identical returns: {ident['return_ids']} for customer {ident['_id']['customer_email']}")
            else:
                self.log_result("MongoDB - Identical Returns", True,
                              "No identical returns found")
            
            # Test 6: Get sample return documents for analysis
            sample_returns = await self.db.returns.find({"tenant_id": TEST_TENANT_ID}).limit(3).to_list(length=3)
            
            print(f"\n   📋 Sample Return Document Structure:")
            if sample_returns:
                sample = sample_returns[0]
                print(f"      Fields: {list(sample.keys())}")
                print(f"      ID: {sample.get('id')}")
                print(f"      Customer: {sample.get('customer_email')}")
                print(f"      Order: {sample.get('order_id')}")
                print(f"      Status: {sample.get('status')}")
                print(f"      Created: {sample.get('created_at')}")
            
        except Exception as e:
            self.log_result("MongoDB Collection Access", False, f"Error accessing MongoDB: {str(e)}")
    
    async def test_tenant_isolation(self):
        """Test if tenant isolation is working correctly"""
        print("\n🔍 TESTING TENANT ISOLATION")
        print("=" * 50)
        
        # Test 1: Check returns for our tenant
        success, response, status = await self.make_api_request("/returns")
        
        if success and 'returns' in response:
            our_returns = response.get('returns', [])
            our_count = len(our_returns)
            
            # Test 2: Check returns for a different tenant
            other_tenant_headers = {"X-Tenant-Id": "tenant-fashion-store"}
            success2, response2, status2 = await self.make_api_request("/returns", headers=other_tenant_headers)
            
            if success2 and 'returns' in response2:
                other_returns = response2.get('returns', [])
                other_count = len(other_returns)
                
                print(f"   📊 Tenant Comparison:")
                print(f"      {TEST_TENANT_ID}: {our_count} returns")
                print(f"      tenant-fashion-store: {other_count} returns")
                
                # Check if any returns appear in both tenant results
                our_ids = set(ret.get('id') for ret in our_returns if ret.get('id'))
                other_ids = set(ret.get('id') for ret in other_returns if ret.get('id'))
                
                cross_tenant_ids = our_ids.intersection(other_ids)
                
                if cross_tenant_ids:
                    self.log_result("Tenant Isolation", False,
                                  f"Found {len(cross_tenant_ids)} returns appearing in both tenants", list(cross_tenant_ids))
                else:
                    self.log_result("Tenant Isolation", True,
                                  "No returns appear across multiple tenants")
            else:
                self.log_result("Other Tenant Access", False, f"Could not access other tenant data: {status2}")
        else:
            self.log_result("Our Tenant Access", False, f"Could not access our tenant data: {status}")
    
    async def test_api_response_structure_analysis(self):
        """Analyze the exact API response structure"""
        print("\n🔍 ANALYZING API RESPONSE STRUCTURE")
        print("=" * 50)
        
        success, response, status = await self.make_api_request("/returns", params={"limit": 5})
        
        if not success:
            self.log_result("API Response Analysis", False, f"Could not get API response: {status}")
            return
        
        print(f"   📋 Response Structure Analysis:")
        print(f"      Response type: {type(response)}")
        print(f"      Top-level keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if 'returns' in response:
            returns_array = response['returns']
            print(f"      Returns array length: {len(returns_array)}")
            
            if returns_array:
                first_return = returns_array[0]
                print(f"      First return keys: {list(first_return.keys()) if isinstance(first_return, dict) else 'Not a dict'}")
                print(f"      First return ID: {first_return.get('id')}")
                print(f"      First return customer: {first_return.get('customer_email')}")
        
        if 'pagination' in response:
            pagination = response['pagination']
            print(f"      Pagination: {pagination}")
        
        # Check if response contains expected fields
        expected_fields = ['returns', 'total', 'page', 'limit', 'pagination']
        missing_fields = [field for field in expected_fields if field not in response]
        
        if missing_fields:
            self.log_result("API Response Structure", False,
                          f"Missing expected fields: {missing_fields}")
        else:
            self.log_result("API Response Structure", True,
                          "Response contains all expected fields")
    
    async def run_investigation(self):
        """Run the complete duplicate investigation"""
        print("🚨 URGENT DUPLICATE RETURNS INVESTIGATION")
        print("🎯 Target: /api/returns/ endpoint for tenant-rms34")
        print("=" * 60)
        
        # Run all investigation tests
        api_returns = await self.test_api_returns_endpoint_duplicates()
        await self.test_api_with_different_parameters()
        await self.test_mongodb_collection_directly()
        await self.test_tenant_isolation()
        await self.test_api_response_structure_analysis()
        
        # Generate investigation summary
        self.print_investigation_summary()
    
    def print_investigation_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 60)
        print("📊 DUPLICATE INVESTIGATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        clean_tests = sum(1 for result in self.test_results if result["clean"])
        issues_found = total_tests - clean_tests
        
        print(f"Total Checks: {total_tests}")
        print(f"✅ Clean: {clean_tests}")
        print(f"🚨 Issues Found: {issues_found}")
        
        if issues_found > 0:
            print(f"\n🚨 ISSUES IDENTIFIED:")
            for result in self.test_results:
                if not result["clean"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 INVESTIGATION CONCLUSION:")
        
        # Categorize findings
        api_issues = [r for r in self.test_results if not r["clean"] and "API" in r["test"]]
        db_issues = [r for r in self.test_results if not r["clean"] and "MongoDB" in r["test"]]
        isolation_issues = [r for r in self.test_results if not r["clean"] and "Tenant" in r["test"]]
        
        if api_issues:
            print(f"   🚨 API ENDPOINT ISSUES: {len(api_issues)} problems found")
            print(f"      The /api/returns/ endpoint is returning duplicate data")
        else:
            print(f"   ✅ API ENDPOINT CLEAN: No duplicates found in API responses")
        
        if db_issues:
            print(f"   🚨 DATABASE ISSUES: {len(db_issues)} problems found")
            print(f"      The MongoDB 'returns' collection contains duplicate records")
        else:
            print(f"   ✅ DATABASE CLEAN: No duplicate records in MongoDB")
        
        if isolation_issues:
            print(f"   🚨 TENANT ISOLATION ISSUES: {len(isolation_issues)} problems found")
            print(f"      Data is leaking between tenants")
        else:
            print(f"   ✅ TENANT ISOLATION WORKING: Data properly isolated")
        
        # Final recommendation
        if issues_found == 0:
            print(f"\n✅ FINAL ASSESSMENT: No backend duplicates found")
            print(f"   The duplicate issue reported by user is likely in frontend rendering")
            print(f"   Recommend investigating AllReturns.jsx component logic")
        else:
            print(f"\n🚨 FINAL ASSESSMENT: Backend is serving duplicate data")
            print(f"   The duplicate issue is confirmed in the backend API")
            print(f"   Immediate fix required in backend data handling")

async def main():
    """Main investigation execution"""
    async with DuplicateReturnsInvestigation() as investigation:
        await investigation.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())