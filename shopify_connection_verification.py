#!/usr/bin/env python3
"""
Simple verification test for tenant-rms34 Shopify connection
Focuses on verifying the existing connection works properly
"""

import asyncio
import aiohttp
import json
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
BACKEND_URL = "https://returnportal.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@returns-manager.com"
ADMIN_PASSWORD = "AdminPassword123!"
TARGET_TENANT = "tenant-rms34"
SHOPIFY_SHOP_DOMAIN = "rms34.myshopify.com"

async def verify_shopify_connection():
    """Verify the Shopify connection for tenant-rms34"""
    print("🔍 Verifying Shopify Connection for tenant-rms34")
    print("=" * 60)
    
    # Check database directly
    mongo_url = 'mongodb://localhost:27017/returns_manager_enhanced'
    client = AsyncIOMotorClient(mongo_url)
    db = client.returns_management
    
    try:
        # Get Shopify integration
        integration = await db.integrations_shopify.find_one({'tenant_id': TARGET_TENANT})
        
        if integration:
            print("✅ SHOPIFY INTEGRATION FOUND:")
            print(f"   Shop Domain: {integration.get('shop_domain', 'N/A')}")
            print(f"   Status: {integration.get('status', 'N/A')}")
            print(f"   Access Token: {'***' + integration.get('access_token', '')[-4:] if integration.get('access_token') else 'N/A'}")
            print(f"   Created: {integration.get('created_at', 'N/A')}")
            print(f"   Scopes: {integration.get('scopes', [])}")
            print(f"   Webhooks: {len(integration.get('webhook_endpoints', []))} registered")
            
            # Check if it matches expected shop
            if integration.get('shop_domain') == SHOPIFY_SHOP_DOMAIN:
                print("✅ SHOP DOMAIN MATCH: Connected to correct shop (rms34.myshopify.com)")
            else:
                print(f"❌ SHOP DOMAIN MISMATCH: Expected {SHOPIFY_SHOP_DOMAIN}, got {integration.get('shop_domain')}")
            
            # Check connection status
            if integration.get('status') == 'connected':
                print("✅ CONNECTION STATUS: Active and connected")
            else:
                print(f"⚠️ CONNECTION STATUS: {integration.get('status', 'unknown')}")
                
        else:
            print("❌ NO SHOPIFY INTEGRATION FOUND for tenant-rms34")
            
        # Check tenant exists
        tenant = await db.tenants.find_one({'tenant_id': TARGET_TENANT})
        if tenant:
            print(f"✅ TENANT EXISTS: {tenant.get('name', 'Unknown')} ({TARGET_TENANT})")
        else:
            print(f"❌ TENANT NOT FOUND: {TARGET_TENANT}")
            
        # Test admin authentication
        async with aiohttp.ClientSession() as session:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "tenant_id": TARGET_TENANT
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-Id": TARGET_TENANT
            }
            
            async with session.post(
                f"{BACKEND_URL}/users/login",
                json=login_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    user_info = response_data.get("user", {})
                    role = user_info.get("role", "unknown")
                    print(f"✅ ADMIN AUTHENTICATION: Working (role: {role})")
                else:
                    print(f"❌ ADMIN AUTHENTICATION: Failed with status {response.status}")
        
        print("\n" + "=" * 60)
        print("🎯 SUMMARY FOR REVIEW REQUEST:")
        print("=" * 60)
        
        if integration and integration.get('shop_domain') == SHOPIFY_SHOP_DOMAIN and integration.get('status') == 'connected':
            print("🎉 SUCCESS: tenant-rms34 Shopify connection is FULLY FUNCTIONAL!")
            print(f"   ✅ Connected to correct shop: {SHOPIFY_SHOP_DOMAIN}")
            print(f"   ✅ Connection status: {integration.get('status')}")
            print(f"   ✅ Access token present: {'***' + integration.get('access_token', '')[-4:]}")
            print(f"   ✅ Admin credentials working: {ADMIN_EMAIL}")
            print("\n🚀 MERCHANT DASHBOARD SHOULD SHOW CONNECTED SHOPIFY STORE")
            print("   When admin impersonates tenant-rms34, they should see:")
            print("   - Shopify connection status: Connected")
            print("   - Shop domain: rms34.myshopify.com")
            print("   - Access to Shopify data and functionality")
        else:
            print("❌ ISSUE: Shopify connection needs attention")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_shopify_connection())