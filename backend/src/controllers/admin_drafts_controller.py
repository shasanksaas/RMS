"""
Admin Controller for Managing Return Drafts (Fallback Mode)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ..utils.dependencies import get_tenant_id
from ..config.database import db
from ..services.email_service_advanced import email_service

router = APIRouter(prefix="/admin/returns", tags=["admin", "drafts"])
logger = logging.getLogger(__name__)

@router.get("/pending")
async def get_pending_drafts(
    tenant_id: str = Depends(get_tenant_id),
    page: int = 1,
    page_size: int = 25,
    status: str = "pending_validation"
):
    """Get pending return draft validation requests"""
    try:
        # Build query
        query = {
            "tenant_id": tenant_id,
            "status": status
        }
        
        # Get total count
        total = await db.return_drafts.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        cursor = db.return_drafts.find(query).sort("submitted_at", -1).skip(skip).limit(page_size)
        drafts = await cursor.to_list(page_size)
        
        # Convert ObjectId to string
        for draft in drafts:
            if '_id' in draft:
                draft['_id'] = str(draft['_id'])
        
        return {
            "items": drafts,
            "pagination": {
                "current_page": page,
                "per_page": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next_page": skip + len(drafts) < total,
                "has_prev_page": page > 1
            }
        }
        
    except Exception as e:
        logger.error(f"Get pending drafts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending drafts")

@router.post("/pending/{draft_id}/approve")
async def approve_draft(
    draft_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Approve a pending return draft"""
    try:
        # Find draft
        draft = await db.return_drafts.find_one({
            "id": draft_id,
            "tenant_id": tenant_id,
            "status": "pending_validation"
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Update draft status
        await db.return_drafts.update_one(
            {"id": draft_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "approved",
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": "admin_user",
                    "linked_shopify_order_id": data.get("shopify_order_id")
                }
            }
        )
        
        # Create actual return request
        from ..services.returns_service_advanced import advanced_returns_service
        
        # Convert draft to return request format
        return_data = {
            "order_id": data.get("order_id", f"manual-{draft['order_number']}"),
            "items": draft.get("items", []),
            "preferred_outcome": "REFUND",
            "return_method": "PREPAID_LABEL",
            "channel": "admin",
            "lookup_mode": "fallback",
            "draft_id": draft_id
        }
        
        result = await advanced_returns_service.create_return_request(tenant_id, return_data)
        
        # Send approval email to customer
        try:
            await email_service.send_draft_approved(tenant_id, draft, result.get("return_id"))
        except Exception as e:
            logger.error(f"Failed to send approval email: {e}")
        
        return {
            "success": True,
            "message": "Draft approved and return request created",
            "return_id": result.get("return_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve draft error: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve draft")

@router.post("/pending/{draft_id}/reject")
async def reject_draft(
    draft_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Reject a pending return draft"""
    try:
        reason = data.get("reason", "Unable to verify order details")
        
        # Find draft
        draft = await db.return_drafts.find_one({
            "id": draft_id,
            "tenant_id": tenant_id,
            "status": "pending_validation"
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Update draft status
        await db.return_drafts.update_one(
            {"id": draft_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "rejected",
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": "admin_user",
                    "rejection_reason": reason
                }
            }
        )
        
        # Send rejection email to customer
        try:
            await email_service.send_draft_rejected(tenant_id, draft, reason)
        except Exception as e:
            logger.error(f"Failed to send rejection email: {e}")
        
        return {
            "success": True,
            "message": "Draft rejected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject draft error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject draft")

@router.post("/pending/{draft_id}/link-shopify")
async def link_draft_to_shopify(
    draft_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Link a draft to a Shopify order and recompute eligibility"""
    try:
        shopify_order_id = data.get("shopify_order_id")
        if not shopify_order_id:
            raise HTTPException(status_code=400, detail="Shopify order ID required")
        
        # Find draft
        draft = await db.return_drafts.find_one({
            "id": draft_id,
            "tenant_id": tenant_id,
            "status": "pending_validation"
        })
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Try to lookup order in Shopify to recompute eligibility
        from ..services.shopify_graphql_enhanced import ShopifyGraphQLService
        
        graphql_service = ShopifyGraphQLService(tenant_id)
        order_data = await graphql_service.lookup_order_by_name_and_email(
            draft["order_number"], 
            draft["email"]
        )
        
        if not order_data:
            raise HTTPException(status_code=404, detail="Order not found in Shopify")
        
        # Update draft with Shopify link
        await db.return_drafts.update_one(
            {"id": draft_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "linked",
                    "linked_shopify_order_id": shopify_order_id,
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": "admin_user",
                    "metadata.shopify_order_data": order_data
                }
            }
        )
        
        return {
            "success": True,
            "message": "Draft linked to Shopify order successfully",
            "order_data": order_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link draft to Shopify error: {e}")
        raise HTTPException(status_code=500, detail="Failed to link draft to Shopify")