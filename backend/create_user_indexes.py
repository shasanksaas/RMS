#!/usr/bin/env python3
"""
Create User Management Database Indexes
Production-ready indexes for optimal query performance
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = "returns_management"

async def create_user_indexes():
    """Create all user management indexes"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        print("🔧 CREATING USER MANAGEMENT INDEXES")
        print("=" * 50)
        
        # === USERS COLLECTION INDEXES ===
        print("\n📊 Creating users collection indexes...")
        
        # 1. Unique compound index for tenant_id + user_id
        await db.users.create_index([
            ("tenant_id", 1),
            ("user_id", 1)
        ], unique=True, name="tenant_user_unique")
        print("   ✅ Created tenant_id + user_id unique index")
        
        # 2. Unique compound index for tenant_id + email
        await db.users.create_index([
            ("tenant_id", 1), 
            ("email", 1)
        ], unique=True, name="tenant_email_unique")
        print("   ✅ Created tenant_id + email unique index")
        
        # 3. Compound index for tenant_id + role (for role-based queries)
        await db.users.create_index([
            ("tenant_id", 1),
            ("role", 1)
        ], name="tenant_role")
        print("   ✅ Created tenant_id + role index")
        
        # 4. Index for auth_provider (for authentication method queries)
        await db.users.create_index([
            ("auth_provider", 1)
        ], name="auth_provider")
        print("   ✅ Created auth_provider index")
        
        # 5. Index for is_active + tenant_id (for active users queries)
        await db.users.create_index([
            ("tenant_id", 1),
            ("is_active", 1)
        ], name="tenant_active_users")
        print("   ✅ Created tenant_id + is_active index")
        
        # 6. Index for google_user_id (for Google OAuth lookup)
        await db.users.create_index([
            ("google_user_id", 1)
        ], sparse=True, name="google_user_id")
        print("   ✅ Created google_user_id sparse index")
        
        # 7. Index for created_at (for chronological queries)
        await db.users.create_index([
            ("created_at", -1)
        ], name="created_at_desc")
        print("   ✅ Created created_at descending index")
        
        # 8. Index for last_login_at (for activity tracking)
        await db.users.create_index([
            ("last_login_at", -1)
        ], sparse=True, name="last_login_desc")
        print("   ✅ Created last_login_at descending index")
        
        # === SESSIONS COLLECTION INDEXES ===
        print("\n🔐 Creating sessions collection indexes...")
        
        # 1. Unique index for session_token
        await db.sessions.create_index([
            ("session_token", 1)
        ], unique=True, name="session_token_unique")
        print("   ✅ Created session_token unique index")
        
        # 2. Compound index for tenant_id + user_id (for user sessions)
        await db.sessions.create_index([
            ("tenant_id", 1),
            ("user_id", 1)
        ], name="tenant_user_sessions")
        print("   ✅ Created tenant_id + user_id sessions index")
        
        # 3. Index for expires_at (for session cleanup)
        await db.sessions.create_index([
            ("expires_at", 1)
        ], name="expires_at")
        print("   ✅ Created expires_at index")
        
        # 4. Compound index for is_active + expires_at (for active session queries)
        await db.sessions.create_index([
            ("is_active", 1),
            ("expires_at", 1)
        ], name="active_sessions")
        print("   ✅ Created is_active + expires_at index")
        
        # 5. Index for created_at (for session tracking)
        await db.sessions.create_index([
            ("created_at", -1)
        ], name="sessions_created_desc")
        print("   ✅ Created sessions created_at index")
        
        # 6. TTL index for automatic session cleanup (expires after session expiry)
        await db.sessions.create_index([
            ("expires_at", 1)
        ], expireAfterSeconds=3600, name="session_ttl")  # Clean up 1 hour after expiry
        print("   ✅ Created TTL index for automatic session cleanup")
        
        print(f"\n🎉 USER MANAGEMENT INDEXES CREATED SUCCESSFULLY!")
        print("   Total indexes created: 14 (8 users + 6 sessions)")
        
        # Verify indexes
        print("\n🔍 VERIFYING INDEXES...")
        users_indexes = await db.users.list_indexes().to_list(length=None)
        sessions_indexes = await db.sessions.list_indexes().to_list(length=None)
        
        print(f"\n👥 Users collection indexes ({len(users_indexes)}):")
        for idx in users_indexes:
            print(f"   - {idx['name']}: {idx.get('key', 'N/A')}")
        
        print(f"\n🔐 Sessions collection indexes ({len(sessions_indexes)}):")
        for idx in sessions_indexes:
            print(f"   - {idx['name']}: {idx.get('key', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_user_indexes())