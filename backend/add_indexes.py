#!/usr/bin/env python3
"""
Add database indexes for optimal query performance
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.config.database import db

async def add_indexes():
    """Add indexes to improve query performance"""
    
    try:
        print("Adding database indexes for performance optimization...")
        
        # Returns collection indexes
        print("Adding returns collection indexes...")
        
        # Tenant ID index (most important)
        await db.returns.create_index("tenant_id")
        print("✓ Created index on returns.tenant_id")
        
        # Compound index for tenant_id + common filters
        await db.returns.create_index([
            ("tenant_id", 1), 
            ("status", 1)
        ])
        print("✓ Created compound index on returns.tenant_id + status")
        
        await db.returns.create_index([
            ("tenant_id", 1), 
            ("created_at", -1)
        ])
        print("✓ Created compound index on returns.tenant_id + created_at")
        
        # Search fields index
        await db.returns.create_index([
            ("tenant_id", 1),
            ("customer_email", 1)
        ])
        print("✓ Created compound index on returns.tenant_id + customer_email")
        
        await db.returns.create_index([
            ("tenant_id", 1),
            ("order_id", 1)
        ])
        print("✓ Created compound index on returns.tenant_id + order_id")
        
        # Orders collection indexes
        print("Adding orders collection indexes...")
        
        await db.orders.create_index("tenant_id")
        print("✓ Created index on orders.tenant_id")
        
        await db.orders.create_index([
            ("tenant_id", 1),
            ("id", 1)
        ])
        print("✓ Created compound index on orders.tenant_id + id")
        
        # Text search index for customer names/emails
        try:
            await db.returns.create_index([
                ("customer_name", "text"),
                ("customer_email", "text"),
                ("order_number", "text")
            ])
            print("✓ Created text search index on returns")
        except Exception as e:
            print(f"Note: Text index creation failed (may already exist): {e}")
        
        # Check existing indexes
        print("\nCurrent indexes:")
        
        returns_indexes = await db.returns.index_information()
        print(f"Returns indexes: {list(returns_indexes.keys())}")
        
        orders_indexes = await db.orders.index_information()
        print(f"Orders indexes: {list(orders_indexes.keys())}")
        
        print("✅ Database indexes optimization complete!")
        
    except Exception as e:
        print(f"❌ Error adding indexes: {e}")
        
if __name__ == "__main__":
    asyncio.run(add_indexes())