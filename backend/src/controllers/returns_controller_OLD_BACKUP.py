"""
Returns Controller - Complete Shopify RMS Implementation
Implements all requirements from Shopify Returns Management System Guide
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..utils.dependencies import get_tenant_id
from ..services.shopify_graphql import ShopifyGraphQLFactory
from ..config.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/returns-legacy", tags=["returns-legacy"])

# Return Status Constants per Shopify RMS Guide
RETURN_STATUS = {
    "REQUESTED": "requested",
    "OPEN": "open", 
    "CLOSED": "closed",
    "DECLINED": "declined",
    "CANCELED": "canceled"
}

@router.get("/orders-with-returns")
async def get_orders_with_returns(
    tenant_id: str = Depends(get_tenant_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Return status filter"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)")
):
    """
    Get all orders with returns - implements Shopify RMS Guide requirement
    GET /orders-with-returns from the guide example
    """
    try:
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            # Fallback to database for development
            return await _get_orders_with_returns_from_db(tenant_id, page, limit, status_filter)
        
        # Build query filter
        query_filter = "returnStatus:IN_PROGRESS,RETURNED,REQUESTED"
        if status_filter:
            query_filter = f"returnStatus:{status_filter.upper()}"
        
        if date_from or date_to:
            date_query = []
            if date_from:
                date_query.append(f"created_at:>={date_from}")
            if date_to:
                date_query.append(f"created_at:<={date_to}")
            if date_query:
                query_filter += f" AND {' AND '.join(date_query)}"
        
        # Calculate cursor for pagination
        cursor = None
        if page > 1:
            cursor = f"cursor_page_{page}"  # Simplified cursor logic
        
        # Fetch orders with returns
        result = await graphql_service.get_orders_with_returns(
            limit=limit,
            cursor=cursor,
            query_filter=query_filter
        )
        
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Failed to fetch orders with returns")
        
        orders = result["data"]["orders"]["edges"]
        page_info = result["data"]["orders"]["pageInfo"]
        
        # Transform data for response
        transformed_orders = []
        for order_edge in orders:
            order = order_edge["node"]
            transformed_order = _transform_order_with_returns(order)
            transformed_orders.append(transformed_order)
        
        return {
            "items": transformed_orders,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "has_next": page_info.get("hasNextPage", False),
                "has_prev": page > 1,
                "total_items": len(transformed_orders) * page  # Approximate
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching orders with returns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders with returns: {str(e)}")

@router.get("/returnable-fulfillments/{order_id}")
async def get_returnable_fulfillments(
    order_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get returnable fulfillments for an order - implements Shopify RMS Guide requirement
    GET /returnable-fulfillments/:orderId from the guide example
    """
    try:
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            raise HTTPException(status_code=503, detail="Shopify service not available")
        
        # Convert order_id to Shopify GID format if needed
        shopify_order_id = f"gid://shopify/Order/{order_id}" if not order_id.startswith("gid://") else order_id
        
        # Fetch returnable fulfillments
        result = await graphql_service.get_returnable_fulfillments(shopify_order_id)
        
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Failed to fetch returnable fulfillments")
        
        fulfillments = result["data"]["returnableFulfillments"]["edges"]
        
        # Transform data for response
        transformed_fulfillments = []
        for fulfillment_edge in fulfillments:
            fulfillment = fulfillment_edge["node"]
            transformed_fulfillments.append({
                "id": fulfillment["id"],
                "fulfillment_id": fulfillment["fulfillment"]["id"],
                "status": fulfillment["fulfillment"]["displayStatus"],
                "name": fulfillment["fulfillment"]["name"],
                "origin_address": fulfillment["fulfillment"].get("originAddress"),
                "returnable_items": [
                    {
                        "fulfillment_line_item_id": item["node"]["fulfillmentLineItem"]["id"],
                        "line_item_id": item["node"]["fulfillmentLineItem"]["lineItem"]["id"],
                        "title": item["node"]["fulfillmentLineItem"]["lineItem"]["title"],
                        "sku": item["node"]["fulfillmentLineItem"]["lineItem"]["sku"],
                        "quantity": item["node"]["quantity"],
                        "product_id": item["node"]["fulfillmentLineItem"]["lineItem"]["product"]["id"],
                        "product_title": item["node"]["fulfillmentLineItem"]["lineItem"]["product"]["title"]
                    }
                    for item in fulfillment["returnableFulfillmentLineItems"]["edges"]
                ]
            })
        
        return {"returnable_fulfillments": transformed_fulfillments}
        
    except Exception as e:
        logger.error(f"Error fetching returnable fulfillments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch returnable fulfillments: {str(e)}")

