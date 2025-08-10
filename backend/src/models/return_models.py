"""
Return Request Data Models
Production-ready models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid

class PortalChannel(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class ReturnStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED" 
    LABEL_ISSUED = "LABEL_ISSUED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    REFUNDED = "REFUNDED"
    EXCHANGED = "EXCHANGED"
    DECLINED = "DECLINED"
    CANCELED = "CANCELED"

class PreferredOutcome(str, Enum):
    REFUND = "REFUND"
    STORE_CREDIT = "STORE_CREDIT"
    EXCHANGE = "EXCHANGE"
    REPLACEMENT = "REPLACEMENT"

class ReturnMethod(str, Enum):
    PREPAID_LABEL = "PREPAID_LABEL"
    QR_DROPOFF = "QR_DROPOFF"
    IN_STORE = "IN_STORE"
    CUSTOMER_SHIPS = "CUSTOMER_SHIPS"

class ExternalSyncStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    SYNCED = "synced"
    ERROR = "error"

class ReturnItemRequest(BaseModel):
    line_item_id: str
    sku: str
    qty: int = Field(ge=1)
    reason_code: str
    reason_note: Optional[str] = ""

class PhotoUpload(BaseModel):
    s3_url: str
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class FeeApplied(BaseModel):
    type: Literal["RESTOCK", "SHIPPING", "OTHER"]
    amount: float
    description: Optional[str] = ""

class PromoApplied(BaseModel):
    code: str
    type: Literal["BONUS_CREDIT", "DISCOUNT", "KEEP_ITEM_CREDIT"] 
    value: float
    calculated_amount: float

class AuditLogEntry(BaseModel):
    at: datetime = Field(default_factory=datetime.utcnow)
    actor: Dict[str, Any]  # {type: 'system'|'user'|'customer', id?: str}
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)

class ReturnRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_id: str
    portal_channel: PortalChannel
    status: ReturnStatus = ReturnStatus.REQUESTED
    preferred_outcome: PreferredOutcome
    reason_code: str
    reason_note: Optional[str] = ""
    items: List[ReturnItemRequest]
    photos: List[PhotoUpload] = Field(default_factory=list)
    return_method: ReturnMethod
    fees_applied: List[FeeApplied] = Field(default_factory=list)
    estimated_refund_amount: float
    final_refund_amount: Optional[float] = None
    promo_applied: Optional[PromoApplied] = None
    external_sync_status: ExternalSyncStatus = ExternalSyncStatus.NONE
    external_ids: Dict[str, str] = Field(default_factory=dict)
    audit_log: List[AuditLogEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    external_id: Optional[str] = None  # Shopify GID
    order_number: str
    customer_email: str
    customer_name: str
    created_at: datetime
    fulfillment_status: Optional[str] = None
    financial_status: Optional[str] = None
    currency: str = "USD"
    total_amount: float
    items: List[Dict[str, Any]] = Field(default_factory=list)
    source: Literal["manual", "shopify"] = "manual"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Policy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    return_window_days: int = 30
    window_overrides: List[Dict[str, Any]] = Field(default_factory=list)
    excluded: Dict[str, List[str]] = Field(default_factory=dict)
    condition_requirements: Dict[str, List[str]] = Field(default_factory=dict)
    fees: Dict[str, Any] = Field(default_factory=dict)
    auto_approve: Dict[str, Any] = Field(default_factory=dict)
    eligible_outcomes: List[str] = Field(default_factory=list)
    eligible_methods: List[str] = Field(default_factory=list)
    offers: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Offer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    active: bool = True
    triggers: Dict[str, Any] = Field(default_factory=dict)
    type: Literal["BONUS_STORE_CREDIT", "EXCHANGE_DISCOUNT", "KEEP_ITEM_CREDIT", "UPSELL"]
    value: Dict[str, float] = Field(default_factory=dict)
    upsell_target: Optional[Dict[str, str]] = None
    ab_flag: Optional[Literal["A", "B"]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ShippingLabel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    return_request_id: str
    carrier: str
    method: str
    label_url: Optional[str] = None
    tracking: Optional[str] = None
    cost: float = 0.0
    status: Literal["ISSUED", "VOIDED"] = "ISSUED"
    created_at: datetime = Field(default_factory=datetime.utcnow)