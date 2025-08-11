"""
Return Domain Entity - Core business logic
Elite-grade domain model with state machine and business rules
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

from ..value_objects import (
    ReturnId, OrderId, TenantId, Email, ReturnReason, 
    Money, PolicySnapshot, AuditEntry
)
from ..events import DomainEvent, ReturnCreated, ReturnApproved, ReturnRejected


class ReturnStatus(Enum):
    DRAFT = "draft"
    REQUESTED = "requested"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    DECLINED = "declined"
    CANCELED = "canceled"
    CLOSED = "closed"


class ReturnChannel(Enum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    API = "api"


class ReturnMethod(Enum):
    PREPAID_LABEL = "prepaid_label"
    QR_DROPOFF = "qr_dropoff"
    IN_STORE = "in_store"
    CUSTOMER_SHIPS = "customer_ships"


@dataclass
class ReturnLineItem:
    """Individual item being returned"""
    line_item_id: str
    sku: str
    title: str
    variant_title: Optional[str]
    quantity: int
    unit_price: Money
    reason: ReturnReason
    condition: str  # new, used, damaged
    photos: List[str] = field(default_factory=list)
    notes: str = ""
    
    def calculate_value(self) -> Money:
        """Calculate total value of this line item"""
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


@dataclass
class Return:
    """
    Return Aggregate Root
    Encapsulates business logic and state transitions
    """
    id: ReturnId
    tenant_id: TenantId
    order_id: OrderId
    channel: ReturnChannel
    status: ReturnStatus
    customer_email: Email
    line_items: List[ReturnLineItem]
    return_method: ReturnMethod
    policy_snapshot: PolicySnapshot
    estimated_refund: Money
    final_refund: Optional[Money] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    submitted_by: Optional[str] = None
    processed_by: Optional[str] = None
    
    # Audit trail
    audit_log: List[AuditEntry] = field(default_factory=list)
    
    # Domain events (for CQRS)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    # State machine transitions
    _allowed_transitions = {
        ReturnStatus.DRAFT: [ReturnStatus.REQUESTED, ReturnStatus.CANCELED],
        ReturnStatus.REQUESTED: [ReturnStatus.APPROVED, ReturnStatus.DECLINED, ReturnStatus.CANCELED],
        ReturnStatus.APPROVED: [ReturnStatus.IN_TRANSIT, ReturnStatus.CANCELED],
        ReturnStatus.IN_TRANSIT: [ReturnStatus.RECEIVED, ReturnStatus.CANCELED],
        ReturnStatus.RECEIVED: [ReturnStatus.REFUNDED, ReturnStatus.EXCHANGED],
        ReturnStatus.REFUNDED: [ReturnStatus.CLOSED],
        ReturnStatus.EXCHANGED: [ReturnStatus.CLOSED],
        ReturnStatus.DECLINED: [],
        ReturnStatus.CANCELED: [],
        ReturnStatus.CLOSED: []
    }
    
    def add_domain_event(self, event: DomainEvent):
        """Add domain event for eventual publishing"""
        self._domain_events.append(event)
    
    def clear_domain_events(self):
        """Clear domain events after publishing"""
        self._domain_events.clear()
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get pending domain events"""
        return self._domain_events.copy()
    
    def change_status(self, new_status: ReturnStatus, actor: str, reason: str = "") -> None:
        """
        Change return status with business rule validation
        Implements state machine with guards
        """
        if new_status not in self._allowed_transitions.get(self.status, []):
            raise ValueError(
                f"Invalid state transition from {self.status.value} to {new_status.value}"
            )
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Add audit entry
        audit_entry = AuditEntry(
            timestamp=datetime.utcnow(),
            actor=actor,
            action=f"status_changed",
            details={
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason
            }
        )
        self.audit_log.append(audit_entry)
        
        # Emit domain events
        if new_status == ReturnStatus.REQUESTED:
            self.add_domain_event(ReturnCreated(
                return_id=self.id,
                tenant_id=self.tenant_id,
                order_id=self.order_id,
                customer_email=self.customer_email,
                channel=self.channel,
                estimated_refund=self.estimated_refund,
                occurred_at=datetime.utcnow(),
                correlation_id=None  # Will be set by command handler if available
            ))
        elif new_status == ReturnStatus.APPROVED:
            self.add_domain_event(ReturnApproved(
                return_id=self.id,
                tenant_id=self.tenant_id,
                approved_by=actor,
                occurred_at=datetime.utcnow(),
                correlation_id=None
            ))
        elif new_status == ReturnStatus.DECLINED:
            self.add_domain_event(ReturnRejected(
                return_id=self.id,
                tenant_id=self.tenant_id,
                rejected_by=actor,
                reason=reason,
                occurred_at=datetime.utcnow(),
                correlation_id=None
            ))
    
    def approve(self, approver: str, override_policy: bool = False, notes: str = "") -> None:
        """Approve return with business logic"""
        if not self.can_be_approved():
            raise ValueError("Return cannot be approved in current state")
        
        if override_policy and not notes:
            raise ValueError("Notes required when overriding policy")
        
        self.change_status(ReturnStatus.APPROVED, approver, notes)
        self.processed_by = approver
    
    def reject(self, rejector: str, reason: str) -> None:
        """Reject return with reason"""
        if not reason:
            raise ValueError("Reason required for rejection")
        
        self.change_status(ReturnStatus.DECLINED, rejector, reason)
        self.processed_by = rejector
    
    def can_be_approved(self) -> bool:
        """Business rule: check if return can be approved"""
        return self.status == ReturnStatus.REQUESTED and self.is_within_policy()
    
    def is_within_policy(self) -> bool:
        """Check if return meets policy requirements"""
        # Check return window
        days_since_order = (datetime.utcnow() - self.created_at).days
        if days_since_order > self.policy_snapshot.return_window_days:
            return False
        
        # Check if all items have valid reasons
        for item in self.line_items:
            if not item.reason or item.reason.code == "":
                return False
        
        return True
    
    def calculate_refund(self) -> Money:
        """Calculate refund amount based on policy and items"""
        from decimal import Decimal
        
        total_item_value = sum(
            item.calculate_value().amount for item in self.line_items
        )
        
        # Apply policy fees - use Decimal for all calculations
        fees = Decimal('0')
        if self.policy_snapshot.restock_fee_enabled:
            restock_percentage = Decimal(str(self.policy_snapshot.restock_fee_percent)) / Decimal('100')
            fees += total_item_value * restock_percentage
        
        if self.policy_snapshot.shipping_fee_enabled:
            fees += Decimal(str(self.policy_snapshot.shipping_fee_amount))
        
        refund_amount = max(Decimal('0'), total_item_value - fees)
        
        return Money(refund_amount, self.estimated_refund.currency)
    
    def add_line_item(self, line_item: ReturnLineItem) -> None:
        """Add item to return"""
        if self.status != ReturnStatus.DRAFT:
            raise ValueError("Cannot modify items after submission")
        
        self.line_items.append(line_item)
        self.updated_at = datetime.utcnow()
    
    def remove_line_item(self, line_item_id: str) -> None:
        """Remove item from return"""
        if self.status != ReturnStatus.DRAFT:
            raise ValueError("Cannot modify items after submission")
        
        self.line_items = [item for item in self.line_items if item.line_item_id != line_item_id]
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_new(
        cls,
        tenant_id: TenantId,
        order_id: OrderId,
        customer_email: Email,
        channel: ReturnChannel,
        return_method: ReturnMethod,
        policy_snapshot: PolicySnapshot
    ) -> "Return":
        """Factory method for creating new returns"""
        return_id = ReturnId(str(uuid.uuid4()))
        
        return cls(
            id=return_id,
            tenant_id=tenant_id,
            order_id=order_id,
            channel=channel,
            status=ReturnStatus.DRAFT,
            customer_email=customer_email,
            line_items=[],
            return_method=return_method,
            policy_snapshot=policy_snapshot,
            estimated_refund=Money(0.0, "USD")
        )


