"""
Tenant Management Models - Production Multi-Tenancy System
Handles tenant creation, management, and strict isolation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import re

class TenantStatus(str, Enum):
    NEW = "new"
    CLAIMED = "claimed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class IntegrationStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class TenantCreate(BaseModel):
    name: Optional[str] = Field(None, description="Display name for the tenant")
    tenant_id: Optional[str] = Field(None, description="Custom tenant ID (auto-generated if not provided)")
    notes: Optional[str] = Field(None, description="Admin notes about the tenant")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        if v is not None:
            # Must start with tenant- and contain only lowercase, numbers, hyphens
            if not re.match(r'^tenant-[a-z0-9-]+$', v):
                raise ValueError('Tenant ID must start with "tenant-" and contain only lowercase letters, numbers, and hyphens')
            if len(v) < 8 or len(v) > 50:
                raise ValueError('Tenant ID must be between 8 and 50 characters')
        return v

    @validator('name')
    def validate_name(cls, v):
        if v is not None and (len(v.strip()) < 2 or len(v.strip()) > 100):
            raise ValueError('Tenant name must be between 2 and 100 characters')
        return v.strip() if v else None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[TenantStatus] = None

class TenantIntegrations(BaseModel):
    shopify: Dict[str, Any] = Field(default_factory=dict)
    stripe: Dict[str, Any] = Field(default_factory=dict)
    sendgrid: Dict[str, Any] = Field(default_factory=dict)

class TenantStats(BaseModel):
    total_users: int = 0
    total_orders: int = 0
    total_returns: int = 0
    total_customers: int = 0
    revenue_processed: float = 0.0
    returns_processed: int = 0

class Tenant(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier")
    name: Optional[str] = Field(None, description="Display name for the tenant")
    status: TenantStatus = Field(TenantStatus.NEW, description="Current tenant status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    claimed_at: Optional[datetime] = Field(None, description="When first merchant user was created")
    last_activity_at: Optional[datetime] = Field(None, description="Last user activity")
    
    # Integrations
    integrations: TenantIntegrations = Field(default_factory=TenantIntegrations)
    
    # Metadata
    notes: Optional[str] = Field(None, description="Admin notes")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    
    # Stats (cached for performance)
    stats: TenantStats = Field(default_factory=TenantStats)
    
    # Settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant-specific settings")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TenantListResponse(BaseModel):
    tenants: List[Tenant]
    total: int
    page: int
    page_size: int
    total_pages: int

class TenantMerchantSignup(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID to join")
    email: str = Field(..., description="Merchant email address")
    password: str = Field(..., min_length=8, description="Account password")
    confirm_password: str = Field(..., description="Password confirmation")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    store_name: Optional[str] = Field(None, description="Store/business name")
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('tenant_id')
    def validate_tenant_id_signup(cls, v):
        if not re.match(r'^tenant-[a-z0-9-]+$', v.strip()):
            raise ValueError('Invalid tenant ID format')
        return v.strip()

class TenantIntegrationStatus(BaseModel):
    tenant_id: str
    shopify: Dict[str, Any] = Field(default_factory=lambda: {
        "connected": False,
        "shop_domain": None,
        "connected_at": None,
        "last_sync": None,
        "status": IntegrationStatus.DISCONNECTED,
        "error": None
    })
    stripe: Dict[str, Any] = Field(default_factory=lambda: {
        "connected": False,
        "account_id": None,
        "connected_at": None,
        "status": IntegrationStatus.DISCONNECTED
    })
    sendgrid: Dict[str, Any] = Field(default_factory=lambda: {
        "connected": False,
        "api_key_set": False,
        "verified": False,
        "status": IntegrationStatus.DISCONNECTED
    })

class TenantConnection(BaseModel):
    """Response model for tenant connection status"""
    tenant_id: str
    connected: bool = False
    connected_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    shop_domain: Optional[str] = None
    integration_status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    error_message: Optional[str] = None
    features_available: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }