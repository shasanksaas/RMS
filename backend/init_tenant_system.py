#!/usr/bin/env python3
"""
Initialize Tenant Management Database Indexes
Creates necessary indexes for optimal tenant isolation and performance
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tenant_indexes():
    """Create all necessary indexes for tenant management system"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'returns_')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Tenant collection indexes
        tenant_indexes = [
            IndexModel([("tenant_id", 1)], unique=True),
            IndexModel([("status", 1)]),
            IndexModel([("created_at", 1)]),
            IndexModel([("claimed_at", 1)]),
            IndexModel([("last_activity_at", 1)]),
            IndexModel([("settings.created_by", 1)]),
        ]
        
        await db.tenants.create_indexes(tenant_indexes)
        logger.info("✅ Created tenant collection indexes")
        
        # Enhanced user indexes for tenant isolation
        user_indexes = [
            IndexModel([("tenant_id", 1), ("email", 1)], unique=True),
            IndexModel([("tenant_id", 1), ("role", 1)]),
            IndexModel([("tenant_id", 1), ("user_id", 1)], unique=True),
            IndexModel([("tenant_id", 1), ("created_at", 1)]),
            IndexModel([("tenant_id", 1), ("last_login", 1)]),
            IndexModel([("tenant_id", 1), ("auth_provider", 1)]),
        ]
        
        await db.users.create_indexes(user_indexes)
        logger.info("✅ Created enhanced user collection indexes")
        
        # Enhanced returns indexes for tenant isolation
        returns_indexes = [
            IndexModel([("tenant_id", 1), ("return_id", 1)], unique=True),
            IndexModel([("tenant_id", 1), ("order_id", 1)]),
            IndexModel([("tenant_id", 1), ("customer_email", 1)]),
            IndexModel([("tenant_id", 1), ("status", 1)]),
            IndexModel([("tenant_id", 1), ("created_at", 1)]),
            IndexModel([("tenant_id", 1), ("updated_at", 1)]),
        ]
        
        await db.returns.create_indexes(returns_indexes)
        logger.info("✅ Created enhanced returns collection indexes")
        
        # Enhanced orders indexes for tenant isolation
        orders_indexes = [
            IndexModel([("tenant_id", 1), ("order_id", 1)], unique=True),
            IndexModel([("tenant_id", 1), ("order_number", 1)]),
            IndexModel([("tenant_id", 1), ("customer.email", 1)]),
            IndexModel([("tenant_id", 1), ("financial_status", 1)]),
            IndexModel([("tenant_id", 1), ("created_at", 1)]),
        ]
        
        await db.orders.create_indexes(orders_indexes)
        logger.info("✅ Created enhanced orders collection indexes")
        
        # Enhanced integrations indexes for tenant isolation
        integrations_indexes = [
            IndexModel([("tenant_id", 1)], unique=True),
            IndexModel([("tenant_id", 1), ("shop", 1)]),
            IndexModel([("tenant_id", 1), ("created_at", 1)]),
            IndexModel([("tenant_id", 1), ("last_sync", 1)]),
        ]
        
        await db.integrations_shopify.create_indexes(integrations_indexes)
        logger.info("✅ Created enhanced integrations collection indexes")
        
        # Sessions collection for tenant isolation
        sessions_indexes = [
            IndexModel([("tenant_id", "session_id")], unique=True),
            IndexModel([("tenant_id", "user_id")]),
            IndexModel([("tenant_id", "expires_at")]),
            IndexModel([("tenant_id", "created_at")]),
        ]
        
        await db.sessions.create_indexes(sessions_indexes)
        logger.info("✅ Created enhanced sessions collection indexes")
        
        # Create sample admin user if none exists
        admin_exists = await db.users.find_one({"role": "admin"})
        if not admin_exists:
            from datetime import datetime
            import uuid
            import bcrypt
            
            # Create default admin user
            admin_user = {
                "user_id": str(uuid.uuid4()),
                "tenant_id": "admin-system",
                "email": "admin@returns-manager.com",
                "password_hash": bcrypt.hashpw("AdminPassword123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "role": "admin",
                "permissions": ["*"],  # All permissions
                "auth_provider": "email",
                "first_name": "Admin",
                "last_name": "User",
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.users.insert_one(admin_user)
            logger.info("✅ Created default admin user (email: admin@returns-manager.com, password: AdminPassword123!)")
        
        logger.info("🎉 Tenant management database initialization complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tenant indexes: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_tenant_indexes())