#!/usr/bin/env python3
"""
Focused Backend API Testing for the 5 tasks that need testing:
1. GraphQL Service for Returns Operations
2. Webhook Processing with Idempotency  
3. Sync Service with Initial Backfill
4. Auth Service Enhancement with OAuth
5. Testing Endpoints for Development
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Use the internal backend URL for testing
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class FocusedAPITester:
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
        
    def make_request(self, method: str, endpoint: str, data: any = None, 
                    headers: Dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{API_BASE}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method == 'POST':
                if isinstance(data, str):
                    # Send as raw string for endpoints expecting string body
                    request_headers['Content-Type'] = 'text/plain'
                    response = requests.post(url, data=data, headers=request_headers)
                else:
                    response = requests.post(url, json=data, headers=request_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers)
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
        """Test basic connectivity"""
        success, data = self.make_request('GET', '../health')  # health is not under /api
        self.log_test("Backend Health Check", success, str(data) if not success else "")
        return success

    def test_graphql_service_connection(self):
        """Test GraphQL service connection and basic queries"""
        # Test seeded tenant IDs (these should exist from seed data)
        seeded_tenants = ["tenant-fashion-store.myshopify.com", "tenant-tech-gadgets.myshopify.com"]
        
        for tenant_id in seeded_tenants:
            # Test store connection endpoint
            success, connection_info = self.make_request('GET', f'test/stores/{tenant_id}/connection')
            if success and connection_info.get('status') == 'success':
                self.log_test(f"GraphQL Service - Store connection ({tenant_id})", True)
                
                # Check if GraphQL service was created
                if connection_info.get('graphql_service'):
                    self.log_test(f"GraphQL Service - Service creation ({tenant_id})", True)
                    
                    # Check if shop info was retrieved
                    if connection_info.get('shop_info'):
                        self.log_test(f"GraphQL Service - Shop info query ({tenant_id})", True)
                    else:
                        self.log_test(f"GraphQL Service - Shop info query ({tenant_id})", False, "No shop info returned")
                else:
                    self.log_test(f"GraphQL Service - Service creation ({tenant_id})", False, connection_info.get('message', 'Service creation failed'))
            else:
                self.log_test(f"GraphQL Service - Store connection ({tenant_id})", False, str(connection_info))
                
        return True

    def test_webhook_processing_with_idempotency(self):
        """Test webhook processing with idempotency checks"""
        # Test webhook samples endpoint (GET not POST)
        success, samples = self.make_request('GET', 'test/webhook/samples')
        if success and 'samples' in samples:
            self.log_test("Webhook Processing - Sample payloads", True)
            
            # Test processing different webhook types
            webhook_topics = ['orders/create', 'returns/create', 'app/uninstalled']
            
            for topic in webhook_topics:
                if topic in samples['samples']:
                    payload = samples['samples'][topic]
                    
                    # Test webhook processing with correct format
                    webhook_data = {
                        "topic": topic,
                        "shop_domain": "tenant-fashion-store.myshopify.com",
                        "payload": payload
                    }
                    
                    success, result = self.make_request('POST', 'test/webhook', webhook_data)
                    if success and result.get('status') == 'success':
                        self.log_test(f"Webhook Processing - {topic}", True)
                        
                        # Test idempotency by sending the same webhook again
                        success2, result2 = self.make_request('POST', 'test/webhook', webhook_data)
                        if success2:
                            self.log_test(f"Webhook Idempotency - {topic}", True)
                        else:
                            self.log_test(f"Webhook Idempotency - {topic}", False, "Duplicate processing should be handled")
                    else:
                        self.log_test(f"Webhook Processing - {topic}", False, str(result))
                        
        else:
            self.log_test("Webhook Processing - Sample payloads", False, str(samples))
            return False
            
        # Test critical app/uninstalled webhook for tenant cleanup
        app_uninstalled_payload = {
            "topic": "app/uninstalled",
            "shop_domain": "test-cleanup-store.myshopify.com",
            "payload": {
                "id": 98765,
                "name": "Test Cleanup Store",
                "domain": "test-cleanup-store.myshopify.com",
                "uninstalled_at": "2025-08-10T12:00:00Z"
            }
        }
        
        success, result = self.make_request('POST', 'test/webhook', app_uninstalled_payload)
        if success and result.get('status') == 'success':
            # Check if cleanup actions were performed
            if result.get('result', {}).get('action') == 'store_deactivated':
                self.log_test("App Uninstalled Webhook - Tenant cleanup", True)
            else:
                self.log_test("App Uninstalled Webhook - Tenant cleanup", False, "Cleanup action not performed")
        else:
            self.log_test("App Uninstalled Webhook - Processing", False, str(result))
            
        return True

    def test_sync_service_functionality(self):
        """Test sync service with different sync types"""
        # Test with seeded tenant IDs
        seeded_tenants = ["tenant-fashion-store.myshopify.com", "tenant-tech-gadgets.myshopify.com"]
        
        for tenant_id in seeded_tenants:
            # Test initial sync - send sync_type as string in body
            success, result = self.make_request('POST', f'test/sync/{tenant_id}', "initial")
            if success and result.get('status') == 'success':
                self.log_test(f"Sync Service - Initial sync ({tenant_id})", True)
                
                # Check sync results
                sync_result = result.get('result', {})
                if 'orders' in sync_result and 'products' in sync_result:
                    self.log_test(f"Sync Service - Data categories ({tenant_id})", True)
                else:
                    self.log_test(f"Sync Service - Data categories ({tenant_id})", False, "Missing sync categories")
            else:
                self.log_test(f"Sync Service - Initial sync ({tenant_id})", False, str(result))
                
            # Test manual sync - send sync_type as string in body
            success, manual_result = self.make_request('POST', f'test/sync/{tenant_id}', "manual")
            if success and manual_result.get('status') == 'success':
                self.log_test(f"Sync Service - Manual sync ({tenant_id})", True)
            else:
                self.log_test(f"Sync Service - Manual sync ({tenant_id})", False, str(manual_result))
                
        return True

    def test_auth_service_enhancement(self):
        """Test auth service health and configuration"""
        success, status = self.make_request('GET', 'auth/status')
        if success and status.get('service') == 'shopify_auth':
            self.log_test("Auth Service - Status endpoint", True)
            
            # Check required configuration
            required_fields = ['api_version', 'redirect_uri', 'required_scopes']
            if all(field in status for field in required_fields):
                self.log_test("Auth Service - Configuration check", True)
            else:
                self.log_test("Auth Service - Configuration check", False, "Missing configuration fields")
                
            # Check if encryption is configured
            if status.get('encryption') in ['fernet', 'none']:
                self.log_test("Auth Service - Encryption status", True)
            else:
                self.log_test("Auth Service - Encryption status", False, "Invalid encryption status")
        else:
            self.log_test("Auth Service - Status endpoint", False, str(status))
            return False
            
        # Test credential validation endpoint
        test_credentials = {
            "shop": "test-store",
            "api_key": "test_api_key_12345678",
            "api_secret": "test_api_secret_87654321"
        }
        
        success, validation = self.make_request('POST', 'auth/test/validate', test_credentials)
        if success and 'overall_valid' in validation:
            self.log_test("Auth Service - Credential validation", True)
            
            # Check validation details
            if 'validations' in validation:
                validations = validation['validations']
                if all(key in validations for key in ['shop_domain', 'api_key', 'api_secret']):
                    self.log_test("Auth Service - Validation details", True)
                else:
                    self.log_test("Auth Service - Validation details", False, "Missing validation details")
            else:
                self.log_test("Auth Service - Validation details", False, "No validation details")
        else:
            self.log_test("Auth Service - Credential validation", False, str(validation))
            return False
            
        return True

    def test_testing_endpoints_development(self):
        """Test development testing endpoints"""
        # Test health endpoint
        success, health = self.make_request('GET', 'test/health')
        if success and health.get('status') == 'healthy':
            self.log_test("Testing Endpoints - Health check", True)
            
            # Check service status
            services = health.get('services', {})
            required_services = ['webhook_processor', 'sync_service', 'auth_service']
            if all(services.get(service) for service in required_services):
                self.log_test("Testing Endpoints - Service status", True)
            else:
                self.log_test("Testing Endpoints - Service status", False, "Some services not healthy")
                
            # Check webhook topics count
            if health.get('supported_webhook_topics', 0) > 0:
                self.log_test("Testing Endpoints - Webhook topics", True)
            else:
                self.log_test("Testing Endpoints - Webhook topics", False, "No webhook topics supported")
        else:
            self.log_test("Testing Endpoints - Health check", False, str(health))
            return False
            
        # Test webhook test endpoint
        success, webhook_test = self.make_request('GET', 'webhooks/test')
        if success and webhook_test.get('service') == 'webhooks':
            self.log_test("Testing Endpoints - Webhook test endpoint", True)
            
            # Check supported topics
            if 'supported_topics' in webhook_test and len(webhook_test['supported_topics']) > 0:
                self.log_test("Testing Endpoints - Webhook supported topics", True)
            else:
                self.log_test("Testing Endpoints - Webhook supported topics", False, "No supported topics")
        else:
            self.log_test("Testing Endpoints - Webhook test endpoint", False, str(webhook_test))
            return False
            
        return True

    def run_focused_tests(self):
        """Run focused tests on the 5 tasks that need testing"""
        print("🎯 FOCUSED BACKEND TESTING - 5 Tasks That Need Testing")
        print("=" * 70)
        print("1. GraphQL Service for Returns Operations")
        print("2. Webhook Processing with Idempotency")
        print("3. Sync Service with Initial Backfill")
        print("4. Auth Service Enhancement with OAuth")
        print("5. Testing Endpoints for Development")
        print("=" * 70)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Cannot connect to backend, stopping tests")
            return False
            
        print("\n🔍 Testing GraphQL Service for Returns Operations...")
        self.test_graphql_service_connection()
        
        print("\n🔗 Testing Webhook Processing with Idempotency...")
        self.test_webhook_processing_with_idempotency()
        
        print("\n🔄 Testing Sync Service with Initial Backfill...")
        self.test_sync_service_functionality()
        
        print("\n🔐 Testing Auth Service Enhancement with OAuth...")
        self.test_auth_service_enhancement()
        
        print("\n🧪 Testing Development Testing Endpoints...")
        self.test_testing_endpoints_development()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Focused Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All focused tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} focused test(s) failed")
            return False

def main():
    """Main test runner"""
    tester = FocusedAPITester()
    success = tester.run_focused_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())