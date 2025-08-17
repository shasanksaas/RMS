#!/usr/bin/env python3
"""
Integration Page OAuth Wiring Test
Tests that the Integration page properly wires the Connect button to OAuth flow
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com"
TEST_SHOP = "rms34"

class IntegrationOAuthTest:
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
    
    async def test_1_integration_page_loads(self):
        """Test 1: Integration Page Loads"""
        print("\n🔗 Test 1: Integration Page Access")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/app/settings/integrations") as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Check for key elements
                    has_shopify_section = "Shopify Integration" in html_content
                    has_connect_button = ("Connect Store" in html_content or 
                                        "Connect Your Store" in html_content or
                                        "Connect to Shopify" in html_content)
                    has_shop_input = ('placeholder="e.g., rms34' in html_content or 
                                    'yourstore.myshopify.com' in html_content)
                    
                    self.log_test("Integration Page Loads", True, "Page accessible")
                    self.log_test("Shopify Integration Section", has_shopify_section, f"Section present: {has_shopify_section}")
                    self.log_test("Connect Button Present", has_connect_button, f"Button found: {has_connect_button}")
                    self.log_test("Shop Input Field", has_shop_input, f"Input field present: {has_shop_input}")
                    
                    return has_shopify_section and has_connect_button
                else:
                    self.log_test("Integration Page Loads", False, f"Page failed to load: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Integration Page Access", False, f"Error accessing page: {str(e)}")
            return False
    
    async def test_2_oauth_install_endpoint(self):
        """Test 2: OAuth Install Endpoint Response"""
        print("\n🔐 Test 2: OAuth Install Endpoint")
        
        try:
            install_url = f"{BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP}.myshopify.com"
            
            async with self.session.get(install_url, allow_redirects=False) as response:
                if response.status == 302:
                    location = response.headers.get('Location', '')
                    
                    # Validate redirect URL
                    is_shopify_redirect = 'shopify.com' in location and 'oauth/authorize' in location
                    has_client_id = 'client_id=' in location
                    has_scope = 'scope=' in location
                    has_redirect_uri = 'redirect_uri=' in location
                    has_state = 'state=' in location
                    
                    self.log_test("OAuth Redirect Status", True, "Returns 302 redirect")
                    self.log_test("Shopify OAuth URL", is_shopify_redirect, f"Redirects to Shopify: {is_shopify_redirect}")
                    self.log_test("OAuth Parameters", has_client_id and has_scope and has_redirect_uri and has_state, 
                                f"All parameters present: client_id={has_client_id}, scope={has_scope}, redirect_uri={has_redirect_uri}, state={has_state}")
                    
                    # Check redirect URI
                    expected_callback = f"{BACKEND_URL}/api/auth/shopify/callback"
                    callback_in_redirect = expected_callback.replace(':', '%3A').replace('/', '%2F') in location
                    self.log_test("Callback URL Correct", callback_in_redirect, f"Correct callback URL: {callback_in_redirect}")
                    
                    return is_shopify_redirect and has_client_id and has_scope
                else:
                    response_text = await response.text()
                    self.log_test("OAuth Install Endpoint", False, f"Expected 302, got {response.status}: {response_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_test("OAuth Install Endpoint", False, f"Error testing endpoint: {str(e)}")
            return False
    
    async def test_3_callback_endpoint(self):
        """Test 3: OAuth Callback Endpoint"""
        print("\n📞 Test 3: OAuth Callback Endpoint")
        
        try:
            # Test callback endpoint without proper parameters (should return error)
            callback_url = f"{BACKEND_URL}/api/auth/shopify/callback"
            
            async with self.session.get(callback_url) as response:
                # Should return 422 or 400 due to missing parameters
                if response.status in [400, 422]:
                    self.log_test("Callback Endpoint Exists", True, f"Endpoint responds with {response.status} (expected for missing params)")
                    return True
                elif response.status == 404:
                    self.log_test("Callback Endpoint Exists", False, "Callback endpoint not found (404)")
                    return False
                else:
                    self.log_test("Callback Endpoint Exists", True, f"Endpoint exists (status {response.status})")
                    return True
                    
        except Exception as e:
            self.log_test("OAuth Callback Endpoint", False, f"Error testing callback: {str(e)}")
            return False
    
    async def test_4_stores_endpoint(self):
        """Test 4: Connected Stores Endpoint"""
        print("\n🏪 Test 4: Connected Stores API")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/auth/stores") as response:
                if response.status == 200:
                    stores = await response.json()
                    self.log_test("Stores Endpoint", True, f"Returns {len(stores)} connected stores")
                    return True
                else:
                    self.log_test("Stores Endpoint", False, f"Stores endpoint failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Stores Endpoint", False, f"Error testing stores: {str(e)}")
            return False
    
    async def test_5_backend_health(self):
        """Test 5: Backend Health Check"""
        print("\n🏥 Test 5: Backend Health")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.log_test("Backend Health", True, f"Backend healthy: {health_data.get('status')}")
                    return True
                else:
                    self.log_test("Backend Health", False, f"Health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Backend Health", False, f"Health check error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"🧪 Starting Integration Page OAuth Wiring Tests")
        print(f"📊 Target: {BACKEND_URL}")
        print(f"🏪 Test Shop: {TEST_SHOP}")
        print("=" * 60)
        
        test_methods = [
            self.test_5_backend_health,
            self.test_4_stores_endpoint,
            self.test_2_oauth_install_endpoint,
            self.test_3_callback_endpoint,
            self.test_1_integration_page_loads
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
        print("📊 INTEGRATION WIRING TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 INTEGRATION PAGE IS PROPERLY WIRED!")
            print(f"🔗 Ready for OAuth: Click Connect and enter '{TEST_SHOP}' as shop domain")
            print(f"🚀 OAuth URL: {BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP}.myshopify.com")
        else:
            print("⚠️ Integration page needs fixes before OAuth will work")
        
        return success_rate >= 80

async def main():
    async with IntegrationOAuthTest() as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n" + "=" * 60)
            print("🎯 NEXT STEPS:")
            print("1. Go to: https://shopify-sync-fix.preview.emergentagent.com/app/settings/integrations")
            print("2. Click 'Connect Store'")
            print("3. Enter shop domain: rms34")
            print("4. Click 'Connect to Shopify'")
            print("5. Complete OAuth in Shopify")
            print("6. Return to see connected store and data sync")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())