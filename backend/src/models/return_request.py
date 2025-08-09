"""
Return request model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid

from .order import OrderItem


class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"


class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    WRONG_SIZE = "wrong_size"
    WRONG_COLOR = "wrong_color"
    NOT_AS_DESCRIBED = "not_as_described"
    DAMAGED_IN_SHIPPING = "damaged_in_shipping"
    CHANGED_MIND = "changed_mind"
    QUALITY_ISSUES = "quality_issues"


class ReturnRequest(BaseModel):
    """Return request model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_id: str
    customer_email: str
    customer_name: str
    reason: ReturnReason
    status: ReturnStatus = ReturnStatus.REQUESTED
    items_to_return: List[OrderItem]
    refund_amount: float = 0.0
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReturnRequestCreate(BaseModel):
    """Schema for creating a return request"""
    order_id: str
    reason: ReturnReason
    items_to_return: List[OrderItem]
    notes: Optional[str] = None


class ReturnStatusUpdate(BaseModel):
    """Schema for updating return status"""
    status: ReturnStatus
    notes: Optional[str] = None
    tracking_number: Optional[str] = None