#!/usr/bin/env python3
"""
Focused Order Lookup Test - Testing the specific endpoints requested
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://f07a6717-33e5-45c0-b306-b76d55047333.preview.emergentagent.com/api"

async def test_order_lookup_endpoints():
    """Test the specific endpoints requested in the review"""
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Testing Enhanced Order Lookup System")
        print("=" * 50)
        
        # Test 1: POST /api/returns/order-lookup with tenant-rms34
        print("\n1. Testing Shopify Mode Order Lookup")
        lookup_data = {
            "order_number": "1001",
            "email": "customer@example.com", 
            "channel": "customer"
        }
        headers = {"X-Tenant-Id": "tenant-rms34", "Content-Type": "application/json"}
        
        async with session.post(f"{BACKEND_URL}/returns/order-lookup", json=lookup_data, headers=headers) as response:
            print(f"   Status: {response.status}")
            data = await response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("mode") == "shopify":
                print("   ✅ Successfully using Shopify mode")
            elif data.get("mode") == "fallback":
                print("   ⚠️ Using fallback mode (tenant may not have Shopify integration)")
            else:
                print("   ❌ Unexpected mode or error")
        
        # Test 2: POST /api/returns/policy-preview
        print("\n2. Testing Policy Preview Endpoint")
        policy_data = {
            "items": [
                {
                    "id": "item-1",
                    "name": "Test Product",
                    "price": 100.00,
                    "quantity": 1,
                    "reason": "defective"
                }
            ],
            "orderMeta": {
                "orderNumber": "1001",
                "totalValue": 100.00
            }
        }
        
        async with session.post(f"{BACKEND_URL}/returns/policy-preview", json=policy_data, headers=headers) as response:
            print(f"   Status: {response.status}")
            data = await response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if response.status == 200 and data.get("success"):
                print("   ✅ Policy preview working correctly")
            else:
                print("   ❌ Policy preview has issues")
        
        # Test 3: Test fallback mode with different tenant
        print("\n3. Testing Fallback Mode")
        fallback_headers = {"X-Tenant-Id": "tenant-fashion-store", "Content-Type": "application/json"}
        fallback_data = {
            "order_number": "FB-1001",
            "email": "fallback@example.com",
            "channel": "customer"
        }
        
        async with session.post(f"{BACKEND_URL}/returns/order-lookup", json=fallback_data, headers=fallback_headers) as response:
            print(f"   Status: {response.status}")
            data = await response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("mode") == "fallback":
                print("   ✅ Successfully using fallback mode")
            else:
                print("   ❌ Expected fallback mode")
        
        # Test 4: GET /api/admin/returns/pending
        print("\n4. Testing Admin Drafts Endpoint")
        async with session.get(f"{BACKEND_URL}/admin/returns/pending", headers=fallback_headers) as response:
            print(f"   Status: {response.status}")
            data = await response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if response.status == 200 and "items" in data:
                print(f"   ✅ Admin drafts endpoint working, found {len(data['items'])} drafts")
            else:
                print("   ❌ Admin drafts endpoint has issues")
        
        # Test 5: Test GraphQL service connectivity
        print("\n5. Testing GraphQL Service")
        async with session.get(f"{BACKEND_URL}/shopify-test/quick-test", headers=headers) as response:
            print(f"   Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                if data.get("quick_test", {}).get("overall_success"):
                    print("   ✅ GraphQL service connectivity working")
                else:
                    print("   ❌ GraphQL service has connectivity issues")
            else:
                print("   ❌ GraphQL service endpoint not accessible")
        
        # Test 6: Check controller registration
        print("\n6. Testing Controller Registration")
        test_endpoints = [
            "/returns/order-lookup",
            "/returns/policy-preview", 
            "/admin/returns/pending"
        ]
        
        for endpoint in test_endpoints:
            # Test with minimal data to check if endpoint exists
            test_data = {"test": "data"} if endpoint != "/admin/returns/pending" else None
            method = "POST" if endpoint != "/admin/returns/pending" else "GET"
            
            if method == "POST":
                async with session.post(f"{BACKEND_URL}{endpoint}", json=test_data, headers=headers) as response:
                    status = response.status
            else:
                async with session.get(f"{BACKEND_URL}{endpoint}", headers=headers) as response:
                    status = response.status
            
            if status == 404:
                print(f"   ❌ {endpoint}: Not found (controller not registered)")
            else:
                print(f"   ✅ {endpoint}: Registered (status: {status})")

if __name__ == "__main__":
    asyncio.run(test_order_lookup_endpoints())