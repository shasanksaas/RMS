"""
Enhanced Tenant Service - Production Multi-Tenancy Management
Handles tenant creation, management, strict isolation, and integration status
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel
import secrets
import string
import uuid
import re

from ..models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantStatus, 
    TenantListResponse, TenantMerchantSignup,
    TenantIntegrationStatus, TenantConnection, IntegrationStatus
)
from ..models.user import UserCreate, UserRole, AuthProvider
from .auth_service import auth_service

logger = logging.getLogger(__name__)

class TenantServiceEnhanced:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        if db is not None:
            self.tenants_collection = db.tenants
            self.users_collection = db.users
            self.integrations_collection = db.integrations_shopify
        else:
            self.tenants_collection = None
            self.users_collection = None
            self.integrations_collection = None
        
    async def initialize(self):
        """Initialize indexes for optimal performance and security"""
        if self.db is None:
            raise ValueError("Database connection required for initialization")
        
        # Set collections if not already set
        if self.tenants_collection is None:
            self.tenants_collection = self.db.tenants
            self.users_collection = self.db.users
            self.integrations_collection = self.db.integrations_shopify
        
        try:
            # Simple tenant index - only if no existing data
            existing_tenants = await self.tenants_collection.count_documents({})
            if existing_tenants == 0:
                tenant_indexes = [
                    IndexModel([("tenant_id", 1)], unique=True),
                ]
                await self.tenants_collection.create_indexes(tenant_indexes)
            
            logger.info("Enhanced tenant service indexes created successfully")
        except Exception as e:
            logger.warning(f"Tenant service indexes warning (non-fatal): {e}")
            # Don't fail startup for index issues

    def _generate_tenant_id(self) -> str:
        """Generate a unique, human-friendly tenant ID"""
        # Generate random suffix for uniqueness
        suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return f"tenant-{suffix}"
    
    async def _ensure_tenant_id_unique(self, tenant_id: str) -> str:
        """Ensure tenant ID is unique, generate new one if needed"""
        max_attempts = 10
        current_id = tenant_id
        
        for attempt in range(max_attempts):
            existing = await self.tenants_collection.find_one({"tenant_id": current_id})
            if not existing:
                return current_id
            
            # Generate new ID if collision
            current_id = self._generate_tenant_id()
        
        raise ValueError("Unable to generate unique tenant ID after multiple attempts")

    async def create_tenant(self, tenant_data: TenantCreate, created_by_admin_id: str) -> Tenant:
        """Create a new tenant with strict validation"""
        try:
            # Generate or validate tenant ID
            if tenant_data.tenant_id:
                tenant_id = await self._ensure_tenant_id_unique(tenant_data.tenant_id)
            else:
                tenant_id = await self._ensure_tenant_id_unique(self._generate_tenant_id())
            
            # Create tenant document
            tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_data.name or f"Store {tenant_id}",
                status=TenantStatus.NEW,
                notes=tenant_data.notes,
                created_at=datetime.utcnow(),
                settings={
                    "created_by": created_by_admin_id,
                    "signup_enabled": True,
                    "features": {
                        "returns_management": True,
                        "analytics": True,
                        "automation": True
                    }
                }
            )
            
            # Insert into database
            await self.tenants_collection.insert_one(tenant.dict())
            
            logger.info(f"Created new tenant: {tenant_id} by admin: {created_by_admin_id}")
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise ValueError(f"Failed to create tenant: {str(e)}")

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID with full validation"""
        try:
            tenant_doc = await self.tenants_collection.find_one({"tenant_id": tenant_id})
            if not tenant_doc:
                return None
            
            # Remove MongoDB _id for clean response
            tenant_doc.pop('_id', None)
            return Tenant(**tenant_doc)
            
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None

    async def list_tenants(self, page: int = 1, page_size: int = 50, status: Optional[TenantStatus] = None) -> TenantListResponse:
        """List all tenants with pagination and filtering"""
        try:
            # Build filter
            filter_query = {}
            if status:
                filter_query["status"] = status.value
            
            # Get total count
            total = await self.tenants_collection.count_documents(filter_query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Fetch tenants with stats
            pipeline = [
                {"$match": filter_query},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": page_size},
                # Lookup user count
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "tenant_id",
                        "foreignField": "tenant_id",
                        "as": "users"
                    }
                },
                # Add computed stats
                {
                    "$addFields": {
                        "stats.total_users": {"$size": "$users"}
                    }
                },
                {"$project": {"users": 0}}  # Remove users array from response
            ]
            
            cursor = self.tenants_collection.aggregate(pipeline)
            tenant_docs = await cursor.to_list(length=page_size)
            
            # Convert to Tenant objects
            tenants = []
            for doc in tenant_docs:
                doc.pop('_id', None)
                tenants.append(Tenant(**doc))
            
            return TenantListResponse(
                tenants=tenants,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            raise ValueError(f"Failed to list tenants: {str(e)}")

    async def update_tenant(self, tenant_id: str, update_data: TenantUpdate) -> Optional[Tenant]:
        """Update tenant with validation"""
        try:
            # Prepare update document
            update_doc = {}
            if update_data.name is not None:
                update_doc["name"] = update_data.name.strip()
            if update_data.notes is not None:
                update_doc["notes"] = update_data.notes
            if update_data.status is not None:
                update_doc["status"] = update_data.status.value
                if update_data.status == TenantStatus.ARCHIVED:
                    update_doc["archived_at"] = datetime.utcnow()
            
            if not update_doc:
                # No changes to make
                return await self.get_tenant_by_id(tenant_id)
            
            # Update tenant
            result = await self.tenants_collection.update_one(
                {"tenant_id": tenant_id},
                {"$set": update_doc}
            )
            
            if result.matched_count == 0:
                return None
            
            logger.info(f"Updated tenant {tenant_id}: {list(update_doc.keys())}")
            return await self.get_tenant_by_id(tenant_id)
            
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise ValueError(f"Failed to update tenant: {str(e)}")

    async def archive_tenant(self, tenant_id: str, archived_by_admin_id: str) -> bool:
        """Archive a tenant (soft delete)"""
        try:
            result = await self.tenants_collection.update_one(
                {"tenant_id": tenant_id, "status": {"$ne": TenantStatus.ARCHIVED.value}},
                {
                    "$set": {
                        "status": TenantStatus.ARCHIVED.value,
                        "archived_at": datetime.utcnow(),
                        "settings.archived_by": archived_by_admin_id
                    }
                }
            )
            
            success = result.matched_count > 0
            if success:
                logger.info(f"Archived tenant {tenant_id} by admin {archived_by_admin_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to archive tenant {tenant_id}: {e}")
            return False

    async def merchant_signup(self, signup_data: TenantMerchantSignup) -> Tuple[Dict[str, Any], bool]:
        """Handle merchant signup with tenant validation"""
        try:
            # Validate tenant exists and is active
            tenant = await self.get_tenant_by_id(signup_data.tenant_id)
            if not tenant:
                raise ValueError("Tenant ID not found")
            
            if tenant.status == TenantStatus.ARCHIVED:
                raise ValueError("This tenant is no longer active")
            
            # Check if tenant already has merchant users (first signup claim logic)
            existing_merchant = await self.users_collection.find_one({
                "tenant_id": signup_data.tenant_id,
                "role": UserRole.MERCHANT.value
            })
            
            is_first_merchant = existing_merchant is None
            
            # Create user via auth service
            user_create_data = UserCreate(
                tenant_id=signup_data.tenant_id,
                email=signup_data.email,
                password=signup_data.password,
                confirm_password=signup_data.confirm_password,
                role=UserRole.MERCHANT,
                auth_provider=AuthProvider.EMAIL,
                first_name=signup_data.first_name,
                last_name=signup_data.last_name,
                permissions=[
                    "view_returns", "manage_returns", "view_analytics", 
                    "manage_settings", "view_orders", "manage_customers"
                ]
            )
            
            # Create user
            user = await auth_service.create_user(user_create_data)
            
            # If first merchant, update tenant to claimed
            if is_first_merchant:
                await self.tenants_collection.update_one(
                    {"tenant_id": signup_data.tenant_id},
                    {
                        "$set": {
                            "status": TenantStatus.CLAIMED.value,
                            "claimed_at": datetime.utcnow(),
                            "settings.store_name": signup_data.store_name
                        }
                    }
                )
                logger.info(f"Tenant {signup_data.tenant_id} claimed by first merchant: {signup_data.email}")
            
            # Create login session
            from ..models.user import LoginRequest
            login_data = LoginRequest(
                tenant_id=signup_data.tenant_id,
                email=signup_data.email,
                password=signup_data.password,
                remember_me=True
            )
            
            authenticated_user, _ = await auth_service.authenticate_email_password(login_data)
            session = await auth_service.create_session(authenticated_user, "127.0.0.1", "merchant_signup", True)
            
            return {
                "user": {
                    "user_id": str(authenticated_user.user_id),
                    "email": authenticated_user.email,
                    "first_name": authenticated_user.first_name,
                    "last_name": authenticated_user.last_name,
                    "role": authenticated_user.role.value,
                    "tenant_id": authenticated_user.tenant_id
                },
                "access_token": session.session_token,
                "refresh_token": session.refresh_token,
                "tenant_id": signup_data.tenant_id,
                "is_first_merchant": is_first_merchant
            }, is_first_merchant
            
        except Exception as e:
            logger.error(f"Merchant signup failed for tenant {signup_data.tenant_id}: {e}")
            raise ValueError(str(e))

    async def get_tenant_integration_status(self, tenant_id: str) -> TenantConnection:
        """Get comprehensive integration status for a tenant"""
        try:
            # Get Shopify integration status
            shopify_integration = await self.integrations_collection.find_one({"tenant_id": tenant_id})
            
            if not shopify_integration:
                return TenantConnection(
                    tenant_id=tenant_id,
                    connected=False,
                    integration_status=IntegrationStatus.DISCONNECTED,
                    features_available=["manual_returns", "basic_analytics"]
                )
            
            # Determine connection status
            is_connected = bool(
                shopify_integration.get("access_token") and 
                shopify_integration.get("shop")
            )
            
            features = ["manual_returns", "basic_analytics"]
            if is_connected:
                features.extend([
                    "shopify_sync", "order_import", "customer_sync", 
                    "webhook_updates", "advanced_analytics", "automation"
                ])
            
            return TenantConnection(
                tenant_id=tenant_id,
                connected=is_connected,
                connected_at=shopify_integration.get("created_at"),
                last_sync=shopify_integration.get("last_sync"),
                shop_domain=shopify_integration.get("shop"),
                integration_status=IntegrationStatus.CONNECTED if is_connected else IntegrationStatus.DISCONNECTED,
                features_available=features
            )
            
        except Exception as e:
            logger.error(f"Failed to get integration status for tenant {tenant_id}: {e}")
            return TenantConnection(
                tenant_id=tenant_id,
                connected=False,
                integration_status=IntegrationStatus.ERROR,
                error_message=str(e)
            )

    async def is_tenant_connected(self, tenant_id: str) -> bool:
        """Quick check if tenant has Shopify connected"""
        try:
            integration = await self.integrations_collection.find_one({
                "tenant_id": tenant_id,
                "access_token": {"$exists": True, "$ne": None},
                "shop": {"$exists": True, "$ne": None}
            })
            return integration is not None
        except Exception as e:
            logger.error(f"Failed to check tenant connection status: {e}")
            return False

    async def update_tenant_activity(self, tenant_id: str):
        """Update tenant's last activity timestamp"""
        try:
            await self.tenants_collection.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"last_activity_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Failed to update tenant activity: {e}")

# Global enhanced tenant service instance
enhanced_tenant_service = TenantServiceEnhanced(None)  # Will be initialized with DB