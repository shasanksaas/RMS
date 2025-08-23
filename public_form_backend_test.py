#!/usr/bin/env python3
"""
Public Form Configuration Backend Testing
Tests the specific requirements from the review request:
1. Public form config endpoint at /api/public/forms/{tenant_id}/config
2. Tenant isolation middleware bypass for /api/public paths
3. Regression check for /api/orders requiring X-Tenant-Id
4. CORS and ingress behavior for /api/public endpoints
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://returnflow-4.preview.emergentagent.com"
TEST_TENANT_RMS34 = "tenant-rms34"
RANDOM_TENANT = "tenant-random-test"

class PublicFormTestSuite:
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
    
    async def test_public_form_config_tenant_rms34(self):
        """Test 1: Public form config endpoint for tenant-rms34"""
        print("\n🔍 Testing Public Form Config for tenant-rms34...")
        
        # Test without any headers (no auth, no X-Tenant-Id)
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{TEST_TENANT_RMS34}/config"
        )
        
        if success and isinstance(response, dict):
            # Check required keys
            required_keys = ["config"]
            config_keys = ["branding", "layout", "form"]
            
            has_required = all(key in response for key in required_keys)
            has_config_keys = all(key in response.get("config", {}) for key in config_keys)
            
            if has_required and has_config_keys:
                self.log_test(
                    "Public Form Config: tenant-rms34 structure", 
                    True, 
                    f"Response has required keys: {required_keys} and config keys: {config_keys}"
                )
                
                # Check branding structure
                branding = response["config"].get("branding", {})
                branding_keys = ["primary_color", "secondary_color", "background_color", "text_color"]
                has_branding = any(key in branding for key in branding_keys)
                
                self.log_test(
                    "Public Form Config: tenant-rms34 branding", 
                    has_branding, 
                    f"Branding config present with keys: {list(branding.keys())}"
                )
                
                # Check layout structure
                layout = response["config"].get("layout", {})
                layout_keys = ["preset", "corner_radius", "spacing_density"]
                has_layout = any(key in layout for key in layout_keys)
                
                self.log_test(
                    "Public Form Config: tenant-rms34 layout", 
                    has_layout, 
                    f"Layout config present with keys: {list(layout.keys())}"
                )
                
                # Check form structure
                form = response["config"].get("form", {})
                form_keys = ["return_reasons", "available_resolutions", "return_window_days"]
                has_form = any(key in form for key in form_keys)
                
                self.log_test(
                    "Public Form Config: tenant-rms34 form", 
                    has_form, 
                    f"Form config present with keys: {list(form.keys())}"
                )
                
            else:
                self.log_test(
                    "Public Form Config: tenant-rms34 structure", 
                    False, 
                    f"Missing required keys. Response keys: {list(response.keys())}"
                )
        else:
            self.log_test(
                "Public Form Config: tenant-rms34 access", 
                False, 
                f"Failed to get config. Status: {status}, Response: {response}"
            )
    
    async def test_public_form_config_random_tenant(self):
        """Test 2: Public form config endpoint for random tenant (should return defaults)"""
        print("\n🎲 Testing Public Form Config for random tenant...")
        
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{RANDOM_TENANT}/config"
        )
        
        if success and isinstance(response, dict):
            # Should return default configuration
            config = response.get("config", {})
            
            # Check for default values
            branding = config.get("branding", {})
            default_primary_color = branding.get("primary_color") == "#3B82F6"
            default_font = branding.get("font_family") == "Inter"
            
            layout = config.get("layout", {})
            default_preset = layout.get("preset") == "wizard"
            
            form = config.get("form", {})
            default_window = form.get("return_window_days") == 30
            
            has_defaults = any([default_primary_color, default_font, default_preset, default_window])
            
            self.log_test(
                "Public Form Config: random tenant defaults", 
                has_defaults, 
                f"Returns default configuration for non-existent tenant"
            )
        else:
            self.log_test(
                "Public Form Config: random tenant access", 
                False, 
                f"Failed to get config. Status: {status}, Response: {response}"
            )
    
    async def test_tenant_isolation_bypass(self):
        """Test 3: Verify tenant isolation middleware allows /api/public/forms paths"""
        print("\n🛡️ Testing Tenant Isolation Middleware Bypass...")
        
        # Test 1: /api/public/forms should work without X-Tenant-Id header
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{TEST_TENANT_RMS34}/config"
        )
        
        self.log_test(
            "Tenant Isolation: /api/public bypass", 
            success, 
            f"Public endpoint accessible without tenant header. Status: {status}"
        )
        
        # Test 2: /api/public/forms should work with wrong X-Tenant-Id header
        wrong_headers = {"X-Tenant-Id": "wrong-tenant-id"}
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{TEST_TENANT_RMS34}/config",
            headers=wrong_headers
        )
        
        self.log_test(
            "Tenant Isolation: /api/public with wrong tenant", 
            success, 
            f"Public endpoint accessible with wrong tenant header. Status: {status}"
        )
        
        # Test 3: /api/public/forms should work without any authentication
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{TEST_TENANT_RMS34}/config",
            headers={}
        )
        
        self.log_test(
            "Tenant Isolation: /api/public no auth", 
            success, 
            f"Public endpoint accessible without authentication. Status: {status}"
        )
    
    async def test_orders_regression_check(self):
        """Test 4: Regression check - /api/orders still requires X-Tenant-Id"""
        print("\n🔄 Testing Orders Endpoint Regression...")
        
        # Test 1: /api/orders without X-Tenant-Id should fail
        success, response, status = await self.make_request(
            "GET", 
            "/api/orders"
        )
        
        should_fail = not success and status in [400, 401, 403]
        self.log_test(
            "Orders Regression: requires tenant header", 
            should_fail, 
            f"Orders endpoint correctly requires tenant header. Status: {status}"
        )
        
        # Test 2: /api/orders with X-Tenant-Id should work
        tenant_headers = {"X-Tenant-Id": TEST_TENANT_RMS34}
        success, response, status = await self.make_request(
            "GET", 
            "/api/orders",
            headers=tenant_headers
        )
        
        self.log_test(
            "Orders Regression: works with tenant header", 
            success, 
            f"Orders endpoint works with tenant header. Status: {status}"
        )
        
        # Test 3: Verify no route conflicts with new /api/public include
        if success and isinstance(response, dict):
            # Should return orders data structure
            has_items = "items" in response or isinstance(response, list)
            self.log_test(
                "Orders Regression: no route conflicts", 
                has_items, 
                f"Orders endpoint returns expected data structure"
            )
        else:
            self.log_test(
                "Orders Regression: no route conflicts", 
                False, 
                f"Orders endpoint not returning expected data. Response: {response}"
            )
    
    async def test_cors_and_ingress_behavior(self):
        """Test 5: Confirm CORS and ingress behavior for /api/public endpoints"""
        print("\n🌐 Testing CORS and Ingress Behavior...")
        
        # Test 1: OPTIONS request for CORS preflight
        try:
            url = f"{BACKEND_URL}/api/public/forms/{TEST_TENANT_RMS34}/config"
            async with self.session.options(url) as response:
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                has_cors = any(header for header in cors_headers.values())
                self.log_test(
                    "CORS: OPTIONS preflight", 
                    response.status == 200 or has_cors, 
                    f"CORS headers present: {cors_headers}"
                )
        except Exception as e:
            self.log_test(
                "CORS: OPTIONS preflight", 
                False, 
                f"OPTIONS request failed: {str(e)}"
            )
        
        # Test 2: Verify no HTML fallback (should return JSON, not HTML)
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{TEST_TENANT_RMS34}/config"
        )
        
        if success:
            is_json = isinstance(response, dict)
            is_not_html = not (isinstance(response, str) and response.strip().startswith("<"))
            
            self.log_test(
                "Ingress: no HTML fallback", 
                is_json and is_not_html, 
                f"Response is JSON, not HTML. Type: {type(response)}"
            )
        else:
            self.log_test(
                "Ingress: no HTML fallback", 
                False, 
                f"Could not test HTML fallback due to request failure"
            )
        
        # Test 3: Verify frontend capture doesn't interfere
        # Check that the endpoint returns API response, not frontend app
        if success and isinstance(response, dict):
            has_api_structure = "config" in response
            self.log_test(
                "Ingress: no frontend capture", 
                has_api_structure, 
                f"Response has API structure, not frontend app"
            )
        else:
            self.log_test(
                "Ingress: no frontend capture", 
                False, 
                f"Could not verify API structure"
            )
    
    async def test_error_json_capture(self):
        """Test 6: Capture error JSON and route mappings if failures occur"""
        print("\n🚨 Testing Error Scenarios...")
        
        # Test 1: Invalid tenant ID format
        success, response, status = await self.make_request(
            "GET", 
            "/api/public/forms/invalid-tenant-format/config"
        )
        
        # Should still return default config, not error
        if success:
            self.log_test(
                "Error Handling: invalid tenant format", 
                True, 
                f"Returns default config for invalid tenant format"
            )
        else:
            self.log_test(
                "Error Handling: invalid tenant format", 
                False, 
                f"Error response: {response}"
            )
        
        # Test 2: Very long tenant ID
        long_tenant = "tenant-" + "x" * 100
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{long_tenant}/config"
        )
        
        if success:
            self.log_test(
                "Error Handling: long tenant ID", 
                True, 
                f"Handles long tenant ID gracefully"
            )
        else:
            self.log_test(
                "Error Handling: long tenant ID", 
                False, 
                f"Error response: {response}"
            )
        
        # Test 3: Special characters in tenant ID
        special_tenant = "tenant-test@#$%"
        success, response, status = await self.make_request(
            "GET", 
            f"/api/public/forms/{special_tenant}/config"
        )
        
        if success:
            self.log_test(
                "Error Handling: special characters", 
                True, 
                f"Handles special characters gracefully"
            )
        else:
            self.log_test(
                "Error Handling: special characters", 
                False, 
                f"Error response: {response}"
            )
    
    async def run_all_tests(self):
        """Run all public form configuration tests"""
        print("🚀 Starting Public Form Configuration Testing")
        print("=" * 60)
        
        # Run all test suites
        await self.test_public_form_config_tenant_rms34()
        await self.test_public_form_config_random_tenant()
        await self.test_tenant_isolation_bypass()
        await self.test_orders_regression_check()
        await self.test_cors_and_ingress_behavior()
        await self.test_error_json_capture()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 PUBLIC FORM CONFIGURATION TESTING SUMMARY")
        print("=" * 60)
        
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
        
        # Analyze results by category
        categories = {
            "Public Form Config": [r for r in self.test_results if "Public Form Config:" in r["test"]],
            "Tenant Isolation": [r for r in self.test_results if "Tenant Isolation:" in r["test"]],
            "Orders Regression": [r for r in self.test_results if "Orders Regression:" in r["test"]],
            "CORS": [r for r in self.test_results if "CORS:" in r["test"]],
            "Ingress": [r for r in self.test_results if "Ingress:" in r["test"]],
            "Error Handling": [r for r in self.test_results if "Error Handling:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")

async def main():
    """Main test execution"""
    async with PublicFormTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())