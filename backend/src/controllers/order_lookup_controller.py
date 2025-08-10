"""
Enhanced Order Lookup Controller
Handles both Shopify and fallback modes
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from ..services.shopify_graphql_enhanced import ShopifyGraphQLService
from ..utils.dependencies import get_tenant_id_optional
from ..config.database import db

router = APIRouter(prefix="/returns", tags=["returns", "lookup"])
logger = logging.getLogger(__name__)

@router.post("/order-lookup")
async def order_lookup(
    request_data: Dict[str, Any],
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """
    Enhanced order lookup with Shopify and fallback modes
    """
    try:
        # Extract data from request
        order_number = request_data.get("orderNumber") or request_data.get("order_number", "")
        email = request_data.get("email", "")
        channel = request_data.get("channel", "customer")
        
        # Determine tenant (can be from header or inferred)
        if not tenant_id and request_data.get("shop_domain"):
            # Try to resolve tenant by shop domain
            integration = await db.integrations_shopify.find_one({
                "shop": request_data["shop_domain"].replace("https://", "").replace("http://", "")
            })
            if integration:
                tenant_id = integration["tenant_id"]
        
        if not tenant_id:
            tenant_id = "tenant-rms34"  # Default for testing
        
        # Clean inputs
        order_number = order_number.replace("#", "").strip()
        email = email.lower().strip()
        
        if not order_number or not email:
            raise HTTPException(status_code=400, detail="Order number and email are required")
        
        # Check if tenant has Shopify integration
        integration = await db.integrations_shopify.find_one({
            "tenant_id": tenant_id,
            "status": "connected"
        })
        
        if integration:
            # Shopify mode - try to fetch order from Shopify
            logger.info(f"Using Shopify mode for tenant {tenant_id}")
            
            graphql_service = ShopifyGraphQLService(tenant_id)
            order_data = await graphql_service.lookup_order_by_name_and_email(order_number, email)
            
            if order_data:
                # Successfully found order in Shopify
                return {
                    "mode": "shopify",
                    "order": order_data
                }
            else:
                # Order not found in Shopify or email mismatch
                raise HTTPException(
                    status_code=404, 
                    detail="ORDER_NOT_FOUND_OR_EMAIL_MISMATCH"
                )
        
        else:
            # Fallback mode - store request for manual validation
            logger.info(f"Using fallback mode for tenant {tenant_id}")
            
            # Check if we already have a draft for this order/email combo
            existing_draft = await db.return_drafts.find_one({
                "tenant_id": tenant_id,
                "order_number": order_number,
                "email": email,
                "status": "pending_validation"
            })
            
            if existing_draft:
                # Return existing draft info
                return {
                    "mode": "fallback",
                    "status": "pending_validation",
                    "message": "We already received your request for this order. It's under review.",
                    "captured": {
                        "orderNumber": order_number,
                        "email": email,
                        "submittedAt": existing_draft["submitted_at"]
                    }
                }
            
            # Create new draft record
            draft_doc = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "order_number": order_number,
                "email": email,
                "channel": channel,
                "items": [],
                "photos": [],
                "status": "pending_validation",
                "submitted_at": datetime.utcnow(),
                "reviewed_at": None,
                "reviewed_by": None,
                "linked_shopify_order_id": None,
                "rejection_reason": None,
                "customer_note": "",
                "metadata": {}
            }
            
            # Save to database
            await db.return_drafts.insert_one(draft_doc)
            
            return {
                "mode": "fallback",
                "status": "pending_validation",
                "message": "Store not connected to Shopify. Your request will be reviewed within 24 hours.",
                "captured": {
                    "orderNumber": order_number,
                    "email": email,
                    "submittedAt": draft_doc["submitted_at"]
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order lookup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process order lookup")

@router.post("/policy-preview")
async def policy_preview(
    data: Dict[str, Any],
    tenant_id: Optional[str] = Depends(get_tenant_id_optional)
):
    """
    Get policy preview for return request
    """
    try:
        if not tenant_id:
            tenant_id = "tenant-guest"
        
        # Basic policy preview implementation
        items = data.get("items", [])
        order_meta = data.get("orderMeta", {})
        
        # Calculate basic estimates
        total_value = sum(
            float(item.get("price", 0)) * item.get("quantity", 1) 
            for item in items
        )
        
        # Basic fee calculation (10% restocking + $5 shipping)
        restocking_fee = total_value * 0.10
        shipping_fee = 5.00 if total_value < 100 else 0.00  # Free over $100
        total_fees = restocking_fee + shipping_fee
        
        estimated_refund = max(0, total_value - total_fees)
        
        return {
            "success": True,
            "eligible": True,
            "fees": [
                {"type": "RESTOCK", "amount": restocking_fee, "description": "Restocking fee (10%)"},
                {"type": "SHIPPING", "amount": shipping_fee, "description": "Return shipping"}
            ],
            "estimatedRefund": estimated_refund,
            "totalItemValue": total_value,
            "returnWindow": {
                "daysRemaining": 25,  # Mock value
                "eligible": True
            }
        }
        
    except Exception as e:
        logger.error(f"Policy preview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate policy preview")