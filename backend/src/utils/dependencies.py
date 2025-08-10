"""
FastAPI Dependencies
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> str:
    """Get tenant ID from header (required)"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header is required")
    return x_tenant_id

async def get_tenant_id_optional(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id")) -> Optional[str]:
    """Get tenant ID from header (optional)"""
    return x_tenant_id

async def get_shopify_service():
    """Get Shopify service instance"""
    from ..services.shopify_service import ShopifyService
    return ShopifyService()

async def get_tenant_service():
    """Get Tenant service instance"""
    from ..services.tenant_service import TenantService
    return TenantService()

async def rate_limit_by_ip(max_requests: int = 10, window_minutes: int = 5):
    """Rate limiting decorator (placeholder)"""
    # TODO: Implement proper rate limiting with Redis
    pass