#!/usr/bin/env python3
"""
🔧 SHOPIFY CREDENTIALS UPDATE TEST
Tests the updated Shopify connectivity with new credentials provided by user:
- Store: rms34.myshopify.com
- API Key: 0ef6de8c4bf0b4a3d8f7f99b42c53695
- API Secret: db79f6174721b7acf332b69ef8f84374  
- Access Token: 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

Priority Test Endpoints:
1. /api/shopify-test/quick-test - Verify connection to rms34.myshopify.com
2. /api/auth/status - Verify new API key is loaded correctly
3. /api/auth/test/validate - Test validation with new credentials
4. /api/auth/initiate - Test OAuth URL generation with new credentials
"""

import requests
import sys
import json
from datetime import datetime

# Use the external backend URL for testing
BACKEND_URL = "https://bb5d0b5c-0639-4f12-be95-7ef6a2bfa2ef.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Updated credentials from user
NEW_CREDENTIALS = {
    "store": "rms34.myshopify.com",
    "api_key": "0ef6de8c4bf0b4a3d8f7f99b42c53695",
    "api_secret": "db79f6174721b7acf332b69ef8f84374",
    "access_token": "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"
}

class ShopifyCredentialsTest:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   📋 {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   🚨 {details}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    headers: dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{API_BASE}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
                
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}
                
            return success, response_data
            
        except requests.exceptions.Timeout:
            return False, "Request timeout (30s)"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - backend may be down"
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_shopify_connectivity(self):
        """Test 1: Shopify Connectivity Test - /api/shopify-test/quick-test"""
        print(f"\n🔗 Testing Shopify Connectivity with Store: {NEW_CREDENTIALS['store']}")
        
        success, response = self.make_request('GET', 'shopify-test/quick-test')
        
        if success:
            quick_test = response.get('quick_test', {})
            shop_info = response.get('shop_info', {})
            products_sample = response.get('products_sample', {})
            
            if quick_test.get('overall_success'):
                shop_name = shop_info.get('shop_name', 'Unknown')
                products_count = products_sample.get('products_count', 0)
                self.log_test(
                    "Shopify Quick Test", 
                    True, 
                    f"Connected to {NEW_CREDENTIALS['store']}, retrieved {products_count} products"
                )
                return True
            else:
                self.log_test(
                    "Shopify Quick Test", 
                    False, 
                    f"Connection test failed: {quick_test.get('error', 'Unknown error')}"
                )
                return False
        else:
            self.log_test(
                "Shopify Quick Test", 
                False, 
                f"Request failed: {response}"
            )
            return False

    def test_auth_service_status(self):
        """Test 2: Auth Service Status - /api/auth/status"""
        print(f"\n🔐 Testing Auth Service Status")
        
        success, response = self.make_request('GET', 'auth/status')
        
        if success:
            api_version = response.get('api_version', '')
            redirect_uri = response.get('redirect_uri', '')
            required_scopes = response.get('required_scopes', [])
            encryption = response.get('encryption', '')
            
            # Check API version
            if api_version == "2025-07":
                self.log_test(
                    "Auth Service Status - API Version", 
                    True, 
                    f"API Version: {api_version}"
                )
            else:
                self.log_test(
                    "Auth Service Status - API Version", 
                    False, 
                    f"Expected 2025-07, got {api_version}"
                )
            
            # Check redirect URI
            if redirect_uri:
                self.log_test(
                    "Auth Service Status - Redirect URI", 
                    True, 
                    f"Redirect URI configured: {redirect_uri}"
                )
            else:
                self.log_test(
                    "Auth Service Status - Redirect URI", 
                    False, 
                    "Redirect URI not configured"
                )
            
            # Check required scopes
            if required_scopes:
                self.log_test(
                    "Auth Service Status - Required Scopes", 
                    True, 
                    f"Scopes configured: {', '.join(required_scopes)}"
                )
            else:
                self.log_test(
                    "Auth Service Status - Required Scopes", 
                    False, 
                    "Required scopes not configured"
                )
            
            # Check encryption
            if encryption:
                self.log_test(
                    "Auth Service Status - Encryption", 
                    True, 
                    f"Encryption: {encryption}"
                )
            else:
                self.log_test(
                    "Auth Service Status - Encryption", 
                    False, 
                    "Encryption not configured"
                )
            
            return True
        else:
            self.log_test(
                "Auth Service Status", 
                False, 
                f"Status check failed: {response}"
            )
            return False

    def test_credential_validation(self):
        """Test 3: Credential Validation - /api/auth/test/validate"""
        print(f"\n✅ Testing Credential Validation")
        
        validation_data = {
            "shop": "rms34",  # Just the shop name without .myshopify.com
            "api_key": NEW_CREDENTIALS['api_key'],
            "api_secret": NEW_CREDENTIALS['api_secret']
        }
        
        success, response = self.make_request('POST', 'auth/test/validate', validation_data)
        
        if success:
            overall_valid = response.get('overall_valid', False)
            validations = response.get('validations', {})
            ready_for_oauth = response.get('ready_for_oauth', False)
            
            # Check overall validation
            if overall_valid:
                self.log_test(
                    "Credential Validation - Overall", 
                    True, 
                    f"All credentials valid, ready for OAuth: {ready_for_oauth}"
                )
            else:
                self.log_test(
                    "Credential Validation - Overall", 
                    False, 
                    f"Credential validation failed"
                )
            
            # Check individual validations
            shop_validation = validations.get('shop_domain', {})
            if shop_validation.get('valid'):
                normalized_shop = shop_validation.get('normalized', '')
                self.log_test(
                    "Credential Validation - Shop Domain", 
                    True, 
                    f"Shop domain valid, normalized to: {normalized_shop}"
                )
            else:
                self.log_test(
                    "Credential Validation - Shop Domain", 
                    False, 
                    f"Shop domain validation failed"
                )
            
            api_key_validation = validations.get('api_key', {})
            if api_key_validation.get('valid'):
                key_length = api_key_validation.get('length', 0)
                self.log_test(
                    "Credential Validation - API Key", 
                    True, 
                    f"API key valid, length: {key_length}"
                )
            else:
                self.log_test(
                    "Credential Validation - API Key", 
                    False, 
                    f"API key validation failed"
                )
            
            api_secret_validation = validations.get('api_secret', {})
            if api_secret_validation.get('valid'):
                secret_length = api_secret_validation.get('length', 0)
                self.log_test(
                    "Credential Validation - API Secret", 
                    True, 
                    f"API secret valid, length: {secret_length}"
                )
            else:
                self.log_test(
                    "Credential Validation - API Secret", 
                    False, 
                    f"API secret validation failed"
                )
            
            return overall_valid
        else:
            self.log_test(
                "Credential Validation", 
                False, 
                f"Validation request failed: {response}"
            )
            return False

    def test_oauth_initiation(self):
        """Test 4: OAuth Initiation - /api/auth/initiate"""
        print(f"\n🔗 Testing OAuth URL Generation")
        
        oauth_data = {
            "shop": "rms34",
            "scopes": ["read_orders", "write_returns", "read_products"]
        }
        
        success, response = self.make_request('POST', 'auth/initiate', oauth_data)
        
        if success:
            auth_url = response.get('auth_url', '')
            state = response.get('state', '')
            
            if auth_url and 'rms34.myshopify.com' in auth_url:
                self.log_test(
                    "OAuth Initiation - Auth URL", 
                    True, 
                    f"OAuth URL generated for rms34.myshopify.com"
                )
            else:
                self.log_test(
                    "OAuth Initiation - Auth URL", 
                    False, 
                    f"Invalid auth URL: {auth_url}"
                )
                return False
            
            if state:
                self.log_test(
                    "OAuth Initiation - State Parameter", 
                    True, 
                    f"State parameter generated: {state[:8]}..."
                )
            else:
                self.log_test(
                    "OAuth Initiation - State Parameter", 
                    False, 
                    "State parameter missing"
                )
            
            return True
        else:
            self.log_test(
                "OAuth Initiation", 
                False, 
                f"OAuth initiation failed: {response}"
            )
            return False

    def run_all_tests(self):
        """Run all Shopify credential tests"""
        print("🔧 SHOPIFY CREDENTIALS UPDATE TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Store: {NEW_CREDENTIALS['store']}")
        print(f"API Key: {NEW_CREDENTIALS['api_key'][:8]}...")
        print("=" * 60)
        
        # Test 1: Shopify Connectivity
        connectivity_success = self.test_shopify_connectivity()
        
        # Test 2: Auth Service Status
        auth_status_success = self.test_auth_service_status()
        
        # Test 3: Credential Validation
        validation_success = self.test_credential_validation()
        
        # Test 4: OAuth Initiation
        oauth_success = self.test_oauth_initiation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Shopify credentials are working correctly.")
            print("✅ Backend is ready for Shopify integration testing from web interface.")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed.")
            print("❌ Some issues need to be resolved before web interface testing.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ShopifyCredentialsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)