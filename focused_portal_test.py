#!/usr/bin/env python3
"""
Focused test for the specific customer returns portal APIs requested
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "https://returnhub-1.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"

async def test_specific_portal_apis():
    """Test the specific APIs requested by the user"""
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Testing Specific Customer Returns Portal APIs")
        print("=" * 60)
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        # Test 1: Order lookup: POST /api/portal/returns/lookup-order
        print("\n1. Testing POST /api/portal/returns/lookup-order")
        lookup_data = {
            "orderNumber": "1001",
            "email": "customer@example.com"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/portal/returns/lookup-order", 
                                  json=lookup_data, headers=headers) as response:
                response_data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(response_data, indent=2)}")
                if response.status == 200:
                    print("   ✅ Order lookup working")
                else:
                    print("   ❌ Order lookup has issues")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Policy preview: POST /api/portal/returns/policy-preview
        print("\n2. Testing POST /api/portal/returns/policy-preview")
        preview_data = {
            "items": [
                {
                    "line_item_id": "test-item-1",
                    "quantity": 1,
                    "reason": "damaged_defective"
                }
            ],
            "order_id": "test-order-id"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/portal/returns/policy-preview", 
                                  json=preview_data, headers=headers) as response:
                response_data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(response_data, indent=2)}")
                if response.status == 200:
                    print("   ✅ Policy preview working")
                else:
                    print("   ❌ Policy preview has issues")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Admin returns endpoints: GET /api/returns
        print("\n3. Testing GET /api/returns")
        
        try:
            async with session.get(f"{BACKEND_URL}/returns", headers=headers) as response:
                response_data = await response.json()
                print(f"   Status: {response.status}")
                if response.status == 200:
                    print(f"   ✅ Admin returns working - Found {len(response_data.get('items', []))} returns")
                    print(f"   Response structure: {list(response_data.keys())}")
                else:
                    print(f"   ❌ Admin returns has issues: {response_data}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Return creation: POST /api/portal/returns/create
        print("\n4. Testing POST /api/portal/returns/create")
        create_data = {
            "orderNumber": "1001",
            "email": "customer@example.com",
            "items": [
                {
                    "line_item_id": "test-item-1",
                    "quantity": 1,
                    "reason": "damaged_defective",
                    "reason_note": "Item arrived damaged"
                }
            ],
            "preferred_outcome": "refund_original",
            "return_method": "prepaid_label"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/portal/returns/create", 
                                  json=create_data, headers=headers) as response:
                response_data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(response_data, indent=2)}")
                if response.status == 200:
                    print("   ✅ Return creation working")
                else:
                    print("   ❌ Return creation has issues")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 5: Check available endpoints
        print("\n5. Testing endpoint availability")
        endpoints_to_test = [
            "/portal/returns/lookup-order",
            "/portal/returns/policy-preview", 
            "/portal/returns/create",
            "/returns"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Use HEAD request to check if endpoint exists
                async with session.head(f"{BACKEND_URL}{endpoint}", headers=headers) as response:
                    if response.status != 404:
                        print(f"   ✅ {endpoint} - Available (status: {response.status})")
                    else:
                        print(f"   ❌ {endpoint} - Not found")
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_portal_apis())