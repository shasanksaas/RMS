#!/usr/bin/env python3
"""
Debug routing behavior for returns endpoints
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"

async def test_routing():
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        endpoints_to_test = [
            "/returns",      # Without trailing slash
            "/returns/",     # With trailing slash
            "/returns?limit=5",  # With query params
            "/returns/?limit=5", # With trailing slash and query params
        ]
        
        print("🔍 Testing routing behavior for returns endpoints:")
        print("=" * 60)
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                print(f"\nTesting: {url}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"Status: {response.status}")
                    print(f"URL after redirects: {response.url}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, dict):
                                print(f"Response keys: {list(data.keys())}")
                                if "returns" in data:
                                    print(f"Returns count: {len(data['returns'])}")
                            else:
                                print(f"Response type: {type(data)}")
                        except:
                            text = await response.text()
                            print(f"Response text length: {len(text)}")
                    else:
                        try:
                            error_data = await response.json()
                            print(f"Error: {error_data}")
                        except:
                            error_text = await response.text()
                            print(f"Error text: {error_text[:200]}")
                            
            except Exception as e:
                print(f"Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_routing())