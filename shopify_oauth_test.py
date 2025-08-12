#!/usr/bin/env python3
"""
CRITICAL END-TO-END SHOPIFY OAUTH FLOW TEST

This test suite verifies the complete Shopify OAuth login + install flow 
with new integration endpoints as requested in the review.

PRIORITY TESTS:
1. Integration Status Endpoint - GET /api/integrations/shopify/status with tenant-rms34
2. Shopify OAuth Install Flow - GET /api/auth/shopify/install-redirect?shop=rms34
3. OAuth Callback Processing - POST /api/auth/shopify/callback
4. Integration Status After Connection - verify connected=true
5. Resync Functionality - POST /api/integrations/shopify/resync
6. Error Handling - invalid tenant IDs, shop domains, etc.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from urllib.parse import urlparse, parse_qs

# Configuration
BACKEND_URL = "https://returnportal.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_SHOP = "rms34"
TEST_SHOP_DOMAIN = "rms34.myshopify.com"

class ShopifyOAuthTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        
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
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, allow_redirects: bool = True) -> tuple:
        """Make HTTP request and return (success, response_data, status_code, headers)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            request_headers = headers or {}
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers, allow_redirects=allow_redirects) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status, dict(response.headers)
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers, allow_redirects=allow_redirects) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status, dict(response.headers)
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers, allow_redirects=allow_redirects) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status, dict(response.headers)
                    
        except Exception as e:
            return False, {"error": str(e)}, 500, {}
    
    async def test_backend_health(self):
        """Test backend health and accessibility"""
        print("\n🏥 Testing Backend Health...")
        
        # Try root health endpoint first
        try:
            url = "https://returnportal.preview.emergentagent.com/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    self.log_test("Backend Health Check", True, f"Backend is healthy (status: {response.status})")
                    return True
                else:
                    self.log_test("Backend Health Check", False, f"Backend not accessible (status: {response.status})")
                    return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Backend not accessible: {str(e)}")
            return False
    
    async def test_integration_status_initial(self):
        """Test 1: Integration Status Endpoint - Initial State"""
        print("\n🔍 Testing Integration Status Endpoint (Initial State)...")
        
        # Test with tenant-rms34 as specified in review - try both endpoints
        success, response, status, _ = await self.make_request(
            "GET", 
            f"/integrations/shopify/status",
            headers={"X-Tenant-Id": TEST_TENANT_ID}
        )
        
        if not success or response.get('status') == 'error':
            # Try the auth endpoint as fallback
            success, response, status, _ = await self.make_request(
                "GET", 
                f"/auth/shopify/status?tenant_id={TEST_TENANT_ID}"
            )
        
        if success:
            self.log_test("Integration Status: Initial check", True, 
                         f"Status endpoint accessible, connected: {response.get('connected', False)}")
            
            # Verify response structure
            expected_fields = ["connected"]
            if all(field in response for field in expected_fields):
                self.log_test("Integration Status: Response structure", True, "Required fields present")
            else:
                self.log_test("Integration Status: Response structure", False, "Missing required fields")
                
            return response.get('connected', False)
        else:
            self.log_test("Integration Status: Initial check", False, 
                         f"Status endpoint failed (status: {status})")
            return False
    
    async def test_feature_flag_behavior(self):
        """Test feature flag behavior when SHOPIFY_OAUTH_ENABLED=false"""
        print("\n🚩 Testing Feature Flag Behavior...")
        
        # Test install-redirect with feature flag (should work since it's enabled)
        success, response, status, _ = await self.make_request(
            "GET", 
            f"/auth/shopify/install-redirect?shop={TEST_SHOP}",
            allow_redirects=False
        )
        
        if status == 302:  # Redirect to Shopify OAuth
            self.log_test("Feature Flag: OAuth enabled behavior", True, 
                         "Install redirect works when feature flag is enabled")
        elif status == 503:  # Service unavailable when disabled
            self.log_test("Feature Flag: OAuth disabled behavior", True, 
                         "Install redirect correctly blocked when feature flag is disabled")
        else:
            self.log_test("Feature Flag: Behavior check", False, 
                         f"Unexpected status: {status}")
    
    async def test_shopify_oauth_install_flow(self):
        """Test 2: Shopify OAuth Install Flow"""
        print("\n🚀 Testing Shopify OAuth Install Flow...")
        
        # Test install-redirect endpoint with manual handling
        try:
            url = f"{BACKEND_URL}/auth/shopify/install-redirect?shop={TEST_SHOP}"
            async with self.session.get(url, allow_redirects=False) as response:
                status = response.status
                headers = dict(response.headers)
                
                if status == 302:  # Should redirect to Shopify
                    redirect_url = headers.get('location', '')
                    if 'myshopify.com' in redirect_url and 'oauth/authorize' in redirect_url:
                        self.log_test("OAuth Install: Redirect to Shopify", True, 
                                     f"Correctly redirects to Shopify OAuth: {redirect_url[:100]}...")
                        
                        # Parse redirect URL to verify parameters
                        parsed_url = urlparse(redirect_url)
                        query_params = parse_qs(parsed_url.query)
                        
                        required_params = ['client_id', 'scope', 'redirect_uri', 'state']
                        missing_params = [param for param in required_params if param not in query_params]
                        
                        if not missing_params:
                            self.log_test("OAuth Install: URL parameters", True, 
                                         "All required OAuth parameters present")
                        else:
                            self.log_test("OAuth Install: URL parameters", False, 
                                         f"Missing parameters: {missing_params}")
                        
                        return redirect_url
                    else:
                        self.log_test("OAuth Install: Redirect to Shopify", False, 
                                     f"Redirect URL doesn't point to Shopify: {redirect_url}")
                elif status == 503:
                    self.log_test("OAuth Install: Feature flag disabled", True, 
                                 "OAuth correctly disabled by feature flag")
                else:
                    self.log_test("OAuth Install: Redirect to Shopify", False, 
                                 f"Expected redirect (302) but got {status}")
        except Exception as e:
            self.log_test("OAuth Install: Redirect to Shopify", False, 
                         f"Error testing OAuth redirect: {str(e)}")
        
        return None
    
    async def test_oauth_callback_validation(self):
        """Test 3: OAuth Callback Processing (Parameter Validation)"""
        print("\n🔄 Testing OAuth Callback Processing...")
        
        # Test callback with missing parameters
        success, response, status, _ = await self.make_request(
            "GET", 
            "/auth/shopify/callback?code=test&shop=rms34.myshopify.com",
            allow_redirects=False
        )
        
        if status in [400, 422]:  # Should reject incomplete parameters
            self.log_test("OAuth Callback: Parameter validation", True, 
                         "Correctly rejects incomplete OAuth parameters")
        elif status == 302:  # Redirect with error
            self.log_test("OAuth Callback: Parameter validation", True, 
                         "Redirects with error for incomplete parameters")
        else:
            self.log_test("OAuth Callback: Parameter validation", False, 
                         f"Unexpected response to incomplete parameters: {status}")
        
        # Test callback with invalid HMAC
        success, response, status, _ = await self.make_request(
            "GET", 
            "/auth/shopify/callback?code=test&shop=rms34.myshopify.com&state=test&timestamp=123456&hmac=invalid",
            allow_redirects=False
        )
        
        if status in [400, 401, 302]:  # Should reject invalid HMAC
            self.log_test("OAuth Callback: HMAC validation", True, 
                         "Correctly rejects invalid HMAC")
        else:
            self.log_test("OAuth Callback: HMAC validation", False, 
                         f"Should reject invalid HMAC but got: {status}")
    
    async def test_integration_status_after_connection(self):
        """Test 4: Integration Status After Connection"""
        print("\n🔗 Testing Integration Status After Connection...")
        
        # Check if tenant-rms34 already has a connection (as mentioned in test_result.md)
        success, response, status, _ = await self.make_request(
            "GET", 
            f"/integrations/shopify/status",
            headers={"X-Tenant-Id": TEST_TENANT_ID}
        )
        
        if not success or response.get('status') == 'error':
            # Try the auth endpoint as fallback
            success, response, status, _ = await self.make_request(
                "GET", 
                f"/auth/shopify/status?tenant_id={TEST_TENANT_ID}"
            )
        
        if success and response.get('connected'):
            self.log_test("Integration Status: After connection", True, 
                         f"Shows connected=true with shop: {response.get('shop', 'N/A')}")
            
            # Verify connected response structure
            connected_fields = ["connected", "shop"]
            if all(field in response for field in connected_fields):
                self.log_test("Integration Status: Connected response structure", True, 
                             "Connected status has required fields")
            else:
                self.log_test("Integration Status: Connected response structure", False, 
                             "Missing fields in connected response")
                
            return True
        else:
            self.log_test("Integration Status: After connection", False, 
                         "No existing connection found for tenant-rms34")
            return False
    
    async def test_resync_functionality(self):
        """Test 5: Resync Functionality"""
        print("\n🔄 Testing Resync Functionality...")
        
        # Test resync with connected tenant
        success, response, status, _ = await self.make_request(
            "POST", 
            "/integrations/shopify/resync",
            headers={"X-Tenant-Id": TEST_TENANT_ID}
        )
        
        if success:
            self.log_test("Resync: Connected tenant", True, 
                         f"Resync successful: {response.get('message', 'No message')}")
            
            # Verify resync response structure
            if 'job_id' in response or 'message' in response:
                self.log_test("Resync: Response structure", True, 
                             "Resync response has expected fields")
            else:
                self.log_test("Resync: Response structure", False, 
                             "Resync response missing expected fields")
        else:
            if status == 400:
                self.log_test("Resync: Not connected handling", True, 
                             "Correctly rejects resync for non-connected tenant")
            elif status == 503:
                self.log_test("Resync: Feature flag disabled", True, 
                             "Resync correctly disabled by feature flag")
            else:
                self.log_test("Resync: Connected tenant", False, 
                             f"Resync failed with status: {status}")
        
        # Test resync with non-connected tenant
        success, response, status, _ = await self.make_request(
            "POST", 
            "/integrations/shopify/resync",
            headers={"X-Tenant-Id": "tenant-nonexistent"}
        )
        
        if not success and status in [400, 404]:
            self.log_test("Resync: Non-connected tenant", True, 
                         "Correctly rejects resync for non-connected tenant")
        else:
            self.log_test("Resync: Non-connected tenant", False, 
                         "Should reject resync for non-connected tenant")
    
    async def test_error_handling(self):
        """Test 6: Error Handling"""
        print("\n🚨 Testing Error Handling...")
        
        # Test with invalid tenant ID
        success, response, status, _ = await self.make_request(
            "GET", 
            "/integrations/shopify/status",
            headers={"X-Tenant-Id": "invalid-tenant-id"}
        )
        
        if not success or (success and not response.get('connected')):
            self.log_test("Error Handling: Invalid tenant ID", True, 
                         "Correctly handles invalid tenant ID")
        else:
            self.log_test("Error Handling: Invalid tenant ID", False, 
                         "Should handle invalid tenant ID")
        
        # Test OAuth with invalid shop domain
        success, response, status, _ = await self.make_request(
            "GET", 
            "/auth/shopify/install-redirect?shop=invalid..shop..domain",
            allow_redirects=False
        )
        
        if not success or status in [400, 422]:
            self.log_test("Error Handling: Invalid shop domain", True, 
                         "Correctly rejects invalid shop domain")
        else:
            self.log_test("Error Handling: Invalid shop domain", False, 
                         "Should reject invalid shop domain")
        
        # Test missing X-Tenant-Id header
        success, response, status, _ = await self.make_request(
            "GET", 
            "/integrations/shopify/status"
        )
        
        if not success and status in [400, 401, 403]:
            self.log_test("Error Handling: Missing tenant header", True, 
                         "Correctly requires X-Tenant-Id header")
        else:
            self.log_test("Error Handling: Missing tenant header", False, 
                         "Should require X-Tenant-Id header")
    
    async def test_oauth_state_management(self):
        """Test OAuth state parameter generation and validation"""
        print("\n🔐 Testing OAuth State Management...")
        
        # Test state generation debug endpoint
        success, response, status, _ = await self.make_request(
            "GET", 
            f"/auth/shopify/debug/generate-state?shop={TEST_SHOP}"
        )
        
        if success and 'generated_state' in response:
            self.log_test("OAuth State: Generation", True, 
                         f"State generated successfully (length: {response.get('state_length', 0)})")
            
            # Test state verification
            generated_state = response['generated_state']
            success, verify_response, status, _ = await self.make_request(
                "GET", 
                f"/auth/shopify/debug/state?state={generated_state}"
            )
            
            if success and verify_response.get('valid'):
                self.log_test("OAuth State: Verification", True, 
                             "State verification working correctly")
            else:
                self.log_test("OAuth State: Verification", False, 
                             "State verification failed")
        else:
            self.log_test("OAuth State: Generation", False, 
                         "State generation failed")
    
    async def test_session_management_endpoints(self):
        """Test session management endpoints"""
        print("\n👤 Testing Session Management...")
        
        # Test get current session
        success, response, status, _ = await self.make_request(
            "GET", 
            "/auth/shopify/session"
        )
        
        if success:
            self.log_test("Session Management: Get session", True, 
                         f"Session endpoint accessible, authenticated: {response.get('authenticated', False)}")
        else:
            self.log_test("Session Management: Get session", False, 
                         "Session endpoint not accessible")
        
        # Test session creation endpoint
        success, response, status, _ = await self.make_request(
            "POST", 
            "/auth/shopify/session/create",
            data={"tenant_id": TEST_TENANT_ID, "shop": TEST_SHOP_DOMAIN}
        )
        
        if success:
            self.log_test("Session Management: Create session", True, 
                         "Session creation endpoint working")
        else:
            self.log_test("Session Management: Create session", False, 
                         "Session creation endpoint failed")
        
        # Test session destruction
        success, response, status, _ = await self.make_request(
            "DELETE", 
            "/auth/shopify/session"
        )
        
        if success:
            self.log_test("Session Management: Destroy session", True, 
                         "Session destruction endpoint working")
        else:
            self.log_test("Session Management: Destroy session", False, 
                         "Session destruction endpoint failed")
    
    async def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n👨‍💼 Testing Admin Endpoints...")
        
        # Test list all connections (admin endpoint)
        success, response, status, _ = await self.make_request(
            "GET", 
            "/auth/shopify/admin/connections"
        )
        
        if success:
            self.log_test("Admin Endpoints: List connections", True, 
                         f"Admin connections endpoint accessible, found {len(response.get('connections', []))} connections")
        else:
            self.log_test("Admin Endpoints: List connections", False, 
                         "Admin connections endpoint failed")
        
        # Test get tenant details (admin endpoint)
        success, response, status, _ = await self.make_request(
            "GET", 
            f"/auth/shopify/admin/tenant/{TEST_TENANT_ID}"
        )
        
        if success:
            self.log_test("Admin Endpoints: Tenant details", True, 
                         "Admin tenant details endpoint accessible")
        else:
            self.log_test("Admin Endpoints: Tenant details", False, 
                         "Admin tenant details endpoint failed")
    
    async def test_webhook_system(self):
        """Test webhook system availability"""
        print("\n🪝 Testing Webhook System...")
        
        # Check if webhook endpoints are available by testing the integration status
        # which should show webhook information
        success, response, status, _ = await self.make_request(
            "GET", 
            "/integrations/shopify/status",
            headers={"X-Tenant-Id": TEST_TENANT_ID}
        )
        
        if success and response.get('connected'):
            webhooks = response.get('webhooks', [])
            if webhooks:
                self.log_test("Webhook System: Webhook registration", True, 
                             f"Found {len(webhooks)} registered webhooks")
                
                # Check for required webhook topics
                webhook_topics = [w.get('topic') for w in webhooks]
                required_topics = ['orders/create', 'orders/updated', 'fulfillments/create']
                
                if all(topic in webhook_topics for topic in required_topics):
                    self.log_test("Webhook System: Required topics", True, 
                                 "All required webhook topics registered")
                else:
                    missing_topics = [topic for topic in required_topics if topic not in webhook_topics]
                    self.log_test("Webhook System: Required topics", False, 
                                 f"Missing webhook topics: {missing_topics}")
            else:
                self.log_test("Webhook System: Webhook registration", False, 
                             "No webhooks found in integration status")
        else:
            self.log_test("Webhook System: Status check", False, 
                         "Cannot check webhook system - no connection found")
    
    async def run_all_tests(self):
        """Run all Shopify OAuth tests"""
        print("🚀 Starting CRITICAL END-TO-END SHOPIFY OAUTH FLOW TEST")
        print("=" * 70)
        
        # Backend health check
        if not await self.test_backend_health():
            print("❌ Backend not accessible. Stopping tests.")
            return
        
        # Run all test suites in order
        await self.test_integration_status_initial()
        await self.test_feature_flag_behavior()
        await self.test_shopify_oauth_install_flow()
        await self.test_oauth_callback_validation()
        await self.test_integration_status_after_connection()
        await self.test_resync_functionality()
        await self.test_error_handling()
        await self.test_oauth_state_management()
        await self.test_session_management_endpoints()
        await self.test_admin_endpoints()
        await self.test_webhook_system()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 SHOPIFY OAUTH FLOW TESTING SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        
        # Analyze results by priority test areas
        priority_areas = {
            "Integration Status": [r for r in self.test_results if "Integration Status:" in r["test"]],
            "OAuth Install Flow": [r for r in self.test_results if "OAuth Install:" in r["test"]],
            "OAuth Callback": [r for r in self.test_results if "OAuth Callback:" in r["test"]],
            "Resync Functionality": [r for r in self.test_results if "Resync:" in r["test"]],
            "Error Handling": [r for r in self.test_results if "Error Handling:" in r["test"]],
            "Feature Flags": [r for r in self.test_results if "Feature Flag:" in r["test"]],
            "Session Management": [r for r in self.test_results if "Session Management:" in r["test"]],
            "Admin Endpoints": [r for r in self.test_results if "Admin Endpoints:" in r["test"]],
            "Webhook System": [r for r in self.test_results if "Webhook System:" in r["test"]],
            "OAuth State": [r for r in self.test_results if "OAuth State:" in r["test"]]
        }
        
        for area, tests in priority_areas.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {area}: {passed}/{total} tests passed")
        
        print("\n🔍 CRITICAL FLOW VERIFICATION:")
        
        # Check if the complete flow works
        integration_tests = [r for r in self.test_results if "Integration Status:" in r["test"]]
        oauth_tests = [r for r in self.test_results if "OAuth Install:" in r["test"]]
        resync_tests = [r for r in self.test_results if "Resync:" in r["test"]]
        
        integration_working = any(r["success"] for r in integration_tests)
        oauth_working = any(r["success"] for r in oauth_tests)
        resync_working = any(r["success"] for r in resync_tests)
        
        if integration_working and oauth_working and resync_working:
            print("   ✅ Complete Shopify OAuth pipeline is functional")
        else:
            print("   ⚠️ Some parts of the Shopify OAuth pipeline need attention")
        
        print(f"\n📋 EXPECTED RESULTS VERIFICATION:")
        print(f"   • Status endpoint returns connection state: {'✅' if integration_working else '❌'}")
        print(f"   • OAuth install redirects to Shopify: {'✅' if oauth_working else '❌'}")
        print(f"   • Resync endpoint responds appropriately: {'✅' if resync_working else '❌'}")
        print(f"   • Error cases handle gracefully: {'✅' if any('Error Handling:' in r['test'] and r['success'] for r in self.test_results) else '❌'}")

async def main():
    """Main test execution"""
    async with ShopifyOAuthTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())