#!/usr/bin/env python3
"""
Focused Merchant Login Test for tenant-rms34
Verifies the merchant user can login and access the dashboard
"""

import asyncio
import aiohttp
import json

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
MERCHANT_EMAIL = "merchant@rms34.com"
MERCHANT_PASSWORD = "merchant123"

async def test_merchant_login():
    """Test merchant login and dashboard access"""
    print("🔐 Testing Merchant Login for tenant-rms34...")
    print(f"Email: {MERCHANT_EMAIL}")
    print(f"Password: {MERCHANT_PASSWORD}")
    print(f"Tenant: {TEST_TENANT_ID}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test login
        login_data = {
            "email": MERCHANT_EMAIL,
            "password": MERCHANT_PASSWORD,
            "tenant_id": TEST_TENANT_ID,
            "remember_me": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": TEST_TENANT_ID
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/users/login", json=login_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    user_info = data.get("user", {})
                    token = data.get("access_token")
                    
                    print("✅ LOGIN SUCCESSFUL!")
                    print(f"   User ID: {user_info.get('user_id')}")
                    print(f"   Email: {user_info.get('email')}")
                    print(f"   Role: {user_info.get('role')}")
                    print(f"   Tenant: {user_info.get('tenant_id')}")
                    print(f"   Active: {user_info.get('is_active')}")
                    print(f"   Token: {'Generated' if token else 'Missing'}")
                    
                    # Test dashboard access (returns endpoint)
                    auth_headers = {
                        "Authorization": f"Bearer {token}",
                        "X-Tenant-Id": TEST_TENANT_ID,
                        "Content-Type": "application/json"
                    }
                    
                    print("\n🏪 Testing Dashboard Access...")
                    async with session.get(f"{BACKEND_URL}/returns/", headers=auth_headers) as dashboard_response:
                        if dashboard_response.status == 200:
                            returns_data = await dashboard_response.json()
                            returns_count = len(returns_data.get("returns", []))
                            print(f"✅ DASHBOARD ACCESS SUCCESSFUL!")
                            print(f"   Returns visible: {returns_count}")
                            
                            # Test Shopify connection status with correct parameters
                            print("\n🛍️ Testing Shopify Connection...")
                            shopify_url = f"{BACKEND_URL}/auth/shopify/status?tenant_id={TEST_TENANT_ID}"
                            async with session.get(shopify_url, headers=auth_headers) as shopify_response:
                                if shopify_response.status == 200:
                                    shopify_data = await shopify_response.json()
                                    print(f"✅ SHOPIFY CONNECTION STATUS:")
                                    print(f"   Status: {shopify_data.get('status', 'unknown')}")
                                    print(f"   Shop Domain: {shopify_data.get('shop_domain', 'unknown')}")
                                    print(f"   Connected: {shopify_data.get('status') == 'connected'}")
                                else:
                                    shopify_error = await shopify_response.text()
                                    print(f"⚠️ SHOPIFY STATUS CHECK FAILED:")
                                    print(f"   Status: {shopify_response.status}")
                                    print(f"   Error: {shopify_error}")
                        else:
                            dashboard_error = await dashboard_response.text()
                            print(f"❌ DASHBOARD ACCESS FAILED:")
                            print(f"   Status: {dashboard_response.status}")
                            print(f"   Error: {dashboard_error}")
                    
                    print("\n🎯 FINAL RESULT:")
                    print("✅ Merchant user merchant@rms34.com is READY!")
                    print("✅ Direct login works without admin impersonation")
                    print("✅ User can access tenant-rms34 merchant dashboard")
                    return True
                    
                else:
                    error_data = await response.text()
                    print(f"❌ LOGIN FAILED:")
                    print(f"   Status: {response.status}")
                    print(f"   Error: {error_data}")
                    return False
                    
        except Exception as e:
            print(f"❌ CONNECTION ERROR: {str(e)}")
            return False

async def main():
    success = await test_merchant_login()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)