#!/usr/bin/env python3
"""
Debug script to check MongoDB rules collection
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

async def check_rules_collection():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔍 Checking rules collection...")
    
    # Count total rules
    total_rules = await db.return_rules.count_documents({})
    print(f"Total rules in database: {total_rules}")
    
    if total_rules > 0:
        # Get first few rules to inspect
        rules_cursor = db.return_rules.find({}).limit(3)
        rules = await rules_cursor.to_list(length=3)
        
        print("\n📋 Sample rules:")
        for i, rule in enumerate(rules):
            print(f"\nRule {i+1}:")
            print(f"  _id: {rule.get('_id')} (type: {type(rule.get('_id'))})")
            print(f"  id: {rule.get('id')} (type: {type(rule.get('id'))})")
            print(f"  name: {rule.get('name')}")
            print(f"  tenant_id: {rule.get('tenant_id')}")
            print(f"  created_at: {rule.get('created_at')} (type: {type(rule.get('created_at'))})")
            print(f"  condition_groups: {rule.get('condition_groups')}")
            print(f"  actions: {rule.get('actions')}")
    
    # Check for tenant-fashion-store specifically
    tenant_rules = await db.return_rules.count_documents({"tenant_id": "tenant-fashion-store"})
    print(f"\nRules for tenant-fashion-store: {tenant_rules}")
    
    if tenant_rules > 0:
        tenant_rules_cursor = db.return_rules.find({"tenant_id": "tenant-fashion-store"}).limit(2)
        tenant_rules_list = await tenant_rules_cursor.to_list(length=2)
        
        print("\n📋 Tenant-specific rules:")
        for i, rule in enumerate(tenant_rules_list):
            print(f"\nTenant Rule {i+1}:")
            print(f"  _id: {rule.get('_id')}")
            print(f"  id: {rule.get('id')}")
            print(f"  name: {rule.get('name')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_rules_collection())