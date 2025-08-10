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
async def get_orders(
    tenant_id: str = Depends(get_tenant_id),
    search: Optional[str] = Query(None, description="Search in order number, customer email, or SKU"),
    status: Optional[str] = Query(None, description="Order status filter"),
    financial_status: Optional[str] = Query(None, alias="financialStatus", description="Financial status filter"),
    fulfillment_status: Optional[str] = Query(None, alias="fulfillmentStatus", description="Fulfillment status filter"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date filter (ISO format)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date filter (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize", description="Items per page"),
    sort: str = Query("-created_at", description="Sort field and direction")
):
    """
    Get orders with server-side filtering, search, and pagination
    """
    try:
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
        
        # Format orders for response
        formatted_orders = []
        for order in orders:
            # Count line items
            line_items = order.get("line_items", [])
            item_count = sum(item.get("quantity", 0) for item in line_items)
            
            formatted_orders.append({
                "id": order["id"],
                "order_number": order.get("order_number", ""),
                "shopify_order_id": order.get("shopify_order_id"),
                "customer_name": order.get("customer_name", ""),
                "customer_email": order.get("customer_email", ""),
                "financial_status": order.get("financial_status", ""),
                "fulfillment_status": order.get("fulfillment_status", ""),
                "total_price": order.get("total_price", 0),
                "currency": order.get("currency", "USD"),
                "item_count": item_count,
                "created_at": order.get("created_at", ""),
                "updated_at": order.get("updated_at", "")
            })
        
        return {
            "orders": formatted_orders,
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
    Get detailed order information by ID
    """
    try:
        # Find order
        order = await db.orders.find_one({
            "id": order_id,
            "tenant_id": tenant_id
        })
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get related returns
        returns = await db.return_requests.find({
            "order_id": order_id,
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
            "id": order["id"],
            "order_number": order.get("order_number", ""),
            "shopify_order_id": order.get("shopify_order_id"),
            "customer": {
                "name": order.get("customer_name", ""),
                "email": order.get("customer_email", ""),
            },
            "financial_status": order.get("financial_status", ""),
            "fulfillment_status": order.get("fulfillment_status", ""),
            "total_price": order.get("total_price", 0),
            "currency": order.get("currency", "USD"),
            "created_at": order.get("created_at", ""),
            "updated_at": order.get("updated_at", ""),
            "line_items": line_items,
            "billing_address": order.get("billing_address", {}),
            "shipping_address": order.get("shipping_address", {}),
            "returns": formatted_returns,
            "shopify_admin_url": shopify_admin_url,
            "raw_order_data": order.get("raw_order_data", {}) if order.get("raw_order_data") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get order detail")