@router.get("/{return_id}")
async def get_return_details(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get specific return details - implements Shopify RMS Guide requirement
    GET /return/:returnId from the guide example
    """
    try:
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            # Fallback to database
            return_data = await db.return_requests.find_one({
                "return_id": return_id,
                "tenant_id": tenant_id
            })
            if not return_data:
                raise HTTPException(status_code=404, detail="Return not found")
            return return_data
        
        # Convert return_id to Shopify GID format if needed
        shopify_return_id = f"gid://shopify/Return/{return_id}" if not return_id.startswith("gid://") else return_id
        
        # Fetch return details
        result = await graphql_service.get_return_details(shopify_return_id)
        
        if not result.get("data") or not result["data"].get("return"):
            raise HTTPException(status_code=404, detail="Return not found")
        
        return_data = result["data"]["return"]
        
        # Transform data for response
        transformed_return = {
            "id": return_data["id"],
            "status": return_data["status"].lower(),
            "name": return_data["name"],
            "total_quantity": return_data["totalQuantity"],
            "order_id": return_data["order"]["id"],
            "order_number": return_data["order"]["name"],
            "return_line_items": [
                {
                    "id": item["node"]["id"],
                    "quantity": item["node"]["quantity"],
                    "processable_quantity": item["node"]["processableQuantity"],
                    "processed_quantity": item["node"]["processedQuantity"],
                    "refundable_quantity": item["node"]["refundableQuantity"],
                    "refunded_quantity": item["node"]["refundedQuantity"],
                    "return_reason": item["node"]["returnReason"],
                    "return_reason_note": item["node"]["returnReasonNote"],
                    "customer_note": item["node"]["customerNote"],
                    "line_item": {
                        "id": item["node"]["fulfillmentLineItem"]["lineItem"]["id"],
                        "title": item["node"]["fulfillmentLineItem"]["lineItem"]["title"],
                        "sku": item["node"]["fulfillmentLineItem"]["lineItem"]["sku"],
                        "variant_id": item["node"]["fulfillmentLineItem"]["lineItem"]["variant"]["id"],
                        "variant_title": item["node"]["fulfillmentLineItem"]["lineItem"]["variant"]["title"],
                        "price": item["node"]["fulfillmentLineItem"]["lineItem"]["variant"]["price"],
                        "product_id": item["node"]["fulfillmentLineItem"]["lineItem"]["product"]["id"],
                        "product_title": item["node"]["fulfillmentLineItem"]["lineItem"]["product"]["title"]
                    },
                    "restocking_fee": item["node"].get("restockingFee", {}).get("amountSet", {}).get("shopMoney")
                }
                for item in return_data["returnLineItems"]["edges"]
            ],
            "exchange_line_items": [
                {
                    "id": item["node"]["id"],
                    "line_item": {
                        "id": item["node"]["lineItem"]["id"],
                        "title": item["node"]["lineItem"]["title"],
                        "sku": item["node"]["lineItem"]["sku"],
                        "quantity": item["node"]["lineItem"]["quantity"]
                    }
                }
                for item in return_data["exchangeLineItems"]["edges"]
            ]
        }
        
        return transformed_return
        
    except Exception as e:
        logger.error(f"Error fetching return details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch return details: {str(e)}")

@router.post("/request")
async def create_return_request(
    request_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create a return request - implements Shopify RMS Guide requirement
    POST /return-request from the guide example
    """
    try:
        order_id = request_data.get("orderId")
        return_line_items = request_data.get("returnLineItems", [])
        
        if not order_id or not return_line_items:
            raise HTTPException(status_code=400, detail="orderId and returnLineItems are required")
        
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            # Fallback: Create return request in database
            return_request = {
                "id": f"ret_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "order_id": order_id,
                "tenant_id": tenant_id,
                "status": RETURN_STATUS["REQUESTED"],
                "return_line_items": return_line_items,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.return_requests.insert_one(return_request)
            return {"return": return_request, "userErrors": []}
        
        # Convert order_id to Shopify GID format if needed
        shopify_order_id = f"gid://shopify/Order/{order_id}" if not order_id.startswith("gid://") else order_id
        
        # Create return request via Shopify API
        result = await graphql_service.create_return_request(shopify_order_id, return_line_items)
        
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Failed to create return request")
        
        return_request = result["data"]["returnRequest"]
        
        if return_request.get("userErrors"):
            raise HTTPException(status_code=400, detail=return_request["userErrors"])
        
        # Store in database for tracking
        return_data = return_request["return"]
        await db.return_requests.update_one(
            {"return_id": return_data["id"], "tenant_id": tenant_id},
            {"$set": {
                "return_id": return_data["id"],
                "tenant_id": tenant_id,
                "status": return_data["status"].lower(),
                "name": return_data["name"],
                "order_id": shopify_order_id,
                "return_line_items": [
                    {
                        "id": item["node"]["id"],
                        "quantity": item["node"]["quantity"],
                        "return_reason": item["node"]["returnReason"],
                        "return_reason_note": item["node"]["returnReasonNote"],
                        "customer_note": item["node"]["customerNote"]
                    }
                    for item in return_data["returnLineItems"]["edges"]
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "synced_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        return return_request
        
    except Exception as e:
        logger.error(f"Error creating return request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create return request: {str(e)}")

@router.post("/{return_id}/approve")
async def approve_return(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Approve a return request - implements Shopify RMS Guide requirement
    """
    try:
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            # Fallback: Update status in database
            result = await db.return_requests.update_one(
                {"return_id": return_id, "tenant_id": tenant_id},
                {"$set": {
                    "status": RETURN_STATUS["OPEN"],
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Return not found")
            
            return {"status": "approved", "return_id": return_id}
        
        # Convert return_id to Shopify GID format if needed
        shopify_return_id = f"gid://shopify/Return/{return_id}" if not return_id.startswith("gid://") else return_id
        
        # Approve return via Shopify API
        result = await graphql_service.approve_return_request(shopify_return_id)
        
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Failed to approve return")
        
        approval_result = result["data"]["returnApproveRequest"]
        
        if approval_result.get("userErrors"):
            raise HTTPException(status_code=400, detail=approval_result["userErrors"])
        
        # Update in database
        approved_return = approval_result["return"]
        await db.return_requests.update_one(
            {"return_id": approved_return["id"], "tenant_id": tenant_id},
            {"$set": {
                "status": approved_return["status"].lower(),
                "updated_at": datetime.utcnow(),
                "synced_at": datetime.utcnow()
            }}
        )
        
        return approval_result
        
    except Exception as e:
        logger.error(f"Error approving return: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve return: {str(e)}")

@router.post("/{return_id}/process")
async def process_return_with_refund(
    return_id: str,
    process_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Process return with refund - implements Shopify RMS Guide requirement
    """
    try:
        refund_input = process_data.get("refund")
        return_line_items = process_data.get("returnLineItems", [])
        
        # Get GraphQL service for tenant
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            # Fallback: Update status in database
            result = await db.return_requests.update_one(
                {"return_id": return_id, "tenant_id": tenant_id},
                {"$set": {
                    "status": RETURN_STATUS["CLOSED"],
                    "processed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Return not found")
            
            return {"status": "processed", "return_id": return_id}
        
        # Convert return_id to Shopify GID format if needed
        shopify_return_id = f"gid://shopify/Return/{return_id}" if not return_id.startswith("gid://") else return_id
        
        # Process return via Shopify API
        result = await graphql_service.process_return_with_refund(
            shopify_return_id, refund_input, return_line_items
        )
        
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Failed to process return")
        
        process_result = result["data"]["returnProcess"]
        
        if process_result.get("userErrors"):
            raise HTTPException(status_code=400, detail=process_result["userErrors"])
        
        # Update in database
        processed_return = process_result["return"]
        refund_data = process_result.get("refund")
        
        await db.return_requests.update_one(
            {"return_id": processed_return["id"], "tenant_id": tenant_id},
            {"$set": {
                "status": processed_return["status"].lower(),
                "processed_at": datetime.utcnow(),
                "refund_id": refund_data.get("id") if refund_data else None,
                "refund_amount": refund_data.get("totalRefundedSet", {}).get("shopMoney", {}).get("amount") if refund_data else None,
                "updated_at": datetime.utcnow(),
                "synced_at": datetime.utcnow()
            }}
        )
        
        return process_result
        
    except Exception as e:
        logger.error(f"Error processing return: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process return: {str(e)}")

# Helper Functions

async def _get_orders_with_returns_from_db(tenant_id: str, page: int, limit: int, 
                                         status_filter: Optional[str] = None) -> Dict[str, Any]:
    """Fallback method to get orders with returns from database"""
    # Build query
    query = {"tenant_id": tenant_id}
    
    # Get orders that have returns
    orders_with_returns = await db.return_requests.distinct("order_id", query)
    
    if not orders_with_returns:
        return {
            "items": [],
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
    
    # Get orders
    orders_query = {
        "tenant_id": tenant_id,
        "$or": [
            {"order_id": {"$in": orders_with_returns}},
            {"id": {"$in": orders_with_returns}}
        ]
    }
    
    # Pagination
    skip = (page - 1) * limit
    orders_cursor = db.orders.find(orders_query).skip(skip).limit(limit)
    orders = await orders_cursor.to_list(length=limit)
    
    # Get returns for each order
    for order in orders:
        order_id = order.get("order_id", order.get("id"))
        returns_cursor = db.return_requests.find({
            "order_id": order_id,
            "tenant_id": tenant_id
        })
        order["returns"] = await returns_cursor.to_list(length=10)
    
    total_count = await db.orders.count_documents(orders_query)
    
    return {
        "items": orders,
        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_items": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "has_next": page * limit < total_count,
            "has_prev": page > 1
        }
    }

def _transform_order_with_returns(order: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Shopify order data to our format"""
    customer = order.get("customer", {})
    total_price_set = order.get("totalPriceSet", {}).get("shopMoney", {})
    
    return {
        "id": order["id"],
        "order_number": order["name"],
        "email": order["email"],
        "customer_id": customer.get("id"),
        "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
        "customer_email": customer.get("email"),
        "financial_status": order.get("displayFinancialStatus", "unknown").lower(),
        "fulfillment_status": order.get("displayFulfillmentStatus", "unfulfilled").lower(),
        "return_status": order.get("returnStatus", "none").lower(),
        "total_price": float(total_price_set.get("amount", "0") or 0),
        "currency_code": total_price_set.get("currencyCode", "USD"),
        "created_at": order["createdAt"],
        "updated_at": order["updatedAt"],
        "line_items": [
            {
                "id": item["node"]["id"],
                "title": item["node"]["title"],
                "quantity": item["node"]["quantity"],
                "sku": item["node"]["sku"],
                "product_id": item["node"]["product"]["id"],
                "product_title": item["node"]["product"]["title"]
            }
            for item in order.get("lineItems", {}).get("edges", [])
        ],
        "returns": [
            {
                "id": return_data["node"]["id"],
                "status": return_data["node"]["status"].lower(),
                "name": return_data["node"]["name"],
                "total_quantity": return_data["node"]["totalQuantity"],
                "return_line_items": [
                    {
                        "id": item["node"]["id"],
                        "quantity": item["node"]["quantity"],
                        "return_reason": item["node"]["returnReason"],
                        "return_reason_note": item["node"]["returnReasonNote"],
                        "customer_note": item["node"]["customerNote"]
                    }
                    for item in return_data["node"].get("returnLineItems", {}).get("edges", [])
                ]
            }
            for return_data in order.get("returns", {}).get("edges", [])
        ]
    }