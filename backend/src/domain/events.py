"""
Domain Events for CQRS Implementation
Events are fired when domain state changes occur
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from .value_objects import ReturnId, TenantId, OrderId, Email, Money


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events"""
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    @abstractmethod
    def get_event_type(self) -> str:
        pass


@dataclass
class ReturnCreated(DomainEvent):
    """Fired when a return request is created"""
    return_id: ReturnId
    tenant_id: TenantId
    order_id: OrderId
    customer_email: Email
    channel: str
    estimated_refund: Money
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.created"


@dataclass
class ReturnApproved(DomainEvent):
    """Fired when a return is approved"""
    return_id: ReturnId
    tenant_id: TenantId
    approved_by: str
    occurred_at: datetime
    auto_approved: bool = False
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.approved"


@dataclass
class ReturnRejected(DomainEvent):
    """Fired when a return is rejected"""
    return_id: ReturnId
    tenant_id: TenantId
    rejected_by: str
    reason: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.rejected"


@dataclass
class ReturnShipmentCreated(DomainEvent):
    """Fired when return shipment/label is created"""
    return_id: ReturnId
    tenant_id: TenantId
    carrier: str
    tracking_number: str
    label_url: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.shipment_created"


@dataclass
class ReturnReceived(DomainEvent):
    """Fired when returned items are received"""
    return_id: ReturnId
    tenant_id: TenantId
    received_by: str
    condition_notes: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.received"


@dataclass
class ReturnRefunded(DomainEvent):
    """Fired when refund is processed"""
    return_id: ReturnId
    tenant_id: TenantId
    refund_amount: Money
    refund_method: str
    processed_by: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "return.refunded"


@dataclass
class DraftCreated(DomainEvent):
    """Fired when return draft is created (fallback mode)"""
    draft_id: str
    tenant_id: TenantId
    order_number: str
    customer_email: Email
    channel: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "draft.created"


@dataclass
class DraftApproved(DomainEvent):
    """Fired when return draft is approved"""
    draft_id: str
    tenant_id: TenantId
    return_id: ReturnId
    approved_by: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "draft.approved"


@dataclass
class DraftLinkedToOrder(DomainEvent):
    """Fired when draft is linked to Shopify order"""
    draft_id: str
    tenant_id: TenantId
    order_id: OrderId
    linked_by: str
    occurred_at: datetime
    correlation_id: Optional[str] = None
    
    def get_event_type(self) -> str:
        return "draft.linked_to_order"


# Event Handler Interface
class DomainEventHandler(ABC):
    """Interface for domain event handlers"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event"""
        pass


# Event Publisher Interface  
class EventPublisher(ABC):
    """Interface for publishing domain events"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events as a batch"""
        pass