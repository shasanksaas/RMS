"""
Shopify Integration Models - Shop-based Multi-tenant Architecture
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class ShopifyConnectionStatus(str, Enum):
    """Status of Shopify integration"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class TenantStatus(str, Enum):
    """Tenant status based on Shopify connection"""
    NEW = "new"
    PROVISIONED = "provisioned"
    ACTIVE = "active"
    SUSPENDED = "suspended"

# === Shopify Integration Models ===

class ShopifyIntegrationBase(BaseModel):
    """Base model for Shopify integration"""
    shop: str  # e.g., "rms34.myshopify.com"
    scopes: List[str] = [
        "read_orders",
        "read_fulfillments", 
        "read_products",
        "read_customers",
        "read_returns",
        "write_returns"
    ]
    status: ShopifyConnectionStatus = ShopifyConnectionStatus.CONNECTING

class ShopifyIntegrationCreate(ShopifyIntegrationBase):
    """Model for creating Shopify integration"""
    access_token: str
    tenant_id: str

class ShopifyIntegrationDB(ShopifyIntegrationBase):
    """Database model for Shopify integration"""
    tenant_id: str
    access_token_encrypted: str
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None
    webhook_ids: Dict[str, str] = Field(default_factory=dict)  # topic -> webhook_id
    metadata: Dict[str, Any] = Field(default_factory=dict)

# === Shop-based Tenant Models ===

class ShopBasedTenantBase(BaseModel):
    """Base model for shop-based tenant"""
    shop: str  # Normalized shop domain (rms34.myshopify.com)
    name: Optional[str] = None  # Store name from Shopify
    
class ShopBasedTenantCreate(ShopBasedTenantBase):
    """Model for creating shop-based tenant"""
    pass

class ShopBasedTenantDB(ShopBasedTenantBase):
    """Database model for shop-based tenant"""
    tenant_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TenantStatus = TenantStatus.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

# === Shopify User Models ===

class ShopifyUserBase(BaseModel):
    """Base model for Shopify-authenticated user"""
    shop: str
    role: str = "merchant_owner"
    provider: str = "shopify"

class ShopifyUserCreate(ShopifyUserBase):
    """Model for creating Shopify user"""
    tenant_id: str
    shopify_user_id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ShopifyUserDB(ShopifyUserBase):
    """Database model for Shopify user"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    shopify_user_id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# === OAuth Flow Models ===

class ShopifyOAuthState(BaseModel):
    """OAuth state payload for security"""
    shop: str
    nonce: str
    timestamp: float
    redirect_after: Optional[str] = "/app/dashboard?connected=1"

class ShopifyInstallRequest(BaseModel):
    """Request model for Shopify installation"""
    shop: str  # Can be "rms34" or "rms34.myshopify.com"

class ShopifyCallbackRequest(BaseModel):
    """Request model for Shopify OAuth callback"""
    code: str
    hmac: str
    shop: str
    state: str
    timestamp: str

# === Response Models ===

class ShopifyConnectionResponse(BaseModel):
    """Response model for connection status"""
    connected: bool
    shop: Optional[str] = None
    tenant_id: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    status: ShopifyConnectionStatus
    scopes: List[str] = Field(default_factory=list)

class ShopifyInstallResponse(BaseModel):
    """Response model for installation URL"""
    install_url: str
    shop: str
    state: str

class ShopifyConnectSuccessResponse(BaseModel):
    """Response model for successful connection"""
    success: bool = True
    message: str = "Store connected successfully"
    shop: str
    tenant_id: str
    redirect_url: str = "/app/dashboard?connected=1"

# === Webhook Models ===

class ShopifyWebhookPayload(BaseModel):
    """Base model for Shopify webhook payloads"""
    shop_domain: str
    topic: str
    data: Dict[str, Any]
    webhook_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ShopifyWebhookVerification(BaseModel):
    """Model for webhook HMAC verification"""
    body: str
    headers: Dict[str, str]
    shop: str