#!/usr/bin/env python3
"""
Debug unified returns endpoint issues
"""

import asyncio
import aiohttp
import json

async def debug_unified_returns():
    """Debug the unified returns endpoints"""
    
    BACKEND_URL = "https://f4ede537-31b1-4ba8-b14e-a9ada50dbb28.preview.emergentagent.com"
    TEST_TENANT_ID = "tenant-fashion-store"
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-Id": TEST_TENANT_ID
    }
    
    async with aiohttp.ClientSession() as session:
        
        # First, get a real order from the seeded data
        print("🔍 Getting seeded order data...")
        async with session.get(f"{BACKEND_URL}/api/orders?limit=1", headers=headers) as response:
            if response.status == 200:
                orders_data = await response.json()
                if orders_data.get("items"):
                    order = orders_data["items"][0]
                    print(f"✅ Found order: {order['order_number']} for {order['customer_email']}")
                    
                    # Test order lookup with real data
                    print("\n🔍 Testing order lookup with real data...")
                    lookup_data = {
                        "order_number": order["order_number"],
                        "email": order["customer_email"]
                    }
                    
                    async with session.post(f"{BACKEND_URL}/api/unified-returns/order/lookup", 
                                          json=lookup_data, headers=headers) as lookup_response:
                        print(f"Status: {lookup_response.status}")
                        try:
                            response_data = await lookup_response.json()
                            print(f"Response: {json.dumps(response_data, indent=2)}")
                        except:
                            response_text = await lookup_response.text()
                            print(f"Response text: {response_text}")
                    
                    # Test eligible items endpoint
                    print(f"\n📦 Testing eligible items for order {order['id']}...")
                    async with session.get(f"{BACKEND_URL}/api/unified-returns/order/{order['id']}/eligible-items", 
                                         headers=headers) as items_response:
                        print(f"Status: {items_response.status}")
                        try:
                            response_data = await items_response.json()
                            print(f"Response: {json.dumps(response_data, indent=2)}")
                        except:
                            response_text = await items_response.text()
                            print(f"Response text: {response_text}")
                else:
                    print("❌ No orders found in seeded data")
            else:
                print(f"❌ Failed to get orders: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")

if __name__ == "__main__":
    asyncio.run(debug_unified_returns())