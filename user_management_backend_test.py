#!/usr/bin/env python3
"""
User Management System Backend Testing
Comprehensive testing of user registration, authentication, profile management, and admin operations
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import base64

# Configuration
BACKEND_URL = "https://multi-tenant-rms.preview.emergentagent.com/api"
TEST_TENANT_ID = "tenant-rms34"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TEST_TENANT_ID
}

class UserManagementTestSuite:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_users = {}  # Store created test users
        self.admin_token = None
        self.merchant_token = None
        self.customer_token = None
        
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
            request_headers = {**TEST_HEADERS, **(headers or {})}
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status < 400, response_data, response.status
                    
        except Exception as e:
            return False, {"error": str(e)}, 500

    async def test_backend_health(self):
        """Test backend health and user endpoints availability"""
        print("\n🏥 Testing Backend Health and User Endpoints...")
        
        # Test 1: Backend health check
        success, health_data, status = await self.make_request("GET", "/health", headers={})
        if success:
            self.log_test("Backend Health: API health check", True, "Backend is healthy and accessible")
        else:
            self.log_test("Backend Health: API health check", False, f"Backend not accessible: {status}")
            return False
        
        # Test 2: User endpoints availability
        endpoints_to_test = [
            "/users/register",
            "/users/login", 
            "/users/login/google",
            "/users/me",
            "/users"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Test with invalid data to check if endpoint exists
                success, response, status = await self.make_request("POST", endpoint, {"test": "data"})
                if status == 404:
                    self.log_test(f"Endpoint Availability: {endpoint}", False, "Endpoint not found")
                elif status in [400, 401, 403, 422, 500]:
                    self.log_test(f"Endpoint Availability: {endpoint}", True, f"Endpoint exists (status: {status})")
                else:
                    self.log_test(f"Endpoint Availability: {endpoint}", True, f"Endpoint available (status: {status})")
            except Exception as e:
                self.log_test(f"Endpoint Availability: {endpoint}", False, f"Error: {str(e)}")
        
        return True

    async def test_user_registration(self):
        """Test user registration with different roles and validation"""
        print("\n👤 Testing User Registration...")
        
        # Test 1: Register customer with email/password
        customer_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": f"customer.test.{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "role": "customer",
            "auth_provider": "email",
            "first_name": "John",
            "last_name": "Customer",
            "is_active": True
        }
        
        success, response, status = await self.make_request("POST", "/users/register", customer_data)
        if success and response.get("user_id"):
            self.test_users["customer"] = {
                "user_id": response["user_id"],
                "email": customer_data["email"],
                "password": customer_data["password"],
                "role": "customer"
            }
            self.log_test("User Registration: Customer with email/password", True, 
                         f"Created customer user {response['user_id']}")
        else:
            self.log_test("User Registration: Customer with email/password", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Register merchant with email/password
        merchant_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": f"merchant.test.{uuid.uuid4().hex[:8]}@example.com",
            "password": "MerchantPass456!",
            "confirm_password": "MerchantPass456!",
            "role": "merchant",
            "auth_provider": "email",
            "first_name": "Jane",
            "last_name": "Merchant",
            "is_active": True
        }
        
        success, response, status = await self.make_request("POST", "/users/register", merchant_data)
        if success and response.get("user_id"):
            self.test_users["merchant"] = {
                "user_id": response["user_id"],
                "email": merchant_data["email"],
                "password": merchant_data["password"],
                "role": "merchant"
            }
            self.log_test("User Registration: Merchant with email/password", True, 
                         f"Created merchant user {response['user_id']}")
        else:
            self.log_test("User Registration: Merchant with email/password", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 3: Register admin with email/password
        admin_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": f"admin.test.{uuid.uuid4().hex[:8]}@example.com",
            "password": "AdminPassword789!",
            "confirm_password": "AdminPassword789!",
            "role": "admin",
            "auth_provider": "email",
            "first_name": "Admin",
            "last_name": "User",
            "is_active": True
        }
        
        success, response, status = await self.make_request("POST", "/users/register", admin_data)
        if success and response.get("user_id"):
            self.test_users["admin"] = {
                "user_id": response["user_id"],
                "email": admin_data["email"],
                "password": admin_data["password"],
                "role": "admin"
            }
            self.log_test("User Registration: Admin with email/password", True, 
                         f"Created admin user {response['user_id']}")
        else:
            self.log_test("User Registration: Admin with email/password", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 4: Duplicate email prevention
        duplicate_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": customer_data["email"],  # Same email as customer
            "password": "DifferentPassword123!",
            "confirm_password": "DifferentPassword123!",
            "role": "merchant",
            "auth_provider": "email",
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        success, response, status = await self.make_request("POST", "/users/register", duplicate_data)
        if not success and status == 409:
            self.log_test("User Registration: Duplicate email prevention", True, 
                         "Correctly rejected duplicate email")
        else:
            self.log_test("User Registration: Duplicate email prevention", False, 
                         "Should have rejected duplicate email")
        
        # Test 5: Password validation
        weak_password_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": f"weak.test.{uuid.uuid4().hex[:8]}@example.com",
            "password": "123",  # Too weak
            "confirm_password": "123",
            "role": "customer",
            "auth_provider": "email",
            "first_name": "Weak",
            "last_name": "Password"
        }
        
        success, response, status = await self.make_request("POST", "/users/register", weak_password_data)
        if not success and status in [400, 422]:
            self.log_test("User Registration: Password strength validation", True, 
                         "Correctly rejected weak password")
        else:
            self.log_test("User Registration: Password strength validation", False, 
                         "Should have rejected weak password")
        
        # Test 6: Required fields validation
        incomplete_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": f"incomplete.test.{uuid.uuid4().hex[:8]}@example.com",
            # Missing password and other required fields
            "role": "customer"
        }
        
        success, response, status = await self.make_request("POST", "/users/register", incomplete_data)
        if not success and status in [400, 422]:
            self.log_test("User Registration: Required fields validation", True, 
                         "Correctly rejected incomplete data")
        else:
            self.log_test("User Registration: Required fields validation", False, 
                         "Should have rejected incomplete data")

    async def test_user_authentication(self):
        """Test user authentication with email/password and Google OAuth simulation"""
        print("\n🔐 Testing User Authentication...")
        
        # Test 1: Email/password login for customer
        if "customer" in self.test_users:
            login_data = {
                "tenant_id": TEST_TENANT_ID,
                "email": self.test_users["customer"]["email"],
                "password": self.test_users["customer"]["password"],
                "remember_me": False
            }
            
            success, response, status = await self.make_request("POST", "/users/login", login_data)
            if success and response.get("access_token"):
                self.customer_token = response["access_token"]
                self.log_test("User Authentication: Customer email/password login", True, 
                             f"Successfully logged in customer, token received")
            else:
                self.log_test("User Authentication: Customer email/password login", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 2: Email/password login for merchant
        if "merchant" in self.test_users:
            login_data = {
                "tenant_id": TEST_TENANT_ID,
                "email": self.test_users["merchant"]["email"],
                "password": self.test_users["merchant"]["password"],
                "remember_me": True  # Test remember me functionality
            }
            
            success, response, status = await self.make_request("POST", "/users/login", login_data)
            if success and response.get("access_token"):
                self.merchant_token = response["access_token"]
                # Check if refresh token is provided for remember_me
                has_refresh = response.get("refresh_token") is not None
                self.log_test("User Authentication: Merchant email/password login with remember_me", True, 
                             f"Successfully logged in merchant, refresh token: {has_refresh}")
            else:
                self.log_test("User Authentication: Merchant email/password login with remember_me", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 3: Email/password login for admin
        if "admin" in self.test_users:
            login_data = {
                "tenant_id": TEST_TENANT_ID,
                "email": self.test_users["admin"]["email"],
                "password": self.test_users["admin"]["password"],
                "remember_me": False
            }
            
            success, response, status = await self.make_request("POST", "/users/login", login_data)
            if success and response.get("access_token"):
                self.admin_token = response["access_token"]
                self.log_test("User Authentication: Admin email/password login", True, 
                             f"Successfully logged in admin, token received")
            else:
                self.log_test("User Authentication: Admin email/password login", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 4: Invalid credentials handling
        invalid_login_data = {
            "tenant_id": TEST_TENANT_ID,
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
            "remember_me": False
        }
        
        success, response, status = await self.make_request("POST", "/users/login", invalid_login_data)
        if not success and status == 401:
            self.log_test("User Authentication: Invalid credentials handling", True, 
                         "Correctly rejected invalid credentials")
        else:
            self.log_test("User Authentication: Invalid credentials handling", False, 
                         "Should have rejected invalid credentials")
        
        # Test 5: Google OAuth endpoint availability (simulation)
        google_oauth_data = {
            "tenant_id": TEST_TENANT_ID,
            "auth_code": "mock_google_auth_code_for_testing",
            "role": "customer"
        }
        
        success, response, status = await self.make_request("POST", "/users/login/google", google_oauth_data)
        # We expect this to fail with 400 (bad auth code) but endpoint should exist
        if status in [400, 401] and not (status == 404):
            self.log_test("User Authentication: Google OAuth endpoint availability", True, 
                         "Google OAuth endpoint exists and handles requests")
        elif status == 404:
            self.log_test("User Authentication: Google OAuth endpoint availability", False, 
                         "Google OAuth endpoint not found")
        else:
            self.log_test("User Authentication: Google OAuth endpoint availability", True, 
                         f"Google OAuth endpoint available (status: {status})")
        
        # Test 6: Account lockout mechanism simulation
        if "customer" in self.test_users:
            # Try multiple failed logins
            failed_attempts = 0
            for i in range(6):  # Try 6 times to trigger lockout (max is usually 5)
                wrong_login_data = {
                    "tenant_id": TEST_TENANT_ID,
                    "email": self.test_users["customer"]["email"],
                    "password": "WrongPassword123!",
                    "remember_me": False
                }
                
                success, response, status = await self.make_request("POST", "/users/login", wrong_login_data)
                if not success:
                    failed_attempts += 1
                    if status == 423:  # Account locked
                        self.log_test("User Authentication: Account lockout mechanism", True, 
                                     f"Account locked after {failed_attempts} failed attempts")
                        break
            
            if failed_attempts >= 5 and status != 423:
                self.log_test("User Authentication: Account lockout mechanism", False, 
                             "Account should be locked after multiple failed attempts")

    async def test_user_profile_management(self):
        """Test user profile retrieval and updates"""
        print("\n👤 Testing User Profile Management...")
        
        # Test 1: Get current user profile (customer)
        if self.customer_token:
            auth_headers = {"Authorization": f"Bearer {self.customer_token}"}
            success, response, status = await self.make_request("GET", "/users/me", headers=auth_headers)
            
            if success and response.get("user_id"):
                self.log_test("User Profile: Get current user profile (customer)", True, 
                             f"Retrieved profile for user {response['user_id']}")
                
                # Validate response structure
                required_fields = ["user_id", "email", "role", "tenant_id", "created_at"]
                if all(field in response for field in required_fields):
                    self.log_test("User Profile: Profile response structure", True, 
                                 "All required fields present in profile response")
                else:
                    missing_fields = [field for field in required_fields if field not in response]
                    self.log_test("User Profile: Profile response structure", False, 
                                 f"Missing fields: {missing_fields}")
            else:
                self.log_test("User Profile: Get current user profile (customer)", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 2: Update user profile
        if self.customer_token:
            auth_headers = {"Authorization": f"Bearer {self.customer_token}"}
            update_data = {
                "first_name": "UpdatedJohn",
                "last_name": "UpdatedCustomer",
                "metadata": {"updated_by_test": True}
            }
            
            success, response, status = await self.make_request("PUT", "/users/me", update_data, auth_headers)
            if success and response.get("first_name") == "UpdatedJohn":
                self.log_test("User Profile: Update user profile", True, 
                             "Successfully updated user profile")
            else:
                self.log_test("User Profile: Update user profile", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 3: Password change functionality
        if self.customer_token and "customer" in self.test_users:
            auth_headers = {"Authorization": f"Bearer {self.customer_token}"}
            password_change_data = {
                "current_password": self.test_users["customer"]["password"],
                "new_password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
            
            success, response, status = await self.make_request("POST", "/users/me/change-password", 
                                                               password_change_data, auth_headers)
            if success:
                self.log_test("User Profile: Password change functionality", True, 
                             "Successfully changed password")
                # Update stored password for future tests
                self.test_users["customer"]["password"] = "NewSecurePassword123!"
            else:
                self.log_test("User Profile: Password change functionality", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 4: Session management and token validation
        if self.merchant_token:
            auth_headers = {"Authorization": f"Bearer {self.merchant_token}"}
            success, response, status = await self.make_request("GET", "/users/me", headers=auth_headers)
            
            if success:
                self.log_test("User Profile: Token validation and session management", True, 
                             "Token is valid and session is active")
            else:
                self.log_test("User Profile: Token validation and session management", False, 
                             f"Token validation failed: {status}")
        
        # Test 5: Logout functionality
        if self.customer_token:
            auth_headers = {"Authorization": f"Bearer {self.customer_token}"}
            success, response, status = await self.make_request("POST", "/users/logout", headers=auth_headers)
            
            if success:
                self.log_test("User Profile: Logout functionality", True, 
                             "Successfully logged out user")
                
                # Test that token is now invalid
                success, response, status = await self.make_request("GET", "/users/me", headers=auth_headers)
                if not success and status == 401:
                    self.log_test("User Profile: Token invalidation after logout", True, 
                                 "Token correctly invalidated after logout")
                else:
                    self.log_test("User Profile: Token invalidation after logout", False, 
                                 "Token should be invalid after logout")
            else:
                self.log_test("User Profile: Logout functionality", False, 
                             f"Status: {status}, Response: {response}")

    async def test_admin_user_management(self):
        """Test admin-only user management endpoints"""
        print("\n👨‍💼 Testing Admin User Management...")
        
        if not self.admin_token:
            self.log_test("Admin User Management: No admin token available", False, 
                         "Cannot test admin endpoints without admin authentication")
            return
        
        auth_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Get users list with pagination
        success, response, status = await self.make_request("GET", "/users?page=1&page_size=10", 
                                                           headers=auth_headers)
        if success and "users" in response:
            self.log_test("Admin User Management: Get users list with pagination", True, 
                         f"Retrieved {len(response['users'])} users")
            
            # Validate pagination structure
            pagination_fields = ["total_count", "page", "page_size", "total_pages", "has_next", "has_prev"]
            if all(field in response for field in pagination_fields):
                self.log_test("Admin User Management: Pagination structure", True, 
                             "All pagination fields present")
            else:
                self.log_test("Admin User Management: Pagination structure", False, 
                             "Missing pagination fields")
        else:
            self.log_test("Admin User Management: Get users list with pagination", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 2: Filter users by role
        success, response, status = await self.make_request("GET", "/users?role=customer", 
                                                           headers=auth_headers)
        if success and "users" in response:
            # Check if all returned users have customer role
            all_customers = all(user.get("role") == "customer" for user in response["users"])
            if all_customers:
                self.log_test("Admin User Management: Filter users by role", True, 
                             f"Successfully filtered {len(response['users'])} customer users")
            else:
                self.log_test("Admin User Management: Filter users by role", False, 
                             "Role filtering not working correctly")
        else:
            self.log_test("Admin User Management: Filter users by role", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test 3: Get specific user by ID
        if "customer" in self.test_users:
            customer_id = self.test_users["customer"]["user_id"]
            success, response, status = await self.make_request("GET", f"/users/{customer_id}", 
                                                               headers=auth_headers)
            if success and response.get("user_id") == customer_id:
                self.log_test("Admin User Management: Get user by ID", True, 
                             f"Successfully retrieved user {customer_id}")
            else:
                self.log_test("Admin User Management: Get user by ID", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 4: Update user by ID (admin operation)
        if "merchant" in self.test_users:
            merchant_id = self.test_users["merchant"]["user_id"]
            update_data = {
                "first_name": "AdminUpdatedMerchant",
                "is_active": True,
                "metadata": {"updated_by_admin": True}
            }
            
            success, response, status = await self.make_request("PUT", f"/users/{merchant_id}", 
                                                               update_data, auth_headers)
            if success and response.get("first_name") == "AdminUpdatedMerchant":
                self.log_test("Admin User Management: Update user by ID", True, 
                             f"Successfully updated user {merchant_id}")
            else:
                self.log_test("Admin User Management: Update user by ID", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test 5: Role-based access control (non-admin should be denied)
        if self.merchant_token:
            merchant_headers = {"Authorization": f"Bearer {self.merchant_token}"}
            success, response, status = await self.make_request("GET", "/users", 
                                                               headers=merchant_headers)
            if not success and status == 403:
                self.log_test("Admin User Management: Role-based access control", True, 
                             "Non-admin correctly denied access to admin endpoints")
            else:
                self.log_test("Admin User Management: Role-based access control", False, 
                             "Non-admin should be denied access to admin endpoints")
        
        # Test 6: User deletion (soft delete)
        if "customer" in self.test_users:
            customer_id = self.test_users["customer"]["user_id"]
            success, response, status = await self.make_request("DELETE", f"/users/{customer_id}", 
                                                               headers=auth_headers)
            if success:
                self.log_test("Admin User Management: User deletion (soft delete)", True, 
                             f"Successfully deleted user {customer_id}")
                
                # Verify user is marked as inactive
                success, user_response, status = await self.make_request("GET", f"/users/{customer_id}", 
                                                                        headers=auth_headers)
                if success and user_response.get("is_active") == False:
                    self.log_test("Admin User Management: Soft delete verification", True, 
                                 "User correctly marked as inactive")
                else:
                    self.log_test("Admin User Management: Soft delete verification", False, 
                                 "User should be marked as inactive after deletion")
            else:
                self.log_test("Admin User Management: User deletion (soft delete)", False, 
                             f"Status: {status}, Response: {response}")

    async def test_database_integration(self):
        """Test database integration and data persistence"""
        print("\n🗄️ Testing Database Integration...")
        
        # Test 1: Verify users collection exists and has proper indexes
        # We can't directly test MongoDB, but we can test data persistence through API
        if "merchant" in self.test_users and self.admin_token:
            auth_headers = {"Authorization": f"Bearer {self.admin_token}"}
            merchant_id = self.test_users["merchant"]["user_id"]
            
            # Get user data
            success, response, status = await self.make_request("GET", f"/users/{merchant_id}", 
                                                               headers=auth_headers)
            if success:
                self.log_test("Database Integration: Data persistence and retrieval", True, 
                             "User data successfully persisted and retrieved")
                
                # Check required fields are present
                required_fields = ["user_id", "tenant_id", "email", "role", "created_at", "updated_at"]
                if all(field in response for field in required_fields):
                    self.log_test("Database Integration: Required fields persistence", True, 
                                 "All required fields properly stored")
                else:
                    missing_fields = [field for field in required_fields if field not in response]
                    self.log_test("Database Integration: Required fields persistence", False, 
                                 f"Missing fields: {missing_fields}")
            else:
                self.log_test("Database Integration: Data persistence and retrieval", False, 
                             f"Failed to retrieve user data: {status}")
        
        # Test 2: Test tenant isolation
        wrong_tenant_headers = {**TEST_HEADERS, "X-Tenant-Id": "wrong-tenant-id"}
        if self.admin_token:
            auth_headers = {**wrong_tenant_headers, "Authorization": f"Bearer {self.admin_token}"}
            success, response, status = await self.make_request("GET", "/users", headers=auth_headers)
            
            if not success and status in [400, 403, 404]:
                self.log_test("Database Integration: Tenant isolation", True, 
                             "Correctly isolated data by tenant")
            else:
                self.log_test("Database Integration: Tenant isolation", False, 
                             "Tenant isolation not working properly")
        
        # Test 3: Test sessions collection functionality
        if "merchant" in self.test_users:
            # Login to create a session
            login_data = {
                "tenant_id": TEST_TENANT_ID,
                "email": self.test_users["merchant"]["email"],
                "password": self.test_users["merchant"]["password"],
                "remember_me": False
            }
            
            success, response, status = await self.make_request("POST", "/users/login", login_data)
            if success and response.get("access_token"):
                self.log_test("Database Integration: Sessions collection functionality", True, 
                             "Session successfully created and token issued")
                
                # Test token validation (which requires session lookup)
                auth_headers = {"Authorization": f"Bearer {response['access_token']}"}
                success, profile_response, status = await self.make_request("GET", "/users/me", 
                                                                           headers=auth_headers)
                if success:
                    self.log_test("Database Integration: Session validation", True, 
                                 "Session validation working correctly")
                else:
                    self.log_test("Database Integration: Session validation", False, 
                                 "Session validation failed")
            else:
                self.log_test("Database Integration: Sessions collection functionality", False, 
                             "Failed to create session")

    async def test_authentication_middleware(self):
        """Test JWT token creation, validation, and middleware"""
        print("\n🔐 Testing Authentication Middleware...")
        
        # Test 1: JWT token creation and structure
        if "merchant" in self.test_users:
            login_data = {
                "tenant_id": TEST_TENANT_ID,
                "email": self.test_users["merchant"]["email"],
                "password": self.test_users["merchant"]["password"],
                "remember_me": False
            }
            
            success, response, status = await self.make_request("POST", "/users/login", login_data)
            if success and response.get("access_token"):
                token = response["access_token"]
                
                # Basic JWT structure check (should have 3 parts separated by dots)
                token_parts = token.split('.')
                if len(token_parts) == 3:
                    self.log_test("Authentication Middleware: JWT token structure", True, 
                                 "JWT token has correct structure (3 parts)")
                    
                    # Test token validation by using it
                    auth_headers = {"Authorization": f"Bearer {token}"}
                    success, profile_response, status = await self.make_request("GET", "/users/me", 
                                                                               headers=auth_headers)
                    if success:
                        self.log_test("Authentication Middleware: JWT token validation", True, 
                                     "JWT token validation working correctly")
                        
                        # Check if token contains expected user data
                        if (profile_response.get("email") == self.test_users["merchant"]["email"] and
                            profile_response.get("tenant_id") == TEST_TENANT_ID):
                            self.log_test("Authentication Middleware: Token payload validation", True, 
                                         "Token contains correct user and tenant information")
                        else:
                            self.log_test("Authentication Middleware: Token payload validation", False, 
                                         "Token payload doesn't match expected user data")
                    else:
                        self.log_test("Authentication Middleware: JWT token validation", False, 
                                     "JWT token validation failed")
                else:
                    self.log_test("Authentication Middleware: JWT token structure", False, 
                                 "JWT token doesn't have correct structure")
            else:
                self.log_test("Authentication Middleware: JWT token creation", False, 
                             "Failed to create JWT token")
        
        # Test 2: Tenant header validation
        if self.merchant_token:
            # Test with missing tenant header
            headers_no_tenant = {"Authorization": f"Bearer {self.merchant_token}"}
            success, response, status = await self.make_request("GET", "/users/me", headers=headers_no_tenant)
            
            if not success and status in [400, 403]:
                self.log_test("Authentication Middleware: Tenant header validation", True, 
                             "Correctly requires tenant header")
            else:
                self.log_test("Authentication Middleware: Tenant header validation", False, 
                             "Should require tenant header")
        
        # Test 3: Protected endpoint access control
        # Test accessing protected endpoint without token
        success, response, status = await self.make_request("GET", "/users/me")
        if not success and status == 401:
            self.log_test("Authentication Middleware: Protected endpoint access control", True, 
                         "Correctly denies access without authentication")
        else:
            self.log_test("Authentication Middleware: Protected endpoint access control", False, 
                         "Should deny access without authentication")
        
        # Test 4: Invalid token handling
        invalid_headers = {"Authorization": "Bearer invalid.jwt.token"}
        success, response, status = await self.make_request("GET", "/users/me", headers=invalid_headers)
        if not success and status == 401:
            self.log_test("Authentication Middleware: Invalid token handling", True, 
                         "Correctly rejects invalid tokens")
        else:
            self.log_test("Authentication Middleware: Invalid token handling", False, 
                         "Should reject invalid tokens")

    async def run_all_tests(self):
        """Run all user management tests"""
        print("🚀 Starting User Management System Backend Testing")
        print("=" * 70)
        
        # Test sequence
        if not await self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return
        
        await self.test_user_registration()
        await self.test_user_authentication()
        await self.test_user_profile_management()
        await self.test_admin_user_management()
        await self.test_database_integration()
        await self.test_authentication_middleware()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 USER MANAGEMENT SYSTEM TESTING SUMMARY")
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
        
        # Analyze results by category
        categories = {
            "Backend Health": [r for r in self.test_results if "Backend Health:" in r["test"] or "Endpoint Availability:" in r["test"]],
            "User Registration": [r for r in self.test_results if "User Registration:" in r["test"]],
            "User Authentication": [r for r in self.test_results if "User Authentication:" in r["test"]],
            "User Profile": [r for r in self.test_results if "User Profile:" in r["test"]],
            "Admin User Management": [r for r in self.test_results if "Admin User Management:" in r["test"]],
            "Database Integration": [r for r in self.test_results if "Database Integration:" in r["test"]],
            "Authentication Middleware": [r for r in self.test_results if "Authentication Middleware:" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")
        
        print(f"\n🔑 TEST USERS CREATED:")
        for role, user_data in self.test_users.items():
            print(f"   • {role.title()}: {user_data['email']} (ID: {user_data['user_id']})")

async def main():
    """Main test execution"""
    async with UserManagementTestSuite() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())