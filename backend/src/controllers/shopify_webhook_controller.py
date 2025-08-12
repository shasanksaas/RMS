"""
Shopify Webhook Controller - Real-time data sync handlers
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional, Dict, Any
import json

from ..services.shopify_oauth_service import ShopifyOAuthService
from ..models.shopify import ShopifyWebhookPayload, ShopifyWebhookVerification

# Initialize router and service
router = APIRouter(prefix="/webhooks/shopify", tags=["shopify-webhooks"])
shopify_oauth = ShopifyOAuthService()

async def verify_webhook_authenticity(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
) -> bool:
    """Verify webhook authenticity using HMAC"""
    if not x_shopify_hmac_sha256 or not x_shopify_shop_domain:
        return False
    
    body = await request.body()
    body_str = body.decode('utf-8')
    
    return shopify_oauth.verify_webhook_hmac(body_str, x_shopify_hmac_sha256)

@router.post("/orders-create")
async def handle_orders_create(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle orders/create webhook
    
    This webhook fires when a new order is created in Shopify
    Real-time sync: Add new order to tenant's order collection
    """
    # Verify webhook authenticity
    if not await verify_webhook_authenticity(request, x_shopify_hmac_sha256, x_shopify_shop_domain):
        raise HTTPException(status_code=401, detail="Webhook verification failed")
    
    try:
        body = await request.json()
        shop_domain = shopify_oauth.normalize_shop_domain(x_shopify_shop_domain)
        
        # Get tenant_id for this shop
        from ..config.database import get_database
        db = await get_database()
        tenant = await db["tenants"].find_one({"shop": shop_domain})
        
        if not tenant:
            print(f"⚠️ No tenant found for shop: {shop_domain}")
            return {"status": "ignored", "reason": "no_tenant"}
        
        tenant_id = tenant["tenant_id"]
        
        # Process order data for storage
        order_data = {
            "tenant_id": tenant_id,
            "shopify_order_id": str(body["id"]),
            "order_number": body.get("order_number"),
            "name": body.get("name"),
            "email": body.get("email"),
            "total_price": float(body.get("total_price", 0)),
            "currency": body.get("currency", "USD"),
            "customer": body.get("customer", {}),
            "line_items": body.get("line_items", []),
            "shipping_address": body.get("shipping_address", {}),
            "billing_address": body.get("billing_address", {}),
            "fulfillment_status": body.get("fulfillment_status"),
            "financial_status": body.get("financial_status"),
            "created_at": body.get("created_at"),
            "updated_at": body.get("updated_at"),
            "tags": body.get("tags", "").split(",") if body.get("tags") else [],
            "source_name": body.get("source_name"),
            "raw_data": body,  # Store full Shopify order for reference
            "synced_at": "datetime.utcnow()"
        }
        
        # Store order in tenant-isolated collection
        await db["orders"].replace_one(
            {"tenant_id": tenant_id, "shopify_order_id": str(body["id"])},
            order_data,
            upsert=True
        )
        
        print(f"✅ Order created webhook processed: {body['name']} for tenant {tenant_id}")
        
        return {"status": "processed", "order_id": body["id"]}
        
    except Exception as e:
        print(f"❌ Orders create webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/orders-updated")
