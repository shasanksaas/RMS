"""
Customer Portal Returns Controller
Handles customer-facing return requests
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..services.returns_service_advanced import advanced_returns_service
from ..utils.dependencies import get_tenant_id_optional
from ..middleware.security import rate_limit_by_ip
from ..database import db

router = APIRouter(prefix="/portal/returns", tags=["portal", "returns"])
logger = logging.getLogger(__name__)

@router.post("/lookup-order")
@rate_limit_by_ip(max_requests=10, window_minutes=5)
async def lookup_order(
    request: Request,
    data: Dict[str, Any],
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """
    Lookup order for return eligibility
    Rate limited to prevent abuse
    """
    try:
        # Extract shop domain from request if no tenant_id
        if not tenant_id:
            # Try to determine tenant from order number or other means
            # For now, default to a guest flow
            tenant_id = "tenant-guest"
        
        order_number = data.get("orderNumber", "").strip()
        email = data.get("email", "").strip().lower()
        
        if not order_number or not email:
            raise HTTPException(status_code=400, detail="Order number and email are required")
        
        # Lookup order and get eligibility
        result = await advanced_returns_service.lookup_order(tenant_id, order_number, email)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order lookup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to lookup order")

@router.post("/create")
async def create_return_request(
    data: Dict[str, Any],
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """Create a new return request from customer portal"""
    try:
        if not tenant_id:
            tenant_id = "tenant-guest"
        
        # Validate required fields
        required_fields = ["order_id", "items", "preferred_outcome", "return_method"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Add channel info
        data["channel"] = "customer"
        
        # Create return request
        result = await advanced_returns_service.create_return_request(tenant_id, data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create return request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create return request")

@router.post("/policy-preview")
async def get_policy_preview(
    data: Dict[str, Any],
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """Get policy preview for return request"""
    try:
        if not tenant_id:
            tenant_id = "tenant-guest"
        
        result = await advanced_returns_service.preview_policy(
            tenant_id,
            data.get("order_id"),
            data.get("items", []),
            data.get("preferred_outcome", "REFUND"),
            data.get("return_method", "PREPAID_LABEL")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Policy preview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview policy")

@router.get("/status/{return_id}")
async def get_return_status(
    return_id: str,
    email: str,
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """Get return status - customer can check with email verification"""
    try:
        if not tenant_id:
            tenant_id = "tenant-guest"
        
        # Find return and verify email matches
        return_request = await db.return_requests.find_one({
            "id": return_id,
            "tenant_id": tenant_id
        })
        
        if not return_request:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # Get associated order to verify email
        order = await db.orders.find_one({
            "id": return_request["order_id"],
            "tenant_id": tenant_id,
            "customer_email": email.lower()
        })
        
        if not order:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "return_id": return_id,
            "status": return_request["status"],
            "created_at": return_request["created_at"],
            "estimated_refund": return_request["estimated_refund_amount"],
            "tracking": return_request.get("tracking"),
            "audit_log": [
                {
                    "action": entry["action"],
                    "at": entry["at"],
                    "details": entry.get("details", {})
                } for entry in return_request.get("audit_log", [])
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get return status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get return status")