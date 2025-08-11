"""
Tenant service - handles tenant business logic
"""
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Tenant, TenantCreate, TenantUpdate
from ..config.database import db, COLLECTIONS


class TenantService:
    """Service class for tenant operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self.db = database
        self.collection = self.db[COLLECTIONS['tenants']]
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant with default settings"""
        tenant = Tenant(**tenant_data.dict())
        
        # Set default settings
        tenant.settings = {
            "return_window_days": 30,
            "auto_approve_exchanges": True,
            "require_photos": False,
            "brand_color": "#3b82f6",
            "custom_message": "We're here to help with your return!",
            "email_notifications": True,
            "auto_generate_labels": False
        }
        
        await self.collection.insert_one(tenant.dict())
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        tenant_data = await self.collection.find_one({"id": tenant_id, "is_active": True})
        if tenant_data:
            return Tenant(**tenant_data)
        return None
    
    async def get_all_tenants(self) -> List[Tenant]:
        """Get all active tenants"""
        tenants = await self.collection.find({"is_active": True}).to_list(100)
        return [Tenant(**tenant) for tenant in tenants]
    
    async def update_tenant(self, tenant_id: str, update_data: TenantUpdate) -> Optional[Tenant]:
        """Update tenant information"""
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if update_dict:
            await self.collection.update_one(
                {"id": tenant_id, "is_active": True},
                {"$set": update_dict}
            )
        
        return await self.get_tenant_by_id(tenant_id)
    
    async def update_tenant_settings(self, tenant_id: str, settings: Dict[str, Any]) -> Optional[Tenant]:
        """Update tenant settings"""
        await self.collection.update_one(
            {"id": tenant_id, "is_active": True},
            {"$set": {"settings": settings}}
        )
        
        return await self.get_tenant_by_id(tenant_id)
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate a tenant (soft delete)"""
        result = await self.collection.update_one(
            {"id": tenant_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    async def verify_tenant_exists(self, tenant_id: str) -> bool:
        """Verify if tenant exists and is active"""
        tenant = await self.collection.find_one({"id": tenant_id, "is_active": True})
        return tenant is not None