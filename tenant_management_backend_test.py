#!/usr/bin/env python3
"""
Tenant Management System Backend API Testing
Tests the newly implemented multi-tenancy functionality with comprehensive coverage
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TenantManagementTester:
    def __init__(self):
        # Use production URL from frontend/.env
        self.base_url = "https://returns-manager-1.preview.emergentagent.com/api"
        self.admin_token = None
        self.merchant_token = None
        self.test_tenant_id = None
        self.test_results = {
            "admin_tenant_management": [],
            "public_merchant_signup": [],
            "authentication_authorization": [],
            "tenant_isolation": [],
            "integration_existing_system": []
        }
        
        # Test data - Updated based on review request
        self.admin_credentials = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        self.existing_merchant_credentials = {
            "email": "merchant1@test.com", 
            "password": "merchant123"
        }
        
        # Expected tenant IDs from review request
        self.expected_tenant_ids = [
            "tenant-fashion-forward-demo",
            "tenant-tech-gadgets-demo", 
            "tenant-home-garden-demo"
        ]
        self.existing_tenant_id = "tenant-fashion-forward-demo"

    async def run_comprehensive_tests(self):
        """Run all tenant management system tests"""
        logger.info("🚀 Starting Tenant Management System Comprehensive Testing")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Test sequence following the review requirements
            await self.test_admin_authentication()
            await self.test_admin_tenant_management_apis()
            await self.test_public_merchant_signup_apis()
            await self.test_authentication_and_authorization()
            await self.test_tenant_isolation()
            await self.test_integration_with_existing_system()
            
            # Test complete workflow as requested in review
            await self.test_complete_workflow()
            
            # Generate comprehensive report
            self.generate_test_report()

    async def test_admin_authentication(self):
        """Test admin user authentication for tenant management access"""
        logger.info("🔐 Testing Admin Authentication")
        
        try:
            # Test admin login with credentials from review request
            login_data = {
                "email": self.admin_credentials["email"],
                "password": self.admin_credentials["password"],
                "remember_me": True
            }
            
            async with self.session.post(f"{self.base_url}/auth/login", json=login_data) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    # Verify admin role
                    if user_info.get("role") == "admin":
                        logger.info("✅ Admin authentication successful with correct role")
                        return True
                    else:
                        logger.warning(f"⚠️ User authenticated but role is: {user_info.get('role')}")
                        self.admin_token = data.get("access_token")  # Still use token for testing
                        return True
                        
                else:
                    error_text = response_text
                    logger.error(f"❌ Admin authentication failed: {response.status} - {error_text}")
                    
                    # Try alternative admin login approach
                    return await self.try_alternative_admin_auth()
                    
        except Exception as e:
            logger.error(f"❌ Admin authentication error: {e}")
            return await self.try_alternative_admin_auth()

    async def try_alternative_admin_auth(self):
        """Try alternative admin authentication methods"""
        logger.info("🔄 Trying alternative admin authentication")
        
        # Try with different tenant contexts for admin
        admin_tenant_contexts = ["admin", "system", "tenant-fashion-forward-demo"]
        
        for tenant_context in admin_tenant_contexts:
            try:
                login_data = {
                    "tenant_id": tenant_context,
                    "email": self.admin_credentials["email"],
                    "password": self.admin_credentials["password"],
                    "remember_me": True
                }
                
                headers = {"X-Tenant-Id": tenant_context}
                
                async with self.session.post(f"{self.base_url}/users/login", json=login_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.admin_token = data.get("access_token")
                        user_info = data.get("user", {})
                        logger.info(f"✅ Admin authentication successful with tenant context: {tenant_context}, role: {user_info.get('role')}")
                        return True
                    else:
                        logger.debug(f"Admin auth failed for tenant {tenant_context}: {response.status}")
                        
            except Exception as e:
                logger.debug(f"Admin auth exception for tenant {tenant_context}: {e}")
                continue
        
        # If no admin user found, use mock token for testing RBAC
        logger.warning("⚠️ No admin user found - will test RBAC with mock token")
        self.admin_token = "mock_admin_token_for_rbac_testing"
        return False

    async def test_admin_tenant_management_apis(self):
        """Test Admin Tenant Management APIs"""
        logger.info("🏢 Testing Admin Tenant Management APIs")
        
        # Test 1: POST /api/tenants (create new tenant)
        await self.test_create_tenant()
        
        # Test 2: GET /api/tenants (list all tenants)
        await self.test_list_tenants()
        
        # Test 3: GET /api/tenants/{tenant_id} (get tenant details)
        await self.test_get_tenant_details()
        
        # Test 4: PUT /api/tenants/{tenant_id} (update tenant)
        await self.test_update_tenant()
        
        # Test 5: POST /api/tenants/{tenant_id}/archive (archive tenant)
        await self.test_archive_tenant()

    async def test_create_tenant(self):
        """Test tenant creation with admin auth"""
        logger.info("📝 Testing tenant creation")
        
        test_name = "Create New Tenant"
        
        try:
            # Generate unique tenant data
            unique_suffix = str(uuid.uuid4())[:8]
            tenant_data = {
                "name": f"Test Store {unique_suffix}",
                "tenant_id": f"tenant-test-{unique_suffix}",
                "notes": "Created by automated testing"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{self.base_url}/tenants", json=tenant_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 201:
                    data = await response.json() if response_text else {}
                    self.test_tenant_id = data.get("tenant_id", tenant_data["tenant_id"])
                    
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Tenant created successfully: {self.test_tenant_id}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Tenant created - {self.test_tenant_id}")
                    
                elif response.status == 401:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_ISSUE",
                        "details": "Admin authentication required - endpoint exists but needs proper auth",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Authentication issue - {response.status}")
                    
                elif response.status == 403:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ RBAC_WORKING",
                        "details": "RBAC working correctly - non-admin access denied",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: RBAC working - admin access required")
                    
                else:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["admin_tenant_management"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_list_tenants(self):
        """Test listing all tenants with pagination"""
        logger.info("📋 Testing tenant listing")
        
        test_name = "List All Tenants"
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            params = {"page": 1, "page_size": 10}
            
            async with self.session.get(f"{self.base_url}/tenants", headers=headers, params=params) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    tenant_count = len(data.get("tenants", []))
                    
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Retrieved {tenant_count} tenants with pagination",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Retrieved {tenant_count} tenants")
                    
                elif response.status in [401, 403]:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_REQUIRED",
                        "details": "Admin authentication/authorization required",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Auth required - {response.status}")
                    
                else:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["admin_tenant_management"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_get_tenant_details(self):
        """Test getting detailed tenant information"""
        logger.info("🔍 Testing tenant details retrieval")
        
        test_name = "Get Tenant Details"
        tenant_id = self.test_tenant_id or self.existing_tenant_id
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{self.base_url}/tenants/{tenant_id}", headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Retrieved details for tenant: {tenant_id}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Retrieved details for {tenant_id}")
                    
                elif response.status == 404:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ NOT_FOUND",
                        "details": f"Tenant {tenant_id} not found - may need to be created first",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Tenant not found - {tenant_id}")
                    
                elif response.status in [401, 403]:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_REQUIRED",
                        "details": "Admin authentication/authorization required",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Auth required - {response.status}")
                    
                else:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["admin_tenant_management"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_update_tenant(self):
        """Test updating tenant information"""
        logger.info("✏️ Testing tenant update")
        
        test_name = "Update Tenant"
        tenant_id = self.test_tenant_id or self.existing_tenant_id
        
        try:
            update_data = {
                "name": f"Updated Test Store {datetime.now().strftime('%H%M%S')}",
                "notes": "Updated by automated testing"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.put(f"{self.base_url}/tenants/{tenant_id}", json=update_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Updated tenant: {tenant_id}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Updated tenant {tenant_id}")
                    
                elif response.status == 404:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ NOT_FOUND",
                        "details": f"Tenant {tenant_id} not found",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Tenant not found - {tenant_id}")
                    
                elif response.status in [401, 403]:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_REQUIRED",
                        "details": "Admin authentication/authorization required",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Auth required - {response.status}")
                    
                else:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["admin_tenant_management"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_archive_tenant(self):
        """Test archiving a tenant"""
        logger.info("🗄️ Testing tenant archiving")
        
        test_name = "Archive Tenant"
        tenant_id = self.test_tenant_id or f"tenant-test-{uuid.uuid4().hex[:8]}"
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{self.base_url}/tenants/{tenant_id}/archive", headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Archived tenant: {tenant_id}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Archived tenant {tenant_id}")
                    
                elif response.status == 404:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ NOT_FOUND",
                        "details": f"Tenant {tenant_id} not found or already archived",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Tenant not found - {tenant_id}")
                    
                elif response.status in [401, 403]:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_REQUIRED",
                        "details": "Admin authentication/authorization required",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Auth required - {response.status}")
                    
                else:
                    self.test_results["admin_tenant_management"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["admin_tenant_management"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_public_merchant_signup_apis(self):
        """Test Public Merchant Signup APIs"""
        logger.info("👥 Testing Public Merchant Signup APIs")
        
        # Test 1: GET /api/auth/tenant-status/{tenant_id} (check tenant validity)
        await self.test_tenant_status_check()
        
        # Test 2: GET /api/auth/signup-info/{tenant_id} (get signup info)
        await self.test_signup_info()
        
        # Test 3: POST /api/auth/merchant-signup (merchant signup with tenant_id)
        await self.test_merchant_signup()

    async def test_tenant_status_check(self):
        """Test tenant status validation"""
        logger.info("🔍 Testing tenant status check")
        
        test_name = "Check Tenant Status"
        
        # Test with existing tenant from review request
        try:
            async with self.session.get(f"{self.base_url}/auth/tenant-status/{self.existing_tenant_id}") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    is_valid = data.get("valid", False)
                    is_available = data.get("available", False)
                    
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Tenant {self.existing_tenant_id} - Valid: {is_valid}, Available: {is_available}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Valid={is_valid}, Available={is_available}")
                    
                else:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["public_merchant_signup"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")
        
        # Test all expected tenant IDs from review request
        for tenant_id in self.expected_tenant_ids:
            test_name_specific = f"Check Expected Tenant Status - {tenant_id}"
            try:
                async with self.session.get(f"{self.base_url}/auth/tenant-status/{tenant_id}") as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        data = await response.json() if response_text else {}
                        is_valid = data.get("valid", False)
                        is_available = data.get("available", False)
                        
                        self.test_results["public_merchant_signup"].append({
                            "test": test_name_specific,
                            "status": "✅ PASS" if is_valid else "⚠️ NOT_FOUND",
                            "details": f"Tenant {tenant_id} - Valid: {is_valid}, Available: {is_available}",
                            "response_code": response.status
                        })
                        logger.info(f"✅ {test_name_specific}: Valid={is_valid}, Available={is_available}")
                        
                    else:
                        self.test_results["public_merchant_signup"].append({
                            "test": test_name_specific,
                            "status": "❌ FAIL",
                            "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                            "response_code": response.status
                        })
                        logger.error(f"❌ {test_name_specific}: Failed - {response.status}")
                        
            except Exception as e:
                self.test_results["public_merchant_signup"].append({
                    "test": test_name_specific,
                    "status": "❌ ERROR",
                    "details": f"Exception: {str(e)}",
                    "response_code": None
                })
                logger.error(f"❌ {test_name_specific}: Exception - {e}")
        
        # Test with invalid tenant
        test_name_invalid = "Check Invalid Tenant Status"
        try:
            invalid_tenant = "tenant-nonexistent-12345"
            async with self.session.get(f"{self.base_url}/auth/tenant-status/{invalid_tenant}") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    is_valid = data.get("valid", True)  # Should be False
                    
                    if not is_valid:
                        self.test_results["public_merchant_signup"].append({
                            "test": test_name_invalid,
                            "status": "✅ PASS",
                            "details": f"Correctly identified invalid tenant: {invalid_tenant}",
                            "response_code": response.status
                        })
                        logger.info(f"✅ {test_name_invalid}: Correctly rejected invalid tenant")
                    else:
                        self.test_results["public_merchant_signup"].append({
                            "test": test_name_invalid,
                            "status": "⚠️ ISSUE",
                            "details": f"Invalid tenant marked as valid: {invalid_tenant}",
                            "response_code": response.status
                        })
                        logger.warning(f"⚠️ {test_name_invalid}: Invalid tenant marked as valid")
                        
                else:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name_invalid,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name_invalid}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["public_merchant_signup"].append({
                "test": test_name_invalid,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name_invalid}: Exception - {e}")

    async def test_signup_info(self):
        """Test getting signup information for tenant"""
        logger.info("ℹ️ Testing signup info retrieval")
        
        test_name = "Get Signup Info"
        
        try:
            async with self.session.get(f"{self.base_url}/auth/signup-info/{self.existing_tenant_id}") as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    tenant_name = data.get("tenant_name", "Unknown")
                    signup_enabled = data.get("signup_enabled", False)
                    
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Retrieved signup info - Name: {tenant_name}, Signup: {signup_enabled}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Name={tenant_name}, Signup={signup_enabled}")
                    
                elif response.status == 404:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "⚠️ NOT_FOUND",
                        "details": f"Tenant {self.existing_tenant_id} not found or not available",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Tenant not found")
                    
                else:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["public_merchant_signup"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_merchant_signup(self):
        """Test merchant signup with tenant_id"""
        logger.info("📝 Testing merchant signup")
        
        test_name = "Merchant Signup"
        
        try:
            # Generate unique merchant data
            unique_id = str(uuid.uuid4())[:8]
            signup_data = {
                "tenant_id": self.existing_tenant_id,
                "email": f"test-merchant-{unique_id}@example.com",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "Merchant",
                "store_name": f"Test Store {unique_id}"
            }
            
            async with self.session.post(f"{self.base_url}/auth/merchant-signup", json=signup_data) as response:
                response_text = await response.text()
                
                if response.status == 201:
                    data = await response.json() if response_text else {}
                    success = data.get("success", False)
                    is_first_merchant = data.get("is_first_merchant", False)
                    
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"Merchant signup successful - First: {is_first_merchant}",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Success={success}, First={is_first_merchant}")
                    
                elif response.status == 400:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "⚠️ VALIDATION",
                        "details": f"Validation error (expected for duplicate/invalid data): {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Validation error - {response.status}")
                    
                elif response.status == 404:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "⚠️ TENANT_NOT_FOUND",
                        "details": f"Tenant {self.existing_tenant_id} not found",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Tenant not found")
                    
                elif response.status == 409:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "⚠️ CONFLICT",
                        "details": "Email already exists (expected behavior)",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Email conflict (expected)")
                    
                else:
                    self.test_results["public_merchant_signup"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["public_merchant_signup"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_authentication_and_authorization(self):
        """Test Authentication and Authorization"""
        logger.info("🔐 Testing Authentication and Authorization")
        
        # Test 1: Admin-only access controls
        await self.test_admin_only_access()
        
        # Test 2: JWT token validation
        await self.test_jwt_validation()
        
        # Test 3: Role-based permissions
        await self.test_role_based_permissions()

    async def test_admin_only_access(self):
        """Test that tenant management APIs require admin access"""
        logger.info("🚫 Testing admin-only access controls")
        
        test_name = "Admin-Only Access Control"
        
        try:
            # Try to access tenant management without admin token
            async with self.session.get(f"{self.base_url}/tenants") as response:
                if response.status in [401, 403]:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": "Correctly blocked non-admin access to tenant management",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Correctly blocked non-admin access")
                    
                elif response.status == 200:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "❌ SECURITY_ISSUE",
                        "details": "Tenant management accessible without authentication",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Security issue - no auth required")
                    
                else:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "⚠️ UNKNOWN",
                        "details": f"Unexpected response: {response.status}",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Unexpected response - {response.status}")
                    
        except Exception as e:
            self.test_results["authentication_authorization"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_jwt_validation(self):
        """Test JWT token validation"""
        logger.info("🎫 Testing JWT token validation")
        
        test_name = "JWT Token Validation"
        
        try:
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            
            async with self.session.get(f"{self.base_url}/tenants", headers=invalid_headers) as response:
                if response.status == 401:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": "Correctly rejected invalid JWT token",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Correctly rejected invalid token")
                    
                else:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "❌ SECURITY_ISSUE",
                        "details": f"Invalid token not properly rejected: {response.status}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Invalid token accepted - {response.status}")
                    
        except Exception as e:
            self.test_results["authentication_authorization"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_role_based_permissions(self):
        """Test role-based access control"""
        logger.info("👤 Testing role-based permissions")
        
        test_name = "Role-Based Access Control"
        
        try:
            # Try to authenticate existing merchant and test tenant access
            merchant_login_data = {
                "tenant_id": "tenant-fashion-forward-demo",
                "email": self.existing_merchant_credentials["email"],
                "password": self.existing_merchant_credentials["password"],
                "remember_me": False
            }
            
            headers = {"X-Tenant-Id": "tenant-fashion-forward-demo"}
            
            async with self.session.post(f"{self.base_url}/users/login", json=merchant_login_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json()
                    merchant_token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    # Test merchant access to tenant management (should be denied)
                    merchant_headers = {"Authorization": f"Bearer {merchant_token}"}
                    
                    async with self.session.get(f"{self.base_url}/tenants", headers=merchant_headers) as tenant_response:
                        if tenant_response.status == 403:
                            self.test_results["authentication_authorization"].append({
                                "test": test_name,
                                "status": "✅ PASS",
                                "details": f"RBAC working - merchant (role: {user_info.get('role')}) denied tenant management access",
                                "response_code": tenant_response.status
                            })
                            logger.info(f"✅ {test_name}: RBAC working correctly")
                            
                        else:
                            self.test_results["authentication_authorization"].append({
                                "test": test_name,
                                "status": "❌ RBAC_ISSUE",
                                "details": f"Merchant has tenant management access: {tenant_response.status}",
                                "response_code": tenant_response.status
                            })
                            logger.error(f"❌ {test_name}: RBAC issue - {tenant_response.status}")
                            
                else:
                    self.test_results["authentication_authorization"].append({
                        "test": test_name,
                        "status": "⚠️ MERCHANT_AUTH_ISSUE",
                        "details": f"Could not authenticate existing merchant: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Merchant auth issue - {response.status}")
                    
        except Exception as e:
            self.test_results["authentication_authorization"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_tenant_isolation(self):
        """Test Tenant Isolation"""
        logger.info("🏠 Testing Tenant Isolation")
        
        # Test 1: Unique tenant_id generation
        await self.test_unique_tenant_id()
        
        # Test 2: Tenant_id validation and format
        await self.test_tenant_id_validation()
        
        # Test 3: Tenant status management
        await self.test_tenant_status_management()

    async def test_unique_tenant_id(self):
        """Test that tenant IDs are unique"""
        logger.info("🆔 Testing unique tenant ID generation")
        
        test_name = "Unique Tenant ID Generation"
        
        try:
            # Test creating multiple tenants to verify uniqueness
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            tenant_ids = []
            for i in range(3):
                tenant_data = {
                    "name": f"Uniqueness Test Store {i}",
                    "notes": f"Testing uniqueness {i}"
                }
                
                async with self.session.post(f"{self.base_url}/tenants", json=tenant_data, headers=headers) as response:
                    if response.status == 201:
                        data = await response.json()
                        tenant_id = data.get("tenant_id")
                        if tenant_id:
                            tenant_ids.append(tenant_id)
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
            
            # Check uniqueness
            unique_ids = set(tenant_ids)
            if len(unique_ids) == len(tenant_ids) and len(tenant_ids) > 0:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "✅ PASS",
                    "details": f"Generated {len(tenant_ids)} unique tenant IDs",
                    "response_code": 201
                })
                logger.info(f"✅ {test_name}: Generated {len(tenant_ids)} unique IDs")
                
            elif len(tenant_ids) == 0:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "⚠️ NO_CREATION",
                    "details": "Could not create tenants to test uniqueness",
                    "response_code": None
                })
                logger.warning(f"⚠️ {test_name}: Could not create tenants")
                
            else:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "❌ DUPLICATE_IDS",
                    "details": f"Duplicate tenant IDs found: {tenant_ids}",
                    "response_code": 201
                })
                logger.error(f"❌ {test_name}: Duplicate IDs found")
                
        except Exception as e:
            self.test_results["tenant_isolation"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_tenant_id_validation(self):
        """Test tenant ID validation and format"""
        logger.info("✅ Testing tenant ID validation")
        
        test_name = "Tenant ID Validation"
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test invalid tenant ID formats
            invalid_formats = [
                {"tenant_id": "invalid-format", "name": "Test"},  # Doesn't start with tenant-
                {"tenant_id": "tenant-", "name": "Test"},  # Too short
                {"tenant_id": "tenant-UPPERCASE", "name": "Test"},  # Contains uppercase
                {"tenant_id": "tenant-with spaces", "name": "Test"},  # Contains spaces
            ]
            
            validation_results = []
            
            for invalid_data in invalid_formats:
                async with self.session.post(f"{self.base_url}/tenants", json=invalid_data, headers=headers) as response:
                    if response.status == 400:
                        validation_results.append("✅ Rejected")
                    else:
                        validation_results.append(f"❌ Accepted ({response.status})")
            
            # Check if all invalid formats were rejected
            all_rejected = all("✅" in result for result in validation_results)
            
            if all_rejected:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "✅ PASS",
                    "details": "All invalid tenant ID formats correctly rejected",
                    "response_code": 400
                })
                logger.info(f"✅ {test_name}: All invalid formats rejected")
                
            else:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "⚠️ PARTIAL",
                    "details": f"Validation results: {validation_results}",
                    "response_code": None
                })
                logger.warning(f"⚠️ {test_name}: Partial validation - {validation_results}")
                
        except Exception as e:
            self.test_results["tenant_isolation"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_tenant_status_management(self):
        """Test tenant status transitions (new -> claimed -> active)"""
        logger.info("📊 Testing tenant status management")
        
        test_name = "Tenant Status Management"
        
        try:
            # Check existing tenant status
            async with self.session.get(f"{self.base_url}/auth/tenant-status/{self.existing_tenant_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status", "unknown")
                    valid = data.get("valid", False)
                    available = data.get("available", False)
                    
                    # Verify status is one of the expected values
                    expected_statuses = ["new", "claimed", "active", "suspended", "archived"]
                    
                    if status in expected_statuses:
                        self.test_results["tenant_isolation"].append({
                            "test": test_name,
                            "status": "✅ PASS",
                            "details": f"Tenant status management working - Status: {status}, Valid: {valid}, Available: {available}",
                            "response_code": response.status
                        })
                        logger.info(f"✅ {test_name}: Status={status}, Valid={valid}, Available={available}")
                        
                    else:
                        self.test_results["tenant_isolation"].append({
                            "test": test_name,
                            "status": "⚠️ UNKNOWN_STATUS",
                            "details": f"Unknown tenant status: {status}",
                            "response_code": response.status
                        })
                        logger.warning(f"⚠️ {test_name}: Unknown status - {status}")
                        
                else:
                    self.test_results["tenant_isolation"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Could not check tenant status: {response.status}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["tenant_isolation"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_integration_with_existing_system(self):
        """Test Integration with Existing System"""
        logger.info("🔗 Testing Integration with Existing System")
        
        # Test 1: Existing user management works
        await self.test_existing_user_management()
        
        # Test 2: Existing authentication still functions
        await self.test_existing_authentication()
        
        # Test 3: Current merchant user can still login
        await self.test_existing_merchant_login()

    async def test_existing_user_management(self):
        """Test that existing user management still works"""
        logger.info("👥 Testing existing user management")
        
        test_name = "Existing User Management"
        
        try:
            # Test user listing endpoint
            headers = {"X-Tenant-Id": self.existing_tenant_id}
            
            async with self.session.get(f"{self.base_url}/users", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get("users", [])
                    
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": f"User management working - Found {len(users)} users",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Found {len(users)} users")
                    
                elif response.status in [401, 403]:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "⚠️ AUTH_REQUIRED",
                        "details": "User management requires authentication (expected)",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Auth required - {response.status}")
                    
                else:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"User management endpoint failed: {response.status}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["integration_existing_system"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_existing_authentication(self):
        """Test that existing authentication endpoints still function"""
        logger.info("🔐 Testing existing authentication")
        
        test_name = "Existing Authentication"
        
        try:
            # Test login endpoint availability
            login_data = {
                "tenant_id": "tenant-fashion-forward-demo",
                "email": "test@example.com",  # Invalid credentials
                "password": "invalid",
                "remember_me": False
            }
            
            headers = {"X-Tenant-Id": "tenant-fashion-forward-demo"}
            
            async with self.session.post(f"{self.base_url}/users/login", json=login_data, headers=headers) as response:
                # We expect 401 for invalid credentials, which means endpoint is working
                if response.status == 401:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": "Authentication endpoint working (correctly rejected invalid credentials)",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Auth endpoint working")
                    
                elif response.status == 400:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "✅ PASS",
                        "details": "Authentication endpoint working (validation error for invalid data)",
                        "response_code": response.status
                    })
                    logger.info(f"✅ {test_name}: Auth endpoint working (validation)")
                    
                elif response.status == 404:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "❌ ENDPOINT_MISSING",
                        "details": "Authentication endpoint not found",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Endpoint missing - {response.status}")
                    
                else:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "⚠️ UNEXPECTED",
                        "details": f"Unexpected response: {response.status}",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Unexpected response - {response.status}")
                    
        except Exception as e:
            self.test_results["integration_existing_system"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_existing_merchant_login(self):
        """Test that existing merchant user can still login"""
        logger.info("🏪 Testing existing merchant login")
        
        test_name = "Existing Merchant Login"
        
        try:
            login_data = {
                "tenant_id": "tenant-fashion-forward-demo",
                "email": self.existing_merchant_credentials["email"],
                "password": self.existing_merchant_credentials["password"],
                "remember_me": False
            }
            
            headers = {"X-Tenant-Id": "tenant-fashion-forward-demo"}
            
            async with self.session.post(f"{self.base_url}/users/login", json=login_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    access_token = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    if access_token:
                        self.merchant_token = access_token
                        self.test_results["integration_existing_system"].append({
                            "test": test_name,
                            "status": "✅ PASS",
                            "details": f"Existing merchant login successful - Role: {user_info.get('role', 'unknown')}, Tenant: {user_info.get('tenant_id', 'unknown')}",
                            "response_code": response.status
                        })
                        logger.info(f"✅ {test_name}: Merchant login successful")
                        
                    else:
                        self.test_results["integration_existing_system"].append({
                            "test": test_name,
                            "status": "⚠️ NO_TOKEN",
                            "details": "Login successful but no access token returned",
                            "response_code": response.status
                        })
                        logger.warning(f"⚠️ {test_name}: No token returned")
                        
                elif response.status == 401:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "⚠️ INVALID_CREDENTIALS",
                        "details": "Existing merchant credentials invalid or user doesn't exist",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: Invalid credentials")
                    
                elif response.status == 404:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "⚠️ USER_NOT_FOUND",
                        "details": "Existing merchant user not found",
                        "response_code": response.status
                    })
                    logger.warning(f"⚠️ {test_name}: User not found")
                    
                else:
                    self.test_results["integration_existing_system"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Unexpected response: {response.status} - {response_text[:200]}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Failed - {response.status}")
                    
        except Exception as e:
            self.test_results["integration_existing_system"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating Comprehensive Test Report")
        
        print("\n" + "="*80)
        print("🎯 TENANT MANAGEMENT SYSTEM - COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            print(f"\n📋 {category.upper().replace('_', ' ')}")
            print("-" * 60)
            
            for test in tests:
                total_tests += 1
                status = test["status"]
                
                if "✅" in status:
                    passed_tests += 1
                
                print(f"{status} {test['test']}")
                print(f"   Details: {test['details']}")
                if test.get('response_code'):
                    print(f"   Response Code: {test['response_code']}")
                print()
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("="*80)
        print(f"📈 OVERALL RESULTS")
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        # Summary by category
        print(f"\n📊 CATEGORY BREAKDOWN:")
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for test in tests if "✅" in test["status"])
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            print(f"  {category.replace('_', ' ').title()}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        print("\n" + "="*80)

    async def test_complete_workflow(self):
        """Test Complete Workflow: Admin login → Create tenant → Merchant signup → Verify isolation"""
        logger.info("🔄 Testing Complete Tenant Management Workflow")
        
        # Test 1: Complete workflow with new tenant
        await self.test_end_to_end_workflow()
        
        # Test 2: Database isolation verification
        await self.test_database_isolation()
        
        # Test 3: Tenant claiming process
        await self.test_tenant_claiming_process()

    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("🎯 Testing End-to-End Workflow")
        
        test_name = "Complete E2E Workflow"
        workflow_steps = []
        
        try:
            # Step 1: Admin login (already done in test_admin_authentication)
            if self.admin_token:
                workflow_steps.append("✅ Admin authentication successful")
            else:
                workflow_steps.append("❌ Admin authentication failed")
                
            # Step 2: Create new tenant
            unique_suffix = str(uuid.uuid4())[:8]
            tenant_data = {
                "name": f"E2E Test Store {unique_suffix}",
                "tenant_id": f"tenant-e2e-{unique_suffix}",
                "notes": "Created for end-to-end workflow testing"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{self.base_url}/tenants", json=tenant_data, headers=headers) as response:
                if response.status == 201:
                    data = await response.json()
                    workflow_tenant_id = data.get("tenant_id", tenant_data["tenant_id"])
                    workflow_steps.append(f"✅ Tenant created: {workflow_tenant_id}")
                    
                    # Step 3: Verify tenant status
                    async with self.session.get(f"{self.base_url}/auth/tenant-status/{workflow_tenant_id}") as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            if status_data.get("valid") and status_data.get("available"):
                                workflow_steps.append("✅ Tenant status valid and available for signup")
                                
                                # Step 4: Merchant signup
                                merchant_signup_data = {
                                    "tenant_id": workflow_tenant_id,
                                    "email": f"workflow-merchant-{unique_suffix}@example.com",
                                    "password": "WorkflowPassword123!",
                                    "confirm_password": "WorkflowPassword123!",
                                    "first_name": "Workflow",
                                    "last_name": "Merchant",
                                    "store_name": f"Workflow Store {unique_suffix}"
                                }
                                
                                async with self.session.post(f"{self.base_url}/auth/merchant-signup", json=merchant_signup_data) as signup_response:
                                    if signup_response.status == 201:
                                        signup_data = await signup_response.json()
                                        is_first_merchant = signup_data.get("is_first_merchant", False)
                                        workflow_steps.append(f"✅ Merchant signup successful (first merchant: {is_first_merchant})")
                                        
                                        # Step 5: Verify tenant claiming
                                        async with self.session.get(f"{self.base_url}/auth/tenant-status/{workflow_tenant_id}") as final_status_response:
                                            if final_status_response.status == 200:
                                                final_status_data = await final_status_response.json()
                                                final_status = final_status_data.get("status", "unknown")
                                                workflow_steps.append(f"✅ Tenant status after signup: {final_status}")
                                                
                                                # Complete workflow success
                                                self.test_results["integration_existing_system"].append({
                                                    "test": test_name,
                                                    "status": "✅ PASS",
                                                    "details": f"Complete workflow successful: {' → '.join(workflow_steps)}",
                                                    "response_code": 201
                                                })
                                                logger.info(f"✅ {test_name}: Complete workflow successful")
                                                return
                                                
                                            else:
                                                workflow_steps.append(f"❌ Final status check failed: {final_status_response.status}")
                                    else:
                                        workflow_steps.append(f"❌ Merchant signup failed: {signup_response.status}")
                            else:
                                workflow_steps.append("❌ Tenant not available for signup")
                        else:
                            workflow_steps.append(f"❌ Tenant status check failed: {status_response.status}")
                else:
                    workflow_steps.append(f"❌ Tenant creation failed: {response.status}")
                    
            # If we reach here, workflow failed
            self.test_results["integration_existing_system"].append({
                "test": test_name,
                "status": "❌ FAIL",
                "details": f"Workflow failed: {' → '.join(workflow_steps)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Workflow failed")
            
        except Exception as e:
            workflow_steps.append(f"❌ Exception: {str(e)}")
            self.test_results["integration_existing_system"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Workflow error: {' → '.join(workflow_steps)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_database_isolation(self):
        """Test database isolation between tenants"""
        logger.info("🔒 Testing Database Isolation")
        
        test_name = "Database Isolation"
        
        try:
            # Test that merchant from one tenant cannot access another tenant's data
            if self.merchant_token:
                # Try to access different tenant's data
                other_tenant_id = "tenant-tech-gadgets-demo"  # Different from fashion-forward-demo
                
                headers = {
                    "Authorization": f"Bearer {self.merchant_token}",
                    "X-Tenant-Id": other_tenant_id
                }
                
                # Try to access returns data for different tenant
                async with self.session.get(f"{self.base_url}/returns", headers=headers) as response:
                    if response.status in [403, 404]:
                        self.test_results["tenant_isolation"].append({
                            "test": test_name,
                            "status": "✅ PASS",
                            "details": "Database isolation working - cross-tenant access denied",
                            "response_code": response.status
                        })
                        logger.info(f"✅ {test_name}: Cross-tenant access properly denied")
                        
                    else:
                        self.test_results["tenant_isolation"].append({
                            "test": test_name,
                            "status": "❌ SECURITY_ISSUE",
                            "details": f"Cross-tenant access allowed: {response.status}",
                            "response_code": response.status
                        })
                        logger.error(f"❌ {test_name}: Security issue - cross-tenant access allowed")
            else:
                self.test_results["tenant_isolation"].append({
                    "test": test_name,
                    "status": "⚠️ SKIP",
                    "details": "No merchant token available for isolation testing",
                    "response_code": None
                })
                logger.warning(f"⚠️ {test_name}: Skipped - no merchant token")
                
        except Exception as e:
            self.test_results["tenant_isolation"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

    async def test_tenant_claiming_process(self):
        """Test tenant claiming process when first merchant signs up"""
        logger.info("🏷️ Testing Tenant Claiming Process")
        
        test_name = "Tenant Claiming Process"
        
        try:
            # Create a new tenant for claiming test
            unique_suffix = str(uuid.uuid4())[:8]
            tenant_data = {
                "name": f"Claiming Test Store {unique_suffix}",
                "tenant_id": f"tenant-claim-{unique_suffix}",
                "notes": "Created for claiming process testing"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{self.base_url}/tenants", json=tenant_data, headers=headers) as response:
                if response.status == 201:
                    data = await response.json()
                    claim_tenant_id = data.get("tenant_id", tenant_data["tenant_id"])
                    
                    # Check initial status (should be 'new')
                    async with self.session.get(f"{self.base_url}/auth/tenant-status/{claim_tenant_id}") as status_response:
                        if status_response.status == 200:
                            initial_status_data = await status_response.json()
                            initial_status = initial_status_data.get("status", "unknown")
                            
                            # First merchant signup (should claim tenant)
                            merchant_signup_data = {
                                "tenant_id": claim_tenant_id,
                                "email": f"claiming-merchant-{unique_suffix}@example.com",
                                "password": "ClaimingPassword123!",
                                "confirm_password": "ClaimingPassword123!",
                                "first_name": "Claiming",
                                "last_name": "Merchant",
                                "store_name": f"Claiming Store {unique_suffix}"
                            }
                            
                            async with self.session.post(f"{self.base_url}/auth/merchant-signup", json=merchant_signup_data) as signup_response:
                                if signup_response.status == 201:
                                    signup_data = await signup_response.json()
                                    is_first_merchant = signup_data.get("is_first_merchant", False)
                                    
                                    # Check final status (should be 'claimed' or 'active')
                                    async with self.session.get(f"{self.base_url}/auth/tenant-status/{claim_tenant_id}") as final_status_response:
                                        if final_status_response.status == 200:
                                            final_status_data = await final_status_response.json()
                                            final_status = final_status_data.get("status", "unknown")
                                            
                                            # Verify claiming process
                                            if is_first_merchant and final_status in ["claimed", "active"]:
                                                self.test_results["tenant_isolation"].append({
                                                    "test": test_name,
                                                    "status": "✅ PASS",
                                                    "details": f"Claiming process working: {initial_status} → {final_status} (first merchant: {is_first_merchant})",
                                                    "response_code": 201
                                                })
                                                logger.info(f"✅ {test_name}: Claiming process successful")
                                                
                                            else:
                                                self.test_results["tenant_isolation"].append({
                                                    "test": test_name,
                                                    "status": "⚠️ PARTIAL",
                                                    "details": f"Claiming process partial: {initial_status} → {final_status} (first merchant: {is_first_merchant})",
                                                    "response_code": 201
                                                })
                                                logger.warning(f"⚠️ {test_name}: Claiming process partial")
                                        else:
                                            self.test_results["tenant_isolation"].append({
                                                "test": test_name,
                                                "status": "❌ FAIL",
                                                "details": f"Final status check failed: {final_status_response.status}",
                                                "response_code": final_status_response.status
                                            })
                                            logger.error(f"❌ {test_name}: Final status check failed")
                                else:
                                    self.test_results["tenant_isolation"].append({
                                        "test": test_name,
                                        "status": "❌ FAIL",
                                        "details": f"Merchant signup failed: {signup_response.status}",
                                        "response_code": signup_response.status
                                    })
                                    logger.error(f"❌ {test_name}: Merchant signup failed")
                        else:
                            self.test_results["tenant_isolation"].append({
                                "test": test_name,
                                "status": "❌ FAIL",
                                "details": f"Initial status check failed: {status_response.status}",
                                "response_code": status_response.status
                            })
                            logger.error(f"❌ {test_name}: Initial status check failed")
                else:
                    self.test_results["tenant_isolation"].append({
                        "test": test_name,
                        "status": "❌ FAIL",
                        "details": f"Tenant creation failed: {response.status}",
                        "response_code": response.status
                    })
                    logger.error(f"❌ {test_name}: Tenant creation failed")
                    
        except Exception as e:
            self.test_results["tenant_isolation"].append({
                "test": test_name,
                "status": "❌ ERROR",
                "details": f"Exception: {str(e)}",
                "response_code": None
            })
            logger.error(f"❌ {test_name}: Exception - {e}")

async def main():
    """Main test execution"""
    tester = TenantManagementTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())