"""
CQRS Queries for Return Operations
Queries represent requests for data without side effects
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from ..domain.value_objects import TenantId, Email


@dataclass
class Query:
    """Base query class"""
    pass


@dataclass
class GetReturnById(Query):
    """Query to get return by ID"""
    return_id: str
    tenant_id: TenantId


@dataclass
class GetReturnsByOrder(Query):
    """Query to get returns for an order"""
    order_id: str
    tenant_id: TenantId


@dataclass
class SearchReturns(Query):
    """Query to search returns with filters"""
    tenant_id: TenantId
    status: Optional[str] = None
    customer_email: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_term: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class GetReturnAnalytics(Query):
    """Query to get return analytics"""
    tenant_id: TenantId
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class GetPendingDrafts(Query):
    """Query to get pending drafts for admin review"""
    tenant_id: TenantId
    limit: int = 20
    offset: int = 0


@dataclass
class LookupOrderForReturn(Query):
    """Query to lookup order for return creation"""
    order_number: str
    tenant_id: TenantId
    customer_email: Optional[str] = None  # Optional for lookup


@dataclass
class GetEligibleItemsForReturn(Query):
    """Query to get items eligible for return from an order"""
    order_id: str
    tenant_id: TenantId


@dataclass
class GetPolicyPreview(Query):
    """Query to get policy preview for return"""
    tenant_id: TenantId
    order_id: str
    items: List[dict]


@dataclass
class GetReturnAuditLog(Query):
    """Query to get return audit log"""
    return_id: str
    tenant_id: TenantId