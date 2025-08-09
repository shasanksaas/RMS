"""
Tenant controller - handles tenant-related HTTP endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models import Tenant, TenantCreate, TenantUpdate, TenantSettings
from ..services.tenant.service import TenantService
from ..utils.dependencies import get_tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=Tenant)
async def create_tenant(
    tenant_data: TenantCreate,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant"""
    return await tenant_service.create_tenant(tenant_data)


@router.get("/", response_model=List[Tenant])
async def get_tenants(
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get all active tenants"""
    return await tenant_service.get_all_tenants()


@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by ID"""
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant information"""
    tenant = await tenant_service.update_tenant(tenant_id, update_data)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}/settings", response_model=Tenant)
async def update_tenant_settings(
    tenant_id: str,
    settings: TenantSettings,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant settings"""
    tenant = await tenant_service.update_tenant_settings(tenant_id, settings)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.delete("/{tenant_id}")
async def deactivate_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Deactivate a tenant"""
    success = await tenant_service.deactivate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deactivated successfully"}