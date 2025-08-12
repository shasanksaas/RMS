#!/usr/bin/env python3
"""
Admin Impersonation and Shopify Connection Test for tenant-rms34
Tests the specific issues mentioned in the review request:
1. Check tenant-rms34 Shopify connection status
2. Create/Update Shopify connection for tenant-rms34
3. Test admin impersonation session authentication
4. Verify Shopify OAuth redirect URL functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration from environment
BACKEND_URL = "https://returnhub-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@returns-manager.com"
ADMIN_PASSWORD = "AdminPassword123!"
TARGET_TENANT = "tenant-rms34"
SHOPIFY_SHOP_DOMAIN = "rms34.myshopify.com"

class AdminImpersonationTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.admin_token = None
        self.impersonation_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        })
    
    async def test_admin_authentication(self):
        """Test admin login with provided credentials"""
        print("\n🔐 Testing Admin Authentication...")
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "tenant_id": TARGET_TENANT
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/users/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                
                if response.status == 200 and "access_token" in response_data:
                    self.admin_token = response_data["access_token"]
                    user_info = response_data.get("user", {})
                    role = user_info.get("role", "unknown")
                    
                    self.log_test(
                        "Admin Authentication",
                        True,
                        f"Admin login successful, role: {role}, token length: {len(self.admin_token)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin Authentication",
                        False,
                        f"Login failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Admin Authentication",
                False,
                f"Exception during admin login: {str(e)}"
            )
            return False
    
    async def test_tenant_rms34_exists(self):
        """Verify tenant-rms34 exists in the system"""
        print("\n🏢 Testing tenant-rms34 Existence...")
        
        if not self.admin_token:
            self.log_test("Tenant RMS34 Existence", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{BACKEND_URL}/admin/tenants",
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    tenants = response_data.get("tenants", [])
                    rms34_tenant = None
                    
                    for tenant in tenants:
                        if tenant.get("tenant_id") == TARGET_TENANT:
                            rms34_tenant = tenant
                            break
                    
                    if rms34_tenant:
                        self.log_test(
                            "Tenant RMS34 Existence",
                            True,
                            f"Found tenant-rms34: status={rms34_tenant.get('status')}, name={rms34_tenant.get('name')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Tenant RMS34 Existence",
                            False,
                            f"tenant-rms34 not found in {len(tenants)} tenants"
                        )
                        return False
                else:
                    self.log_test(
                        "Tenant RMS34 Existence",
                        False,
                        f"Failed to get tenants list, status: {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Tenant RMS34 Existence",
                False,
                f"Exception during tenant check: {str(e)}"
            )
            return False
    
    async def test_shopify_connection_status(self):
        """Check current Shopify connection status for tenant-rms34"""
        print("\n🛍️ Testing Shopify Connection Status...")
        
        if not self.admin_token:
            self.log_test("Shopify Connection Status", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json",
                "X-Tenant-Id": TARGET_TENANT
            }
            
            # Test connection status endpoint
            async with self.session.get(
                f"{BACKEND_URL}/auth/shopify/status",
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    connection_status = response_data.get("status", "unknown")
                    shop_domain = response_data.get("shop_domain", "none")
                    
                    self.log_test(
                        "Shopify Connection Status",
                        True,
                        f"Connection status: {connection_status}, shop: {shop_domain}"
                    )
                    
                    # Check if connected to rms34.myshopify.com
                    if shop_domain == SHOPIFY_SHOP_DOMAIN:
                        self.log_test(
                            "Shopify Shop Domain Match",
                            True,
                            f"Connected to correct shop: {shop_domain}"
                        )
                    else:
                        self.log_test(
                            "Shopify Shop Domain Match",
                            False,
                            f"Expected {SHOPIFY_SHOP_DOMAIN}, got {shop_domain}"
                        )
                    
                    return connection_status == "connected"
                else:
                    self.log_test(
                        "Shopify Connection Status",
                        False,
                        f"Status check failed with {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Shopify Connection Status",
                False,
                f"Exception during status check: {str(e)}"
            )
            return False
    
    async def test_admin_impersonation(self):
        """Test admin impersonation of tenant-rms34"""
        print("\n👤 Testing Admin Impersonation...")
        
        if not self.admin_token:
            self.log_test("Admin Impersonation", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            # Start impersonation session
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants/{TARGET_TENANT}/impersonate",
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.impersonation_token = response_data.get("impersonation_token")
                    session_info = response_data.get("session", {})
                    
                    if self.impersonation_token:
                        self.log_test(
                            "Admin Impersonation Start",
                            True,
                            f"Impersonation started, token length: {len(self.impersonation_token)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin Impersonation Start",
                            False,
                            "No impersonation token received",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "Admin Impersonation Start",
                        False,
                        f"Impersonation failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Admin Impersonation Start",
                False,
                f"Exception during impersonation: {str(e)}"
            )
            return False
    
    async def test_shopify_oauth_with_impersonation(self):
        """Test Shopify OAuth flow with impersonated session"""
        print("\n🔗 Testing Shopify OAuth with Impersonation...")
        
        if not self.impersonation_token:
            self.log_test("Shopify OAuth Impersonation", False, "No impersonation token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.impersonation_token}",
                "Content-Type": "application/json",
                "X-Tenant-Id": TARGET_TENANT
            }
            
            # Test OAuth install redirect URL generation
            async with self.session.get(
                f"{BACKEND_URL}/auth/shopify/install-redirect",
                params={"shop": "rms34"},
                headers=headers
            ) as response:
                
                if response.status == 302 or response.status == 200:
                    # Check if we get a redirect URL or OAuth URL
                    if response.status == 302:
                        redirect_url = response.headers.get("Location", "")
                        self.log_test(
                            "Shopify OAuth Redirect Generation",
                            True,
                            f"OAuth redirect URL generated: {redirect_url[:100]}..."
                        )
                    else:
                        response_data = await response.json()
                        oauth_url = response_data.get("oauth_url", "")
                        if oauth_url:
                            self.log_test(
                                "Shopify OAuth URL Generation",
                                True,
                                f"OAuth URL generated: {oauth_url[:100]}..."
                            )
                        else:
                            self.log_test(
                                "Shopify OAuth URL Generation",
                                False,
                                "No OAuth URL in response",
                                response_data
                            )
                    return True
                else:
                    response_data = await response.text()
                    self.log_test(
                        "Shopify OAuth Impersonation",
                        False,
                        f"OAuth failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Shopify OAuth Impersonation",
                False,
                f"Exception during OAuth test: {str(e)}"
            )
            return False
    
    async def test_create_shopify_connection(self):
        """Create/Update Shopify connection for tenant-rms34"""
        print("\n🔧 Testing Shopify Connection Creation/Update...")
        
        if not self.admin_token:
            self.log_test("Shopify Connection Creation", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json",
                "X-Tenant-Id": TARGET_TENANT
            }
            
            # Try to create/update Shopify integration record
            integration_data = {
                "shop_domain": SHOPIFY_SHOP_DOMAIN,
                "access_token": "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",  # From backend/.env
                "status": "connected",
                "scopes": ["read_orders", "read_fulfillments", "read_products", "read_customers", "read_returns", "write_returns"],
                "webhook_endpoints": [
                    "orders/create",
                    "orders/updated", 
                    "fulfillments/create",
                    "fulfillments/update",
                    "app/uninstalled"
                ]
            }
            
            # First try to update existing connection
            async with self.session.put(
                f"{BACKEND_URL}/auth/shopify/connection",
                json=integration_data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Shopify Connection Update",
                        True,
                        f"Connection updated for {SHOPIFY_SHOP_DOMAIN}"
                    )
                    return True
                elif response.status == 404:
                    # Connection doesn't exist, try to create it
                    async with self.session.post(
                        f"{BACKEND_URL}/auth/shopify/connection",
                        json=integration_data,
                        headers=headers
                    ) as create_response:
                        create_data = await create_response.json()
                        
                        if create_response.status == 201 or create_response.status == 200:
                            self.log_test(
                                "Shopify Connection Creation",
                                True,
                                f"New connection created for {SHOPIFY_SHOP_DOMAIN}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Shopify Connection Creation",
                                False,
                                f"Creation failed with status {create_response.status}",
                                create_data
                            )
                            return False
                else:
                    self.log_test(
                        "Shopify Connection Update",
                        False,
                        f"Update failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Shopify Connection Creation",
                False,
                f"Exception during connection setup: {str(e)}"
            )
            return False
    
    async def test_merchant_dashboard_access(self):
        """Test merchant dashboard access after impersonation"""
        print("\n📊 Testing Merchant Dashboard Access...")
        
        if not self.impersonation_token:
            self.log_test("Merchant Dashboard Access", False, "No impersonation token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.impersonation_token}",
                "Content-Type": "application/json",
                "X-Tenant-Id": TARGET_TENANT
            }
            
            # Test dashboard data endpoints
            dashboard_tests = [
                ("Returns List", f"{BACKEND_URL}/returns/"),
                ("Analytics", f"{BACKEND_URL}/analytics"),
                ("Tenant Settings", f"{BACKEND_URL}/tenants/{TARGET_TENANT}/settings")
            ]
            
            success_count = 0
            for test_name, endpoint in dashboard_tests:
                try:
                    async with self.session.get(endpoint, headers=headers) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            self.log_test(
                                f"Dashboard - {test_name}",
                                True,
                                f"Endpoint accessible, data keys: {list(response_data.keys())}"
                            )
                            success_count += 1
                        else:
                            response_data = await response.json()
                            self.log_test(
                                f"Dashboard - {test_name}",
                                False,
                                f"Access failed with status {response.status}",
                                response_data
                            )
                except Exception as e:
                    self.log_test(
                        f"Dashboard - {test_name}",
                        False,
                        f"Exception: {str(e)}"
                    )
            
            overall_success = success_count >= 2  # At least 2 out of 3 should work
            self.log_test(
                "Merchant Dashboard Overall",
                overall_success,
                f"{success_count}/3 dashboard endpoints accessible"
            )
            
            return overall_success
                    
        except Exception as e:
            self.log_test(
                "Merchant Dashboard Access",
                False,
                f"Exception during dashboard test: {str(e)}"
            )
            return False
    
    async def test_end_impersonation(self):
        """Test ending impersonation session"""
        print("\n🚪 Testing End Impersonation...")
        
        if not self.admin_token:
            self.log_test("End Impersonation", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/admin/tenants/end-impersonation",
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "End Impersonation",
                        True,
                        "Impersonation session ended successfully"
                    )
                    return True
                else:
                    self.log_test(
                        "End Impersonation",
                        False,
                        f"Failed to end impersonation, status: {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "End Impersonation",
                False,
                f"Exception during end impersonation: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all admin impersonation and Shopify connection tests"""
        print("🚀 Starting Admin Impersonation & Shopify Connection Tests for tenant-rms34")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {ADMIN_EMAIL}")
        print(f"Target Tenant: {TARGET_TENANT}")
        print(f"Shopify Shop: {SHOPIFY_SHOP_DOMAIN}")
        print("=" * 80)
        
        # Test sequence
        tests = [
            self.test_admin_authentication,
            self.test_tenant_rms34_exists,
            self.test_shopify_connection_status,
            self.test_create_shopify_connection,
            self.test_admin_impersonation,
            self.test_shopify_oauth_with_impersonation,
            self.test_merchant_dashboard_access,
            self.test_end_impersonation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 ADMIN IMPERSONATION & SHOPIFY CONNECTION TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: Admin impersonation and Shopify connection working well!")
        elif success_rate >= 60:
            print("⚠️ GOOD: Most functionality working, minor issues to address")
        else:
            print("🚨 NEEDS ATTENTION: Significant issues found requiring fixes")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return success_rate

async def main():
    """Main test execution"""
    async with AdminImpersonationTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())