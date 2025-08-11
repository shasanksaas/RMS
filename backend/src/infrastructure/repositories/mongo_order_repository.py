"""
MongoDB implementation of Order Repository
Adapter for order data access using existing orders collection
"""

from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...domain.value_objects import TenantId, OrderId, Email
from ...domain.ports.repositories import OrderRepository


class MongoOrderRepository(OrderRepository):
    """MongoDB implementation of Order Repository"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.orders
    
    async def get_by_id(self, order_id: OrderId, tenant_id: TenantId) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        document = await self.collection.find_one({
            "$or": [
                {"id": order_id.value, "tenant_id": tenant_id.value},
                {"shopify_order_id": order_id.value, "tenant_id": tenant_id.value}
            ]
        })
        
        return document
    
    async def find_by_number_and_email(
        self, 
        order_number: str, 
        customer_email: Email, 
        tenant_id: TenantId
    ) -> Optional[Dict[str, Any]]:
        """Find order by number and customer email"""
        document = await self.collection.find_one({
            "order_number": order_number,
            "customer_email": customer_email.value,
            "tenant_id": tenant_id.value
        })
        
        return document
    
    async def find_by_number(
        self, 
        order_number: str,
        tenant_id: TenantId
    ) -> Optional[Dict[str, Any]]:
        """Find order by number only (ignoring customer email)"""
        document = await self.collection.find_one({
            "order_number": order_number,
            "tenant_id": tenant_id.value
        })
        
        return document
    
    async def get_eligible_items(self, order_id: OrderId, tenant_id: TenantId) -> List[Dict[str, Any]]:
        """Get items eligible for return from an order"""
        order = await self.get_by_id(order_id, tenant_id)
        
        if not order:
            return []
        
        # Extract line items with fulfillment information
        eligible_items = []
        line_items = order.get("line_items", [])
        
        for item in line_items:
            # Only include fulfilled items
            if item.get("fulfillment_status") == "fulfilled":
                eligible_item = {
                    "id": item["id"],
                    "sku": item.get("sku", ""),
                    "title": item.get("title", ""),
                    "variant_title": item.get("variant_title"),
                    "quantity": item["quantity"],
                    "price": item.get("price", 0),
                    "fulfilled_at": item.get("fulfilled_at"),
                    "tags": item.get("tags", []),
                    "product_type": item.get("product_type", ""),
                    "vendor": item.get("vendor", "")
                }
                eligible_items.append(eligible_item)
        
        return eligible_items