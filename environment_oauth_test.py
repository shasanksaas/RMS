#!/usr/bin/env python3
"""
Comprehensive Environment-Agnostic OAuth Test
Tests the new automatic environment detection and OAuth configuration
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://35d12e52-b5b0-4c0d-8c1f-a01716e1ddd2.preview.emergentagent.com"
TEST_SHOP = "rms34"

class EnvironmentAgnosticOAuthTest:
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
    
    async def test_1_environment_detection(self):
        """Test 1: Environment Auto-Detection"""
        print("\n🌍 Test 1: Environment Auto-Detection")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/config") as response:
                if response.status == 200:
                    config = await response.json()
                    
                    # Validate configuration
                    has_app_url = bool(config.get("app_url"))
                    has_redirect_uri = bool(config.get("redirect_uri"))
                    shopify_configured = config.get("shopify_configured", False)
                    is_initialized = config.get("initialized", False)
                    environment = config.get("environment", "unknown")
                    
                    # Check that URLs match expected domain
                    app_url = config.get("app_url", "")
                    redirect_uri = config.get("redirect_uri", "")
                    
                    correct_domain = "733d44a0-d288-43eb-83ff-854115be232e.preview.emergentagent.com" in app_url
                    correct_callback = app_url in redirect_uri and "/api/auth/shopify/callback" in redirect_uri
                    
                    self.log_test("Environment Initialized", is_initialized, f"Config initialized: {is_initialized}")
                    self.log_test("APP_URL Detection", has_app_url and correct_domain, f"APP_URL: {app_url}")
                    self.log_test("Redirect URI Generation", has_redirect_uri and correct_callback, f"Redirect URI: {redirect_uri}")
                    self.log_test("Shopify Credentials", shopify_configured, f"Shopify configured: {shopify_configured}")
                    self.log_test("Environment Type", environment in ["production", "development"], f"Environment: {environment}")
                    
                    return all([is_initialized, has_app_url, has_redirect_uri, shopify_configured])
                else:
                    self.log_test("Environment Detection", False, f"Config endpoint failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Environment Detection", False, f"Error: {str(e)}")
            return False
    
    async def test_2_dynamic_oauth_urls(self):
        """Test 2: Dynamic OAuth URL Generation"""
        print("\n🔗 Test 2: Dynamic OAuth URL Generation")
        
        try:
            install_url = f"{BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP}.myshopify.com"
            
            async with self.session.get(install_url, allow_redirects=False) as response:
                if response.status == 302:
                    location = response.headers.get('Location', '')
                    
                    # Parse OAuth parameters
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(location)
                    params = parse_qs(parsed.query)
                    
                    # Validate OAuth URL structure
                    is_shopify_oauth = f"{TEST_SHOP}.myshopify.com" in location and "oauth/authorize" in location
                    has_client_id = 'client_id' in params
                    has_redirect_uri = 'redirect_uri' in params
                    has_state = 'state' in params
                    has_scopes = 'scope' in params
                    
                    # Check redirect URI uses detected APP_URL
                    redirect_uri = params.get('redirect_uri', [''])[0] if 'redirect_uri' in params else ''
                    correct_redirect = f"{BACKEND_URL}/api/auth/shopify/callback" == redirect_uri
                    
                    # Check scopes
                    scopes = params.get('scope', [''])[0] if 'scope' in params else ''
                    expected_scopes = "read_orders,read_fulfillments,read_products,read_customers,read_returns,write_returns"
                    correct_scopes = scopes == expected_scopes
                    
                    self.log_test("OAuth URL Format", is_shopify_oauth, f"Redirects to Shopify OAuth: {is_shopify_oauth}")
                    self.log_test("OAuth Parameters", all([has_client_id, has_redirect_uri, has_state, has_scopes]), "All required parameters present")
                    self.log_test("Dynamic Redirect URI", correct_redirect, f"Uses detected APP_URL: {correct_redirect}")
                    self.log_test("OAuth Scopes", correct_scopes, f"Correct scopes: {scopes}")
                    
                    return all([is_shopify_oauth, has_client_id, has_redirect_uri, correct_redirect])
                else:
                    response_text = await response.text()
                    self.log_test("Dynamic OAuth URLs", False, f"Expected 302, got {response.status}: {response_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_test("Dynamic OAuth URLs", False, f"Error: {str(e)}")
            return False
    
    async def test_3_enhanced_health_check(self):
        """Test 3: Enhanced Health Check with Environment Info"""
        print("\n🏥 Test 3: Enhanced Health Check")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    health = await response.json()
                    
                    # Validate health response structure
                    has_status = health.get("status") == "ok"
                    has_timestamp = bool(health.get("timestamp"))
                    has_environment = bool(health.get("environment"))
                    
                    # Check environment section
                    env_info = health.get("environment", {})
                    env_has_app_url = bool(env_info.get("app_url"))
                    env_has_redirect = bool(env_info.get("redirect_uri"))
                    env_shopify_config = env_info.get("shopify_configured", False)
                    
                    self.log_test("Health Status", has_status, f"Status: {health.get('status')}")
                    self.log_test("Health Timestamp", has_timestamp, "Timestamp present")
                    self.log_test("Environment Info", has_environment, "Environment section present")
                    self.log_test("Environment Details", all([env_has_app_url, env_has_redirect, env_shopify_config]), 
                                f"APP_URL: {env_has_app_url}, Redirect: {env_has_redirect}, Shopify: {env_shopify_config}")
                    
                    return all([has_status, has_timestamp, has_environment])
                else:
                    self.log_test("Enhanced Health Check", False, f"Health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test("Enhanced Health Check", False, f"Error: {str(e)}")
            return False
    
    async def test_4_no_hardcoded_urls(self):
        """Test 4: Verify No Hardcoded URLs in Responses"""
        print("\n🔒 Test 4: No Hardcoded URLs")
        
        try:
            # Test OAuth install
            install_url = f"{BACKEND_URL}/api/auth/shopify/install?shop={TEST_SHOP}.myshopify.com"
            
            async with self.session.get(install_url, allow_redirects=False) as response:
                location = response.headers.get('Location', '')
                
                # Should not contain hardcoded localhost or specific domains
                no_localhost = 'localhost' not in location
                no_hardcoded_ip = '127.0.0.1' not in location
                uses_current_domain = BACKEND_URL.replace('https://', '').replace('http://', '') in location
                
                self.log_test("No Localhost URLs", no_localhost, f"No localhost in OAuth URL: {no_localhost}")
                self.log_test("No Hardcoded IPs", no_hardcoded_ip, f"No hardcoded IPs: {no_hardcoded_ip}")
                self.log_test("Uses Current Domain", uses_current_domain, f"Uses detected domain: {uses_current_domain}")
                
                return all([no_localhost, no_hardcoded_ip, uses_current_domain])
                
        except Exception as e:
            self.log_test("No Hardcoded URLs", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all environment-agnostic tests"""
        print(f"🧪 Starting Environment-Agnostic Shopify OAuth Tests")
        print(f"📊 Target: {BACKEND_URL}")
        print(f"🏪 Test Shop: {TEST_SHOP}")
        print("=" * 60)
        
        test_methods = [
            self.test_1_environment_detection,
            self.test_2_dynamic_oauth_urls,
            self.test_3_enhanced_health_check,
            self.test_4_no_hardcoded_urls
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
        print("📊 ENVIRONMENT-AGNOSTIC OAUTH TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 ENVIRONMENT-AGNOSTIC OAUTH IS READY!")
            print("✨ System automatically detects environment and configures OAuth correctly")
            print("🚀 Ready for deployment to any environment without manual configuration")
        else:
            print("⚠️ Some environment-agnostic features need fixes")
        
        return success_rate >= 90

async def main():
    async with EnvironmentAgnosticOAuthTest() as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n" + "=" * 60)
            print("🎯 DEPLOYMENT READY:")
            print("• No manual URL configuration needed")
            print("• Automatic environment detection")
            print("• Dynamic OAuth redirect URIs")
            print("• Production-ready for any domain")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())