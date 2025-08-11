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
        
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Get returns with deduplication logic
        cursor = db.returns.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
        all_returns = await cursor.to_list(page_size)
        
        # DEDUPLICATION: Remove duplicate returns based on business logic
        # Keep the most recent return for each unique order_id + customer_email combination (case-insensitive)
        unique_returns_map = {}
        
        # First pass: identify the most recent return for each combination
        for ret in all_returns:
            order_id = ret.get("order_id", "")
            customer_email = ret.get("customer_email", "").lower()  # Case-insensitive comparison
            combination_key = f"{order_id}:{customer_email}"
            
            if combination_key not in unique_returns_map:
                unique_returns_map[combination_key] = ret
            else:
                # Keep the more recent one (by created_at or updated_at)
                existing = unique_returns_map[combination_key]
                current_date = ret.get("updated_at") or ret.get("created_at")
                existing_date = existing.get("updated_at") or existing.get("created_at")
                
                if current_date and existing_date:
                    if isinstance(current_date, str):
                        try:
                            current_date = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
                        except:
                            pass
                    if isinstance(existing_date, str):
                        try:
                            existing_date = datetime.fromisoformat(existing_date.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if current_date > existing_date:
                        unique_returns_map[combination_key] = ret
        
        # Use deduplicated returns
        returns = list(unique_returns_map.values())
        
        # Count total unique documents (after deduplication)
        # For accurate pagination, we need to get ALL documents and deduplicate to get true count
        all_cursor = db.returns.find(query).sort(sort_field, sort_direction)
        all_documents = await all_cursor.to_list(length=None)
        
        # Apply same deduplication logic to all documents for accurate count
        all_unique_returns_map = {}
        for ret in all_documents:
            order_id = ret.get("order_id", "")
            customer_email = ret.get("customer_email", "").lower()
            combination_key = f"{order_id}:{customer_email}"
            
            if combination_key not in all_unique_returns_map:
                all_unique_returns_map[combination_key] = ret
            else:
                existing = all_unique_returns_map[combination_key]
                current_date = ret.get("updated_at") or ret.get("created_at")
                existing_date = existing.get("updated_at") or existing.get("created_at")
                
                if current_date and existing_date:
                    if isinstance(current_date, str):
                        try:
                            current_date = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
                        except:
                            pass
                    if isinstance(existing_date, str):
                        try:
                            existing_date = datetime.fromisoformat(existing_date.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if current_date > existing_date:
                        all_unique_returns_map[combination_key] = ret
        
        total = len(all_unique_returns_map)  # True deduplicated count
        total_pages = (total + page_size - 1) // page_size
        
        # Log deduplication activity
        duplicates_removed = len(all_returns) - len(returns)
        if duplicates_removed > 0:
            print(f"DEDUPLICATION: Removed {duplicates_removed} duplicate returns for tenant {tenant_id}")
            print(f"DEDUPLICATION: Original count: {len(all_returns)}, Deduplicated count: {len(returns)}")
            print(f"DEDUPLICATION: Total unique returns: {total}")
        
        # OPTIMIZATION: Batch fetch all unique order IDs to avoid N+1 queries
        unique_order_ids = list(set(r.get("order_id") for r in returns if r.get("order_id")))
        orders_map = {}
        
        if unique_order_ids:
            # Alternative batch fetch using $or (more reliable than $in)
            or_conditions = [{"id": oid} for oid in unique_order_ids]
            orders_cursor = db.orders.find({
                "$or": or_conditions, 
                "tenant_id": tenant_id
            })
            orders = await orders_cursor.to_list(length=None)
            orders_map = {order["id"]: order for order in orders}
            
            # If $or fails, fall back to individual queries (cached)
            if not orders_map:
                for order_id in unique_order_ids:
                    try:
                        order = await db.orders.find_one({
                            "id": order_id,
                            "tenant_id": tenant_id
                        })
                        if order:
                            orders_map[order_id] = order
                    except Exception as e:
                        print(f"Failed to fetch order {order_id}: {e}")
                        continue
        
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
        
        # Get Shopify integration details for URLs
        shopify_integration = await db.integrations_shopify.find_one({
            "tenant_id": tenant_id
        })
        
        shop_domain = "unknown-store"  # Default fallback
        if shopify_integration:
            # Try different possible field names for shop domain
            shop_domain = (shopify_integration.get("shop_domain") or 
                          shopify_integration.get("store_url", "").replace(".myshopify.com", "") or
                          "unknown-store")
            # Remove .myshopify.com if it's included
            if shop_domain.endswith(".myshopify.com"):
                shop_domain = shop_domain.replace(".myshopify.com", "")
        
        shopify_order_url = f"https://{shop_domain}.myshopify.com/admin/orders/{return_req.get('order_id')}" if return_req.get('order_id') else None
        shopify_return_url = f"https://{shop_domain}.myshopify.com/admin/returns" if shopify_integration else None
        
        # Extract estimated refund
        estimated_refund_data = return_req.get("estimated_refund", {})
        if isinstance(estimated_refund_data, dict):
            estimated_refund = float(estimated_refund_data.get("amount", 0))
        else:
            estimated_refund = float(estimated_refund_data) if estimated_refund_data else 0
        
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
            # Basic Information
            "id": return_req["id"],
            "order_id": return_req.get("order_id", ""),
            "order_number": order_number,
            
            # Customer Information
            "customer": {
                "name": customer_name,
                "email": customer_email
            },
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": order.get("customer", {}).get("phone") if order else return_req.get("customer_phone"),
            
            # Status Information
            "status": return_req.get("status", "").lower(),
            "decision": return_req.get("decision", ""),
            "decision_made_at": return_req.get("decision_made_at"),
            "decision_made_by": return_req.get("decision_made_by", ""),
            
            # Return Details
            "channel": return_req.get("channel", ""),
            "preferred_outcome": return_req.get("preferred_outcome", ""),
            "return_method": return_req.get("return_method", "customer_ships"),
            "return_method_original": return_req.get("return_method_original"),
            "return_reason_category": return_req.get("return_reason_category", ""),
            "customer_note": return_req.get("customer_note", ""),
            "notes": return_req.get("customer_note", ""),
            "reason": return_req.get("return_reason_category", ""),
            
            # Financial Information
            "estimated_refund": return_req.get("estimated_refund", {}),
            "currency": order.get("currency", "INR") if order else "INR",
            "refund_mode": return_req.get("refund_mode", "store_credit"),
            "payment_method": order.get("payment_gateway", "manual payment gateway") if order else "manual payment gateway",
            
            # Items
            "items": formatted_items,
            "line_items": return_req.get("line_items", []),
            
            # Shipping Information
            "shipping_address": order.get("shipping_address", {}) if order else {},
            "shipping": return_req.get("shipping", {}),
            "tracking_number": return_req.get("tracking_number"),
            
            # Shopify Integration
            "shopify_sync_issues": not bool(order),
            "product_deleted": False,  # This would need to be checked against Shopify
            "source": return_req.get("source", "customer_portal"),
            
            # Admin Information
            "admin_override_note": return_req.get("admin_override_note", ""),
            "internal_tags": return_req.get("internal_tags", []),
            "fees": return_req.get("fees", {}),
            "label_url": return_req.get("label_url"),
            "policy_version": return_req.get("policy_version", ""),
            
            # Audit Trail
            "audit_log": return_req.get("audit_log", []),
            "state_history": return_req.get("state_history", []),
            "explain_trace": return_req.get("explain_trace", []),
            
            # Timestamps
            "created_at": created_at_str,
            "updated_at": updated_at_str,
            "expires_at": return_req.get("expires_at"),
            
            # URLs
            "shopify_order_url": shopify_order_url,
            "shopify_return_url": shopify_return_url,
            
            # Order Context
            "order_info": {
                "order_number": order.get("order_number", "") if order else "",
                "total_price": order.get("total_price", 0) if order else 0,
                "currency": order.get("currency", "INR") if order else "INR",
                "created_at": order.get("created_at", "") if order else "",
                "financial_status": order.get("financial_status", "") if order else "",
                "fulfillment_status": order.get("fulfillment_status", "") if order else ""
            } if order else None,
            
            # Additional metadata for UI
            "last_sync": order.get("last_sync") if order else None,
            "metrics": return_req.get("metrics", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting return detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get return detail")


@router.put("/{return_id}/status")
async def update_return_status(
    return_id: str,
    status_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Update return status with audit logging
    """
    try:
        new_status = status_data.get("status", "").lower()
        notes = status_data.get("notes", "")
        
        # Validate status
        valid_statuses = ["requested", "approved", "denied", "rejected", "processing", "completed", "archived"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Update return
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow(),
            "decision": new_status if new_status in ["approved", "denied"] else "",
            "decision_made_at": datetime.utcnow() if new_status in ["approved", "denied"] else None,
            "decision_made_by": "admin"  # In real app, this would be the actual admin user ID
        }
        
        if notes:
            update_data["admin_notes"] = notes
        
        # Add to audit log
        audit_entry = {
            "action": f"status_updated_to_{new_status}",
            "performed_by": "admin",
            "timestamp": datetime.utcnow(),
            "details": {"old_status": "previous", "new_status": new_status, "notes": notes},
            "description": f"Status updated to {new_status.upper()}"
        }
        
        update_data["$push"] = {"audit_log": audit_entry}
        
        result = await db.returns.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": update_data, "$push": {"audit_log": audit_entry}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Return not found")
        
        return {"success": True, "message": f"Return status updated to {new_status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating return status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update return status")


@router.post("/{return_id}/comments")
async def add_comment(
    return_id: str,
    comment_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Add comment to return
    """
    try:
        comment_text = comment_data.get("comment", "").strip()
        if not comment_text:
            raise HTTPException(status_code=400, detail="Comment text is required")
        
        # Create comment entry
        comment_entry = {
            "action": "comment_added",
            "performed_by": "admin",
            "timestamp": datetime.utcnow(),
            "details": {"comment": comment_text},
            "description": f"Comment added: {comment_text[:50]}{'...' if len(comment_text) > 50 else ''}"
        }
        
        result = await db.returns.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$push": {"audit_log": comment_entry}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Return not found")
        
        return {"success": True, "message": "Comment added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.post("/{return_id}/refund")
async def process_refund(
    return_id: str,
    refund_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Process refund for return
    """
    try:
        # Get return
        return_req = await db.returns.find_one({"id": return_id, "tenant_id": tenant_id})
        if not return_req:
            raise HTTPException(status_code=404, detail="Return not found")
        
        refund_method = refund_data.get("refund_method", "original_payment")
        
        # In a real implementation, this would:
        # 1. Call Shopify Refund API
        # 2. Process payment through payment gateway
        # 3. Update order status in Shopify
        
        # For now, simulate processing
        refund_entry = {
            "action": "refund_processed",
            "performed_by": "admin",
            "timestamp": datetime.utcnow(),
            "details": {
                "refund_method": refund_method,
                "amount": return_req.get("estimated_refund", {}).get("amount", 0)
            },
            "description": f"Refund processed via {refund_method}"
        }
        
        update_data = {
            "status": "completed",
            "refund_status": "processed",
            "refund_processed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.returns.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": update_data, "$push": {"audit_log": refund_entry}}
        )
        
        return {"success": True, "message": "Refund processed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing refund: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")


@router.post("/{return_id}/label")
async def generate_return_label(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Generate return shipping label
    """
    try:
        # Get return
        return_req = await db.returns.find_one({"id": return_id, "tenant_id": tenant_id})
        if not return_req:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # In a real implementation, this would:
        # 1. Call shipping API (UPS, FedEx, etc.)
        # 2. Generate PDF label
        # 3. Store label URL
        
        # For now, simulate label generation
        label_url = f"https://storage.example.com/labels/return_{return_id}_label.pdf"
        
        label_entry = {
            "action": "label_generated",
            "performed_by": "admin",
            "timestamp": datetime.utcnow(),
            "details": {"label_url": label_url},
            "description": "Return shipping label generated"
        }
        
        await db.returns.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "label_url": label_url,
                    "label_generated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$push": {"audit_log": label_entry}
            }
        )
        
        return {"success": True, "label_url": label_url, "message": "Return label generated"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating label: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate return label")


@router.post("/{return_id}/email")
async def send_email_update(
    return_id: str,
    email_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Send email update to customer
    """
    try:
        # Get return
        return_req = await db.returns.find_one({"id": return_id, "tenant_id": tenant_id})
        if not return_req:
            raise HTTPException(status_code=404, detail="Return not found")
        
        email_type = email_data.get("type", "status_update")
        message = email_data.get("message", "")
        
        # In a real implementation, this would:
        # 1. Use SendGrid, SES, or other email service
        # 2. Load email template
        # 3. Send personalized email to customer
        
        # For now, simulate email sending
        email_entry = {
            "action": "email_sent",
            "performed_by": "admin",
            "timestamp": datetime.utcnow(),
            "details": {
                "email_type": email_type,
                "recipient": return_req.get("customer_email"),
                "message_preview": message[:100] if message else "Status update email"
            },
            "description": f"Email notification sent to {return_req.get('customer_email')}"
        }
        
        await db.returns.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {
                "$set": {"updated_at": datetime.utcnow()},
                "$push": {"audit_log": email_entry}
            }
        )
        
        return {"success": True, "message": "Email sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")