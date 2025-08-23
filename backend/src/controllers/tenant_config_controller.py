"""
Tenant Configuration Controller
Manages tenant-specific branding, policies, and return form configurations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import logging

from ..middleware.tenant_isolation import get_tenant_from_request
from ..config.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["Tenant Configuration"])

@router.get("/{tenant_id}/config")
async def get_tenant_config(
    tenant_id: str,
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Get tenant-specific configuration for return forms"""
    try:
        # Security: Ensure tenant can only access their own config
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Fetch tenant configuration from database
        tenant = await db.tenants.find_one({"tenant_id": tenant_id})
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Return tenant configuration
        config = {
            "tenant_id": tenant_id,
            "name": tenant.get("name", tenant_id.replace("tenant-", "").title()),
            "primaryColor": tenant.get("branding", {}).get("primary_color", "#3B82F6"),
            "secondaryColor": tenant.get("branding", {}).get("secondary_color", "#1F2937"),
            "logoUrl": tenant.get("branding", {}).get("logo_url"),
            "faviconUrl": tenant.get("branding", {}).get("favicon_url"),
            "supportEmail": tenant.get("contact", {}).get("support_email", "support@example.com"),
            "supportPhone": tenant.get("contact", {}).get("support_phone"),
            "returnPolicy": tenant.get("policies", {}).get("return_policy_text", "Standard 30-day return policy applies."),
            "exchangePolicy": tenant.get("policies", {}).get("exchange_policy_text", "Exchanges available within return window."),
            "shippingInfo": tenant.get("policies", {}).get("shipping_info", "Free return shipping on all orders."),
            "customCss": tenant.get("branding", {}).get("custom_css"),
            "formSettings": {
                "show_photos": tenant.get("form_settings", {}).get("show_photo_upload", True),
                "require_reason": tenant.get("form_settings", {}).get("require_return_reason", True),
                "show_condition": tenant.get("form_settings", {}).get("show_item_condition", True),
                "enable_exchanges": tenant.get("form_settings", {}).get("enable_exchanges", True),
                "enable_store_credit": tenant.get("form_settings", {}).get("enable_store_credit", True),
                "store_credit_bonus": tenant.get("form_settings", {}).get("store_credit_bonus_percent", 10)
            }
        }
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get tenant config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tenant configuration")

@router.put("/{tenant_id}/config")
async def update_tenant_config(
    tenant_id: str,
    config_data: Dict[str, Any],
    current_tenant_id: str = Depends(get_tenant_from_request)
):
    """Update tenant-specific configuration"""
    try:
        # Security: Ensure tenant can only update their own config
        if tenant_id != current_tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update tenant configuration
        update_data = {
            "branding": {
                "primary_color": config_data.get("primaryColor"),
                "secondary_color": config_data.get("secondaryColor"), 
                "logo_url": config_data.get("logoUrl"),
                "favicon_url": config_data.get("faviconUrl"),
                "custom_css": config_data.get("customCss")
            },
            "contact": {
                "support_email": config_data.get("supportEmail"),
                "support_phone": config_data.get("supportPhone")
            },
            "policies": {
                "return_policy_text": config_data.get("returnPolicy"),
                "exchange_policy_text": config_data.get("exchangePolicy"),
                "shipping_info": config_data.get("shippingInfo")
            },
            "form_settings": config_data.get("formSettings", {}),
            "updated_at": {"$currentDate": True}
        }
        
        # Remove None values
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items() if v is not None}
            return d
        
        cleaned_update = clean_dict(update_data)
        
        result = await db.tenants.update_one(
            {"tenant_id": tenant_id},
            {"$set": cleaned_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"success": True, "message": "Configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update tenant config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant configuration")

# Get available tenants for form generation
@router.get("/")
async def get_tenants():
    """Get list of available tenants for form generation"""
    try:
        tenants = []
        async for tenant in db.tenants.find({}, {"tenant_id": 1, "name": 1, "shop": 1}):
            tenants.append({
                "tenant_id": tenant["tenant_id"],
                "name": tenant.get("name", tenant["tenant_id"]),
                "shop": tenant.get("shop"),
                "form_url": f"/returns/{tenant['tenant_id']}/start"
            })
        
        return {
            "tenants": tenants,
            "total_count": len(tenants)
        }
        
    except Exception as e:
        logger.error(f"Get tenants error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tenants")