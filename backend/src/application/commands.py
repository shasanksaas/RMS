"""
CQRS Commands for Return Operations
Commands represent intent to change state
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..domain.value_objects import TenantId, OrderId, Email
from ..domain.entities.return_entity import ReturnChannel, ReturnMethod


@dataclass
class Command:
    """Base command class"""
    correlation_id: Optional[str]


@dataclass
class CreateReturnRequest(Command):
    """Command to create a new return request"""
    tenant_id: TenantId
    order_id: OrderId
    customer_email: Email
    channel: ReturnChannel
    return_method: ReturnMethod
    line_items: List[Dict[str, Any]]
    correlation_id: Optional[str]
    customer_note: str = ""
    submitted_by: Optional[str] = None


@dataclass
class CreateReturnDraft(Command):
    """Command to create return draft (fallback mode)"""
    tenant_id: TenantId
    order_number: str
    customer_email: Email
    channel: ReturnChannel
    items: List[Dict[str, Any]]
    photos: List[str]
    correlation_id: Optional[str]
    customer_note: str = ""


@dataclass
class ApproveReturn(Command):
    """Command to approve a return"""
    return_id: str
    tenant_id: TenantId
    approver: str
    correlation_id: Optional[str]
    override_policy: bool = False
    notes: str = ""


@dataclass
class RejectReturn(Command):
    """Command to reject a return"""
    return_id: str
    tenant_id: TenantId
    rejector: str
    reason: str
    correlation_id: Optional[str]


@dataclass
class ProcessRefund(Command):
    """Command to process refund"""
    return_id: str
    tenant_id: TenantId
    refund_amount: float
    refund_method: str
    processed_by: str
    correlation_id: Optional[str]


@dataclass
class GenerateReturnLabel(Command):
    """Command to generate return label"""
    return_id: str
    tenant_id: TenantId
    from_address: Dict[str, str]
    to_address: Dict[str, str]
    correlation_id: Optional[str]
    service_type: str = "ground"


@dataclass
class ApproveDraftAndConvert(Command):
    """Command to approve draft and convert to return"""
    draft_id: str
    tenant_id: TenantId
    linked_order_id: str
    approver: str
    notes: str = ""