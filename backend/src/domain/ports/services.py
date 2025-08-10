"""
Service Port Definitions
Interfaces for external services
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..value_objects import TenantId, Email, PolicySnapshot, Money, ShippingLabel, Address
from ..entities.return_entity import Return


class ShopifyService(ABC):
    """Port for Shopify integration"""
    
    @abstractmethod
    async def is_connected(self, tenant_id: TenantId) -> bool:
        """Check if tenant has valid Shopify connection"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, tenant_id: TenantId) -> Optional[Dict[str, Any]]:
        """Get order from Shopify"""
        pass
    
    @abstractmethod
    async def find_order_by_number(
        self, 
        order_number: str, 
        tenant_id: TenantId
    ) -> Optional[Dict[str, Any]]:
        """Find order by number"""
        pass
    
    @abstractmethod
    async def create_return(
        self, 
        return_obj: Return, 
        tenant_id: TenantId
    ) -> Dict[str, Any]:
        """Create return in Shopify"""
        pass
    
    @abstractmethod
    async def process_refund(
        self, 
        return_obj: Return, 
        tenant_id: TenantId
    ) -> Dict[str, Any]:
        """Process refund via Shopify"""
        pass


class LabelService(ABC):
    """Port for shipping label generation"""
    
    @abstractmethod
    async def generate_return_label(
        self,
        return_obj: Return,
        from_address: Address,
        to_address: Address
    ) -> ShippingLabel:
        """Generate return shipping label"""
        pass
    
    @abstractmethod
    async def get_label_cost(
        self,
        from_address: Address,
        to_address: Address,
        service_type: str = "ground"
    ) -> Money:
        """Get estimated label cost"""
        pass


class NotificationService(ABC):
    """Port for sending notifications"""
    
    @abstractmethod
    async def send_return_requested_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId
    ) -> bool:
        """Send notification when return is requested"""
        pass
    
    @abstractmethod
    async def send_return_approved_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId,
        label_url: Optional[str] = None
    ) -> bool:
        """Send notification when return is approved"""
        pass
    
    @abstractmethod
    async def send_return_declined_notification(
        self,
        return_obj: Return,
        tenant_id: TenantId,
        reason: str
    ) -> bool:
        """Send notification when return is declined"""
        pass


class PolicyService(ABC):
    """Port for policy management"""
    
    @abstractmethod
    async def get_current_policy(self, tenant_id: TenantId) -> PolicySnapshot:
        """Get current return policy for tenant"""
        pass
    
    @abstractmethod
    async def get_policy_at_date(
        self, 
        tenant_id: TenantId, 
        date: datetime
    ) -> PolicySnapshot:
        """Get policy that was active at specific date"""
        pass


class EventPublisher(ABC):
    """Port for publishing domain events"""
    
    @abstractmethod
    async def publish(self, event: Any) -> None:
        """Publish a single domain event"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[Any]) -> None:
        """Publish multiple domain events"""
        pass