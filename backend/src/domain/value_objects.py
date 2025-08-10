"""
Value Objects for Returns Domain
Immutable objects that encapsulate business concepts
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ReturnId:
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 10:
            raise ValueError("Invalid ReturnId")


@dataclass(frozen=True)
class OrderId:
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Invalid OrderId")


@dataclass(frozen=True)
class TenantId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.startswith("tenant-"):
            raise ValueError("Invalid TenantId")


@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid Email")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    
    def __post_init__(self):
        object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Invalid currency code")
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(max(Decimal('0'), self.amount - other.amount), self.currency)


@dataclass(frozen=True)
class ReturnReason:
    code: str
    description: str
    
    def __post_init__(self):
        if not self.code:
            raise ValueError("Return reason code is required")


@dataclass(frozen=True)
class PolicySnapshot:
    """
    Immutable snapshot of policy at time of return creation
    Ensures consistent processing even if policy changes
    """
    return_window_days: int
    restock_fee_enabled: bool
    restock_fee_percent: Decimal
    shipping_fee_enabled: bool  
    shipping_fee_amount: Decimal
    photo_required_reasons: List[str]
    excluded_categories: List[str]
    excluded_tags: List[str]
    auto_approve_threshold: Decimal
    eligible_outcomes: List[str]
    eligible_methods: List[str]
    created_at: datetime
    
    def __post_init__(self):
        if self.return_window_days <= 0:
            raise ValueError("Return window must be positive")
        if self.restock_fee_percent < 0 or self.restock_fee_percent > 100:
            raise ValueError("Invalid restock fee percentage")


@dataclass
class AuditEntry:
    """Audit log entry for tracking changes"""
    timestamp: datetime
    actor: str
    action: str
    details: Dict[str, Any]
    correlation_id: Optional[str] = None


@dataclass(frozen=True)
class Address:
    """Value object for addresses"""
    line1: str
    line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    
    def __post_init__(self):
        required_fields = [self.line1, self.city, self.state, self.postal_code, self.country]
        if any(not field for field in required_fields):
            raise ValueError("Address missing required fields")


@dataclass(frozen=True)
class ShippingLabel:
    """Value object for shipping labels"""
    carrier: str
    service_type: str
    tracking_number: str
    label_url: str
    cost: Money
    estimated_delivery_date: Optional[datetime] = None
    
    def __post_init__(self):
        if not all([self.carrier, self.service_type, self.tracking_number, self.label_url]):
            raise ValueError("Shipping label missing required fields")


@dataclass(frozen=True)
class Coordinates:
    """GPS coordinates for tracking"""
    latitude: Decimal
    longitude: Decimal
    
    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Invalid latitude")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Invalid longitude")