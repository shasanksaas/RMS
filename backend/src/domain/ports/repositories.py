"""
Repository Port Definitions
Interfaces for persistence layer
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.return_entity import Return, ReturnDraft
from ..value_objects import ReturnId, TenantId, OrderId, Email


class ReturnRepository(ABC):
    """Port for return persistence"""
    
    @abstractmethod
    async def save(self, return_obj: Return) -> None:
        """Save or update a return"""
        pass
    
    @abstractmethod
    async def get_by_id(self, return_id: ReturnId, tenant_id: TenantId) -> Optional[Return]:
        """Get return by ID"""
        pass
    
    @abstractmethod
    async def get_by_order_id(self, order_id: OrderId, tenant_id: TenantId) -> List[Return]:
        """Get returns for an order"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        tenant_id: TenantId,
        status: Optional[str] = None,
        customer_email: Optional[Email] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Return]:
        """Search returns with filters"""
        pass
    
    @abstractmethod
    async def count(
        self, 
        tenant_id: TenantId,
        status: Optional[str] = None,
        customer_email: Optional[Email] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """Count returns with filters"""
        pass


class ReturnDraftRepository(ABC):
    """Port for return draft persistence (fallback mode)"""
    
    @abstractmethod
    async def save(self, draft: ReturnDraft) -> None:
        """Save or update a return draft"""
        pass
    
    @abstractmethod
    async def get_by_id(self, draft_id: str, tenant_id: TenantId) -> Optional[ReturnDraft]:
        """Get draft by ID"""
        pass
    
    @abstractmethod
    async def get_pending_for_tenant(self, tenant_id: TenantId) -> List[ReturnDraft]:
        """Get pending drafts for admin review"""
        pass
    
    @abstractmethod
    async def delete(self, draft_id: str, tenant_id: TenantId) -> None:
        """Delete draft after conversion to return"""
        pass


class OrderRepository(ABC):
    """Port for order data access"""
    
    @abstractmethod
    async def get_by_id(self, order_id: OrderId, tenant_id: TenantId) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def find_by_number_and_email(
        self, 
        order_number: str, 
        customer_email: Email, 
        tenant_id: TenantId
    ) -> Optional[Dict[str, Any]]:
        """Find order by number and customer email"""
        pass
    
    @abstractmethod
    async def get_eligible_items(self, order_id: OrderId, tenant_id: TenantId) -> List[Dict[str, Any]]:
        """Get items eligible for return from an order"""
        pass