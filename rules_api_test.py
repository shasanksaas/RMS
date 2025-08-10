#!/usr/bin/env python3
"""
🔧 RULES API SAVE FUNCTIONALITY DEBUG TEST
Focus: Testing POST /api/rules and GET /api/rules endpoints with database connectivity
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Use the external backend URL from frontend/.env for real testing
BACKEND_URL = "https://511ecf3c-8cd3-47d8-acef-2c70bd69eb4a.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class RulesAPITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tenant_id = None
        self.created_rule_ids = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   Details: {details}")
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
                response_data = {"raw_response": response.text, "status_code": response.status_code}
                
            if not success:
                return False, f"Status {response.status_code}, Expected {expected_status}. Response: {response_data}"
                
            return True, response_data
            
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def setup_test_tenant(self):
        """Create or get a test tenant for rules testing"""
        # Try to get existing tenants first
        success, tenants = self.make_request('GET', 'tenants')
        if success and isinstance(tenants, list) and len(tenants) > 0:
            # Use the first available tenant
            self.tenant_id = tenants[0]['id']
            self.log_test("Setup - Use existing tenant", True, f"Using tenant: {self.tenant_id}")
            return True
        
        # Create a new tenant if none exist
        tenant_data = {
            "name": f"Rules Test Tenant {datetime.now().strftime('%H%M%S')}",
            "domain": f"rules-test-{datetime.now().strftime('%H%M%S')}.com",
            "shopify_store_url": "rules-test-store.myshopify.com"
        }
        
        success, data = self.make_request('POST', 'tenants', tenant_data)
        if success and 'id' in data:
            self.tenant_id = data['id']
            self.log_test("Setup - Create test tenant", True, f"Created tenant: {self.tenant_id}")
            return True
        else:
            self.log_test("Setup - Create test tenant", False, str(data))
            return False

    def test_rules_field_types_endpoint(self):
        """Test GET /api/rules/field-types/options endpoint (no tenant required)"""
        success, options = self.make_request('GET', 'rules/field-types/options')
        if success and 'field_types' in options and 'operators' in options and 'actions' in options:
            self.log_test("Rules API - Field types/operators options", True, 
                         f"Found {len(options['field_types'])} field types, {len(options['operators'])} operators, {len(options['actions'])} actions")
            
            # Verify comprehensive field types
            field_types = [ft['value'] for ft in options['field_types']]
            expected_fields = ['order_amount', 'return_reason', 'days_since_order', 'product_category', 'customer_location']
            missing_fields = set(expected_fields) - set(field_types)
            if not missing_fields:
                self.log_test("Rules API - Comprehensive field types", True)
            else:
                self.log_test("Rules API - Comprehensive field types", False, f"Missing fields: {missing_fields}")
            
            # Verify operators
            operators = [op['value'] for op in options['operators']]
            expected_ops = ['equals', 'greater_than', 'contains', 'in', 'regex']
            missing_ops = set(expected_ops) - set(operators)
            if not missing_ops:
                self.log_test("Rules API - Comprehensive operators", True)
            else:
                self.log_test("Rules API - Comprehensive operators", False, f"Missing operators: {missing_ops}")
                
            return True
        else:
            self.log_test("Rules API - Field types/operators options", False, str(options))
            return False

    def test_create_rule_with_sample_data(self):
        """Test POST /api/rules endpoint with the provided sample data"""
        if not self.tenant_id:
            self.log_test("Create Rule - No tenant available", False, "Tenant setup failed")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        # Use the exact sample data provided in the request
        rule_data = {
            "name": "Test Auto-Approval Rule",
            "description": "Test rule for debugging save functionality",
            "condition_groups": [
                {
                    "conditions": [
                        {
                            "field": "return_reason",
                            "operator": "equals",
                            "value": "defective"
                        }
                    ],
                    "logic_operator": "and"
                }
            ],
            "actions": [
                {
                    "action_type": "auto_approve_return",
                    "parameters": {}
                }
            ],
            "priority": 1,
            "is_active": True,
            "tags": ["test", "debugging"]
        }
        
        success, response = self.make_request('POST', 'rules', rule_data, headers)
        if success and response.get('success') and 'rule_id' in response:
            rule_id = response['rule_id']
            self.created_rule_ids.append(rule_id)
            self.log_test("Rules API - Create rule with sample data", True, 
                         f"Created rule ID: {rule_id}")
            
            # Verify the rule was created with correct data
            created_rule = response.get('rule', {})
            if (created_rule.get('name') == rule_data['name'] and 
                created_rule.get('description') == rule_data['description']):
                self.log_test("Rules API - Rule data integrity", True)
            else:
                self.log_test("Rules API - Rule data integrity", False, "Rule data doesn't match input")
                
            return rule_id
        else:
            self.log_test("Rules API - Create rule with sample data", False, str(response))
            return None

    def test_get_rules_endpoint(self):
        """Test GET /api/rules endpoint to verify saved rules appear"""
        if not self.tenant_id:
            self.log_test("Get Rules - No tenant available", False, "Tenant setup failed")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        success, response = self.make_request('GET', 'rules/', headers=headers)
        if success and 'items' in response and 'pagination' in response:
            rules_list = response['items']
            pagination = response['pagination']
            
            self.log_test("Rules API - Get rules list", True, 
                         f"Retrieved {len(rules_list)} rules, total count: {pagination.get('total_count', 0)}")
            
            # Check if our created rules appear in the list
            if self.created_rule_ids:
                found_rules = []
                for rule in rules_list:
                    if rule.get('id') in self.created_rule_ids:
                        found_rules.append(rule['id'])
                
                if found_rules:
                    self.log_test("Rules API - Created rules appear in list", True, 
                                 f"Found {len(found_rules)} of {len(self.created_rule_ids)} created rules")
                else:
                    self.log_test("Rules API - Created rules appear in list", False, 
                                 "None of the created rules found in list")
            
            # Verify pagination structure
            required_pagination_fields = ['current_page', 'total_pages', 'total_count', 'per_page']
            missing_fields = [field for field in required_pagination_fields if field not in pagination]
            if not missing_fields:
                self.log_test("Rules API - Pagination structure", True)
            else:
                self.log_test("Rules API - Pagination structure", False, f"Missing fields: {missing_fields}")
                
            return True
        else:
            self.log_test("Rules API - Get rules list", False, str(response))
            return False

    def test_get_specific_rule(self, rule_id: str):
        """Test GET /api/rules/{rule_id} endpoint"""
        if not self.tenant_id or not rule_id:
            self.log_test("Get Specific Rule - Missing data", False, "No tenant or rule ID")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        success, response = self.make_request('GET', f'rules/{rule_id}', headers=headers)
        if success and response.get('success') and 'rule' in response:
            rule = response['rule']
            self.log_test("Rules API - Get specific rule", True, 
                         f"Retrieved rule: {rule.get('name', 'Unknown')}")
            
            # Verify rule structure
            required_fields = ['id', 'name', 'description', 'condition_groups', 'actions', 'tenant_id']
            missing_fields = [field for field in required_fields if field not in rule]
            if not missing_fields:
                self.log_test("Rules API - Rule structure complete", True)
            else:
                self.log_test("Rules API - Rule structure complete", False, f"Missing fields: {missing_fields}")
                
            # Verify tenant isolation
            if rule.get('tenant_id') == self.tenant_id:
                self.log_test("Rules API - Tenant isolation", True)
            else:
                self.log_test("Rules API - Tenant isolation", False, 
                             f"Rule tenant_id {rule.get('tenant_id')} != expected {self.tenant_id}")
                
            return True
        else:
            self.log_test("Rules API - Get specific rule", False, str(response))
            return False

    def test_database_connectivity(self):
        """Test database connectivity by creating multiple rules and verifying persistence"""
        if not self.tenant_id:
            self.log_test("Database Connectivity - No tenant", False, "Tenant setup failed")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        # Create multiple rules to test database persistence
        test_rules = [
            {
                "name": "Database Test Rule 1",
                "description": "Testing database persistence - Rule 1",
                "condition_groups": [
                    {
                        "conditions": [
                            {
                                "field": "return_reason",
                                "operator": "equals",
                                "value": "damaged_in_shipping"
                            }
                        ],
                        "logic_operator": "and"
                    }
                ],
                "actions": [
                    {
                        "action_type": "auto_approve_return",
                        "parameters": {}
                    }
                ],
                "priority": 2,
                "is_active": True,
                "tags": ["database-test"]
            },
            {
                "name": "Database Test Rule 2",
                "description": "Testing database persistence - Rule 2",
                "condition_groups": [
                    {
                        "conditions": [
                            {
                                "field": "order_amount",
                                "operator": "greater_than",
                                "value": 100.0
                            }
                        ],
                        "logic_operator": "and"
                    }
                ],
                "actions": [
                    {
                        "action_type": "require_manual_review",
                        "parameters": {}
                    }
                ],
                "priority": 3,
                "is_active": True,
                "tags": ["database-test", "high-value"]
            }
        ]
        
        created_count = 0
        for i, rule_data in enumerate(test_rules):
            success, response = self.make_request('POST', 'rules/', rule_data, headers)
            if success and response.get('success') and 'rule_id' in response:
                rule_id = response['rule_id']
                self.created_rule_ids.append(rule_id)
                created_count += 1
                self.log_test(f"Database Test - Create rule {i+1}", True, f"Rule ID: {rule_id}")
            else:
                self.log_test(f"Database Test - Create rule {i+1}", False, str(response))
        
        if created_count == len(test_rules):
            self.log_test("Database Connectivity - Multiple rule creation", True, 
                         f"Successfully created {created_count} rules")
        else:
            self.log_test("Database Connectivity - Multiple rule creation", False, 
                         f"Only created {created_count} of {len(test_rules)} rules")
        
        # Verify all rules are retrievable
        success, response = self.make_request('GET', 'rules/', headers=headers)
        if success and 'items' in response:
            total_rules = response['pagination']['total_count']
            self.log_test("Database Connectivity - Rule persistence verification", True, 
                         f"Total rules in database: {total_rules}")
            return True
        else:
            self.log_test("Database Connectivity - Rule persistence verification", False, str(response))
            return False

    def test_rules_simulation(self):
        """Test rules simulation endpoint with created rules"""
        if not self.tenant_id or not self.created_rule_ids:
            self.log_test("Rules Simulation - No data", False, "No tenant or created rules")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        # Test simulation with data that should match our first rule (defective reason)
        simulation_data = {
            "order_data": {
                "total_amount": 75.50,
                "order_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "customer_email": "test@example.com",
                "items": [
                    {
                        "product_name": "Test Product",
                        "category": "Electronics",
                        "sku": "TEST-001",
                        "price": 75.50,
                        "quantity": 1
                    }
                ]
            },
            "return_data": {
                "reason": "defective",  # This should match our first rule
                "refund_amount": 75.50,
                "items_to_return": [
                    {
                        "product_name": "Test Product",
                        "sku": "TEST-001",
                        "price": 75.50,
                        "quantity": 1
                    }
                ]
            }
        }
        
        success, response = self.make_request('POST', 'rules/simulate', simulation_data, headers)
        if success and response.get('success') and 'result' in response:
            result = response['result']
            self.log_test("Rules API - Rules simulation", True, 
                         f"Evaluated {result.get('total_rules_evaluated', 0)} rules, "
                         f"matched {result.get('rules_matched', 0)} rules, "
                         f"final status: {result.get('final_status', 'unknown')}")
            
            # Check if auto-approval worked (should be approved due to 'defective' reason)
            if result.get('final_status') == 'approved':
                self.log_test("Rules API - Auto-approval logic", True, "Rule correctly auto-approved defective return")
            else:
                self.log_test("Rules API - Auto-approval logic", False, 
                             f"Expected 'approved', got '{result.get('final_status')}'")
                
            return True
        else:
            self.log_test("Rules API - Rules simulation", False, str(response))
            return False

    def test_error_handling(self):
        """Test error handling scenarios"""
        if not self.tenant_id:
            self.log_test("Error Handling - No tenant", False, "Tenant setup failed")
            return False
            
        headers = {'X-Tenant-Id': self.tenant_id}
        
        # Test 1: Create rule with duplicate name
        duplicate_rule_data = {
            "name": "Test Auto-Approval Rule",  # Same name as first rule
            "description": "Duplicate name test",
            "condition_groups": [
                {
                    "conditions": [
                        {
                            "field": "return_reason",
                            "operator": "equals",
                            "value": "wrong_size"
                        }
                    ],
                    "logic_operator": "and"
                }
            ],
            "actions": [
                {
                    "action_type": "auto_approve_return",
                    "parameters": {}
                }
            ],
            "priority": 1,
            "is_active": True
        }
        
        success, response = self.make_request('POST', 'rules/', duplicate_rule_data, headers, expected_status=400)
        if success:
            self.log_test("Error Handling - Duplicate rule name", True, "Correctly rejected duplicate name")
        else:
            self.log_test("Error Handling - Duplicate rule name", False, "Should reject duplicate names")
        
        # Test 2: Get non-existent rule
        success, response = self.make_request('GET', 'rules/non-existent-rule-id', headers=headers, expected_status=404)
        if success:
            self.log_test("Error Handling - Non-existent rule", True, "Correctly returned 404 for missing rule")
        else:
            self.log_test("Error Handling - Non-existent rule", False, "Should return 404 for missing rule")
        
        # Test 3: Create rule without tenant header
        success, response = self.make_request('POST', 'rules/', duplicate_rule_data, expected_status=400)
        if success:
            self.log_test("Error Handling - Missing tenant header", True, "Correctly rejected missing tenant")
        else:
            self.log_test("Error Handling - Missing tenant header", False, "Should require tenant header")
            
        return True

    def check_backend_logs(self):
        """Check for any backend errors during rule creation"""
        # This is a placeholder - in a real scenario, you'd check server logs
        # For now, we'll just verify the health endpoint
        success, health = self.make_request('GET', '../health')  # Go up one level from /api
        if success and health.get('status') == 'healthy':
            self.log_test("Backend Health - Server status", True, "Backend is healthy")
            
            if health.get('database') == 'connected':
                self.log_test("Backend Health - Database connection", True, "Database is connected")
            else:
                self.log_test("Backend Health - Database connection", False, "Database connection issue")
                
            return True
        else:
            self.log_test("Backend Health - Server status", False, str(health))
            return False

    def run_all_tests(self):
        """Run all Rules API tests"""
        print("🔧 RULES API SAVE FUNCTIONALITY DEBUG TEST")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_tenant():
            print("❌ Cannot proceed without tenant setup")
            return False
        
        # Test sequence
        print("\n📋 Testing Rules API Endpoints...")
        
        # 1. Test field types endpoint (no tenant required)
        self.test_rules_field_types_endpoint()
        
        # 2. Test rule creation with sample data
        rule_id = self.test_create_rule_with_sample_data()
        
        # 3. Test getting rules list
        self.test_get_rules_endpoint()
        
        # 4. Test getting specific rule
        if rule_id:
            self.test_get_specific_rule(rule_id)
        
        # 5. Test database connectivity with multiple rules
        self.test_database_connectivity()
        
        # 6. Test rules simulation
        self.test_rules_simulation()
        
        # 7. Test error handling
        self.test_error_handling()
        
        # 8. Check backend health
        self.check_backend_logs()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.created_rule_ids:
            print(f"Created Rules: {len(self.created_rule_ids)}")
            print(f"Rule IDs: {', '.join(self.created_rule_ids[:3])}{'...' if len(self.created_rule_ids) > 3 else ''}")
        
        print("=" * 60)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = RulesAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)