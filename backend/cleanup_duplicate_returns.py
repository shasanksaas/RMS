#!/usr/bin/env python3
"""
Cleanup Duplicate Returns Data Script
Removes duplicate return records from MongoDB based on order_id + customer_email combinations.
Keeps the most recent return for each unique combination.
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = "returns_management"

async def cleanup_duplicate_returns():
    """
    Remove duplicate returns from the database.
    Keep the most recent return for each unique order_id + customer_email combination.
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        print("🧹 STARTING DUPLICATE RETURNS CLEANUP")
        print("=" * 50)
        
        # Get all tenants
        tenants_cursor = db.tenants.find({})
        tenants = await tenants_cursor.to_list(length=None)
        
        total_removed = 0
        
        for tenant in tenants:
            tenant_id = tenant.get("id", "")
            tenant_name = tenant.get("shop_domain", tenant_id)
            
            print(f"\n📊 Processing tenant: {tenant_name} ({tenant_id})")
            
            # Get all returns for this tenant
            returns_cursor = db.returns.find({"tenant_id": tenant_id}).sort("created_at", -1)
            all_returns = await returns_cursor.to_list(length=None)
            
            if not all_returns:
                print(f"   ✅ No returns found for tenant {tenant_name}")
                continue
            
            print(f"   📈 Found {len(all_returns)} total returns")
            
            # Group returns by order_id + customer_email combination
            combinations_map = {}
            
            for ret in all_returns:
                order_id = ret.get("order_id", "")
                customer_email = ret.get("customer_email", "")
                combination_key = f"{order_id}:{customer_email}"
                
                if combination_key not in combinations_map:
                    combinations_map[combination_key] = []
                combinations_map[combination_key].append(ret)
            
            # Find duplicates and remove them
            returns_to_remove = []
            duplicates_count = 0
            
            for combination_key, returns_list in combinations_map.items():
                if len(returns_list) > 1:
                    duplicates_count += len(returns_list) - 1
                    
                    # Sort by updated_at or created_at (most recent first)
                    sorted_returns = sorted(returns_list, key=lambda x: x.get("updated_at") or x.get("created_at"), reverse=True)
                    
                    # Keep the first (most recent), mark the rest for removal
                    keep_return = sorted_returns[0]
                    remove_returns = sorted_returns[1:]
                    
                    print(f"   🔍 Found {len(remove_returns)} duplicates for {combination_key}")
                    print(f"      Keeping: {keep_return['id']} (created: {keep_return.get('created_at')})")
                    
                    for remove_return in remove_returns:
                        print(f"      Removing: {remove_return['id']} (created: {remove_return.get('created_at')})")
                        returns_to_remove.append(remove_return['id'])
            
            # Remove duplicate returns from database
            if returns_to_remove:
                result = await db.returns.delete_many({
                    "_id": {"$in": [ret['_id'] for ret in all_returns if ret['id'] in returns_to_remove]}
                })
                
                removed_count = result.deleted_count
                total_removed += removed_count
                
                print(f"   ✅ Removed {removed_count} duplicate returns for tenant {tenant_name}")
                
                # Verify cleanup
                remaining_returns = await db.returns.count_documents({"tenant_id": tenant_id})
                print(f"   📊 Remaining returns: {remaining_returns}")
            else:
                print(f"   ✅ No duplicates found for tenant {tenant_name}")
        
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"   Total duplicates removed across all tenants: {total_removed}")
        
        # Final verification - check for any remaining duplicates
        print(f"\n🔍 VERIFICATION: Checking for remaining duplicates...")
        
        for tenant in tenants:
            tenant_id = tenant.get("id", "")
            tenant_name = tenant.get("shop_domain", tenant_id)
            
            returns_cursor = db.returns.find({"tenant_id": tenant_id})
            all_returns = await returns_cursor.to_list(length=None)
            
            combinations_map = {}
            for ret in all_returns:
                order_id = ret.get("order_id", "")
                customer_email = ret.get("customer_email", "")
                combination_key = f"{order_id}:{customer_email}"
                
                if combination_key not in combinations_map:
                    combinations_map[combination_key] = []
                combinations_map[combination_key].append(ret)
            
            duplicates_remaining = sum(1 for returns_list in combinations_map.values() if len(returns_list) > 1)
            
            if duplicates_remaining > 0:
                print(f"   ⚠️  {tenant_name}: {duplicates_remaining} duplicate combinations still exist")
            else:
                print(f"   ✅ {tenant_name}: Clean - no duplicates remaining")
    
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_returns())