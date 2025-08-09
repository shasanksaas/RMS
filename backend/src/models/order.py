"""
Order model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class OrderItem(BaseModel):
    """Order item model"""
    product_id: str
    product_name: str
    quantity: int
    price: float
    sku: str


class Order(BaseModel):
    """Order model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    shopify_order_id: Optional[str] = None
    customer_email: str
    customer_name: str
    order_number: str
    items: List[OrderItem]
    total_amount: float
    order_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderCreate(BaseModel):
    """Schema for creating a new order"""
    customer_email: str
    customer_name: str
    order_number: str
    items: List[OrderItem]
    total_amount: float
    order_date: datetime