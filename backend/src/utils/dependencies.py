"""
FastAPI dependency injection utilities
"""
from fastapi import Header, HTTPException

from ..services.tenant_service import TenantService
from ..services.rules_service import RulesService
from ..services.returns_service import ReturnsService
from ..services.analytics_service import AnalyticsService
from ..services.shopify_service import ShopifyService


async def get_tenant_id(x_tenant_id: str = Header(None)) -> str:
    """Get and validate tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    # Verify tenant exists
    tenant_service = TenantService()
    if not await tenant_service.verify_tenant_exists(x_tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return x_tenant_id


def get_tenant_service() -> TenantService:
    """Get tenant service instance"""
    return TenantService()


def get_rules_service() -> RulesService:
    """Get rules service instance"""
    return RulesService()


def get_returns_service() -> ReturnsService:
    """Get returns service instance"""
    return ReturnsService()


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService()


def get_shopify_service() -> ShopifyService:
    """Get Shopify service instance"""
    return ShopifyService()