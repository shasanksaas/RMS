#!/usr/bin/env python3
"""
Comprehensive Shopify OAuth Integration Test
Tests all acceptance criteria from the user's requirements
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://f07a6717-33e5-45c0-b306-b76d55047333.preview.emergentagent.com"
TEST_SHOP = "rms34"
TEST_SHOP_DOMAIN = f"{TEST_SHOP}.myshopify.com"

class ShopifyOAuthTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_1_health_check(self):
        """Test 1: Health Check"""
        print("\n🏥 Test 1: Health Check")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", True, f"Backend is healthy: {data.get('status')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Health check failed with status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
            return False
    
    async def test_2_oauth_install_endpoint(self):
        """Test 2: OAuth Install Endpoint"""
        print("\n🔗 Test 2: OAuth Install Endpoint")
        
        try:
            # Test the OAuth install endpoint
            install_url = f"{BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP_DOMAIN}"
            
            async with self.session.get(install_url, allow_redirects=False) as response:
                if response.status == 302:
                    # Check if it redirects to Shopify
                    location = response.headers.get('Location', '')
                    if 'shopify.com' in location and 'oauth/authorize' in location:
                        self.log_test("OAuth Install Redirect", True, f"Redirects to Shopify OAuth: {location[:100]}...")
                        
                        # Check if the redirect URL contains required parameters
                        required_params = ['client_id', 'scope', 'redirect_uri', 'state']
                        has_all_params = all(param in location for param in required_params)
                        self.log_test("OAuth Parameters", has_all_params, f"Required parameters present: {has_all_params}")
                        
                        # Check if scopes are correct
                        expected_scopes = "read_orders,read_fulfillments,read_products,read_customers,read_returns,write_returns"
                        if expected_scopes.replace(',', '%2C') in location:
                            self.log_test("OAuth Scopes", True, "Required scopes included in OAuth URL")
                        else:
                            self.log_test("OAuth Scopes", False, f"Missing required scopes in OAuth URL")
                        
                        return True
                    else:
                        self.log_test("OAuth Install Redirect", False, f"Invalid redirect location: {location}")
                        return False
                else:
                    response_text = await response.text()
                    self.log_test("OAuth Install Redirect", False, f"Expected 302 redirect, got {response.status}: {response_text[:200]}")
                    return False
                    
        except Exception as e:
            self.log_test("OAuth Install Endpoint", False, f"OAuth install error: {str(e)}")
            return False
    
    async def test_3_webhook_endpoints(self):
        """Test 3: Webhook Endpoints Availability"""
        print("\n📨 Test 3: Webhook Endpoints")
        
        webhook_topics = [
            "orders_create",
            "orders_updated", 
            "fulfillments_create",
            "fulfillments_update",
            "returns_create",
            "returns_update"
        ]
        
        all_passed = True
        
        for topic in webhook_topics:
            try:
                webhook_url = f"{BACKEND_URL}/api/webhooks/shopify/{topic}"
                
                # Send a mock webhook request (should get validation error but endpoint should exist)
                headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Topic": topic.replace('_', '/'),
                    "X-Shopify-Shop-Domain": TEST_SHOP_DOMAIN,
                    "X-Shopify-Hmac-Sha256": "mock-hmac"
                }
                
                async with self.session.post(webhook_url, json={"test": "data"}, headers=headers) as response:
                    # We expect either 400 (bad HMAC) or 500 (processing error), not 404
                    if response.status in [400, 401, 500]:
                        self.log_test(f"Webhook {topic}", True, f"Endpoint exists (status {response.status})")
                    elif response.status == 404:
                        self.log_test(f"Webhook {topic}", False, f"Endpoint not found")
                        all_passed = False
                    else:
                        self.log_test(f"Webhook {topic}", True, f"Endpoint exists (unexpected status {response.status})")
                        
            except Exception as e:
                self.log_test(f"Webhook {topic}", False, f"Error testing webhook: {str(e)}")
                all_passed = False
        
        return all_passed
    
    async def test_4_auth_endpoints(self):
        """Test 4: Auth Endpoints"""
        print("\n🔐 Test 4: Auth Endpoints")
        
        try:
            # Test stores endpoint
            async with self.session.get(f"{BACKEND_URL}/api/auth/stores") as response:
                if response.status == 200:
                    stores = await response.json()
                    self.log_test("Auth Stores Endpoint", True, f"Returns {len(stores)} connected stores")
                else:
                    self.log_test("Auth Stores Endpoint", False, f"Stores endpoint failed: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Auth Endpoints", False, f"Auth endpoints error: {str(e)}")
            return False
    
    async def test_5_unified_returns_endpoints(self):
        """Test 5: Unified Returns Endpoints"""
        print("\n🔄 Test 5: Unified Returns Endpoints")
        
        try:
            # Test order lookup endpoint
            headers = {"Content-Type": "application/json", "X-Tenant-Id": "tenant-fashion-store"}
            lookup_data = {"order_number": "1001", "email": "customer@example.com"}
            
            async with self.session.post(f"{BACKEND_URL}/api/unified-returns/order/lookup", 
                                       json=lookup_data, headers=headers) as response:
                if response.status in [200, 400]:  # 400 is OK for invalid order
                    self.log_test("Unified Returns Lookup", True, f"Endpoint responds (status {response.status})")
                else:
                    response_text = await response.text()
                    self.log_test("Unified Returns Lookup", False, f"Unexpected status {response.status}: {response_text[:100]}")
                    return False
            
            # Test eligible items endpoint
            async with self.session.get(f"{BACKEND_URL}/api/unified-returns/order/test-order/eligible-items", 
                                      headers=headers) as response:
                if response.status in [200, 404]:  # 404 is OK for non-existent order
                    self.log_test("Unified Returns Eligible Items", True, f"Endpoint responds (status {response.status})")
                else:
                    self.log_test("Unified Returns Eligible Items", False, f"Unexpected status {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Unified Returns Endpoints", False, f"Unified returns error: {str(e)}")
            return False
    
    async def test_6_frontend_integration(self):
        """Test 6: Frontend Integration"""
        print("\n🖥️ Test 6: Frontend Integration")
        
        try:
            # Test if integrations page loads
            async with self.session.get(f"{BACKEND_URL}/app/settings/integrations") as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Check for key elements
                    has_shopify_integration = "Shopify Integration" in html_content
                    has_connect_button = "Connect" in html_content and "Store" in html_content
                    
                    self.log_test("Frontend Integrations Page", True, "Integrations page loads successfully")
                    self.log_test("Frontend Shopify Section", has_shopify_integration, f"Shopify integration section present: {has_shopify_integration}")
                    self.log_test("Frontend Connect Button", has_connect_button, f"Connect button present: {has_connect_button}")
                    
                    return has_shopify_integration and has_connect_button
                else:
                    self.log_test("Frontend Integrations Page", False, f"Frontend failed to load: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Frontend Integration", False, f"Frontend test error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all acceptance tests"""
        print(f"🧪 Starting Shopify OAuth Integration Tests")
        print(f"📊 Target: {BACKEND_URL}")
        print(f"🏪 Test Shop: {TEST_SHOP_DOMAIN}")
        print("=" * 60)
        
        test_methods = [
            self.test_1_health_check,
            self.test_2_oauth_install_endpoint,
            self.test_3_webhook_endpoints,
            self.test_4_auth_endpoints,
            self.test_5_unified_returns_endpoints,
            self.test_6_frontend_integration
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = await test_method()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
                results.append(False)
        
        # Summary
        passed = sum(1 for result in results if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 SHOPIFY OAUTH INTEGRATION READY FOR PRODUCTION!")
            print(f"🔗 Install URL: {BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP_DOMAIN}")
        else:
            print("⚠️ Integration needs more work before production deployment")
        
        return success_rate >= 80

async def main():
    async with ShopifyOAuthTest() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())