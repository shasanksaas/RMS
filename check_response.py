#!/usr/bin/env python3
"""
Quick test to see the actual response structure
"""

import asyncio
import aiohttp
import json

async def check_response():
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-Id": "tenant-rms34"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://1ce8ef7a-c16d-43a6-b3d4-da8a63312de8.preview.emergentagent.com/api/orders", headers=headers) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            print("Response structure:")
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(check_response())