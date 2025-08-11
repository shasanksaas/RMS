#!/usr/bin/env python3
"""
Direct Database Collection Check
Verify which collections have return data and their counts
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join('backend', '.env'))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def check_collections():
    """Check return data in different collections"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔍 COLLECTION VERIFICATION")
    print("=" * 50)
    
    # Check return_requests collection
    return_requests_count = await db.return_requests.count_documents({})
    print(f"return_requests collection: {return_requests_count} documents")
    
    # Check returns collection
    returns_count = await db.returns.count_documents({})
    print(f"returns collection: {returns_count} documents")
    
    # Check by tenant
    tenant_id = "tenant-fashion-store"
    
    return_requests_tenant = await db.return_requests.count_documents({"tenant_id": tenant_id})
    returns_tenant = await db.returns.count_documents({"tenant_id": tenant_id})
    
    print(f"\nFor tenant {tenant_id}:")
    print(f"return_requests: {return_requests_tenant} documents")
    print(f"returns: {returns_tenant} documents")
    
    # Sample documents from each collection
    if return_requests_count > 0:
        sample_return_request = await db.return_requests.find_one({"tenant_id": tenant_id})
        print(f"\nSample return_requests document structure:")
        print(f"  - id: {sample_return_request.get('id', 'N/A')}")
        print(f"  - status: {sample_return_request.get('status', 'N/A')}")
        print(f"  - items_to_return: {len(sample_return_request.get('items_to_return', []))} items")
        print(f"  - refund_amount: {sample_return_request.get('refund_amount', 'N/A')}")
    
    if returns_count > 0:
        sample_return = await db.returns.find_one({"tenant_id": tenant_id})
        print(f"\nSample returns document structure:")
        print(f"  - id: {sample_return.get('id', 'N/A')}")
        print(f"  - status: {sample_return.get('status', 'N/A')}")
        print(f"  - line_items: {len(sample_return.get('line_items', []))} items")
        print(f"  - estimated_refund: {sample_return.get('estimated_refund', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("CONCLUSION:")
    if return_requests_count > 0 and returns_count == 0:
        print("❌ COLLECTION MISMATCH CONFIRMED!")
        print("   Data exists in 'return_requests' but enhanced controller")
        print("   is looking in 'returns' collection.")
    elif returns_count > 0 and return_requests_count == 0:
        print("✅ COLLECTION FIX WORKING!")
        print("   Data exists in 'returns' collection as expected.")
    elif return_requests_count > 0 and returns_count > 0:
        print("⚠️ BOTH COLLECTIONS HAVE DATA!")
        print("   Need to verify which one the API is using.")
    else:
        print("❓ NO RETURN DATA FOUND!")
        print("   Need to seed the database first.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_collections())