async def handle_orders_updated(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle orders/updated webhook
    
    Updates existing order data when order is modified in Shopify
    """
    if not await verify_webhook_authenticity(request, x_shopify_hmac_sha256, x_shopify_shop_domain):
        raise HTTPException(status_code=401, detail="Webhook verification failed")
    
    try:
        body = await request.json()
        shop_domain = shopify_oauth.normalize_shop_domain(x_shopify_shop_domain)
        
        from ..config.database import get_database
        db = await get_database()
        tenant = await db["tenants"].find_one({"shop": shop_domain})
        
        if not tenant:
            return {"status": "ignored", "reason": "no_tenant"}
        
        tenant_id = tenant["tenant_id"]
        
        # Update existing order
        update_data = {
            "total_price": float(body.get("total_price", 0)),
            "fulfillment_status": body.get("fulfillment_status"),
            "financial_status": body.get("financial_status"), 
            "updated_at": body.get("updated_at"),
            "tags": body.get("tags", "").split(",") if body.get("tags") else [],
            "raw_data": body,
            "synced_at": "datetime.utcnow()"
        }
        
        result = await db["orders"].update_one(
            {"tenant_id": tenant_id, "shopify_order_id": str(body["id"])},
            {"$set": update_data}
        )
        
        print(f"✅ Order updated webhook processed: {body['name']} for tenant {tenant_id}")
        
        return {"status": "processed", "updated": result.modified_count > 0}
        
    except Exception as e:
        print(f"❌ Orders updated webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/fulfillments-create")
async def handle_fulfillments_create(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle fulfillments/create webhook
    
    Updates order fulfillment status when items are shipped
    """
    if not await verify_webhook_authenticity(request, x_shopify_hmac_sha256, x_shopify_shop_domain):
        raise HTTPException(status_code=401, detail="Webhook verification failed")
    
    try:
        body = await request.json()
        shop_domain = shopify_oauth.normalize_shop_domain(x_shopify_shop_domain)
        
        from ..config.database import get_database
        db = await get_database()
        tenant = await db["tenants"].find_one({"shop": shop_domain})
        
        if not tenant:
            return {"status": "ignored", "reason": "no_tenant"}
        
        tenant_id = tenant["tenant_id"]
        order_id = str(body.get("order_id"))
        
        # Update order with fulfillment info
        fulfillment_data = {
            "fulfillment_status": "fulfilled",
            "fulfillment_date": body.get("created_at"),
            "tracking_number": body.get("tracking_number"),
            "tracking_company": body.get("tracking_company"),
            "tracking_url": body.get("tracking_url"),
            "synced_at": "datetime.utcnow()"
        }
        
        await db["orders"].update_one(
            {"tenant_id": tenant_id, "shopify_order_id": order_id},
            {"$set": fulfillment_data}
        )
        
        print(f"✅ Fulfillment created webhook processed for order {order_id}, tenant {tenant_id}")
        
        return {"status": "processed", "order_id": order_id}
        
    except Exception as e:
        print(f"❌ Fulfillments create webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/fulfillments-update")
async def handle_fulfillments_update(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle fulfillments/update webhook
    
    Updates fulfillment tracking information
    """
    if not await verify_webhook_authenticity(request, x_shopify_hmac_sha256, x_shopify_shop_domain):
        raise HTTPException(status_code=401, detail="Webhook verification failed")
    
    try:
        body = await request.json()
        shop_domain = shopify_oauth.normalize_shop_domain(x_shopify_shop_domain)
        
        from ..config.database import get_database
        db = await get_database()
        tenant = await db["tenants"].find_one({"shop": shop_domain})
        
        if not tenant:
            return {"status": "ignored", "reason": "no_tenant"}
        
        tenant_id = tenant["tenant_id"]
        order_id = str(body.get("order_id"))
        
        # Update fulfillment tracking
        update_data = {
            "tracking_number": body.get("tracking_number"),
            "tracking_company": body.get("tracking_company"),
            "tracking_url": body.get("tracking_url"),
            "synced_at": "datetime.utcnow()"
        }
        
        await db["orders"].update_one(
            {"tenant_id": tenant_id, "shopify_order_id": order_id},
            {"$set": update_data}
        )
        
        print(f"✅ Fulfillment updated webhook processed for order {order_id}, tenant {tenant_id}")
        
        return {"status": "processed", "order_id": order_id}
        
    except Exception as e:
        print(f"❌ Fulfillments update webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/app-uninstalled")
async def handle_app_uninstalled(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle app/uninstalled webhook
    
    Critical: Clean up tenant data when app is uninstalled
    Mark tenant as disconnected and clean up sensitive data
    """
    if not await verify_webhook_authenticity(request, x_shopify_hmac_sha256, x_shopify_shop_domain):
        raise HTTPException(status_code=401, detail="Webhook verification failed")
    
    try:
        body = await request.json()
        shop_domain = shopify_oauth.normalize_shop_domain(x_shopify_shop_domain)
        
        from ..config.database import get_database
        db = await get_database()
        
        # Find tenant for this shop
        tenant = await db["tenants"].find_one({"shop": shop_domain})
        if not tenant:
            print(f"⚠️ App uninstall webhook: No tenant found for shop {shop_domain}")
            return {"status": "ignored", "reason": "no_tenant"}
        
        tenant_id = tenant["tenant_id"]
        
        # Mark integration as disconnected
        await db["integrations_shopify"].update_one(
            {"tenant_id": tenant_id, "shop": shop_domain},
            {"$set": {
                "status": "disconnected",
                "uninstalled_at": "datetime.utcnow()",
                "access_token_encrypted": "",  # Clear token for security
                "webhook_ids": {}
            }}
        )
        
        # Update tenant status
        await db["tenants"].update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "status": "suspended",
                "uninstalled_at": "datetime.utcnow()"
            }}
        )
        
        # Optionally: Archive or delete tenant data based on retention policy
        # For now, keep data for potential re-installation
        
        print(f"✅ App uninstalled webhook processed for shop {shop_domain}, tenant {tenant_id}")
        print(f"🧹 Tenant marked as suspended, tokens cleared")
        
        return {"status": "processed", "tenant_id": tenant_id, "action": "suspended"}
        
    except Exception as e:
        print(f"❌ App uninstalled webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# === Webhook Testing Endpoints ===

@router.get("/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook routing is working"""
    return {
        "status": "webhook_system_active",
        "endpoints": [
            "orders-create",
            "orders-updated", 
            "fulfillments-create",
            "fulfillments-update",
            "app-uninstalled"
        ],
        "verification": "hmac_required"
    }

@router.post("/test-payload")
async def test_webhook_payload(request: Request):
    """Test endpoint to inspect webhook payload structure"""
    body = await request.json()
    headers = dict(request.headers)
    
    return {
        "headers": headers,
        "payload": body,
        "content_type": request.headers.get("content-type"),
        "user_agent": request.headers.get("user-agent")
    }