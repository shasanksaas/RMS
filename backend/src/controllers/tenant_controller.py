"""
Tenant Management Controller - Admin-only Multi-tenancy APIs
Provides comprehensive tenant management with strict RBAC
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
import logging

from ..models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantStatus, 
    TenantListResponse, TenantMerchantSignup, TenantConnection
)
from ..models.user import User
from ..middleware.security import get_current_user, require_admin_user
from ..services.tenant_service_enhanced import enhanced_tenant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["tenant-management"])

@router.post("/", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(require_admin_user)
):
    """
    Create a new tenant - Admin only
    
    Creates a new tenant with unique tenant_id and proper initialization.
    Returns the complete tenant object including generated tenant_id.
    """
    try:
        tenant = await enhanced_tenant_service.create_tenant(
            tenant_data, 
            str(current_user.user_id)
        )
        
        logger.info(f"Admin {current_user.email} created tenant {tenant.tenant_id}")
        
        return tenant
        
    except ValueError as e:
        logger.warning(f"Tenant creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )

@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[TenantStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_admin_user)
):
    """
    List all tenants with pagination - Admin only
    
    Returns paginated list of all tenants with basic stats and metadata.
    Supports filtering by status and pagination controls.
    """
    try:
        tenant_list = await enhanced_tenant_service.list_tenants(
            page=page, 
            page_size=page_size, 
            status=status
        )
        
        logger.info(f"Admin {current_user.email} listed tenants (page {page})")
        
        return tenant_list
        
    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenants"
        )

@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant_detail(
    tenant_id: str,
    current_user: User = Depends(require_admin_user)
):
    """
    Get detailed tenant information - Admin only
    
    Returns comprehensive tenant details including stats, integrations,
    and metadata for administrative purposes.
    """
    try:
        tenant = await enhanced_tenant_service.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.info(f"Admin {current_user.email} viewed tenant {tenant_id}")
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant"
        )

@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    current_user: User = Depends(require_admin_user)
):
    """
    Update tenant information - Admin only
    
    Updates tenant metadata such as name, notes, and status.
    Provides audit trail of administrative changes.
    """
    try:
        tenant = await enhanced_tenant_service.update_tenant(tenant_id, update_data)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.info(f"Admin {current_user.email} updated tenant {tenant_id}")
        
        return tenant
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Tenant update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant"
        )

@router.post("/{tenant_id}/archive")
async def archive_tenant(
    tenant_id: str,
    current_user: User = Depends(require_admin_user)
):
    """
    Archive a tenant - Admin only
    
    Soft-deletes a tenant by setting status to 'archived'.
    Prevents new signups and marks tenant as inactive.
    """
    try:
        success = await enhanced_tenant_service.archive_tenant(
            tenant_id, 
            str(current_user.user_id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found or already archived"
            )
        
        logger.info(f"Admin {current_user.email} archived tenant {tenant_id}")
        
        return {
            "success": True,
            "message": f"Tenant {tenant_id} has been archived",
            "tenant_id": tenant_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive tenant"
        )

@router.get("/{tenant_id}/connection", response_model=TenantConnection)
async def get_tenant_connection_status(
    tenant_id: str,
    current_user: User = Depends(require_admin_user)
):
    """
    Get tenant's integration connection status - Admin only
    
    Returns detailed information about tenant's Shopify and other
    service integrations, connection health, and available features.
    """
    try:
        connection_status = await enhanced_tenant_service.get_tenant_integration_status(tenant_id)
        
        logger.info(f"Admin {current_user.email} checked connection for tenant {tenant_id}")
        
        return connection_status
        
    except Exception as e:
        logger.error(f"Failed to get connection status for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection status"
        )

@router.post("/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(require_admin_user)
):
    """
    Reactivate an archived tenant - Admin only
    
    Changes tenant status from 'archived' back to 'active',
    allowing normal operations to resume.
    """
    try:
        # Update tenant status to active
        update_data = TenantUpdate(status=TenantStatus.ACTIVE)
        tenant = await enhanced_tenant_service.update_tenant(tenant_id, update_data)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.info(f"Admin {current_user.email} reactivated tenant {tenant_id}")
        
        return {
            "success": True,
            "message": f"Tenant {tenant_id} has been reactivated",
            "tenant_id": tenant_id,
            "status": tenant.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate tenant"
        )

# Tenant stats and analytics endpoints
@router.get("/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    current_user: User = Depends(require_admin_user)
):
    """
    Get tenant statistics and metrics - Admin only
    
    Returns comprehensive analytics and usage statistics
    for administrative monitoring and insights.
    """
    try:
        tenant = await enhanced_tenant_service.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Get connection status for additional context
        connection_status = await enhanced_tenant_service.get_tenant_integration_status(tenant_id)
        
        stats = {
            "tenant_id": tenant_id,
            "basic_stats": tenant.stats.dict(),
            "connection_status": {
                "connected": connection_status.connected,
                "shop_domain": connection_status.shop_domain,
                "last_sync": connection_status.last_sync,
                "features_available": connection_status.features_available
            },
            "tenant_info": {
                "name": tenant.name,
                "status": tenant.status,
                "created_at": tenant.created_at,
                "claimed_at": tenant.claimed_at,
                "last_activity_at": tenant.last_activity_at
            }
        }
        
        logger.info(f"Admin {current_user.email} viewed stats for tenant {tenant_id}")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant stats {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant statistics"
        )