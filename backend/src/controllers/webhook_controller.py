"""
Webhook Controller for Shopify Webhooks
Handles incoming webhook requests with HMAC verification
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
import json
import logging
import uuid
from datetime import datetime

from ..services.webhook_handlers import webhook_processor
from ..modules.auth.service import auth_service
from ..database import db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/shopify/orders_create")
async def handle_shopify_orders_create(
    request: Request,
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain")
):
    """Handle Shopify orders/create webhook - simplified version"""
    try:
        # Get request body
        body = await request.body()
        order_data = json.loads(body)
        
        # Extract shop domain
        if not x_shopify_shop_domain:
            logger.error("Missing shop domain in webhook")
            return {"status": "error", "message": "Missing shop domain"}
        
        # Convert shop domain to tenant ID
        tenant_id = f"tenant-{x_shopify_shop_domain.replace('.myshopify.com', '')}"
        
        # Save order directly using auth service
        await auth_service._save_order(tenant_id, order_data)
        
        logger.info(f"Webhook: Synced order {order_data.get('name', order_data.get('id'))} for {tenant_id}")
        
        return {"status": "success", "message": "Order synced"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/shopify/orders_updated")
async def handle_shopify_orders_updated(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle Shopify orders/updated webhook"""
    return await process_shopify_webhook(
        request, "orders/updated", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/shopify/fulfillments_create")
async def handle_shopify_fulfillments_create(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle Shopify fulfillments/create webhook"""
    return await process_shopify_webhook(
        request, "fulfillments/create", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/shopify/fulfillments_update")
async def handle_shopify_fulfillments_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle Shopify fulfillments/update webhook"""
    return await process_shopify_webhook(
        request, "fulfillments/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/shopify/refunds_create")
async def handle_shopify_refunds_create(
    request: Request,
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain")
):
    """Handle Shopify refunds/create webhook - convert to return"""
    try:
        # Get request body
        body = await request.body()
        refund_data = json.loads(body)
        
        if not x_shopify_shop_domain:
            logger.error("Missing shop domain in webhook")
            return {"status": "error", "message": "Missing shop domain"}
        
        tenant_id = f"tenant-{x_shopify_shop_domain.replace('.myshopify.com', '')}"
        
        # Convert Shopify refund to return format
        return_data = {
            'id': str(uuid.uuid4()),
            'return_id': f"RET-{refund_data.get('return', {}).get('id', refund_data.get('id'))}",
            'tenant_id': tenant_id,
            'order_id': str(refund_data.get('order_id')),
            'customer_name': 'Customer',  # Will be filled from order lookup
            'customer_email': '',
            'status': 'completed',
            'reason': 'return',
            'total_amount': float(refund_data.get('total_duties_set', {}).get('shop_money', {}).get('amount', 0)),
            'currency_code': refund_data.get('total_duties_set', {}).get('shop_money', {}).get('currency_code', 'USD'),
            'refund_amount': float(refund_data.get('total_duties_set', {}).get('shop_money', {}).get('amount', 0)),
            'shopify_return_id': str(refund_data.get('return', {}).get('id', '')),
            'shopify_refund_id': str(refund_data.get('id')),
            'created_at': refund_data.get('created_at', datetime.utcnow().isoformat()),
            'updated_at': refund_data.get('created_at', datetime.utcnow().isoformat()),
            'processed_at': refund_data.get('processed_at')
        }
        
        # Save return
        await db.return_requests.update_one(
            {'return_id': return_data['return_id'], 'tenant_id': tenant_id},
            {'$set': return_data},
            upsert=True
        )
        
        logger.info(f"Webhook: Synced return {return_data['return_id']} for {tenant_id}")
        
        return {"status": "success", "message": "Return synced"}
        
    except Exception as e:
        logger.error(f"Refunds webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/shopify/returns_update")
async def handle_shopify_returns_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle Shopify returns/update webhook"""
    return await process_shopify_webhook(
        request, "returns/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


async def process_shopify_webhook(
    request: Request,
    topic: str,
    shop_domain: Optional[str],
    hmac_signature: Optional[str]
):
    """Process Shopify webhook with HMAC verification and tenant resolution"""
    try:
        if not shop_domain:
            logger.error(f"Missing shop domain for webhook {topic}")
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Get request body
        body = await request.body()
        
        # Verify HMAC signature
        if hmac_signature:
            if not await auth_service.verify_webhook_hmac(body, hmac_signature):
                logger.error(f"HMAC verification failed for {topic} from {shop_domain}")
                raise HTTPException(status_code=401, detail="HMAC verification failed")
        
        # Parse JSON payload
        try:
            webhook_data = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload for {topic} from {shop_domain}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Resolve tenant by shop domain
        tenant_id = f"tenant-{shop_domain.replace('.myshopify.com', '').replace('.', '-').replace('_', '-')}"
        
        # Process webhook data
        result = await webhook_processor.process_webhook(
            topic=topic,
            tenant_id=tenant_id,
            shop_domain=shop_domain,
            webhook_data=webhook_data
        )
        
        if result.get("success"):
            logger.info(f"Successfully processed {topic} webhook for {shop_domain}")
            return JSONResponse({"status": "success", "processed": True})
        else:
            logger.error(f"Failed to process {topic} webhook for {shop_domain}: {result.get('error')}")
            return JSONResponse({"status": "error", "message": result.get("error")}, status_code=500)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {topic} webhook from {shop_domain}: {str(e)}")
        return JSONResponse({"status": "error", "message": "Internal server error"}, status_code=500)


@router.post("/app_uninstalled")
async def handle_app_uninstalled(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle app/uninstalled webhook"""
    return await process_webhook(
        request, "app/uninstalled", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_create")
async def handle_orders_create(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/create webhook"""
    return await process_webhook(
        request, "orders/create", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_updated")
async def handle_orders_updated(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/updated webhook"""
    return await process_webhook(
        request, "orders/updated", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_cancelled")
async def handle_orders_cancelled(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/cancelled webhook"""
    return await process_webhook(
        request, "orders/cancelled", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_fulfilled")
async def handle_orders_fulfilled(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/fulfilled webhook"""
    return await process_webhook(
        request, "orders/fulfilled", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_partially_fulfilled")
async def handle_orders_partially_fulfilled(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/partially_fulfilled webhook"""
    return await process_webhook(
        request, "orders/partially_fulfilled", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/orders_paid")
async def handle_orders_paid(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle orders/paid webhook"""
    return await process_webhook(
        request, "orders/paid", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/returns_create")
async def handle_returns_create(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle returns/create webhook"""
    return await process_webhook(
        request, "returns/create", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/returns_requested")
async def handle_returns_requested(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle returns/requested webhook"""
    return await process_webhook(
        request, "returns/requested", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/returns_approved")
async def handle_returns_approved(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle returns/approved webhook"""
    return await process_webhook(
        request, "returns/approved", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/returns_declined")
async def handle_returns_declined(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle returns/declined webhook"""
    return await process_webhook(
        request, "returns/declined", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/returns_cancelled")
async def handle_returns_cancelled(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle returns/cancelled webhook"""
    return await process_webhook(
        request, "returns/cancelled", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/refunds_create")
async def handle_refunds_create(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle refunds/create webhook"""
    return await process_webhook(
        request, "refunds/create", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/fulfillments_create")
async def handle_fulfillments_create(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle fulfillments/create webhook"""
    return await process_webhook(
        request, "fulfillments/create", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/fulfillments_update")
async def handle_fulfillments_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle fulfillments/update webhook"""
    return await process_webhook(
        request, "fulfillments/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/fulfillments_cancel")
async def handle_fulfillments_cancel(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle fulfillments/cancel webhook"""
    return await process_webhook(
        request, "fulfillments/cancel", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/products_update")
async def handle_products_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle products/update webhook"""
    return await process_webhook(
        request, "products/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/product_variants_update")
async def handle_product_variants_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle product_variants/update webhook"""
    return await process_webhook(
        request, "product_variants/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


@router.post("/inventory_levels_update")
async def handle_inventory_levels_update(
    request: Request,
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256")
):
    """Handle inventory_levels/update webhook"""
    return await process_webhook(
        request, "inventory_levels/update", x_shopify_shop_domain, x_shopify_hmac_sha256
    )


async def process_webhook(
    request: Request,
    topic: str,
    shop_domain: str,
    hmac_signature: str
) -> JSONResponse:
    """
    Common webhook processing with HMAC verification
    """
    try:
        # Get raw body for HMAC verification
        body = await request.body()
        
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Missing X-Shopify-Shop-Domain header")
        
        if not hmac_signature:
            raise HTTPException(status_code=400, detail="Missing X-Shopify-Hmac-Sha256 header")
        
        # Normalize shop domain
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
        
        # Get store credentials for HMAC verification
        tenant_id = shop_domain
        credentials = await auth_service.get_decrypted_credentials(tenant_id)
        
        if not credentials:
            logger.warning(f"No credentials found for shop: {shop_domain}")
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Verify HMAC signature
        if not auth_service.verify_webhook(body, hmac_signature, credentials["api_secret"]):
            logger.error(f"HMAC verification failed for {shop_domain} - {topic}")
            raise HTTPException(status_code=401, detail="HMAC verification failed")
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process the webhook
        result = await webhook_processor.process_webhook(
            topic=topic,
            shop_domain=shop_domain,
            payload=payload
        )
        
        logger.info(f"Webhook {topic} processed successfully for {shop_domain}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "topic": topic,
                "shop": shop_domain,
                "processed_at": datetime.utcnow().isoformat(),
                "result": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook {topic} for {shop_domain}: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.get("/test")
async def webhook_test():
    """Test endpoint for webhook service"""
    return {
        "service": "webhooks",
        "status": "operational",
        "supported_topics": list(webhook_processor.handlers.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test/simulate")
async def simulate_webhook(
    topic: str,
    shop_domain: str,
    payload: dict
):
    """Test endpoint to simulate webhook processing (development only)"""
    try:
        result = await webhook_processor.process_webhook(
            topic=topic,
            shop_domain=shop_domain,
            payload=payload,
            webhook_id=f"test_{datetime.utcnow().timestamp()}"
        )
        
        return {
            "status": "success",
            "simulated": True,
            "topic": topic,
            "shop": shop_domain,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))