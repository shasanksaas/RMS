"""
Quick script to create a return policy for exchange testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

async def create_exchange_policy():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/returns_manager_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client.returns_manager_db
    
    # Create a simple policy with exchange enabled
    policy = {
        "id": "policy-exchange-enabled-test",
        "tenant_id": "tenant-rms34",
        "name": "Exchange Enabled Policy", 
        "description": "Default policy with exchange functionality enabled for testing",
        "is_active": True,
        "exchange_settings": {
            "enabled": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert policy
    result = await db.return_policies.insert_one(policy)
    
    if result.inserted_id:
        print(f"✅ Created return policy with ID: policy-exchange-enabled-test")
        
        # Verify it was created
        created_policy = await db.return_policies.find_one({"id": "policy-exchange-enabled-test"})
        if created_policy:
            print(f"✅ Verified policy exists: {created_policy['name']}")
            print(f"✅ Exchange enabled: {created_policy['exchange_settings']['enabled']}")
        else:
            print("❌ Failed to verify policy creation")
    else:
        print("❌ Failed to create policy")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_exchange_policy())