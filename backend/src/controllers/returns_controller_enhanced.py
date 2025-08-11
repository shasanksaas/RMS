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
    Get returns with server-side filtering, search, and pagination - OPTIMIZED
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
        
        # OPTIMIZATION: Batch fetch all unique order IDs to avoid N+1 queries
        unique_order_ids = list(set(r.get("order_id") for r in returns if r.get("order_id")))
        orders_map = {}
        
        if unique_order_ids:
            # Batch fetch orders from database
            orders_cursor = db.orders.find({
                "id": {"$in": unique_order_ids}, 
                "tenant_id": tenant_id
            })
            orders = await orders_cursor.to_list(length=None)
            orders_map = {order["id"]: order for order in orders}
        
        # OPTIMIZATION: Batch fetch missing orders from Shopify (if needed)
        missing_order_ids = [oid for oid in unique_order_ids if oid not in orders_map]
        if missing_order_ids:
            # Initialize Shopify service once
            from src.services.shopify_service import ShopifyService
            shopify_service = ShopifyService(tenant_id)
            
            # Fetch missing orders from Shopify in batch (if possible)
            for order_id in missing_order_ids:
                try:
                    shopify_order = await shopify_service.get_order_for_return(order_id)
                    if shopify_order:
                        orders_map[order_id] = shopify_order
                except Exception as e:
                    print(f"Failed to fetch order {order_id} from Shopify: {e}")
                    continue
        
        # Format returns for response with cached order data
        formatted_returns = []
        for return_req in returns:
            # Count items from line_items
            line_items = return_req.get("line_items", [])
            item_count = sum(item.get("quantity", 0) for item in line_items)
            
            # Get order data from cached map
            order = orders_map.get(return_req.get("order_id"))
            order_number = ""
            if order:
                order_number = order.get("order_number", order.get("name", ""))
            
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
            
            # OPTIMIZATION: Get customer name from order data with better fallbacks
            customer_name = ""
            customer_email = return_req.get("customer_email", "")
            
            if order:
                # Handle both nested customer object and flattened fields
                if order.get("customer"):
                    customer_data = order.get("customer", {})
                    if isinstance(customer_data, dict):
                        customer_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()
                        if not customer_name and customer_data.get('name'):
                            customer_name = customer_data.get('name', '')
                        if not customer_name and customer_data.get('displayName'):
                            customer_name = customer_data.get('displayName', '')
                    else:
                        customer_name = str(customer_data) if customer_data else ""
                else:
                    # Handle flattened customer fields (common with Shopify sync)
                    customer_name = order.get("customer_name", "")
                    if not customer_name and order.get("customer_display_name"):
                        customer_name = order.get("customer_display_name", "")
                    if not customer_name and order.get("customer_email"):
                        email = order.get("customer_email", "")
                        customer_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            
            # If no customer name from order, extract from return email as fallback
            if not customer_name and customer_email:
                customer_name = customer_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            
            formatted_returns.append({
                "id": return_req["id"],
                "order_number": order_number,
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
    Get detailed return information by ID - OPTIMIZED
    """
    try:
        # Find return
        return_req = await db.returns.find_one({
            "id": return_id,
            "tenant_id": tenant_id
        })
        
        if not return_req:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # Get related order - first try local database
        order = await db.orders.find_one({
            "id": return_req.get("order_id", ""),
            "tenant_id": tenant_id
        })
        
        # OPTIMIZATION: If order not found locally, fetch from Shopify once
        if not order and return_req.get("order_id"):
            try:
                from src.services.shopify_service import ShopifyService
                shopify_service = ShopifyService(tenant_id)
                order = await shopify_service.get_order_for_return(return_req.get("order_id"))
            except Exception as e:
                print(f"Failed to fetch order from Shopify for return detail: {e}")
                order = None
        
        # Format items from line_items
        formatted_items = []
        for item in return_req.get("line_items", []):
            # Extract unit price
            unit_price_data = item.get("unit_price", {})
            if isinstance(unit_price_data, dict):
                price = float(unit_price_data.get("amount", 0))
            else:
                price = float(unit_price_data) if unit_price_data else 0
            
            # Extract reason
            reason_data = item.get("reason", {})
            reason_text = ""
            if isinstance(reason_data, dict):
                reason_text = reason_data.get("description", reason_data.get("code", ""))
            else:
                reason_text = str(reason_data) if reason_data else ""
            
            formatted_items.append({
                "fulfillment_line_item_id": item.get("line_item_id"),
                "title": item.get("title", ""),
                "variant_title": item.get("variant_title"),
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": price,
                "refundable_amount": price * item.get("quantity", 0),  # Calculate refundable amount
                "reason": reason_text,
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
        
        # Extract estimated refund
        estimated_refund_data = return_req.get("estimated_refund", {})
        if isinstance(estimated_refund_data, dict):
            estimated_refund = float(estimated_refund_data.get("amount", 0))
        else:
            estimated_refund = float(estimated_refund_data) if estimated_refund_data else 0
        
        # OPTIMIZATION: Get customer name from order data with better fallbacks
        customer_name = ""
        customer_email = return_req.get("customer_email", "")
        
        if order and order.get("customer"):
            customer_data = order.get("customer", {})
            if isinstance(customer_data, dict):
                customer_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()
                if not customer_name and customer_data.get('name'):
                    customer_name = customer_data.get('name', '')
                if not customer_name and customer_data.get('displayName'):
                    customer_name = customer_data.get('displayName', '')
            else:
                customer_name = str(customer_data) if customer_data else ""
        
        # If no customer name from order, extract from email as fallback
        if not customer_name and customer_email:
            customer_name = customer_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        
        # Get order number from order
        order_number = ""
        if order:
            order_number = order.get("order_number", order.get("name", ""))
        
        # Format dates
        created_at = return_req.get("created_at")
        updated_at = return_req.get("updated_at")
        
        created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else (created_at or "")
        updated_at_str = updated_at.isoformat() if isinstance(updated_at, datetime) else (updated_at or "")
        
        return {
            "id": return_req["id"],
            "order_id": return_req.get("order_id", ""),
            "order_number": order_number,
            "customer": {
                "name": customer_name,
                "email": customer_email
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
            "estimated_refund": estimated_refund,
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