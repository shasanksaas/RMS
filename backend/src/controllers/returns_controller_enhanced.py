"""
Enhanced Returns Controller with Real Shopify Data
Provides server-side filtering, search, and pagination for returns
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

from src.middleware.security import get_tenant_id
from src.config.database import db

router = APIRouter(prefix="/returns", tags=["returns"])


@router.get("/")
async def get_returns(
    tenant_id: str = Depends(get_tenant_id),
    search: Optional[str] = Query(None, description="Search in order number, customer email, or return ID"),
    status: Optional[str] = Query(None, description="Return status filter"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date filter (ISO format)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date filter (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize", description="Items per page"),
    sort: str = Query("-created_at", description="Sort field and direction")
):
    """
    Get returns with server-side filtering, search, and pagination
    """
    try:
        # Build query
        query = {"tenant_id": tenant_id}
        
        # Search filter
        if search:
            search_regex = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"id": search_regex},
                {"order_number": search_regex},
                {"customer_email": search_regex},
                {"customer_name": search_regex}
            ]
        
        # Status filter
        if status:
            query["status"] = status.lower()
        
        # Date range filters
        if from_date or to_date:
            date_filter = {}
            if from_date:
                try:
                    from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    date_filter["$gte"] = from_datetime
                except ValueError:
                    date_filter["$gte"] = from_date
            if to_date:
                try:
                    to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                    date_filter["$lte"] = to_datetime
                except ValueError:
                    date_filter["$lte"] = to_date
            query["created_at"] = date_filter
        
        # Parse sort parameter
        sort_field = sort.lstrip("-+")
        sort_direction = -1 if sort.startswith("-") else 1
        
        # Count total documents
        total = await db.returns.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        # Get returns
        cursor = db.returns.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
        returns = await cursor.to_list(page_size)
        
        # Format returns for response
        formatted_returns = []
        for return_req in returns:
            # Count items from line_items
            line_items = return_req.get("line_items", [])
            item_count = sum(item.get("quantity", 0) for item in line_items)
            
            # Get order number from related order
            order = await db.orders.find_one({
                "id": return_req.get("order_id", ""),
                "tenant_id": tenant_id
            }) if return_req.get("order_id") else None
            
            # Extract estimated refund amount
            estimated_refund_data = return_req.get("estimated_refund", {})
            if isinstance(estimated_refund_data, dict):
                estimated_refund = float(estimated_refund_data.get("amount", 0))
            else:
                estimated_refund = float(estimated_refund_data) if estimated_refund_data else 0
            
            # Format created_at
            created_at = return_req.get("created_at")
            if isinstance(created_at, datetime):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = created_at or ""
            
            # Format updated_at
            updated_at = return_req.get("updated_at")
            if isinstance(updated_at, datetime):
                updated_at_str = updated_at.isoformat()
            else:
                updated_at_str = updated_at or ""
            
            # Get customer name from order or derive from email
            customer_name = ""
            customer_email = return_req.get("customer_email", "")
            if order and order.get("customer"):
                customer_data = order.get("customer", {})
                if isinstance(customer_data, dict):
                    customer_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()
                    if not customer_name and customer_data.get('name'):
                        customer_name = customer_data.get('name', '')
                else:
                    customer_name = str(customer_data) if customer_data else ""
            
            # If no customer name from order, extract from email
            if not customer_name and customer_email:
                customer_name = customer_email.split('@')[0].replace('.', ' ').title()
            
            formatted_returns.append({
                "id": return_req["id"],
                "order_number": order.get("order_number", "") if order else "",
                "order_id": return_req.get("order_id", ""),
                "customer_name": customer_name,
                "customer_email": customer_email,
                "status": return_req.get("status", "").upper(),
                "decision": return_req.get("decision", ""),
                "item_count": item_count,
                "estimated_refund": estimated_refund,
                "created_at": created_at_str,
                "updated_at": updated_at_str
            })
        
        return {
            "returns": formatted_returns,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasNext": page < total_pages,
                "hasPrev": page > 1
            },
            "filters": {
                "search": search,
                "status": status,
                "from": from_date,
                "to": to_date,
                "sort": sort
            }
        }
        
    except Exception as e:
        print(f"Error getting returns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get returns")


@router.get("/{return_id}")
async def get_return_detail(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get detailed return information by ID
    """
    try:
        # Find return
        return_req = await db.returns.find_one({
            "id": return_id,
            "tenant_id": tenant_id
        })
        
        if not return_req:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # Get related order
        order = await db.orders.find_one({
            "id": return_req.get("order_id", ""),
            "tenant_id": tenant_id
        })
        
        # Format items
        formatted_items = []
        for item in return_req.get("items", []):
            formatted_items.append({
                "fulfillment_line_item_id": item.get("fulfillment_line_item_id"),
                "title": item.get("title", ""),
                "variant_title": item.get("variant_title"),
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": item.get("price", 0),
                "refundable_amount": item.get("refundable_amount", 0),
                "reason": item.get("reason", ""),
                "condition": item.get("condition", ""),
                "photos": item.get("photos", [])
            })
        
        # Build Shopify admin URLs
        tenant = await db.tenants.find_one({"id": tenant_id})
        shop_domain = tenant.get("shopify_store", "") if tenant else ""
        
        shopify_order_url = None
        shopify_return_url = None
        
        if shop_domain and order:
            shopify_order_url = f"https://{shop_domain}/admin/orders/{order.get('shopify_order_id')}"
            # Shopify return URL would be similar if return exists in Shopify
        
        # Format dates
        created_at = return_req.get("created_at")
        updated_at = return_req.get("updated_at")
        
        created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else (created_at or "")
        updated_at_str = updated_at.isoformat() if isinstance(updated_at, datetime) else (updated_at or "")
        
        return {
            "id": return_req["id"],
            "order_id": return_req.get("order_id", ""),
            "order_number": return_req.get("order_number", ""),
            "customer": {
                "name": return_req.get("customer_name", ""),
                "email": return_req.get("customer_email", "")
            },
            "status": return_req.get("status", "").upper(),
            "decision": return_req.get("decision", ""),
            "channel": return_req.get("channel", ""),
            "preferred_outcome": return_req.get("preferred_outcome", ""),
            "return_method": return_req.get("return_method", ""),
            "customer_note": return_req.get("customer_note", ""),
            "admin_override_note": return_req.get("admin_override_note", ""),
            "internal_tags": return_req.get("internal_tags", []),
            "items": formatted_items,
            "fees": return_req.get("fees", {}),
            "estimated_refund": return_req.get("estimated_refund", 0),
            "label_url": return_req.get("label_url"),
            "tracking_number": return_req.get("tracking_number"),
            "policy_version": return_req.get("policy_version", ""),
            "created_at": created_at_str,
            "updated_at": updated_at_str,
            "shopify_order_url": shopify_order_url,
            "shopify_return_url": shopify_return_url,
            "explain_trace": return_req.get("explain_trace", []),
            "order_info": {
                "order_number": order.get("order_number", "") if order else "",
                "total_price": order.get("total_price", 0) if order else 0,
                "currency": order.get("currency", "USD") if order else "USD",
                "created_at": order.get("created_at", "") if order else ""
            } if order else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting return detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get return detail")