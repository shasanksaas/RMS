"""
Admin Returns Controller
Handles admin processing of returns
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ..services.returns_service_advanced import advanced_returns_service
from ..utils.dependencies import get_tenant_id
from ..config.database import db

router = APIRouter(prefix="/returns", tags=["admin", "returns"])
logger = logging.getLogger(__name__)

@router.get("")
async def get_returns(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = None,
    q: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 25
):
    """Get returns list with filtering and pagination"""
    try:
        # Build query
        query = {"tenant_id": tenant_id}
        
        if status and status != "all":
            query["status"] = status.upper()
        
        if q:
            # Search in return ID, order number, customer email
            query["$or"] = [
                {"id": {"$regex": q, "$options": "i"}},
                {"order_number": {"$regex": q, "$options": "i"}},
                {"customer_email": {"$regex": q, "$options": "i"}}
            ]
        
        if from_date:
            query["created_at"] = {"$gte": from_date}
        if to_date:
            if "created_at" in query:
                query["created_at"]["$lte"] = to_date
            else:
                query["created_at"] = {"$lte": to_date}
        
        # Get total count
        total = await db.return_requests.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        cursor = db.return_requests.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        returns = await cursor.to_list(page_size)
        
        # Convert ObjectId to string
        for ret in returns:
            if '_id' in ret:
                ret['_id'] = str(ret['_id'])
        
        return {
            "items": returns,
            "pagination": {
                "current_page": page,
                "per_page": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next_page": skip + len(returns) < total,
                "has_prev_page": page > 1
            }
        }
        
    except Exception as e:
        logger.error(f"Get returns error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get returns")

@router.get("/{return_id}")
async def get_return_detail(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get detailed return information"""
    try:
        return_request = await db.return_requests.find_one({
            "id": return_id,
            "tenant_id": tenant_id
        })
        
        if not return_request:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # Get associated order
        order = await db.orders.find_one({
            "id": return_request["order_id"],
            "tenant_id": tenant_id
        })
        
        # Get shipping labels
        labels = await db.shipping_labels.find({
            "return_request_id": return_id,
            "tenant_id": tenant_id
        }).to_list(None)
        
        # Convert ObjectIds
        if '_id' in return_request:
            return_request['_id'] = str(return_request['_id'])
        for label in labels:
            if '_id' in label:
                label['_id'] = str(label['_id'])
        
        return {
            "return_request": return_request,
            "order": order,
            "shipping_labels": labels
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get return detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get return details")

@router.post("/{return_id}/approve")
async def approve_return(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Approve a return request"""
    try:
        # Check idempotency
        if idempotency_key:
            existing = await db.idempotency_keys.find_one({
                "key": idempotency_key,
                "tenant_id": tenant_id
            })
            if existing:
                return existing["response"]
        
        result = await advanced_returns_service.approve_return(tenant_id, return_id, "admin_user")
        
        # Store idempotency result
        if idempotency_key:
            await db.idempotency_keys.insert_one({
                "key": idempotency_key,
                "tenant_id": tenant_id,
                "response": result,
                "created_at": datetime.utcnow()
            })
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve return error: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve return")

@router.post("/{return_id}/decline")
async def decline_return(
    return_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Decline a return request"""
    try:
        reason = data.get("reason", "No reason provided")
        
        # Check idempotency
        if idempotency_key:
            existing = await db.idempotency_keys.find_one({
                "key": idempotency_key,
                "tenant_id": tenant_id
            })
            if existing:
                return existing["response"]
        
        result = await advanced_returns_service.decline_return(tenant_id, return_id, "admin_user", reason)
        
        # Store idempotency result
        if idempotency_key:
            await db.idempotency_keys.insert_one({
                "key": idempotency_key,
                "tenant_id": tenant_id,
                "response": result,
                "created_at": datetime.utcnow()
            })
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decline return error: {e}")
        raise HTTPException(status_code=500, detail="Failed to decline return")

@router.post("/{return_id}/generate-label")
async def generate_label(
    return_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Generate shipping label for return"""
    try:
        result = await advanced_returns_service.generate_label(tenant_id, return_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate label error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate label")

@router.post("/{return_id}/process-refund")
async def process_refund(
    return_id: str,
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Process refund for return"""
    try:
        amount = data.get("amount")
        method = data.get("method", "ORIGINAL")
        
        if not amount:
            raise HTTPException(status_code=400, detail="Refund amount is required")
        
        result = await advanced_returns_service.process_refund(
            tenant_id, return_id, float(amount), method, "admin_user"
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process refund error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")

@router.post("/policy/preview")
async def preview_policy(
    data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """Preview policy decisions for given return scenario"""
    try:
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