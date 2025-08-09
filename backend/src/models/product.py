"""
Product model definitions and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Product(BaseModel):
    """Product model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    shopify_product_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    sku: str
    in_stock: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: str
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: Optional[bool] = None