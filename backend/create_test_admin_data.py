"""
Create test admin user and sample tenant data for testing the tenant management system
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the src directory to the Python path
sys.path.append('/app/backend/src')

from src.config.database import get_database
from src.services.auth_service import AuthService
from src.services.tenant_service_enhanced import TenantServiceEnhanced
from src.models.user import UserCreate
import uuid

# Initialize services
auth_service = AuthService()

async def create_test_admin_user():
    """Create a test admin user"""
    print("Creating test admin user...")
    
    db = await get_database()
    
    # Check if admin already exists (admin users have no tenant_id)
    try:
        existing_admin = await auth_service.get_user_by_email(None, "admin@test.com")
        if existing_admin:
            print("✅ Admin user already exists: admin@test.com")
            return existing_admin
    except:
        pass  # Admin doesn't exist, create it
    
    # Create admin user
    admin_data = UserCreate(
        email="admin@test.com",
        password="admin123",
        first_name="Admin",
        last_name="User",
        role="admin",
        tenant_id=None  # Admin has no specific tenant
    )
    
    try:
        admin_user = await auth_service.create_user(admin_data, created_by=None)
        print(f"✅ Created admin user: {admin_user.email}")
        return admin_user
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return None

async def create_test_tenants():
    """Create sample tenants for testing"""
    print("Creating test tenants...")
    
    db = await get_database()
    tenant_service = TenantServiceEnhanced(db)
    
    # Sample tenants to create
    test_tenants = [
        {
            "name": "Fashion Forward Store",
            "tenant_id": "tenant-fashion-forward-demo",
            "status": "new",
            "notes": "Demo tenant for fashion retail testing"
        },
        {
            "name": "Tech Gadgets Hub",
            "tenant_id": "tenant-tech-gadgets-demo", 
            "status": "new",
            "notes": "Demo tenant for electronics retail testing"
        },
        {
            "name": "Home & Garden Co",
            "tenant_id": "tenant-home-garden-demo",
            "status": "new", 
            "notes": "Demo tenant for home goods testing"
        }
    ]
    
    created_tenants = []
    
    for tenant_data in test_tenants:
        try:
            # Check if tenant already exists
            existing = await tenant_service.get_tenant_by_id(tenant_data["tenant_id"])
            if existing:
                print(f"✅ Tenant already exists: {tenant_data['tenant_id']}")
                created_tenants.append(existing)
                continue
        except:
            pass  # Tenant doesn't exist, create it
        
        try:
            tenant = await tenant_service.create_tenant(
                name=tenant_data["name"],
                tenant_id=tenant_data["tenant_id"],
                status=tenant_data["status"],
                notes=tenant_data["notes"]
            )
            print(f"✅ Created tenant: {tenant.tenant_id} - {tenant.name}")
            created_tenants.append(tenant)
        except Exception as e:
            print(f"❌ Failed to create tenant {tenant_data['tenant_id']}: {e}")
    
    return created_tenants

async def create_test_merchant_users():
    """Create test merchant users for demo tenants"""
    print("Creating test merchant users...")
    
    db = await get_database()
    
    # Test merchant users
    test_merchants = [
        {
            "email": "merchant1@test.com",
            "password": "merchant123",
            "first_name": "John",
            "last_name": "Merchant",
            "role": "merchant",
            "tenant_id": "tenant-fashion-forward-demo"
        },
        {
            "email": "merchant2@test.com", 
            "password": "merchant123",
            "first_name": "Sarah",
            "last_name": "Store",
            "role": "merchant",
            "tenant_id": "tenant-tech-gadgets-demo"
        }
    ]
    
    created_merchants = []
    
    for merchant_data in test_merchants:
        try:
            # Check if merchant already exists
            existing = await auth_service.get_user_by_email(merchant_data["tenant_id"], merchant_data["email"])
            if existing:
                print(f"✅ Merchant user already exists: {merchant_data['email']}")
                created_merchants.append(existing)
                continue
        except:
            pass  # Merchant doesn't exist, create it
        
        try:
            merchant_user = UserCreate(**merchant_data)
            merchant = await auth_service.create_user(merchant_user, created_by=None)
            print(f"✅ Created merchant user: {merchant.email} for tenant {merchant_data['tenant_id']}")
            created_merchants.append(merchant)
        except Exception as e:
            print(f"❌ Failed to create merchant {merchant_data['email']}: {e}")
    
    return created_merchants

async def update_tenant_statuses():
    """Update tenant statuses based on claimed merchants"""
    print("Updating tenant statuses...")
    
    db = await get_database()
    tenant_service = TenantServiceEnhanced(db)
    
    # Update tenants that have merchants to "claimed" status
    tenants_with_merchants = [
        "tenant-fashion-forward-demo",
        "tenant-tech-gadgets-demo"
    ]
    
    for tenant_id in tenants_with_merchants:
        try:
            tenant = await tenant_service.get_tenant_by_id(tenant_id)
            if tenant and tenant.status == "new":
                updated_tenant = await tenant_service.claim_tenant(
                    tenant_id,
                    claimed_by_email="merchant@test.com",
                    claimed_by_name="Test Merchant"
                )
                print(f"✅ Updated tenant {tenant_id} status to: {updated_tenant.status}")
        except Exception as e:
            print(f"❌ Failed to update tenant status {tenant_id}: {e}")

async def print_test_credentials():
    """Print test credentials for user"""
    print("\n" + "="*80)
    print("🎉 TEST DATA SETUP COMPLETE!")
    print("="*80)
    print("\n📧 TEST CREDENTIALS:")
    print("\n1️⃣ ADMIN ACCOUNT:")
    print("   Email: admin@test.com")  
    print("   Password: admin123")
    print("   Role: admin")
    print("   Access: Full tenant management")
    
    print("\n2️⃣ MERCHANT ACCOUNTS:")
    print("   Email: merchant1@test.com")
    print("   Password: merchant123")
    print("   Role: merchant")  
    print("   Tenant: tenant-fashion-forward-demo")
    
    print("\n   Email: merchant2@test.com")
    print("   Password: merchant123")
    print("   Role: merchant")
    print("   Tenant: tenant-tech-gadgets-demo")
    
    print("\n3️⃣ TEST TENANT IDs FOR MERCHANT SIGNUP:")
    print("   • tenant-fashion-forward-demo (Fashion Forward Store)")
    print("   • tenant-tech-gadgets-demo (Tech Gadgets Hub)")  
    print("   • tenant-home-garden-demo (Home & Garden Co) - Available for new signups")
    
    print("\n📋 TESTING WORKFLOW:")
    print("1. Login as admin → Create/manage tenants at /admin/tenants")
    print("2. Copy tenant ID from admin panel")  
    print("3. Use merchant signup at /signup with tenant ID")
    print("4. Login as merchant → Connect Shopify store → See live data")
    
    print("\n🌐 TESTING URLS:")
    print("   • Admin Login: /auth/login")
    print("   • Merchant Signup: /signup")
    print("   • Admin Dashboard: /admin/tenants")
    print("   • Merchant Dashboard: /app/dashboard")
    
    print("="*80)

async def main():
    """Main setup function"""
    print("🚀 Setting up test admin and tenant data...")
    print("="*50)
    
    try:
        # Create admin user
        admin_user = await create_test_admin_user()
        
        # Create test tenants
        tenants = await create_test_tenants()
        
        # Create test merchant users
        merchants = await create_test_merchant_users()
        
        # Update tenant statuses
        await update_tenant_statuses()
        
        # Print test credentials
        await print_test_credentials()
        
        print("\n✅ Test data setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test data setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())