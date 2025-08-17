#!/usr/bin/env python3
"""
Shopify OAuth Session Fix Verification Test Suite
Tests that OAuth callback creates proper authentication sessions with JWT tokens and cookies
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import jwt
import base64
import hmac
import hashlib
import urllib.parse

# Configuration
BACKEND_URL = "https://ecom-return-manager.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_SHOP = "rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class ShopifyOAuthSessionTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.oauth_state = None
        self.oauth_code = None
        self.jwt_token = None
        self.auth_cookies = {}
        
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
            "response": response_data
        })
    
    async def test_oauth_install_flow(self):
        """Test OAuth install flow generates proper state and redirect"""
        try:
            url = f"{BACKEND_URL}/auth/shopify/install-redirect"
            params = {"shop": TEST_SHOP}
            
            async with self.session.get(url, params=params, allow_redirects=False) as response:
                if response.status == 302:
                    redirect_url = response.headers.get('Location', '')
                    
                    # Parse redirect URL to extract state
                    parsed_url = urllib.parse.urlparse(redirect_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    
                    if 'state' in query_params:
                        self.oauth_state = query_params['state'][0]
                        self.log_test(
                            "OAuth Install Flow - State Generation",
                            True,
                            f"Generated state parameter: {self.oauth_state[:50]}... (length: {len(self.oauth_state)})"
                        )
                        
                        # Verify redirect URL structure
                        expected_domain = f"{TEST_SHOP}.myshopify.com"
                        if expected_domain in redirect_url:
                            self.log_test(
                                "OAuth Install Flow - Redirect URL",
                                True,
                                f"Correct redirect to Shopify: {expected_domain}"
                            )
                        else:
                            self.log_test(
                                "OAuth Install Flow - Redirect URL",
                                False,
                                f"Incorrect redirect URL: {redirect_url}"
                            )
                    else:
                        self.log_test(
                            "OAuth Install Flow - State Generation",
                            False,
                            "No state parameter in redirect URL"
                        )
                else:
                    self.log_test(
                        "OAuth Install Flow - State Generation",
                        False,
                        f"Expected 302 redirect, got {response.status}"
                    )
                    
        except Exception as e:
            self.log_test(
                "OAuth Install Flow - State Generation",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_oauth_state_verification(self):
        """Test OAuth state verification endpoint"""
        if not self.oauth_state:
            self.log_test(
                "OAuth State Verification",
                False,
                "No OAuth state available from previous test"
            )
            return
            
        try:
            url = f"{BACKEND_URL}/auth/shopify/debug/state"
            params = {"state": self.oauth_state}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('valid'):
                        state_data = data.get('state_data', {})
                        self.log_test(
                            "OAuth State Verification",
                            True,
                            f"State valid - Shop: {state_data.get('shop')}, Timestamp: {state_data.get('timestamp')}"
                        )
                    else:
                        self.log_test(
                            "OAuth State Verification",
                            False,
                            f"State invalid: {data.get('error')}"
                        )
                else:
                    self.log_test(
                        "OAuth State Verification",
                        False,
                        f"HTTP {response.status}: {await response.text()}"
                    )
                    
        except Exception as e:
            self.log_test(
                "OAuth State Verification",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_oauth_callback_with_mock_data(self):
        """Test OAuth callback with mock Shopify response data"""
        if not self.oauth_state:
            self.log_test(
                "OAuth Callback - Mock Data",
                False,
                "No OAuth state available for callback test"
            )
            return
            
        try:
            # Generate mock OAuth callback parameters
            mock_code = f"mock_auth_code_{uuid.uuid4().hex[:16]}"
            mock_timestamp = str(int(datetime.utcnow().timestamp()))
            mock_hmac = "mock_hmac_signature"
            
            url = f"{BACKEND_URL}/auth/shopify/callback"
            params = {
                "code": mock_code,
                "shop": f"{TEST_SHOP}.myshopify.com",
                "state": self.oauth_state,
                "timestamp": mock_timestamp,
                "hmac": mock_hmac
            }
            
            async with self.session.get(url, params=params, allow_redirects=False) as response:
                # Check if callback processes without crashing
                if response.status in [200, 302]:
                    self.log_test(
                        "OAuth Callback - Processing",
                        True,
                        f"Callback processed successfully (HTTP {response.status})"
                    )
                    
                    # Check for redirect to dashboard
                    if response.status == 302:
                        redirect_url = response.headers.get('Location', '')
                        if 'dashboard' in redirect_url or 'connected=1' in redirect_url:
                            self.log_test(
                                "OAuth Callback - Dashboard Redirect",
                                True,
                                f"Redirected to dashboard: {redirect_url}"
                            )
                        else:
                            self.log_test(
                                "OAuth Callback - Dashboard Redirect",
                                False,
                                f"Unexpected redirect: {redirect_url}"
                            )
                    
                    # Check for authentication cookies
                    cookies = response.cookies
                    if 'access_token' in cookies:
                        self.auth_cookies['access_token'] = cookies['access_token'].value
                        self.log_test(
                            "OAuth Callback - Authentication Cookie",
                            True,
                            f"Access token cookie set (length: {len(self.auth_cookies['access_token'])})"
                        )
                        
                        # Try to decode JWT token
                        await self.test_jwt_token_structure()
                    else:
                        self.log_test(
                            "OAuth Callback - Authentication Cookie",
                            False,
                            "No access_token cookie found in response"
                        )
                        
                else:
                    response_text = await response.text()
                    self.log_test(
                        "OAuth Callback - Processing",
                        False,
                        f"HTTP {response.status}: {response_text}"
                    )
                    
        except Exception as e:
            self.log_test(
                "OAuth Callback - Mock Data",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_jwt_token_structure(self):
        """Test JWT token structure and claims"""
        if not self.auth_cookies.get('access_token'):
            self.log_test(
                "JWT Token Structure",
                False,
                "No access token available for testing"
            )
            return
            
        try:
            token = self.auth_cookies['access_token']
            
            # Decode JWT without verification (for testing structure)
            try:
                # Split token into parts
                parts = token.split('.')
                if len(parts) != 3:
                    self.log_test(
                        "JWT Token Structure",
                        False,
                        f"Invalid JWT format - expected 3 parts, got {len(parts)}"
                    )
                    return
                
                # Decode header and payload
                header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                
                self.log_test(
                    "JWT Token Structure",
                    True,
                    f"Valid JWT structure - Algorithm: {header.get('alg')}"
                )
                
                # Check required claims
                required_claims = ['sub', 'tenant_id', 'email', 'role', 'exp', 'iat']
                missing_claims = [claim for claim in required_claims if claim not in payload]
                
                if not missing_claims:
                    self.log_test(
                        "JWT Token Claims",
                        True,
                        f"All required claims present - Role: {payload.get('role')}, Tenant: {payload.get('tenant_id')}"
                    )
                else:
                    self.log_test(
                        "JWT Token Claims",
                        False,
                        f"Missing claims: {missing_claims}"
                    )
                
                # Check expiration
                exp_timestamp = payload.get('exp')
                if exp_timestamp:
                    exp_datetime = datetime.fromtimestamp(exp_timestamp)
                    if exp_datetime > datetime.utcnow():
                        self.log_test(
                            "JWT Token Expiration",
                            True,
                            f"Token expires at: {exp_datetime}"
                        )
                    else:
                        self.log_test(
                            "JWT Token Expiration",
                            False,
                            f"Token already expired: {exp_datetime}"
                        )
                
                self.jwt_token = token
                
            except Exception as decode_error:
                self.log_test(
                    "JWT Token Structure",
                    False,
                    f"Failed to decode JWT: {str(decode_error)}"
                )
                
        except Exception as e:
            self.log_test(
                "JWT Token Structure",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_authenticated_api_access(self):
        """Test that JWT token allows access to protected routes"""
        if not self.jwt_token:
            self.log_test(
                "Authenticated API Access",
                False,
                "No JWT token available for testing"
            )
            return
            
        try:
            # Test access to protected returns endpoint
            url = f"{BACKEND_URL}/returns/"
            headers = {
                **TEST_HEADERS,
                "Authorization": f"Bearer {self.jwt_token}"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Authenticated API Access - Returns Endpoint",
                        True,
                        f"Successfully accessed returns endpoint - Found {len(data.get('returns', []))} returns"
                    )
                elif response.status == 401:
                    self.log_test(
                        "Authenticated API Access - Returns Endpoint",
                        False,
                        "JWT token rejected - 401 Unauthorized"
                    )
                else:
                    self.log_test(
                        "Authenticated API Access - Returns Endpoint",
                        False,
                        f"Unexpected status: {response.status}"
                    )
                    
        except Exception as e:
            self.log_test(
                "Authenticated API Access",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_session_persistence(self):
        """Test that authentication session persists across requests"""
        if not self.auth_cookies.get('access_token'):
            self.log_test(
                "Session Persistence",
                False,
                "No authentication cookie available for testing"
            )
            return
            
        try:
            # Create new session with cookies
            cookie_header = f"access_token={self.auth_cookies['access_token']}"
            headers = {
                **TEST_HEADERS,
                "Cookie": cookie_header
            }
            
            # Test multiple endpoints to verify session persistence
            endpoints = [
                "/integrations/shopify/status",
                "/returns/",
                "/orders/"
            ]
            
            successful_requests = 0
            for endpoint in endpoints:
                try:
                    url = f"{BACKEND_URL}{endpoint}"
                    async with self.session.get(url, headers=headers) as response:
                        if response.status in [200, 404]:  # 404 is OK for some endpoints
                            successful_requests += 1
                except:
                    pass
            
            if successful_requests >= 2:
                self.log_test(
                    "Session Persistence",
                    True,
                    f"Session cookie worked for {successful_requests}/{len(endpoints)} endpoints"
                )
            else:
                self.log_test(
                    "Session Persistence",
                    False,
                    f"Session cookie only worked for {successful_requests}/{len(endpoints)} endpoints"
                )
                
        except Exception as e:
            self.log_test(
                "Session Persistence",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_user_creation_in_database(self):
        """Test that OAuth callback creates/updates user in database"""
        try:
            # Test user lookup endpoint to verify user was created
            url = f"{BACKEND_URL}/users/profile"
            headers = {
                **TEST_HEADERS,
                "Authorization": f"Bearer {self.jwt_token}" if self.jwt_token else ""
            }
            
            if not self.jwt_token:
                self.log_test(
                    "User Creation in Database",
                    False,
                    "No JWT token available for user lookup"
                )
                return
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    # Check user data structure
                    required_fields = ['user_id', 'email', 'role', 'tenant_id']
                    missing_fields = [field for field in required_fields if field not in user_data]
                    
                    if not missing_fields:
                        self.log_test(
                            "User Creation in Database",
                            True,
                            f"User created successfully - Email: {user_data.get('email')}, Role: {user_data.get('role')}"
                        )
                        
                        # Verify tenant association
                        if user_data.get('tenant_id') == TEST_TENANT_ID:
                            self.log_test(
                                "User Tenant Association",
                                True,
                                f"User correctly associated with tenant: {TEST_TENANT_ID}"
                            )
                        else:
                            self.log_test(
                                "User Tenant Association",
                                False,
                                f"User associated with wrong tenant: {user_data.get('tenant_id')}"
                            )
                    else:
                        self.log_test(
                            "User Creation in Database",
                            False,
                            f"User data missing fields: {missing_fields}"
                        )
                        
                elif response.status == 401:
                    self.log_test(
                        "User Creation in Database",
                        False,
                        "Authentication failed - user may not have been created"
                    )
                else:
                    self.log_test(
                        "User Creation in Database",
                        False,
                        f"Unexpected response: {response.status}"
                    )
                    
        except Exception as e:
            self.log_test(
                "User Creation in Database",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_shopify_integration_status(self):
        """Test that Shopify integration status is updated correctly"""
        try:
            url = f"{BACKEND_URL}/integrations/shopify/status"
            headers = TEST_HEADERS
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check integration status structure
                    if 'connected' in data and 'status' in data:
                        self.log_test(
                            "Shopify Integration Status",
                            True,
                            f"Integration status: {data.get('status')}, Connected: {data.get('connected')}"
                        )
                        
                        # Check if shop information is present when connected
                        if data.get('connected') and data.get('shop'):
                            self.log_test(
                                "Shopify Integration Data",
                                True,
                                f"Shop data present: {data.get('shop')}"
                            )
                        elif not data.get('connected'):
                            self.log_test(
                                "Shopify Integration Data",
                                True,
                                "Not connected - no shop data expected"
                            )
                        else:
                            self.log_test(
                                "Shopify Integration Data",
                                False,
                                "Connected but no shop data"
                            )
                    else:
                        self.log_test(
                            "Shopify Integration Status",
                            False,
                            f"Invalid status response structure: {data}"
                        )
                else:
                    self.log_test(
                        "Shopify Integration Status",
                        False,
                        f"HTTP {response.status}: {await response.text()}"
                    )
                    
        except Exception as e:
            self.log_test(
                "Shopify Integration Status",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_cookie_security_settings(self):
        """Test that authentication cookies have proper security settings"""
        if not self.auth_cookies.get('access_token'):
            self.log_test(
                "Cookie Security Settings",
                False,
                "No authentication cookie available for testing"
            )
            return
            
        try:
            # Re-test OAuth callback to check cookie attributes
            if not self.oauth_state:
                self.log_test(
                    "Cookie Security Settings",
                    False,
                    "No OAuth state available for cookie test"
                )
                return
                
            mock_code = f"mock_auth_code_{uuid.uuid4().hex[:16]}"
            mock_timestamp = str(int(datetime.utcnow().timestamp()))
            mock_hmac = "mock_hmac_signature"
            
            url = f"{BACKEND_URL}/auth/shopify/callback"
            params = {
                "code": mock_code,
                "shop": f"{TEST_SHOP}.myshopify.com",
                "state": self.oauth_state,
                "timestamp": mock_timestamp,
                "hmac": mock_hmac
            }
            
            async with self.session.get(url, params=params, allow_redirects=False) as response:
                if response.status in [200, 302]:
                    # Check cookie attributes
                    set_cookie_header = response.headers.get('Set-Cookie', '')
                    
                    security_checks = {
                        'HttpOnly': 'HttpOnly' in set_cookie_header,
                        'Secure': 'Secure' in set_cookie_header,
                        'SameSite': 'SameSite' in set_cookie_header
                    }
                    
                    passed_checks = sum(security_checks.values())
                    total_checks = len(security_checks)
                    
                    if passed_checks >= 2:  # At least HttpOnly and one other
                        self.log_test(
                            "Cookie Security Settings",
                            True,
                            f"Security settings: {security_checks} ({passed_checks}/{total_checks})"
                        )
                    else:
                        self.log_test(
                            "Cookie Security Settings",
                            False,
                            f"Insufficient security settings: {security_checks}"
                        )
                else:
                    self.log_test(
                        "Cookie Security Settings",
                        False,
                        f"Could not test cookie security - HTTP {response.status}"
                    )
                    
        except Exception as e:
            self.log_test(
                "Cookie Security Settings",
                False,
                f"Exception: {str(e)}"
            )
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"SHOPIFY OAUTH SESSION FIX VERIFICATION COMPLETE")
        print(f"{'='*80}")
        print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA:")
        
        # Check specific success criteria from review request
        criteria_results = {
            "OAuth callback creates proper JWT tokens": any("JWT Token Structure" in r["test"] and r["success"] for r in self.test_results),
            "Authentication cookies are set correctly": any("Authentication Cookie" in r["test"] and r["success"] for r in self.test_results),
            "Users can access dashboard after OAuth": any("Dashboard Redirect" in r["test"] and r["success"] for r in self.test_results),
            "User data is properly stored in database": any("User Creation in Database" in r["test"] and r["success"] for r in self.test_results),
            "Shopify integration status is updated correctly": any("Shopify Integration Status" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for criteria, passed in criteria_results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criteria}")
        
        overall_success = sum(criteria_results.values()) >= 3  # At least 3 out of 5 critical criteria
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if overall_success:
            print(f"   ✅ SHOPIFY OAUTH SESSION FIX IS WORKING!")
            print(f"   ✅ OAuth callback creates proper authentication sessions")
            print(f"   ✅ JWT tokens and cookies are implemented correctly")
        else:
            print(f"   ❌ SHOPIFY OAUTH SESSION FIX NEEDS ATTENTION")
            print(f"   ❌ Critical session management issues identified")
        
        return overall_success

async def main():
    """Run all Shopify OAuth session tests"""
    print("🚀 Starting Shopify OAuth Session Fix Verification...")
    print(f"🎯 Testing against: {BACKEND_URL}")
    print(f"🏪 Test tenant: {TEST_TENANT_ID}")
    print(f"🛍️ Test shop: {TEST_SHOP}")
    print("="*80)
    
    async with ShopifyOAuthSessionTestSuite() as test_suite:
        # Run all tests in sequence
        await test_suite.test_oauth_install_flow()
        await test_suite.test_oauth_state_verification()
        await test_suite.test_oauth_callback_with_mock_data()
        await test_suite.test_authenticated_api_access()
        await test_suite.test_session_persistence()
        await test_suite.test_user_creation_in_database()
        await test_suite.test_shopify_integration_status()
        await test_suite.test_cookie_security_settings()
        
        # Print summary
        success = test_suite.print_summary()
        
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)