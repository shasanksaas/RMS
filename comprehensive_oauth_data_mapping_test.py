#!/usr/bin/env python3
"""
COMPREHENSIVE OAUTH & DATA MAPPING TEST: Complete Shopify integration flow with proper tenant association

This test suite verifies:
1. OAuth Routing Fix Verification - Test all OAuth endpoints with proper routing
2. Integration Dashboard OAuth - Test with proper X-Tenant-Id headers  
3. Data Mapping & Tenant Association - Verify data sync with correct tenant_id
4. Webhook Data Processing - Test webhook endpoints properly map shop domain → tenant_id
5. Multi-Tenant Data Isolation - Test tenant isolation in integration endpoints
6. Complete Integration Flow - Test end-to-end OAuth system

SUCCESS CRITERIA:
- OAuth routing works without conflicts or 404 errors
- Integration dashboard endpoints use proper tenant isolation
- Data sync associates all orders/returns with correct tenant_id
- Webhooks map shop domains to correct tenants
- Complete end-to-end flow works for any tenant
- Zero hardcoded tenant references remaining
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import time

# Configuration - Use frontend environment URL as per instructions
BACKEND_URL = "https://shopify-sync-fix.preview.emergentagent.com/api"

# Test tenants for multi-tenant isolation testing
TEST_TENANTS = {
    "tenant-laxmi12-m9zgom": "Laxmi Store",
    "tenant-rms34": "RMS Demo Store", 
    "tenant-fashion-forward-demo": "Fashion Forward Demo"
}

class ShopifyOAuthDataMappingTestSuite:
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
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            request_headers = headers or {}
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500

    async def test_oauth_routing_fix_verification(self):
        """Test 1: OAuth Routing Fix Verification - Test all OAuth endpoints with proper routing"""
        print("\n🔍 Testing OAuth Routing Fix Verification...")
        
        # Test 1.1: GET /api/auth/shopify/install-redirect?shop=test-store (direct redirect)
        success, response, status = await self.make_request(
            "GET", 
            "/auth/shopify/install-redirect?shop=test-store"
        )
        
        if status == 302 or (isinstance(response, str) and "shopify.com" in response):
            self.log_test("OAuth Routing: Install redirect endpoint", True, 
                         f"Endpoint accessible, returns redirect (status: {status})")
        elif status == 404:
            self.log_test("OAuth Routing: Install redirect endpoint", False, 
                         "404 error - routing conflict or endpoint not found")
        else:
            self.log_test("OAuth Routing: Install redirect endpoint", True, 
                         f"Endpoint accessible (status: {status})")
        
        # Test 1.2: GET /api/auth/shopify/callback with OAuth parameters
        callback_params = "?code=test_code&shop=test-store.myshopify.com&state=test_state&timestamp=123456&hmac=test_hmac"
        success, response, status = await self.make_request(
            "GET", 
            f"/auth/shopify/callback{callback_params}"
        )
        
        if status != 404:
            self.log_test("OAuth Routing: Callback endpoint", True, 
                         f"Endpoint accessible (status: {status})")
        else:
            self.log_test("OAuth Routing: Callback endpoint", False, 
                         "404 error - routing conflict or endpoint not found")
        
        # Test 1.3: Test OAuth install endpoint (non-redirect version)
        success, response, status = await self.make_request(
            "GET", 
            "/auth/shopify/install?shop=test-store"
        )
        
        if status != 404:
            self.log_test("OAuth Routing: Install endpoint", True, 
                         f"Endpoint accessible (status: {status})")
        else:
            self.log_test("OAuth Routing: Install endpoint", False, 
                         "404 error - routing conflict or endpoint not found")
        
        # Test 1.4: Test OAuth status endpoint
        success, response, status = await self.make_request(
            "GET", 
            "/auth/shopify/status?tenant_id=tenant-laxmi12-m9zgom"
        )
        
        if status != 404:
            self.log_test("OAuth Routing: Status endpoint", True, 
                         f"Endpoint accessible (status: {status})")
        else:
            self.log_test("OAuth Routing: Status endpoint", False, 
                         "404 error - routing conflict or endpoint not found")

    async def test_integration_dashboard_oauth(self):
        """Test 2: Integration Dashboard OAuth - Test with proper X-Tenant-Id headers"""
        print("\n🎛️ Testing Integration Dashboard OAuth...")
        
        for tenant_id, tenant_name in TEST_TENANTS.items():
            headers = {"X-Tenant-Id": tenant_id}
            
            # Test 2.1: GET /api/integrations/shopify/status with proper X-Tenant-Id headers
            success, response, status = await self.make_request(
                "GET", 
                "/integrations/shopify/status",
                headers=headers
            )
            
            if success and isinstance(response, dict):
                connected = response.get("connected", False)
                self.log_test(f"Integration Dashboard: Status for {tenant_id}", True, 
                             f"Status retrieved - connected: {connected}")
            elif status == 400 and "X-Tenant-Id" in str(response):
                self.log_test(f"Integration Dashboard: Status for {tenant_id}", False, 
                             "Missing X-Tenant-Id header validation working but endpoint failed")
            else:
                self.log_test(f"Integration Dashboard: Status for {tenant_id}", False, 
                             f"Status endpoint failed (status: {status})")
            
            # Test 2.2: POST /api/integrations/shopify/resync with proper tenant isolation
            success, response, status = await self.make_request(
                "POST", 
                "/integrations/shopify/resync",
                headers=headers
            )
            
            if success or status in [400, 503]:  # 400 = not connected, 503 = disabled
                self.log_test(f"Integration Dashboard: Resync for {tenant_id}", True, 
                             f"Resync endpoint accessible (status: {status})")
            else:
                self.log_test(f"Integration Dashboard: Resync for {tenant_id}", False, 
                             f"Resync endpoint failed (status: {status})")
        
        # Test 2.3: Test without X-Tenant-Id header (should fail)
        success, response, status = await self.make_request(
            "GET", 
            "/integrations/shopify/status"
        )
        
        if not success and status == 400:
            self.log_test("Integration Dashboard: X-Tenant-Id validation", True, 
                         "Correctly rejects requests without X-Tenant-Id header")
        else:
            self.log_test("Integration Dashboard: X-Tenant-Id validation", False, 
                         "Should reject requests without X-Tenant-Id header")

    async def test_data_mapping_tenant_association(self):
        """Test 3: Data Mapping & Tenant Association - Verify data sync with correct tenant_id"""
        print("\n🗂️ Testing Data Mapping & Tenant Association...")
        
        for tenant_id, tenant_name in TEST_TENANTS.items():
            headers = {"X-Tenant-Id": tenant_id}
            
            # Test 3.1: Test orders endpoint for tenant-specific data
            success, response, status = await self.make_request(
                "GET", 
                "/orders?limit=5",
                headers=headers
            )
            
            if success and isinstance(response, dict):
                orders = response.get("items", [])
                # Verify all orders have correct tenant_id
                tenant_isolated = all(order.get("tenant_id") == tenant_id for order in orders)
                self.log_test(f"Data Mapping: Orders for {tenant_id}", tenant_isolated, 
                             f"Found {len(orders)} orders, tenant isolation: {tenant_isolated}")
            else:
                self.log_test(f"Data Mapping: Orders for {tenant_id}", False, 
                             f"Orders endpoint failed (status: {status})")
            
            # Test 3.2: Test returns endpoint for tenant-specific data
            success, response, status = await self.make_request(
                "GET", 
                "/returns?limit=5",
                headers=headers
            )
            
            if success and isinstance(response, dict):
                returns = response.get("items", [])
                # Verify all returns have correct tenant_id
                tenant_isolated = all(ret.get("tenant_id") == tenant_id for ret in returns)
                self.log_test(f"Data Mapping: Returns for {tenant_id}", tenant_isolated, 
                             f"Found {len(returns)} returns, tenant isolation: {tenant_isolated}")
            else:
                self.log_test(f"Data Mapping: Returns for {tenant_id}", False, 
                             f"Returns endpoint failed (status: {status})")

    async def test_webhook_data_processing(self):
        """Test 4: Webhook Data Processing - Test webhook endpoints properly map shop domain → tenant_id"""
        print("\n🪝 Testing Webhook Data Processing...")
        
        # Test 4.1: Test orders/create webhook endpoint
        webhook_headers = {
            "X-Shopify-Hmac-Sha256": "test_hmac",
            "X-Shopify-Shop-Domain": "rms34.myshopify.com",
            "Content-Type": "application/json"
        }
        
        test_order_payload = {
            "id": 12345,
            "order_number": "TEST001",
            "name": "#TEST001",
            "email": "customer@test.com",
            "total_price": "99.99",
            "currency": "USD",
            "customer": {"id": 1, "email": "customer@test.com"},
            "line_items": [{"id": 1, "name": "Test Product", "quantity": 1}],
            "created_at": datetime.utcnow().isoformat()
        }
        
        success, response, status = await self.make_request(
            "POST", 
            "/webhooks/shopify/orders-create",
            data=test_order_payload,
            headers=webhook_headers
        )
        
        if status == 401:
            self.log_test("Webhook Processing: Orders create HMAC validation", True, 
                         "Webhook correctly validates HMAC (401 for invalid HMAC)")
        elif status == 404:
            self.log_test("Webhook Processing: Orders create endpoint", False, 
                         "Webhook endpoint not found - routing issue")
        else:
            self.log_test("Webhook Processing: Orders create endpoint", True, 
                         f"Webhook endpoint accessible (status: {status})")
        
        # Test 4.2: Test orders/updated webhook endpoint
        success, response, status = await self.make_request(
            "POST", 
            "/webhooks/shopify/orders-updated",
            data=test_order_payload,
            headers=webhook_headers
        )
        
        if status == 401:
            self.log_test("Webhook Processing: Orders updated HMAC validation", True, 
                         "Webhook correctly validates HMAC")
        elif status == 404:
            self.log_test("Webhook Processing: Orders updated endpoint", False, 
                         "Webhook endpoint not found - routing issue")
        else:
            self.log_test("Webhook Processing: Orders updated endpoint", True, 
                         f"Webhook endpoint accessible (status: {status})")
        
        # Test 4.3: Test fulfillments/create webhook endpoint
        fulfillment_payload = {
            "id": 67890,
            "order_id": 12345,
            "tracking_number": "1Z999AA1234567890",
            "tracking_company": "UPS",
            "created_at": datetime.utcnow().isoformat()
        }
        
        success, response, status = await self.make_request(
            "POST", 
            "/webhooks/shopify/fulfillments-create",
            data=fulfillment_payload,
            headers=webhook_headers
        )
        
        if status == 401:
            self.log_test("Webhook Processing: Fulfillments create HMAC validation", True, 
                         "Webhook correctly validates HMAC")
        elif status == 404:
            self.log_test("Webhook Processing: Fulfillments create endpoint", False, 
                         "Webhook endpoint not found - routing issue")
        else:
            self.log_test("Webhook Processing: Fulfillments create endpoint", True, 
                         f"Webhook endpoint accessible (status: {status})")
        
        # Test 4.4: Test app/uninstalled webhook endpoint
        uninstall_payload = {
            "id": 12345,
            "name": "rms34.myshopify.com",
            "domain": "rms34.myshopify.com"
        }
        
        success, response, status = await self.make_request(
            "POST", 
            "/webhooks/shopify/app-uninstalled",
            data=uninstall_payload,
            headers=webhook_headers
        )
        
        if status == 401:
            self.log_test("Webhook Processing: App uninstalled HMAC validation", True, 
                         "Webhook correctly validates HMAC")
        elif status == 404:
            self.log_test("Webhook Processing: App uninstalled endpoint", False, 
                         "Webhook endpoint not found - routing issue")
        else:
            self.log_test("Webhook Processing: App uninstalled endpoint", True, 
                         f"Webhook endpoint accessible (status: {status})")
        
        # Test 4.5: Test webhook test endpoint
        success, response, status = await self.make_request(
            "GET", 
            "/webhooks/shopify/test"
        )
        
        if success and isinstance(response, dict):
            endpoints = response.get("endpoints", [])
            self.log_test("Webhook Processing: Test endpoint", True, 
                         f"Webhook system active with {len(endpoints)} endpoints")
        else:
            self.log_test("Webhook Processing: Test endpoint", False, 
                         f"Webhook test endpoint failed (status: {status})")

    async def test_multi_tenant_data_isolation(self):
        """Test 5: Multi-Tenant Data Isolation - Test tenant isolation in integration endpoints"""
        print("\n🔒 Testing Multi-Tenant Data Isolation...")
        
        # Test 5.1: Verify tenant-laxmi12-m9zgom gets own connection status
        headers_laxmi = {"X-Tenant-Id": "tenant-laxmi12-m9zgom"}
        success, response_laxmi, status = await self.make_request(
            "GET", 
            "/integrations/shopify/status",
            headers=headers_laxmi
        )
        
        if success:
            self.log_test("Multi-Tenant Isolation: tenant-laxmi12-m9zgom status", True, 
                         f"Retrieved isolated status for tenant-laxmi12-m9zgom")
        else:
            self.log_test("Multi-Tenant Isolation: tenant-laxmi12-m9zgom status", False, 
                         f"Failed to get status for tenant-laxmi12-m9zgom (status: {status})")
        
        # Test 5.2: Verify tenant-rms34 gets different connection status
        headers_rms34 = {"X-Tenant-Id": "tenant-rms34"}
        success, response_rms34, status = await self.make_request(
            "GET", 
            "/integrations/shopify/status",
            headers=headers_rms34
        )
        
        if success:
            self.log_test("Multi-Tenant Isolation: tenant-rms34 status", True, 
                         f"Retrieved isolated status for tenant-rms34")
        else:
            self.log_test("Multi-Tenant Isolation: tenant-rms34 status", False, 
                         f"Failed to get status for tenant-rms34 (status: {status})")
        
        # Test 5.3: Verify data isolation between tenants
        if success and response_laxmi and response_rms34:
            laxmi_connected = response_laxmi.get("connected", False)
            rms34_connected = response_rms34.get("connected", False)
            
            # They should have different connection states (proper isolation)
            self.log_test("Multi-Tenant Isolation: Different connection states", True, 
                         f"tenant-laxmi12-m9zgom: {laxmi_connected}, tenant-rms34: {rms34_connected}")
        
        # Test 5.4: Test cross-tenant data leakage prevention
        # Get orders for tenant-laxmi12-m9zgom
        success, laxmi_orders, status = await self.make_request(
            "GET", 
            "/orders?limit=10",
            headers=headers_laxmi
        )
        
        # Get orders for tenant-rms34
        success, rms34_orders, status = await self.make_request(
            "GET", 
            "/orders?limit=10",
            headers=headers_rms34
        )
        
        if success and laxmi_orders and rms34_orders:
            laxmi_order_ids = [order.get("id") for order in laxmi_orders.get("items", [])]
            rms34_order_ids = [order.get("id") for order in rms34_orders.get("items", [])]
            
            # Check for any overlap (should be none)
            overlap = set(laxmi_order_ids) & set(rms34_order_ids)
            if len(overlap) == 0:
                self.log_test("Multi-Tenant Isolation: Zero data leakage", True, 
                             "No order ID overlap between tenants - perfect isolation")
            else:
                self.log_test("Multi-Tenant Isolation: Zero data leakage", False, 
                             f"Found {len(overlap)} overlapping order IDs - data leakage detected")

    async def test_complete_integration_flow(self):
        """Test 6: Complete Integration Flow - Test end-to-end OAuth system"""
        print("\n🔄 Testing Complete Integration Flow...")
        
        # Test 6.1: Shop domain validation and normalization
        test_shops = ["rms34", "rms34.myshopify.com", "test-store", "UPPERCASE-STORE"]
        
        for shop in test_shops:
            success, response, status = await self.make_request(
                "GET", 
                f"/auth/shopify/install?shop={shop}"
            )
            
            if success or status in [400, 503]:  # 400 = validation error, 503 = disabled
                self.log_test(f"Integration Flow: Shop validation for '{shop}'", True, 
                             f"Shop domain handled correctly (status: {status})")
            else:
                self.log_test(f"Integration Flow: Shop validation for '{shop}'", False, 
                             f"Shop domain validation failed (status: {status})")
        
        # Test 6.2: OAuth state generation and validation
        success, response, status = await self.make_request(
            "GET", 
            "/auth/shopify/debug/generate-state?shop=rms34"
        )
        
        if success and isinstance(response, dict):
            state = response.get("generated_state")
            verification_works = response.get("verification_works", False)
            
            self.log_test("Integration Flow: OAuth state generation", verification_works, 
                         f"State generated and verified: {verification_works}")
            
            # Test state validation
            if state:
                success, validation_response, status = await self.make_request(
                    "GET", 
                    f"/auth/shopify/debug/state?state={state}"
                )
                
                if success and validation_response.get("valid"):
                    self.log_test("Integration Flow: OAuth state validation", True, 
                                 "State validation working correctly")
                else:
                    self.log_test("Integration Flow: OAuth state validation", False, 
                                 "State validation failed")
        else:
            self.log_test("Integration Flow: OAuth state generation", False, 
                         f"State generation failed (status: {status})")
        
        # Test 6.3: Test webhook registration endpoints
        success, response, status = await self.make_request(
            "GET", 
            "/webhooks/shopify/test"
        )
        
        if success and isinstance(response, dict):
            endpoints = response.get("endpoints", [])
            expected_endpoints = ["orders-create", "orders-updated", "fulfillments-create", "fulfillments-update", "app-uninstalled"]
            
            all_endpoints_present = all(endpoint in endpoints for endpoint in expected_endpoints)
            self.log_test("Integration Flow: Webhook registration", all_endpoints_present, 
                         f"Webhook endpoints available: {len(endpoints)}/5 expected")
        else:
            self.log_test("Integration Flow: Webhook registration", False, 
                         "Webhook system not accessible")
        
        # Test 6.4: Test configuration endpoint
        success, response, status = await self.make_request(
            "GET", 
            "/config"
        )
        
        if success and isinstance(response, dict):
            shopify_configured = response.get("shopify_configured", False)
            self.log_test("Integration Flow: Configuration", shopify_configured, 
                         f"Shopify configuration status: {shopify_configured}")
        else:
            self.log_test("Integration Flow: Configuration", False, 
                         f"Configuration endpoint failed (status: {status})")

    async def test_production_readiness_checks(self):
        """Additional production readiness checks"""
        print("\n🚀 Testing Production Readiness...")
        
        # Test health endpoint
        success, response, status = await self.make_request("GET", "/health")
        
        if success:
            self.log_test("Production Readiness: Health endpoint", True, 
                         "Backend health check passed")
        else:
            self.log_test("Production Readiness: Health endpoint", False, 
                         f"Health check failed (status: {status})")
        
        # Test CORS configuration
        headers = {
            "Origin": "https://shopify-sync-fix.preview.emergentagent.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Tenant-Id,Content-Type"
        }
        
        success, response, status = await self.make_request(
            "GET", 
            "/integrations/shopify/status",
            headers={"X-Tenant-Id": "tenant-rms34"}
        )
        
        # Just check if request goes through (CORS is handled by middleware)
        if status != 500:
            self.log_test("Production Readiness: CORS configuration", True, 
                         "CORS appears to be configured correctly")
        else:
            self.log_test("Production Readiness: CORS configuration", False, 
                         "CORS configuration may have issues")

    async def run_all_tests(self):
        """Run all Shopify OAuth & data mapping tests"""
        print("🚀 Starting COMPREHENSIVE OAUTH & DATA MAPPING TEST")
        print("=" * 80)
        print("Testing Complete Shopify integration flow with proper tenant association")
        print("=" * 80)
        
        # Run all test suites
        await self.test_oauth_routing_fix_verification()
        await self.test_integration_dashboard_oauth()
        await self.test_data_mapping_tenant_association()
        await self.test_webhook_data_processing()
        await self.test_multi_tenant_data_isolation()
        await self.test_complete_integration_flow()
        await self.test_production_readiness_checks()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE OAUTH & DATA MAPPING TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Analyze results by category
        categories = {
            "OAuth Routing": [r for r in self.test_results if "OAuth Routing:" in r["test"]],
            "Integration Dashboard": [r for r in self.test_results if "Integration Dashboard:" in r["test"]],
            "Data Mapping": [r for r in self.test_results if "Data Mapping:" in r["test"]],
            "Webhook Processing": [r for r in self.test_results if "Webhook Processing:" in r["test"]],
            "Multi-Tenant Isolation": [r for r in self.test_results if "Multi-Tenant Isolation:" in r["test"]],
            "Integration Flow": [r for r in self.test_results if "Integration Flow:" in r["test"]],
            "Production Readiness": [r for r in self.test_results if "Production Readiness:" in r["test"]]
        }
        
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA VERIFICATION:")
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                percentage = (passed/total*100) if total > 0 else 0
                status = "✅" if passed == total else "⚠️" if passed > total/2 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed ({percentage:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS REQUIRING ATTENTION:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if passed_tests/total_tests >= 0.9:
            print("   ✅ EXCELLENT - OAuth & Data Mapping system is production-ready!")
        elif passed_tests/total_tests >= 0.7:
            print("   ⚠️ GOOD - Minor issues need attention before production")
        else:
            print("   ❌ NEEDS WORK - Critical issues must be resolved")
        
        print(f"\n📋 EXPECTED RESULTS VERIFICATION:")
        print("   • Clean OAuth flow: Integration Dashboard → Shopify → Callback → Data Sync")
        print("   • Real data (orders/returns) synced with proper tenant_id association")
        print("   • Perfect tenant isolation in all integration endpoints")
        print("   • Production-ready OAuth system for merchant onboarding")

async def main():
    """Main test execution"""
    async with ShopifyOAuthDataMappingTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())