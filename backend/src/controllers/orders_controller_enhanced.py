"""
Enhanced Orders Controller with Real Shopify Data
Provides server-side filtering, search, and pagination
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

from src.middleware.security import get_tenant_id
from src.config.database import db

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/")
@router.get("")  # Handle both /orders/ and /orders
async def get_orders(
    tenant_id: str = Depends(get_tenant_id),
    search: Optional[str] = Query(None, description="Search in order number, customer email, or SKU"),
    status: Optional[str] = Query(None, description="Order status filter"),
    status_filter: Optional[str] = Query(None, description="Legacy status filter parameter"),
    financial_status: Optional[str] = Query(None, alias="financialStatus", description="Financial status filter"),
    fulfillment_status: Optional[str] = Query(None, alias="fulfillmentStatus", description="Fulfillment status filter"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date filter (ISO format)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date filter (ISO format)"),
    date_from: Optional[str] = Query(None, description="Legacy date from parameter"),
    date_to: Optional[str] = Query(None, description="Legacy date to parameter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize", description="Items per page"),
    limit: int = Query(None, ge=1, le=100, description="Legacy limit parameter"),
    sort: str = Query("-created_at", description="Sort field and direction"),
    sort_by: Optional[str] = Query(None, description="Legacy sort field parameter"),
    sort_order: Optional[str] = Query(None, description="Legacy sort order parameter")
):
    """
    Get orders with server-side filtering, search, and pagination
    """
    try:
        # Handle legacy parameters
        if limit:
            page_size = limit
        if status_filter:
            status = status_filter  
        if date_from:
            from_date = date_from
        if date_to:
            to_date = date_to
        if sort_by and sort_order:
            # Convert legacy sort parameters to new format
            sort_prefix = "-" if sort_order.lower() == "desc" else ""
            sort = f"{sort_prefix}{sort_by}"
        
        # Build query
        query = {"tenant_id": tenant_id}
        
        # Search filter
        if search:
            search_regex = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"order_number": search_regex},
                {"customer_email": search_regex},
                {"customer_name": search_regex},
                {"line_items.sku": search_regex},
                {"line_items.title": search_regex}
            ]
        
        # Status filters
        if status:
            query["status"] = status
        if financial_status:
            query["financial_status"] = financial_status
        if fulfillment_status:
            query["fulfillment_status"] = fulfillment_status
        
        # Date range filters
        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = from_date
            if to_date:
                date_filter["$lte"] = to_date
            query["created_at"] = date_filter
        
        # Parse sort parameter
        sort_field = sort.lstrip("-+")
        sort_direction = -1 if sort.startswith("-") else 1
        
        # Count total documents
        total = await db.orders.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        # Get orders
        cursor = db.orders.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
        orders = await cursor.to_list(page_size)
        
        # Format orders for response - match frontend expectations
        formatted_orders = []
        for order in orders:
            # Count line items
            line_items = order.get("line_items", [])
            item_count = sum(item.get("quantity", 0) for item in line_items)
            
            formatted_orders.append({
                "id": order.get("id"),
                "order_id": order.get("order_id"),  # Frontend expects this field
                "order_number": order.get("order_number", ""),
                "shopify_order_id": order.get("shopify_order_id"),
                "customer_name": order.get("customer_name", ""),
                "customer_email": order.get("customer_email", ""),
                "email": order.get("email", order.get("customer_email", "")),
                "financial_status": order.get("financial_status", ""),
                "fulfillment_status": order.get("fulfillment_status", ""),
                "total_price": order.get("total_price", 0),
                "currency_code": order.get("currency_code", "USD"),  # Frontend expects this field
                "line_items": line_items,
                "created_at": order.get("created_at", ""),
                "updated_at": order.get("updated_at", ""),
                "shopify_order_url": order.get("shopify_order_url", "")
            })
        
        return {
            "items": formatted_orders,  # Frontend expects "items"
            "pagination": {
                "current_page": page,
                "per_page": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next_page": page < total_pages,
                "has_prev_page": page > 1
            },
            "filters": {
                "search": search,
                "status": status,
                "financialStatus": financial_status,
                "fulfillmentStatus": fulfillment_status,
                "from": from_date,
                "to": to_date,
                "sort": sort
            }
        }
        
    except Exception as e:
        print(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get orders")


@router.get("/{order_id}")
async def get_order_detail(
    order_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get detailed order information by ID with robust lookup fallbacks.
    Tries: id -> order_id -> shopify_order_id -> order_number (with and without leading #)
    """
    try:
        # Normalize possible order number formats
        normalized = order_id.lstrip('#') if isinstance(order_id, str) else order_id

        # Try multiple lookup strategies for resiliency
        lookup_queries = [
            {"id": order_id, "tenant_id": tenant_id},
            {"order_id": order_id, "tenant_id": tenant_id},
            {"shopify_order_id": order_id, "tenant_id": tenant_id},
            {"order_number": order_id, "tenant_id": tenant_id},
            {"order_number": f"#{normalized}", "tenant_id": tenant_id},
            {"order_number": normalized, "tenant_id": tenant_id},
        ]

        order = None
        for q in lookup_queries:
            order = await db.orders.find_one(q)
            if order:
                break
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Use the resolved order id for downstream queries
        resolved_order_id = order.get("id") or order.get("order_id") or str(order.get("shopify_order_id") or "")

        # Get related returns
        returns = await db.return_requests.find({
            "order_id": resolved_order_id,
            "tenant_id": tenant_id
        }).to_list(100)
        
        # Format line items
        line_items = []
        for item in order.get("line_items", []):
            line_items.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "variant_title": item.get("variant_title"),
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": item.get("price", 0),
                "total": float(item.get("price", 0)) * int(item.get("quantity", 0)),
                "fulfillment_status": item.get("fulfillment_status")
            })
        
        # Format returns
        formatted_returns = []
        for return_req in returns:
            formatted_returns.append({
                "id": return_req["id"],
                "status": return_req.get("status", ""),
                "created_at": return_req.get("created_at", "").isoformat() if return_req.get("created_at") else "",
                "estimated_refund": return_req.get("estimated_refund", 0)
            })
        
        # Build Shopify admin URL
        tenant = await db.tenants.find_one({"id": tenant_id})
        shop_domain = tenant.get("shopify_store", "") if tenant else ""
        shopify_admin_url = f"https://{shop_domain}/admin/orders/{order.get('shopify_order_id')}" if shop_domain else None
        
        return {
            "id": order.get("id") or resolved_order_id,
            "order_number": order.get("order_number", ""),
            "shopify_order_id": order.get("shopify_order_id"),
            "customer_name": order.get("customer_name", ""),
            "customer_email": order.get("customer_email", ""),
            "financial_status": order.get("financial_status", ""),
            "fulfillment_status": order.get("fulfillment_status", ""),
            "total_price": order.get("total_price", 0),
            "currency_code": order.get("currency_code", order.get("currency", "USD")),
            "created_at": order.get("created_at", ""),
            "updated_at": order.get("updated_at", ""),
            "line_items": line_items,
            "billing_address": order.get("billing_address", {}),
            "shipping_address": order.get("shipping_address", {}),
            "returns": formatted_returns,
            "shopify_order_url": shopify_admin_url,
            "raw_order_data": order.get("raw_order_data", {}) if order.get("raw_order_data") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get order detail")