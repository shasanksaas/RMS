#!/usr/bin/env python3
"""
Backend Verification Test - Quick verification of key endpoints after frontend routing changes
Tests the specific endpoints mentioned in the user request
"""

import requests
import json
from datetime import datetime

# Use internal backend URL since external routes to frontend
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test data from seed script
TENANT_IDS = ["tenant-fashion-store", "tenant-tech-gadgets"]

class BackendVerificationTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
    def make_request(self, method: str, endpoint: str, data=None, headers=None, expected_status=200):
        """Make HTTP request and return success status and response data"""
        url = f"{API_BASE}/{endpoint}" if endpoint else f"{BACKEND_URL}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers)
            else:
                return False, f"Unsupported method: {method}"
                
            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
                
            if not success:
                return False, f"Status {response.status_code}, Expected {expected_status}. Response: {response_data}"
                
            return True, response_data
            
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_health_check(self):
        """Test /health endpoint"""
        success, data = self.make_request('GET', '', endpoint='health')
        if success and data.get('status') == 'healthy':
            self.log_test("Health Check", True)
            return True
        else:
            self.log_test("Health Check", False, str(data))
            return False

    def test_returns_api_with_pagination(self, tenant_id: str):
        """Test /api/returns endpoint with pagination and filtering"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test basic returns endpoint
        success, data = self.make_request('GET', 'returns', headers=headers)
        if success and 'items' in data and 'pagination' in data:
            self.log_test(f"Returns API - Basic ({tenant_id})", True)
            
            # Test pagination
            success, paginated = self.make_request('GET', 'returns?page=1&limit=5', headers=headers)
            if success and paginated.get('pagination', {}).get('per_page') == 5:
                self.log_test(f"Returns API - Pagination ({tenant_id})", True)
            else:
                self.log_test(f"Returns API - Pagination ({tenant_id})", False, "Pagination not working")
                
            # Test filtering
            success, filtered = self.make_request('GET', 'returns?status_filter=approved', headers=headers)
            if success and 'items' in filtered:
                self.log_test(f"Returns API - Filtering ({tenant_id})", True)
            else:
                self.log_test(f"Returns API - Filtering ({tenant_id})", False, "Filtering not working")
                
            return True
        else:
            self.log_test(f"Returns API - Basic ({tenant_id})", False, str(data))
            return False

    def test_settings_api(self, tenant_id: str):
        """Test /api/tenants/{tenant_id}/settings GET and PUT endpoints"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test GET settings
        success, settings_data = self.make_request('GET', f'tenants/{tenant_id}/settings', headers=headers)
        if success and 'settings' in settings_data:
            self.log_test(f"Settings API - GET ({tenant_id})", True)
            
            # Test PUT settings
            new_settings = {
                "return_window_days": 45,
                "auto_approve_exchanges": False,
                "brand_color": "#ff6b6b"
            }
            
            success, update_result = self.make_request('PUT', f'tenants/{tenant_id}/settings', new_settings, headers)
            if success and update_result.get('success'):
                self.log_test(f"Settings API - PUT ({tenant_id})", True)
                
                # Verify settings were saved
                success, verified = self.make_request('GET', f'tenants/{tenant_id}/settings', headers=headers)
                if success and verified['settings']['return_window_days'] == 45:
                    self.log_test(f"Settings API - Persistence ({tenant_id})", True)
                else:
                    self.log_test(f"Settings API - Persistence ({tenant_id})", False, "Settings not persisted")
                    
                return True
            else:
                self.log_test(f"Settings API - PUT ({tenant_id})", False, str(update_result))
                return False
        else:
            self.log_test(f"Settings API - GET ({tenant_id})", False, str(settings_data))
            return False

    def test_analytics_api(self, tenant_id: str):
        """Test /api/analytics endpoint for both 7d and 30d timeframes"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test 30-day analytics
        success, analytics_30d = self.make_request('GET', 'analytics?days=30', headers=headers)
        if success and 'total_returns' in analytics_30d:
            self.log_test(f"Analytics API - 30 days ({tenant_id})", True)
        else:
            self.log_test(f"Analytics API - 30 days ({tenant_id})", False, str(analytics_30d))
            return False
            
        # Test 7-day analytics
        success, analytics_7d = self.make_request('GET', 'analytics?days=7', headers=headers)
        if success and 'total_returns' in analytics_7d:
            self.log_test(f"Analytics API - 7 days ({tenant_id})", True)
        else:
            self.log_test(f"Analytics API - 7 days ({tenant_id})", False, str(analytics_7d))
            return False
            
        return True

    def test_multi_tenancy(self):
        """Test multi-tenancy isolation between the two seeded tenants"""
        tenant1_id = TENANT_IDS[0]
        tenant2_id = TENANT_IDS[1]
        
        headers1 = {'X-Tenant-Id': tenant1_id}
        headers2 = {'X-Tenant-Id': tenant2_id}
        
        # Get returns for both tenants
        success1, returns1 = self.make_request('GET', 'returns', headers=headers1)
        success2, returns2 = self.make_request('GET', 'returns', headers=headers2)
        
        if success1 and success2:
            # Verify each tenant has their own data
            tenant1_count = len(returns1.get('items', []))
            tenant2_count = len(returns2.get('items', []))
            
            if tenant1_count > 0 and tenant2_count > 0:
                self.log_test("Multi-Tenancy - Data Isolation", True)
                
                # Try cross-tenant access (should fail)
                if tenant1_count > 0:
                    first_return_id = returns1['items'][0]['id']
                    success, cross_access = self.make_request('GET', f'returns/{first_return_id}', 
                                                            headers=headers2, expected_status=404)
                    if success:
                        self.log_test("Multi-Tenancy - Cross-tenant Access Blocked", True)
                    else:
                        self.log_test("Multi-Tenancy - Cross-tenant Access Blocked", False, "Should block cross-tenant access")
                        
                return True
            else:
                self.log_test("Multi-Tenancy - Data Isolation", False, f"Insufficient data: T1={tenant1_count}, T2={tenant2_count}")
                return False
        else:
            self.log_test("Multi-Tenancy - Data Isolation", False, "Could not fetch tenant data")
            return False

    def test_core_functionality(self):
        """Test a few key endpoints to ensure basic functionality"""
        tenant_id = TENANT_IDS[0]  # Use first tenant
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test tenants endpoint
        success, tenants = self.make_request('GET', 'tenants')
        if success and isinstance(tenants, list) and len(tenants) >= 2:
            self.log_test("Core - Tenants Endpoint", True)
        else:
            self.log_test("Core - Tenants Endpoint", False, str(tenants))
            
        # Test products endpoint
        success, products = self.make_request('GET', 'products', headers=headers)
        if success and isinstance(products, list):
            self.log_test(f"Core - Products Endpoint ({tenant_id})", True)
        else:
            self.log_test(f"Core - Products Endpoint ({tenant_id})", False, str(products))
            
        # Test orders endpoint
        success, orders = self.make_request('GET', 'orders', headers=headers)
        if success and isinstance(orders, list):
            self.log_test(f"Core - Orders Endpoint ({tenant_id})", True)
        else:
            self.log_test(f"Core - Orders Endpoint ({tenant_id})", False, str(orders))

    def run_verification_tests(self):
        """Run the specific verification tests requested"""
        print("🔍 Backend Verification Test - Post Frontend Routing Changes")
        print("=" * 70)
        
        # 1. Health Check
        print("\n1. Testing Health Check...")
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
            
        # 2. Returns API with pagination and filtering
        print("\n2. Testing Returns API...")
        for tenant_id in TENANT_IDS:
            self.test_returns_api_with_pagination(tenant_id)
            
        # 3. Settings API
        print("\n3. Testing Settings API...")
        for tenant_id in TENANT_IDS:
            self.test_settings_api(tenant_id)
            
        # 4. Analytics API
        print("\n4. Testing Analytics API...")
        for tenant_id in TENANT_IDS:
            self.test_analytics_api(tenant_id)
            
        # 5. Multi-tenancy verification
        print("\n5. Testing Multi-Tenancy...")
        self.test_multi_tenancy()
        
        # 6. Core functionality
        print("\n6. Testing Core Functionality...")
        self.test_core_functionality()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Verification Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All verification tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed")
            return False

def main():
    """Main test runner"""
    tester = BackendVerificationTester()
    success = tester.run_verification_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())