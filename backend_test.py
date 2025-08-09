#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Returns Management SaaS
Tests all endpoints, multi-tenant isolation, and business logic
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Use the public backend URL from frontend .env
BACKEND_URL = "https://501365f5-045d-4396-9baf-9d307eab5a9f.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ReturnsAPITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tenant_ids = []
        self.product_ids = []
        self.order_ids = []
        self.return_ids = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, data = self.make_request('GET', '')
        self.log_test("Root endpoint", success, str(data) if not success else "")
        return success

    def test_create_tenant(self) -> str:
        """Test tenant creation and return tenant ID"""
        tenant_data = {
            "name": f"Test Tenant {datetime.now().strftime('%H%M%S')}",
            "domain": f"test-{datetime.now().strftime('%H%M%S')}.com",
            "shopify_store_url": "test-store.myshopify.com"
        }
        
        success, data = self.make_request('POST', 'tenants', tenant_data, expected_status=200)
        if success and 'id' in data:
            tenant_id = data['id']
            self.tenant_ids.append(tenant_id)
            self.log_test("Create tenant", True)
            return tenant_id
        else:
            self.log_test("Create tenant", False, str(data))
            return None

    def test_get_tenants(self):
        """Test getting all tenants"""
        success, data = self.make_request('GET', 'tenants')
        if success and isinstance(data, list):
            self.log_test("Get tenants", True)
            return True
        else:
            self.log_test("Get tenants", False, str(data))
            return False

    def test_tenant_isolation(self):
        """Test that tenants are properly isolated"""
        # Create two tenants
        tenant1_id = self.test_create_tenant()
        tenant2_id = self.test_create_tenant()
        
        if not tenant1_id or not tenant2_id:
            self.log_test("Tenant isolation setup", False, "Could not create test tenants")
            return False
            
        # Create product for tenant1
        product_data = {
            "name": "Isolation Test Product",
            "price": 99.99,
            "category": "Test",
            "sku": "ISO-001"
        }
        
        headers1 = {'X-Tenant-Id': tenant1_id}
        headers2 = {'X-Tenant-Id': tenant2_id}
        
        # Create product in tenant1
        success, product = self.make_request('POST', 'products', product_data, headers1, 200)
        if not success:
            self.log_test("Tenant isolation - create product", False, str(product))
            return False
            
        # Try to get products from tenant2 (should be empty)
        success, tenant2_products = self.make_request('GET', 'products', headers=headers2)
        if success and len(tenant2_products) == 0:
            self.log_test("Tenant isolation", True)
            return True
        else:
            self.log_test("Tenant isolation", False, f"Tenant2 saw tenant1's products: {tenant2_products}")
            return False

    def test_missing_tenant_header(self):
        """Test that endpoints require X-Tenant-Id header"""
        success, data = self.make_request('GET', 'products', expected_status=400)
        if success:
            self.log_test("Missing tenant header validation", True)
            return True
        else:
            self.log_test("Missing tenant header validation", False, "Should return 400 for missing header")
            return False

    def test_products_crud(self, tenant_id: str):
        """Test product CRUD operations"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create product
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 49.99,
            "category": "Electronics",
            "sku": "TEST-001",
            "image_url": "https://example.com/image.jpg"
        }
        
        success, product = self.make_request('POST', 'products', product_data, headers)
        if success and 'id' in product:
            product_id = product['id']
            self.product_ids.append(product_id)
            self.log_test("Create product", True)
        else:
            self.log_test("Create product", False, str(product))
            return False
            
        # Get products
        success, products = self.make_request('GET', 'products', headers=headers)
        if success and isinstance(products, list) and len(products) > 0:
            self.log_test("Get products", True)
        else:
            self.log_test("Get products", False, str(products))
            return False
            
        return True

    def test_orders_crud(self, tenant_id: str):
        """Test order CRUD operations"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create order
        order_data = {
            "customer_email": "test@example.com",
            "customer_name": "Test Customer",
            "order_number": f"ORD-{datetime.now().strftime('%H%M%S')}",
            "items": [
                {
                    "product_id": "test-product-1",
                    "product_name": "Test Product",
                    "quantity": 2,
                    "price": 49.99,
                    "sku": "TEST-001"
                }
            ],
            "total_amount": 99.98,
            "order_date": datetime.utcnow().isoformat()
        }
        
        success, order = self.make_request('POST', 'orders', order_data, headers)
        if success and 'id' in order:
            order_id = order['id']
            self.order_ids.append(order_id)
            self.log_test("Create order", True)
        else:
            self.log_test("Create order", False, str(order))
            return False
            
        # Get orders
        success, orders = self.make_request('GET', 'orders', headers=headers)
        if success and isinstance(orders, list):
            self.log_test("Get orders", True)
        else:
            self.log_test("Get orders", False, str(orders))
            return False
            
        # Get specific order
        success, single_order = self.make_request('GET', f'orders/{order_id}', headers=headers)
        if success and single_order.get('id') == order_id:
            self.log_test("Get single order", True)
        else:
            self.log_test("Get single order", False, str(single_order))
            return False
            
        return True

    def test_return_rules(self, tenant_id: str):
        """Test return rules CRUD operations"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create return rule
        rule_data = {
            "name": "Test Auto-Approve Rule",
            "description": "Auto-approve defective items for testing",
            "conditions": {
                "auto_approve_reasons": ["defective", "damaged_in_shipping"],
                "max_days_since_order": 30
            },
            "actions": {
                "auto_approve": True,
                "generate_label": True
            },
            "priority": 1
        }
        
        success, rule = self.make_request('POST', 'return-rules', rule_data, headers)
        if success and 'id' in rule:
            self.log_test("Create return rule", True)
        else:
            self.log_test("Create return rule", False, str(rule))
            return False
            
        # Get return rules
        success, rules = self.make_request('GET', 'return-rules', headers=headers)
        if success and isinstance(rules, list):
            self.log_test("Get return rules", True)
        else:
            self.log_test("Get return rules", False, str(rules))
            return False
            
        return True

    def test_returns_workflow(self, tenant_id: str):
        """Test complete returns workflow"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # First create an order to return
        order_data = {
            "customer_email": "return-test@example.com",
            "customer_name": "Return Test Customer",
            "order_number": f"RET-ORD-{datetime.now().strftime('%H%M%S')}",
            "items": [
                {
                    "product_id": "return-test-product",
                    "product_name": "Returnable Product",
                    "quantity": 1,
                    "price": 79.99,
                    "sku": "RET-001"
                }
            ],
            "total_amount": 79.99,
            "order_date": (datetime.utcnow() - timedelta(days=5)).isoformat()
        }
        
        success, order = self.make_request('POST', 'orders', order_data, headers)
        if not success:
            self.log_test("Returns workflow - create order", False, str(order))
            return False
            
        order_id = order['id']
        
        # Create return request
        return_data = {
            "order_id": order_id,
            "reason": "defective",
            "items_to_return": order['items'],
            "notes": "Product was defective on arrival"
        }
        
        success, return_request = self.make_request('POST', 'returns', return_data, headers)
        if success and 'id' in return_request:
            return_id = return_request['id']
            self.return_ids.append(return_id)
            self.log_test("Create return request", True)
            
            # Check if auto-approval worked (should be approved due to 'defective' reason)
            if return_request.get('status') == 'approved':
                self.log_test("Return rules engine - auto approval", True)
            else:
                self.log_test("Return rules engine - auto approval", False, 
                            f"Expected 'approved', got '{return_request.get('status')}'")
        else:
            self.log_test("Create return request", False, str(return_request))
            return False
            
        # Get returns
        success, returns = self.make_request('GET', 'returns', headers=headers)
        if success and isinstance(returns, list):
            self.log_test("Get returns", True)
        else:
            self.log_test("Get returns", False, str(returns))
            return False
            
        # Get specific return
        success, single_return = self.make_request('GET', f'returns/{return_id}', headers=headers)
        if success and single_return.get('id') == return_id:
            self.log_test("Get single return", True)
        else:
            self.log_test("Get single return", False, str(single_return))
            return False
            
        # Update return status
        status_update = {
            "status": "refunded",
            "notes": "Refund processed successfully",
            "tracking_number": "TRACK123456"
        }
        
        success, updated_return = self.make_request('PUT', f'returns/{return_id}/status', 
                                                  status_update, headers)
        if success and updated_return.get('status') == 'refunded':
            self.log_test("Update return status", True)
        else:
            self.log_test("Update return status", False, str(updated_return))
            return False
            
        return True

    def test_analytics(self, tenant_id: str):
        """Test analytics endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test analytics with default 30 days
        success, analytics = self.make_request('GET', 'analytics', headers=headers)
        if success and 'total_returns' in analytics:
            self.log_test("Get analytics (30 days)", True)
        else:
            self.log_test("Get analytics (30 days)", False, str(analytics))
            return False
            
        # Test analytics with custom days
        success, analytics_7d = self.make_request('GET', 'analytics?days=7', headers=headers)
        if success and 'total_returns' in analytics_7d:
            self.log_test("Get analytics (7 days)", True)
        else:
            self.log_test("Get analytics (7 days)", False, str(analytics_7d))
            return False
            
        return True

    def test_shopify_webhook(self, tenant_id: str):
        """Test Shopify webhook endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        webhook_data = {
            "id": "shopify-order-123",
            "customer": {"email": "webhook@example.com"},
            "line_items": [{"title": "Webhook Product", "price": "29.99"}]
        }
        
        success, response = self.make_request('POST', 'shopify/webhook/orders/create', 
                                            webhook_data, headers)
        if success and response.get('status') == 'received':
            self.log_test("Shopify webhook", True)
        else:
            self.log_test("Shopify webhook", False, str(response))
            return False
            
        return True

    def test_shopify_oauth_install(self):
        """Test Shopify OAuth installation endpoint"""
        # Test with valid shop name
        success, response = self.make_request('GET', 'shopify/install?shop=test-store')
        if success and 'auth_url' in response:
            self.log_test("Shopify OAuth install", True)
            return True
        else:
            self.log_test("Shopify OAuth install", False, str(response))
            return False

    def test_shopify_connection_status(self):
        """Test Shopify connection status endpoint"""
        success, response = self.make_request('GET', 'shopify/connection-status?shop=test-store')
        if success and 'online' in response:
            self.log_test("Shopify connection status", True)
            return True
        else:
            self.log_test("Shopify connection status", False, str(response))
            return False

    def test_enhanced_features_status(self):
        """Test enhanced features status endpoint"""
        success, response = self.make_request('GET', 'enhanced/status')
        if success and 'email' in response and 'ai' in response and 'export' in response:
            self.log_test("Enhanced features status", True)
            return True
        else:
            self.log_test("Enhanced features status", False, str(response))
            return False

    def test_ai_suggestions(self, tenant_id: str):
        """Test AI return reason suggestions"""
        headers = {'X-Tenant-Id': tenant_id}
        
        ai_request = {
            "product_name": "Wireless Bluetooth Headphones",
            "product_description": "Premium quality wireless headphones with noise cancellation",
            "order_date": "2025-01-15T10:00:00Z"
        }
        
        success, response = self.make_request('POST', 'enhanced/ai/suggest-reasons', 
                                            ai_request, headers)
        if success and 'suggestions' in response and isinstance(response['suggestions'], list):
            self.log_test("AI return reason suggestions", True)
            return True
        else:
            self.log_test("AI return reason suggestions", False, str(response))
            return False

    def test_ai_upsell_generation(self, tenant_id: str):
        """Test AI upsell message generation"""
        headers = {'X-Tenant-Id': tenant_id}
        
        upsell_request = {
            "return_reason": "defective",
            "product_name": "Wireless Headphones"
        }
        
        success, response = self.make_request('POST', 'enhanced/ai/generate-upsell', 
                                            upsell_request, headers)
        if success and 'upsell_message' in response:
            self.log_test("AI upsell generation", True)
            return True
        else:
            self.log_test("AI upsell generation", False, str(response))
            return False

    def test_ai_pattern_analysis(self, tenant_id: str):
        """Test AI return pattern analysis"""
        headers = {'X-Tenant-Id': tenant_id}
        
        success, response = self.make_request('GET', 'enhanced/ai/analyze-patterns?days=30', 
                                            headers=headers)
        if success and 'analysis' in response:
            self.log_test("AI pattern analysis", True)
            return True
        else:
            self.log_test("AI pattern analysis", False, str(response))
            return False

    def test_email_settings(self):
        """Test email service settings"""
        success, response = self.make_request('GET', 'enhanced/email/settings')
        if success and 'enabled' in response:
            self.log_test("Email settings", True)
            return True
        else:
            self.log_test("Email settings", False, str(response))
            return False

    def test_email_test_send(self, tenant_id: str):
        """Test sending test email"""
        headers = {'X-Tenant-Id': tenant_id}
        
        email_request = {
            "email": "test@example.com"
        }
        
        success, response = self.make_request('POST', 'enhanced/email/test', 
                                            email_request, headers)
        if success and 'success' in response:
            self.log_test("Email test send", True)
            return True
        else:
            self.log_test("Email test send", False, str(response))
            return False

    def test_export_csv(self, tenant_id: str):
        """Test CSV export functionality"""
        headers = {'X-Tenant-Id': tenant_id}
        
        success, response = self.make_request('GET', 'enhanced/export/returns/csv?days=30', 
                                            headers=headers, expected_status=200)
        if success:
            self.log_test("Export returns CSV", True)
            return True
        else:
            self.log_test("Export returns CSV", False, str(response))
            return False

    def test_export_pdf(self, tenant_id: str):
        """Test PDF export functionality"""
        headers = {'X-Tenant-Id': tenant_id}
        
        success, response = self.make_request('GET', 'enhanced/export/returns/pdf?days=30', 
                                            headers=headers, expected_status=200)
        if success:
            self.log_test("Export returns PDF", True)
            return True
        else:
            self.log_test("Export returns PDF", False, str(response))
            return False

    def test_export_excel(self, tenant_id: str):
        """Test Excel export functionality"""
        headers = {'X-Tenant-Id': tenant_id}
        
        success, response = self.make_request('GET', 'enhanced/export/analytics/excel?days=30', 
                                            headers=headers, expected_status=200)
        if success:
            self.log_test("Export analytics Excel", True)
            return True
        else:
            self.log_test("Export analytics Excel", False, str(response))
            return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Returns Management SaaS API Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_root_endpoint():
            print("❌ Cannot connect to API, stopping tests")
            return False
            
        # Tenant management
        tenant_id = self.test_create_tenant()
        if not tenant_id:
            print("❌ Cannot create tenant, stopping tests")
            return False
            
        self.test_get_tenants()
        self.test_tenant_isolation()
        self.test_missing_tenant_header()
        
        # Core functionality with the created tenant
        self.test_products_crud(tenant_id)
        self.test_orders_crud(tenant_id)
        self.test_return_rules(tenant_id)
        self.test_returns_workflow(tenant_id)
        self.test_analytics(tenant_id)
        self.test_shopify_webhook(tenant_id)
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed")
            return False

def main():
    """Main test runner"""
    tester = ReturnsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())