"""
Shopify Service Adapter
Concrete implementation using existing Shopify service
"""

from typing import Optional, Dict, Any
from ...domain.value_objects import TenantId
from ...domain.entities.return_entity import Return
from ...domain.ports.services import ShopifyService as ShopifyServicePort
from ...services.shopify_service import ShopifyService as ExistingShopifyService


class ShopifyServiceAdapter(ShopifyServicePort):
    """Adapter for existing Shopify service"""
    
    def __init__(self, shopify_service: ExistingShopifyService):
        self.shopify_service = shopify_service
    
    async def is_connected(self, tenant_id: TenantId) -> bool:
        """Check if tenant has valid Shopify connection"""
        return await self.shopify_service.is_connected(tenant_id.value)
    
    async def get_order(self, order_id: str, tenant_id: TenantId) -> Optional[Dict[str, Any]]:
        """Get order from Shopify"""
        return await self.shopify_service.get_order(order_id, tenant_id.value)
    
    async def find_order_by_number(
        self, 
        order_number: str, 
        tenant_id: TenantId
    ) -> Optional[Dict[str, Any]]:
        """Find order by number"""
        return await self.shopify_service.find_order_by_number(order_number, tenant_id.value)
    
    async def create_return(
        self, 
        return_obj: Return, 
        tenant_id: TenantId
    ) -> Dict[str, Any]:
        """Create return in Shopify"""
        # This would implement the GraphQL return creation
        # For now, return a mock response
        return {
            "shopify_return_id": f"return_{return_obj.id.value}",
            "status": "success"
        }
    
    async def process_refund(
        self, 
        return_obj: Return, 
        tenant_id: TenantId
    ) -> Dict[str, Any]:
        """Process refund via Shopify"""
        # This would implement the GraphQL refund processing
        # For now, return a mock response
        return {
            "refund_id": f"refund_{return_obj.id.value}",
            "amount": float(return_obj.estimated_refund.amount),
            "status": "success"
        }
    
    async def get_order_for_return(self, order_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID for return creation - delegates to underlying service"""
        return await self.shopify_service.get_order_for_return(order_id, tenant_id)