"""
Tenant Administration Models
Pydantic models for admin tenant management operations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re

class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant"""
    tenant_id: str = Field(..., description="Unique tenant identifier (slug format)")
    name: str = Field(..., min_length=1, max_length=100, description="Display name for the tenant")
    shop_domain: Optional[str] = Field(None, description="Shopify shop domain (optional)")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        """Validate tenant_id follows slug format"""
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError('tenant_id must be lowercase alphanumeric with hyphens (slug format)')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('tenant_id must be between 3 and 50 characters')
        return v
    
    @validator('shop_domain')
    def validate_shop_domain(cls, v):
        """Validate shop domain format if provided"""
        if v is not None:
            # Allow both formats: shop-name.myshopify.com or just shop-name
            if not re.match(r'^[a-z0-9-]+(?:\.myshopify\.com)?$', v.lower()):
                raise ValueError('shop_domain must be valid Shopify domain format')
        return v

class TenantResponse(BaseModel):
    """Response model for tenant data"""
    tenant_id: str
    name: str
    shop_domain: Optional[str] = None
    connected_provider: Optional[Literal["shopify"]] = None
    created_at: datetime
    stats: Optional[dict] = None
    
    class Config:
        from_attributes = True

class TenantListResponse(BaseModel):
    """Response model for tenant list"""
    tenants: list[TenantResponse]
    total: int
    page: int
    page_size: int

class TenantDeleteResponse(BaseModel):
    """Response model for tenant deletion"""
    success: bool
    message: str
    tenant_id: str

class ImpersonationRequest(BaseModel):
    """Request model for admin impersonation"""
    tenant_id: str

class ImpersonationResponse(BaseModel):
    """Response model for impersonation"""
    success: bool
    message: str
    redirect_url: str
    impersonation_token: str
    expires_in: int  # seconds

class AuditLogEntry(BaseModel):
    """Audit log entry for admin actions"""
    action: str
    admin_user_id: str
    admin_email: str
    tenant_id: Optional[str] = None
    timestamp: datetime
    details: Optional[dict] = None
    
    class Config:
        from_attributes = True