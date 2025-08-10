"""
Webhook Controller for Shopify Webhooks
Handles incoming webhook requests with HMAC verification
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
import json
import logging
from datetime import datetime

from ..services.webhook_handlers import webhook_processor
from ..modules.auth.service import auth_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


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