@dataclass
class ReturnDraft:
    """
    Return Draft for fallback mode
    Used when Shopify integration is not available
    """
    id: str
    tenant_id: TenantId
    order_number: str
    customer_email: Email
    channel: ReturnChannel
    status: str = "pending_validation"
    items: List[Dict[str, Any]] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)
    customer_note: str = ""
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    linked_order_id: Optional[str] = None
    
    def approve_and_convert_to_return(
        self, 
        approver: str, 
        order_id: OrderId,
        policy_snapshot: PolicySnapshot
    ) -> Return:
        """Convert approved draft to actual return"""
        return_obj = Return.create_new(
            tenant_id=self.tenant_id,
            order_id=order_id,
            customer_email=self.customer_email,
            channel=self.channel,
            return_method=ReturnMethod.PREPAID_LABEL,  # Default
            policy_snapshot=policy_snapshot
        )
        
        # Add line items from draft
        for item_data in self.items:
            line_item = ReturnLineItem(
                line_item_id=item_data.get("id", str(uuid.uuid4())),
                sku=item_data.get("sku", ""),
                title=item_data.get("title", ""),
                variant_title=item_data.get("variant", ""),
                quantity=item_data.get("quantity", 1),
                unit_price=Money(item_data.get("price", 0), "USD"),
                reason=ReturnReason(item_data.get("reason", "other"), "Other"),
                condition=item_data.get("condition", "used")
            )
            return_obj.add_line_item(line_item)
        
        # Submit immediately
        return_obj.change_status(ReturnStatus.REQUESTED, approver, f"Converted from draft {self.id}")
        
        return return_obj