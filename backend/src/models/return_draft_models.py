"""
Return Draft Models for Fallback Mode
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid

class DraftStatus(str, Enum):
    PENDING_VALIDATION = "pending_validation"
    APPROVED = "approved"
    REJECTED = "rejected"
    LINKED = "linked"

class DraftItem(BaseModel):
    title: str
    sku: Optional[str] = ""
    variant: Optional[str] = ""
    quantity: int = Field(ge=1)
    reason: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)

class ReturnDraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_number: str
    email: str
    channel: Literal["customer", "admin"] = "customer"
    items: List[DraftItem] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    status: DraftStatus = DraftStatus.PENDING_VALIDATION
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    linked_shopify_order_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    customer_note: Optional[str] = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrderLookupRequest(BaseModel):
    tenant_id: Optional[str] = None
    shop_domain: Optional[str] = None
    order_number: str
    email: str
    channel: Literal["customer", "admin"] = "customer"

class ShopifyOrderItem(BaseModel):
    id: str
    title: str
    sku: Optional[str] = ""
    variant: Optional[str] = ""
    quantity: int
    fulfillment_status: Optional[str] = None
    eligible_for_return: bool = True
    max_return_qty: int
    price: float = 0.0
    image_url: Optional[str] = ""

class ShopifyOrderResponse(BaseModel):
    mode: Literal["shopify"] = "shopify"
    order: Dict[str, Any]

class FallbackOrderResponse(BaseModel):
    mode: Literal["fallback"] = "fallback"
    status: Literal["pending_validation"] = "pending_validation"
    message: str = "Store not connected to Shopify. Your request will be reviewed."
    captured: Dict[str, Any]