"""
Tenant model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class PlanType(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(BaseModel):
    """Tenant model for multi-tenant SaaS"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: str
    shopify_store_url: Optional[str] = None
    shopify_access_token: Optional[str] = None
    plan: PlanType = PlanType.TRIAL
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class TenantCreate(BaseModel):
    """Schema for creating a new tenant"""
    name: str
    domain: str
    shopify_store_url: Optional[str] = None


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    name: Optional[str] = None
    domain: Optional[str] = None
    shopify_store_url: Optional[str] = None
    plan: Optional[PlanType] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TenantSettings(BaseModel):
    """Tenant-specific settings schema"""
    return_window_days: int = 30
    auto_approve_exchanges: bool = True
    require_photos: bool = False
    brand_color: str = "#3b82f6"
    custom_message: str = "We're here to help with your return!"
    email_notifications: bool = True
    auto_generate_labels: bool = False