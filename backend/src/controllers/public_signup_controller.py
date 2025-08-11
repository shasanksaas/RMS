"""
Public Merchant Signup Controller
Handles merchant signup with tenant validation - No authentication required
"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any
import logging

from ..models.tenant import TenantMerchantSignup
from ..services.tenant_service_enhanced import enhanced_tenant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["public-auth"])

@router.post("/merchant-signup", status_code=status.HTTP_201_CREATED)
async def merchant_signup(
    signup_data: TenantMerchantSignup,
    request: Request
):
    """
    Public merchant signup with tenant validation
    
    Allows merchants to join a tenant using tenant_id.
    Creates merchant user and claims tenant on first signup.
    Returns JWT token for immediate login.
    """
    try:
        # Get client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Process merchant signup
        response_data, is_first_merchant = await enhanced_tenant_service.merchant_signup(signup_data)
        
        logger.info(f"Merchant signup successful: {signup_data.email} -> {signup_data.tenant_id} (first: {is_first_merchant})")
        
        return {
            "success": True,
            "message": "Account created successfully" + (" and tenant claimed" if is_first_merchant else ""),
            "data": response_data,
            "is_first_merchant": is_first_merchant,
            "tenant_id": signup_data.tenant_id,
            "redirect_url": "/app/onboarding" if is_first_merchant else "/app/dashboard"
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Merchant signup failed for {signup_data.email}: {error_msg}")
        
        # Return specific error messages for better UX
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant ID not found. Please check the Tenant ID and try again."
            )
        elif "no longer active" in error_msg.lower() or "archived" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This tenant is no longer accepting new signups. Please contact support."
            )
        elif "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please use a different email or try logging in."
            )
        elif "password" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password requirements not met. Please ensure passwords match and meet security requirements."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except Exception as e:
        logger.error(f"Unexpected error during merchant signup for {signup_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account creation failed. Please try again or contact support."
        )

@router.get("/tenant-status/{tenant_id}")
async def check_tenant_status(tenant_id: str):
    """
    Check if a tenant ID is valid and accepts signups
    
    Public endpoint to validate tenant_id before signup form submission.
    Returns tenant status and signup eligibility.
    """
    try:
        tenant = await enhanced_tenant_service.get_tenant_by_id(tenant_id)
        
        if not tenant:
            return {
                "valid": False,
                "available": False,
                "message": "Tenant ID not found"
            }
        
        # Check if tenant accepts signups
        signup_available = tenant.status in ["new", "claimed", "active"]
        
        return {
            "valid": True,
            "available": signup_available,
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "status": tenant.status,
            "message": "Tenant found and available" if signup_available else "Tenant not accepting signups"
        }
        
    except Exception as e:
        logger.error(f"Failed to check tenant status for {tenant_id}: {e}")
        return {
            "valid": False,
            "available": False,
            "message": "Unable to verify tenant status"
        }

@router.get("/signup-info/{tenant_id}")
async def get_signup_info(tenant_id: str):
    """
    Get tenant information for signup page customization
    
    Returns tenant details that can be used to customize
    the signup page with tenant-specific branding or information.
    """
    try:
        tenant = await enhanced_tenant_service.get_tenant_by_id(tenant_id)
        
        if not tenant or tenant.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found or not available"
            )
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "signup_enabled": tenant.status in ["new", "claimed", "active"],
            "store_name": tenant.settings.get("store_name"),
            "custom_message": tenant.settings.get("signup_message"),
            "branding": tenant.settings.get("branding", {}),
            "features": tenant.settings.get("features", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get signup info for {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve signup information"
        )