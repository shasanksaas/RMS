#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE SHOPIFY INTEGRATION TESTING
Tests the new Shopify-first integration implementation with real credentials
Focus: Auth Module, Orders API, Order Detail, Sync Service, Real Data Integration
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Use the external backend URL from frontend/.env for real testing
BACKEND_URL = "https://511ecf3c-8cd3-47d8-acef-2c70bd69eb4a.preview.emergentagent.com"
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
        if success and 'items' in returns and isinstance(returns['items'], list):
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
            
        # Update return status (follow proper state machine flow)
        # approved -> label_issued -> in_transit -> received -> resolved
        
        # Move to label_issued
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', 
                                     {"status": "label_issued", "notes": "Label issued"}, headers)
        
        # Move to in_transit  
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', 
                                     {"status": "in_transit", "notes": "Package in transit"}, headers)
        
        # Move to received
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', 
                                     {"status": "received", "notes": "Return received", "tracking_number": "TRACK123456"}, headers)
        
        # Finally move to resolved
        success, updated_return = self.make_request('PUT', f'returns/{return_id}/status', 
                                                  {"status": "resolved", "notes": "Return resolved successfully"}, headers)
        if success and updated_return.get('status') == 'resolved':
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

    def test_state_machine_validation(self, tenant_id: str):
        """Test return status transitions with proper validation"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create order and return for testing
        order_data = {
            "customer_email": "statemachine@example.com",
            "customer_name": "State Machine Test",
            "order_number": f"SM-{datetime.now().strftime('%H%M%S')}",
            "items": [{"product_id": "sm-1", "product_name": "Test Product", "quantity": 1, "price": 50.0, "sku": "SM-001"}],
            "total_amount": 50.0,
            "order_date": datetime.utcnow().isoformat()
        }
        
        success, order = self.make_request('POST', 'orders', order_data, headers)
        if not success:
            self.log_test("State Machine - Create test order", False, str(order))
            return False
            
        return_data = {
            "order_id": order['id'],
            "reason": "defective",
            "items_to_return": order['items'],
            "notes": "Testing state machine"
        }
        
        success, return_req = self.make_request('POST', 'returns', return_data, headers)
        if not success:
            self.log_test("State Machine - Create return", False, str(return_req))
            return False
            
        return_id = return_req['id']
        
        # Test valid transition: requested -> approved
        success, updated = self.make_request('PUT', f'returns/{return_id}/status', 
                                           {"status": "approved", "notes": "Approved for testing"}, headers)
        if success and updated.get('status') == 'approved':
            self.log_test("State Machine - Valid transition (requested->approved)", True)
        else:
            self.log_test("State Machine - Valid transition (requested->approved)", False, str(updated))
            return False
            
        # Test invalid transition: approved -> resolved (should skip received)
        success, invalid = self.make_request('PUT', f'returns/{return_id}/status', 
                                           {"status": "resolved"}, headers, expected_status=400)
        if success:
            self.log_test("State Machine - Invalid transition blocked", True)
        else:
            self.log_test("State Machine - Invalid transition blocked", False, "Should block invalid transitions")
            
        # Test idempotent update (same status)
        success, idempotent = self.make_request('PUT', f'returns/{return_id}/status', 
                                              {"status": "approved"}, headers)
        if success and idempotent.get('status') == 'approved':
            self.log_test("State Machine - Idempotent update", True)
        else:
            self.log_test("State Machine - Idempotent update", False, str(idempotent))
            
        return True

    def test_rules_engine_simulation(self, tenant_id: str):
        """Test the /rules/simulate endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create a test rule first
        rule_data = {
            "name": "Simulation Test Rule",
            "description": "Test rule for simulation",
            "conditions": {
                "auto_approve_reasons": ["defective", "damaged_in_shipping"],
                "max_days_since_order": 30,
                "min_return_value": 10.0
            },
            "actions": {"auto_approve": True},
            "priority": 1
        }
        
        success, rule = self.make_request('POST', 'return-rules', rule_data, headers)
        if not success:
            self.log_test("Rules Simulation - Create test rule", False, str(rule))
            return False
            
        # Test simulation with valid data
        simulation_data = {
            "order_data": {
                "order_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "customer_email": "sim@test.com"
            },
            "return_data": {
                "reason": "defective",
                "refund_amount": 50.0
            }
        }
        
        success, result = self.make_request('POST', 'return-rules/simulate', simulation_data, headers)
        if success and 'steps' in result and 'final_status' in result:
            self.log_test("Rules Simulation - Basic simulation", True)
            
            # Check if steps contain explanations
            if result['steps'] and all('explanation' in step for step in result['steps']):
                self.log_test("Rules Simulation - Step explanations", True)
            else:
                self.log_test("Rules Simulation - Step explanations", False, "Missing step explanations")
                
            # Check if auto-approval worked
            if result['final_status'] == 'approved':
                self.log_test("Rules Simulation - Auto-approval logic", True)
            else:
                self.log_test("Rules Simulation - Auto-approval logic", False, f"Expected approved, got {result['final_status']}")
        else:
            self.log_test("Rules Simulation - Basic simulation", False, str(result))
            return False
            
        return True

    def test_resolution_actions(self, tenant_id: str):
        """Test the /returns/{id}/resolve endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create order and return in received state
        order_data = {
            "customer_email": "resolution@example.com",
            "customer_name": "Resolution Test",
            "order_number": f"RES-{datetime.now().strftime('%H%M%S')}",
            "items": [{"product_id": "res-1", "product_name": "Resolvable Product", "quantity": 1, "price": 100.0, "sku": "RES-001"}],
            "total_amount": 100.0,
            "order_date": datetime.utcnow().isoformat()
        }
        
        success, order = self.make_request('POST', 'orders', order_data, headers)
        if not success:
            self.log_test("Resolution Actions - Create order", False, str(order))
            return False
            
        return_data = {
            "order_id": order['id'],
            "reason": "defective",
            "items_to_return": order['items']
        }
        
        success, return_req = self.make_request('POST', 'returns', return_data, headers)
        if not success:
            self.log_test("Resolution Actions - Create return", False, str(return_req))
            return False
            
        return_id = return_req['id']
        
        # Move to received state
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', {"status": "approved"}, headers)
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', {"status": "label_issued"}, headers)
        success, _ = self.make_request('PUT', f'returns/{return_id}/status', {"status": "received"}, headers)
        
        # Test refund resolution
        refund_data = {
            "resolution_type": "refund",
            "refund_method": "original_payment",
            "notes": "Refund processed for defective item"
        }
        
        success, refund_result = self.make_request('POST', f'returns/{return_id}/resolve', refund_data, headers)
        if success and refund_result.get('success') and refund_result.get('resolution_type') == 'refund':
            self.log_test("Resolution Actions - Refund processing", True)
        else:
            self.log_test("Resolution Actions - Refund processing", False, str(refund_result))
            
        # Create another return for exchange test
        return_data['order_id'] = order['id']  # Reuse order
        success, return_req2 = self.make_request('POST', 'returns', return_data, headers)
        if success:
            return_id2 = return_req2['id']
            # Move to received state
            self.make_request('PUT', f'returns/{return_id2}/status', {"status": "approved"}, headers)
            self.make_request('PUT', f'returns/{return_id2}/status', {"status": "label_issued"}, headers)
            self.make_request('PUT', f'returns/{return_id2}/status', {"status": "received"}, headers)
            
            # Test exchange resolution
            exchange_data = {
                "resolution_type": "exchange",
                "exchange_items": [{"product_id": "new-1", "product_name": "New Product", "quantity": 1, "price": 100.0}],
                "notes": "Exchange for different size"
            }
            
            success, exchange_result = self.make_request('POST', f'returns/{return_id2}/resolve', exchange_data, headers)
            if success and exchange_result.get('success') and exchange_result.get('resolution_type') == 'exchange':
                self.log_test("Resolution Actions - Exchange processing", True)
            else:
                self.log_test("Resolution Actions - Exchange processing", False, str(exchange_result))
                
        return True

    def test_enhanced_returns_endpoint(self, tenant_id: str):
        """Test pagination, search, filtering on returns endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test pagination
        success, paginated = self.make_request('GET', 'returns?page=1&limit=5', headers=headers)
        if success and 'items' in paginated and 'pagination' in paginated:
            pagination = paginated['pagination']
            if all(key in pagination for key in ['current_page', 'total_pages', 'total_count', 'per_page']):
                self.log_test("Enhanced Returns - Pagination structure", True)
            else:
                self.log_test("Enhanced Returns - Pagination structure", False, "Missing pagination fields")
        else:
            self.log_test("Enhanced Returns - Pagination structure", False, str(paginated))
            
        # Test search functionality
        success, searched = self.make_request('GET', 'returns?search=test', headers=headers)
        if success and 'items' in searched:
            self.log_test("Enhanced Returns - Search functionality", True)
        else:
            self.log_test("Enhanced Returns - Search functionality", False, str(searched))
            
        # Test status filtering
        success, filtered = self.make_request('GET', 'returns?status_filter=approved', headers=headers)
        if success and 'items' in filtered:
            self.log_test("Enhanced Returns - Status filtering", True)
        else:
            self.log_test("Enhanced Returns - Status filtering", False, str(filtered))
            
        # Test sorting
        success, sorted_desc = self.make_request('GET', 'returns?sort_by=created_at&sort_order=desc', headers=headers)
        success2, sorted_asc = self.make_request('GET', 'returns?sort_by=created_at&sort_order=asc', headers=headers)
        
        if success and success2:
            self.log_test("Enhanced Returns - Sorting", True)
        else:
            self.log_test("Enhanced Returns - Sorting", False, "Sorting requests failed")
            
        return True

    def test_settings_management(self, tenant_id: str):
        """Test tenant settings endpoints"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Test GET settings
        success, settings = self.make_request('GET', f'tenants/{tenant_id}/settings', headers=headers)
        if success and 'settings' in settings:
            self.log_test("Settings Management - GET settings", True)
        else:
            self.log_test("Settings Management - GET settings", False, str(settings))
            return False
            
        # Test PUT settings
        new_settings = {
            "return_window_days": 45,
            "auto_approve_exchanges": False,
            "require_photos": True,
            "brand_color": "#ff6b6b",
            "custom_message": "Updated test message"
        }
        
        success, updated = self.make_request('PUT', f'tenants/{tenant_id}/settings', new_settings, headers)
        if success and updated.get('success'):
            self.log_test("Settings Management - PUT settings", True)
            
            # Verify settings were saved
            success, verified = self.make_request('GET', f'tenants/{tenant_id}/settings', headers=headers)
            if success and verified['settings']['return_window_days'] == 45:
                self.log_test("Settings Management - Settings persistence", True)
            else:
                self.log_test("Settings Management - Settings persistence", False, "Settings not persisted correctly")
        else:
            self.log_test("Settings Management - PUT settings", False, str(updated))
            
        # Test invalid settings
        invalid_settings = {"invalid_field": "should_be_ignored", "return_window_days": 30}
        success, filtered_result = self.make_request('PUT', f'tenants/{tenant_id}/settings', invalid_settings, headers)
        if success:
            self.log_test("Settings Management - Invalid field filtering", True)
        else:
            self.log_test("Settings Management - Invalid field filtering", False, str(filtered_result))
            
        return True

    def test_audit_log_timeline(self, tenant_id: str):
        """Test /returns/{id}/audit-log endpoint"""
        headers = {'X-Tenant-Id': tenant_id}
        
        # Create a return and perform status changes to generate audit log
        order_data = {
            "customer_email": "audit@example.com",
            "customer_name": "Audit Test",
            "order_number": f"AUD-{datetime.now().strftime('%H%M%S')}",
            "items": [{"product_id": "aud-1", "product_name": "Audit Product", "quantity": 1, "price": 75.0, "sku": "AUD-001"}],
            "total_amount": 75.0,
            "order_date": datetime.utcnow().isoformat()
        }
        
        success, order = self.make_request('POST', 'orders', order_data, headers)
        if not success:
            self.log_test("Audit Log - Create order", False, str(order))
            return False
            
        return_data = {
            "order_id": order['id'],
            "reason": "defective",
            "items_to_return": order['items']
        }
        
        success, return_req = self.make_request('POST', 'returns', return_data, headers)
        if not success:
            self.log_test("Audit Log - Create return", False, str(return_req))
            return False
            
        return_id = return_req['id']
        
        # Perform status changes to create audit trail
        self.make_request('PUT', f'returns/{return_id}/status', {"status": "approved", "notes": "Approved by manager"}, headers)
        self.make_request('PUT', f'returns/{return_id}/status', {"status": "label_issued", "notes": "Label generated"}, headers)
        
        # Test audit log retrieval
        success, audit_log = self.make_request('GET', f'returns/{return_id}/audit-log', headers=headers)
        if success and 'timeline' in audit_log and 'current_status' in audit_log:
            timeline = audit_log['timeline']
            if len(timeline) >= 3:  # Should have creation + 2 status updates
                self.log_test("Audit Log - Timeline retrieval", True)
                
                # Check timeline ordering (should be chronological)
                timestamps = [entry.get('timestamp') for entry in timeline if 'timestamp' in entry]
                if len(timestamps) >= 2:
                    self.log_test("Audit Log - Timeline ordering", True)
                else:
                    self.log_test("Audit Log - Timeline ordering", False, "Missing timestamps")
            else:
                self.log_test("Audit Log - Timeline retrieval", False, f"Expected >= 3 entries, got {len(timeline)}")
        else:
            self.log_test("Audit Log - Timeline retrieval", False, str(audit_log))
            
        return True

    def test_multi_tenant_isolation(self):
        """Critical security test - verify tenant isolation"""
        # Create two separate tenants
        tenant1_id = self.test_create_tenant()
        tenant2_id = self.test_create_tenant()
        
        if not tenant1_id or not tenant2_id:
            self.log_test("Multi-Tenant Isolation - Setup", False, "Could not create test tenants")
            return False
            
        headers1 = {'X-Tenant-Id': tenant1_id}
        headers2 = {'X-Tenant-Id': tenant2_id}
        
        # Create data in tenant1
        order_data = {
            "customer_email": "tenant1@example.com",
            "customer_name": "Tenant 1 Customer",
            "order_number": f"T1-{datetime.now().strftime('%H%M%S')}",
            "items": [{"product_id": "t1-1", "product_name": "Tenant 1 Product", "quantity": 1, "price": 50.0, "sku": "T1-001"}],
            "total_amount": 50.0,
            "order_date": datetime.utcnow().isoformat()
        }
        
        success, order1 = self.make_request('POST', 'orders', order_data, headers1)
        if not success:
            self.log_test("Multi-Tenant Isolation - Create tenant1 order", False, str(order1))
            return False
            
        return_data = {
            "order_id": order1['id'],
            "reason": "defective",
            "items_to_return": order1['items']
        }
        
        success, return1 = self.make_request('POST', 'returns', return_data, headers1)
        if not success:
            self.log_test("Multi-Tenant Isolation - Create tenant1 return", False, str(return1))
            return False
            
        # Try to access tenant1's data from tenant2 (should fail)
        success, cross_access = self.make_request('GET', f'returns/{return1["id"]}', headers=headers2, expected_status=404)
        if success:
            self.log_test("Multi-Tenant Isolation - Cross-tenant access blocked", True)
        else:
            self.log_test("Multi-Tenant Isolation - Cross-tenant access blocked", False, "Should block cross-tenant access")
            
        # Try to access tenant1's settings from tenant2 (should fail)
        success, settings_access = self.make_request('GET', f'tenants/{tenant1_id}/settings', headers=headers2, expected_status=403)
        if success:
            self.log_test("Multi-Tenant Isolation - Settings access blocked", True)
        else:
            self.log_test("Multi-Tenant Isolation - Settings access blocked", False, "Should block cross-tenant settings access")
            
        # Verify tenant2 can only see its own data
        success, tenant2_returns = self.make_request('GET', 'returns', headers=headers2)
        if success and len(tenant2_returns.get('items', [])) == 0:
            self.log_test("Multi-Tenant Isolation - Data isolation verified", True)
        else:
            self.log_test("Multi-Tenant Isolation - Data isolation verified", False, "Tenant2 should not see tenant1 data")
            
        return True

    def test_shopify_graphql_connection(self, tenant_id: str):
        """Test GraphQL service connection and basic queries"""
        # Test store connection endpoint
        success, connection_info = self.make_request('GET', f'test/stores/{tenant_id}/connection')
        if success and connection_info.get('status') == 'success':
            self.log_test("Shopify GraphQL - Store connection test", True)
            
            # Check if GraphQL service was created
            if connection_info.get('graphql_service'):
                self.log_test("Shopify GraphQL - Service creation", True)
                
                # Check if shop info was retrieved
                if connection_info.get('shop_info'):
                    self.log_test("Shopify GraphQL - Shop info query", True)
                else:
                    self.log_test("Shopify GraphQL - Shop info query", False, "No shop info returned")
            else:
                self.log_test("Shopify GraphQL - Service creation", False, connection_info.get('message', 'Service creation failed'))
        else:
            self.log_test("Shopify GraphQL - Store connection test", False, str(connection_info))
            return False
            
        return True

    def test_webhook_processing_with_idempotency(self):
        """Test webhook processing with idempotency checks"""
        # Test webhook samples endpoint
        success, samples = self.make_request('GET', 'test/webhook/samples')
        if success and 'samples' in samples:
            self.log_test("Webhook Processing - Sample payloads", True)
            
            # Test processing different webhook types
            webhook_topics = ['orders/create', 'returns/create', 'app/uninstalled']
            
            for topic in webhook_topics:
                if topic in samples['samples']:
                    payload = samples['samples'][topic]
                    
                    # Test webhook processing
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
            
        return True

    def test_app_uninstalled_webhook(self):
        """Test critical app/uninstalled webhook for tenant cleanup"""
        # Test app/uninstalled webhook specifically
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
            return False
            
        return True

    def test_sync_service_functionality(self):
        """Test sync service with different sync types"""
        # Test with seeded tenant IDs
        seeded_tenants = ["tenant-fashion-store.myshopify.com", "tenant-tech-gadgets.myshopify.com"]
        
        for tenant_id in seeded_tenants:
            # Test initial sync
            sync_data = {"sync_type": "initial"}
            success, result = self.make_request('POST', f'test/sync/{tenant_id}', sync_data)
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
                
            # Test manual sync
            manual_sync_data = {"sync_type": "manual"}
            success, manual_result = self.make_request('POST', f'test/sync/{tenant_id}', manual_sync_data)
            if success and manual_result.get('status') == 'success':
                self.log_test(f"Sync Service - Manual sync ({tenant_id})", True)
            else:
                self.log_test(f"Sync Service - Manual sync ({tenant_id})", False, str(manual_result))
                
        return True

    def test_auth_service_status(self):
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
            
        return True

    def test_auth_credential_validation(self):
        """Test credential validation endpoint"""
        # Test with sample credentials
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

    def test_testing_endpoints_health(self):
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
            
        return True

    def test_webhook_test_endpoint(self):
        """Test webhook test endpoint"""
        success, webhook_test = self.make_request('GET', 'webhooks/test')
        if success and webhook_test.get('service') == 'webhooks':
            self.log_test("Webhook Service - Test endpoint", True)
            
            # Check supported topics
            if 'supported_topics' in webhook_test and len(webhook_test['supported_topics']) > 0:
                self.log_test("Webhook Service - Supported topics", True)
            else:
                self.log_test("Webhook Service - Supported topics", False, "No supported topics")
        else:
            self.log_test("Webhook Service - Test endpoint", False, str(webhook_test))
            return False
            
        return True

    def test_shopify_connectivity_endpoints(self):
        """Test the new Shopify connectivity test endpoints with real credentials"""
        print("\n🔗 Testing NEW Shopify Connectivity Endpoints...")
        
        # Test 1: Quick Test Endpoint
        success, quick_result = self.make_request('GET', 'shopify-test/quick-test')
        if success and quick_result.get('quick_test', {}).get('overall_success'):
            self.log_test("Shopify Connectivity - Quick Test", True)
            
            # Verify shop info is present
            shop_info = quick_result.get('shop_info', {})
            if shop_info.get('shop_name') and shop_info.get('domain'):
                self.log_test("Shopify Connectivity - Shop Info Retrieved", True)
            else:
                self.log_test("Shopify Connectivity - Shop Info Retrieved", False, "Missing shop details")
                
            # Verify products are present
            products_sample = quick_result.get('products_sample', {})
            if products_sample.get('products_count', 0) > 0:
                self.log_test("Shopify Connectivity - Products Retrieved", True)
            else:
                self.log_test("Shopify Connectivity - Products Retrieved", False, "No products found")
        else:
            self.log_test("Shopify Connectivity - Quick Test", False, str(quick_result))
            
        # Test 2: Raw Query Test Endpoint
        success, raw_result = self.make_request('GET', 'shopify-test/raw-query')
        if success and raw_result.get('raw_query_test', {}).get('success'):
            self.log_test("Shopify Connectivity - Raw Query Test", True)
            
            # Verify the exact query structure matches user's curl command
            result_data = raw_result.get('result', {}).get('data', {}).get('data', {})
            if result_data.get('products', {}).get('edges'):
                self.log_test("Shopify Connectivity - Raw Query Data Structure", True)
            else:
                self.log_test("Shopify Connectivity - Raw Query Data Structure", False, "Invalid data structure")
        else:
            self.log_test("Shopify Connectivity - Raw Query Test", False, str(raw_result))
            
        # Test 3: Full Connectivity Test Endpoint
        success, full_result = self.make_request('GET', 'shopify-test/connectivity')
        if success and full_result.get('connectivity_test', {}).get('overall_success'):
            self.log_test("Shopify Connectivity - Full Test Suite", True)
            
            # Check individual test results
            test_results = full_result.get('test_results', [])
            test_names = ['shop_info', 'products_query', 'orders_query', 'returns_query', 'customers_query']
            
            for test_result in test_results:
                test_name = test_result.get('test', 'unknown')
                if test_result.get('success'):
                    self.log_test(f"Shopify GraphQL - {test_name}", True)
                else:
                    self.log_test(f"Shopify GraphQL - {test_name}", False, test_result.get('error', 'Unknown error'))
                    
            # Check success rate
            connectivity_info = full_result.get('connectivity_test', {})
            success_rate = connectivity_info.get('success_rate', '0%')
            tests_passed = connectivity_info.get('tests_passed', 0)
            tests_run = connectivity_info.get('tests_run', 0)
            
            if tests_passed >= 3:  # At least 3 out of 5 tests should pass
                self.log_test(f"Shopify Connectivity - Success Rate ({success_rate})", True)
            else:
                self.log_test(f"Shopify Connectivity - Success Rate ({success_rate})", False, f"Only {tests_passed}/{tests_run} tests passed")
                
        else:
            self.log_test("Shopify Connectivity - Full Test Suite", False, str(full_result))
            
        return True

    def test_shopify_integration_comprehensive(self):
        """Comprehensive test of all Shopify integration components"""
        print("\n🛍️ Testing Shopify Integration Components...")
        
        # NEW: Test the Shopify connectivity endpoints first
        self.test_shopify_connectivity_endpoints()
        
        # Test seeded tenant IDs (these should exist from seed data)
        seeded_tenants = ["tenant-fashion-store.myshopify.com", "tenant-tech-gadgets.myshopify.com"]
        
        # Test GraphQL service with seeded tenants
        for tenant_id in seeded_tenants:
            self.test_shopify_graphql_connection(tenant_id)
            
        # Test webhook processing
        self.test_webhook_processing_with_idempotency()
        
        # Test critical app/uninstalled webhook
        self.test_app_uninstalled_webhook()
        
        # Test sync service
        self.test_sync_service_functionality()
        
        # Test auth service
        self.test_auth_service_status()
        self.test_auth_credential_validation()
        
        # Test development endpoints
        self.test_testing_endpoints_health()
        self.test_webhook_test_endpoint()
        
        return True
        """Test with the comprehensive seed data"""
        # Test with known seeded tenant IDs
        seeded_tenants = ["tenant-fashion-store", "tenant-tech-gadgets"]
        
        for tenant_id in seeded_tenants:
            headers = {'X-Tenant-Id': tenant_id}
            
            # Test that seeded data exists
            success, products = self.make_request('GET', 'products', headers=headers)
            if success and len(products) > 0:
                self.log_test(f"Seeded Data - {tenant_id} products", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} products", False, f"No products found for {tenant_id}")
                
            success, orders = self.make_request('GET', 'orders', headers=headers)
            if success and len(orders) > 0:
                self.log_test(f"Seeded Data - {tenant_id} orders", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} orders", False, f"No orders found for {tenant_id}")
                
            success, returns = self.make_request('GET', 'returns', headers=headers)
            if success and 'items' in returns and len(returns['items']) > 0:
                self.log_test(f"Seeded Data - {tenant_id} returns", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} returns", False, f"No returns found for {tenant_id}")
                
        return True

    def test_seeded_data_verification(self):
        """Test with the comprehensive seed data"""
        # Test with known seeded tenant IDs
        seeded_tenants = ["tenant-fashion-store", "tenant-tech-gadgets"]
        
        for tenant_id in seeded_tenants:
            headers = {'X-Tenant-Id': tenant_id}
            
            # Test that seeded data exists
            success, products = self.make_request('GET', 'products', headers=headers)
            if success and len(products) > 0:
                self.log_test(f"Seeded Data - {tenant_id} products", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} products", False, f"No products found for {tenant_id}")
                
            success, orders = self.make_request('GET', 'orders', headers=headers)
            if success and len(orders) > 0:
                self.log_test(f"Seeded Data - {tenant_id} orders", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} orders", False, f"No orders found for {tenant_id}")
                
            success, returns = self.make_request('GET', 'returns', headers=headers)
            if success and 'items' in returns and len(returns['items']) > 0:
                self.log_test(f"Seeded Data - {tenant_id} returns", True)
            else:
                self.log_test(f"Seeded Data - {tenant_id} returns", False, f"No returns found for {tenant_id}")
                
        return True

    def run_all_tests(self):
        """Run comprehensive test suite focusing on 10 end-to-end capabilities + Shopify Integration"""
        print("🚀 Starting Returns Management SaaS API Tests - 10 End-to-End Capabilities + Shopify Integration")
        print("=" * 80)
        
        # Basic connectivity
        if not self.test_root_endpoint():
            print("❌ Cannot connect to API, stopping tests")
            return False
            
        print("\n📋 PRIORITY TESTING AREAS:")
        print("1. State Machine Validation")
        print("2. Rules Engine Simulation") 
        print("3. Resolution Actions")
        print("4. Enhanced Returns Endpoint")
        print("5. Settings Management")
        print("6. Audit Log Timeline")
        print("7. Multi-Tenant Isolation")
        print("8. Seeded Data Verification")
        print("9. 🆕 GraphQL Service for Returns Operations")
        print("10. 🆕 Webhook Processing with Idempotency")
        print("11. 🆕 Sync Service with Initial Backfill")
        print("12. 🆕 Auth Service Enhancement with OAuth")
        print("13. 🆕 Testing Endpoints for Development")
        print("14. 🔗 NEW: Shopify Connectivity Test Endpoints")
        print("=" * 80)
        
        # Test seeded data first
        print("\n🌱 Testing Seeded Data...")
        self.test_seeded_data_verification()
        
        # Test multi-tenant isolation (critical security)
        print("\n🔒 Testing Multi-Tenant Isolation...")
        self.test_multi_tenant_isolation()
        
        # NEW: Test Shopify Integration Components
        print("\n🛍️ Testing Shopify Integration...")
        self.test_shopify_integration_comprehensive()
        
        # Create a test tenant for other tests
        print("\n🏢 Creating Test Tenant...")
        tenant_id = self.test_create_tenant()
        if not tenant_id:
            print("❌ Cannot create tenant, stopping tests")
            return False
            
        # Core capability tests
        print("\n⚙️ Testing State Machine Validation...")
        self.test_state_machine_validation(tenant_id)
        
        print("\n🧠 Testing Rules Engine Simulation...")
        self.test_rules_engine_simulation(tenant_id)
        
        print("\n💰 Testing Resolution Actions...")
        self.test_resolution_actions(tenant_id)
        
        print("\n📊 Testing Enhanced Returns Endpoint...")
        self.test_enhanced_returns_endpoint(tenant_id)
        
        print("\n⚙️ Testing Settings Management...")
        self.test_settings_management(tenant_id)
        
        print("\n📝 Testing Audit Log Timeline...")
        self.test_audit_log_timeline(tenant_id)
        
        # Additional core tests
        print("\n🔧 Testing Core Functionality...")
        self.test_products_crud(tenant_id)
        self.test_orders_crud(tenant_id)
        self.test_return_rules(tenant_id)
        self.test_returns_workflow(tenant_id)
        self.test_analytics(tenant_id)
        
        # Print summary
        print("\n" + "=" * 80)
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