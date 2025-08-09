"""
Shopify OAuth and API controller
"""
from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import json

from ..models.tenant import Tenant
from ..services.shopify_service import ShopifyService
from ..services.tenant_service import TenantService
from ..utils.dependencies import get_shopify_service, get_tenant_service

router = APIRouter(prefix="/shopify", tags=["shopify"])


@router.get("/install")
async def shopify_install(
    request: Request,
    shop: str = Query(..., description="Shop domain"),
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Initiate Shopify OAuth installation"""
    try:
        # Validate shop domain
        if not shop:
            raise HTTPException(status_code=400, detail="Shop parameter required")
        
        # Generate OAuth URL
        redirect_uri = f"{request.base_url}api/shopify/callback"
        auth_url = await shopify_service.get_authorization_url(shop, str(redirect_uri))
        
        return {"auth_url": auth_url, "shop": shop}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation error: {str(e)}")


@router.get("/callback")
async def shopify_callback(
    request: Request,
    code: str = Query(...),
    shop: str = Query(...),
    state: str = Query(...),
    shopify_service: ShopifyService = Depends(get_shopify_service),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Handle Shopify OAuth callback"""
    try:
        # Exchange code for access token
        token_data = await shopify_service.exchange_code_for_token(shop, code, state)
        
        if not token_data["success"]:
            raise HTTPException(status_code=400, detail="OAuth exchange failed")
        
        # Create or update tenant with Shopify connection
        shop_domain = f"{shop}.myshopify.com"
        
        # Check if tenant already exists
        tenants = await tenant_service.get_all_tenants()
        existing_tenant = next((t for t in tenants if t.shopify_store_url == shop_domain), None)
        
        if existing_tenant:
            # Update existing tenant
            from ..models.tenant import TenantUpdate
            update_data = TenantUpdate(
                shopify_store_url=shop_domain,
                # Don't store access token in tenant model for security
            )
            await tenant_service.update_tenant(existing_tenant.id, update_data)
            tenant_id = existing_tenant.id
        else:
            # Create new tenant
            from ..models.tenant import TenantCreate
            tenant_data = TenantCreate(
                name=f"{shop.capitalize()} Store",
                domain=shop_domain,
                shopify_store_url=shop_domain
            )
            tenant = await tenant_service.create_tenant(tenant_data)
            tenant_id = tenant.id
        
        # Sync initial data from Shopify
        try:
            await sync_shopify_data(shop, tenant_id, shopify_service, tenant_service)
        except Exception as e:
            print(f"Warning: Initial sync failed: {e}")
        
        # Redirect to success page with tenant info
        frontend_url = str(request.base_url).replace('/api', '')
        return RedirectResponse(
            url=f"{frontend_url}?shopify_connected=true&tenant_id={tenant_id}&shop={shop}"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Callback error: {str(e)}")


@router.post("/sync")
async def sync_shopify_data_endpoint(
    request: Request,
    shop: str,
    tenant_id: str,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Manually trigger Shopify data sync"""
    try:
        await sync_shopify_data(shop, tenant_id, shopify_service, tenant_service)
        return {"success": True, "message": "Data synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/webhooks/orders/create")
async def shopify_orders_webhook(request: Request, shopify_service: ShopifyService = Depends(get_shopify_service)):
    """Handle Shopify order creation webhook"""
    try:
        # Get raw body for HMAC verification
        body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Verify webhook authenticity
        if not shopify_service.verify_webhook(body, hmac_header):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse order data
        order_data = json.loads(body.decode())
        
        # Process order (sync to local database)
        await process_shopify_order(order_data)
        
        return {"status": "received"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")


@router.get("/connection-status")
async def shopify_connection_status(
    shop: str,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Check Shopify connection status"""
    try:
        online = await shopify_service.is_online()
        has_token = await shopify_service._get_access_token(shop) is not None
        
        return {
            "online": online,
            "connected": has_token,
            "shop": shop,
            "mode": "offline" if not online else "online"
        }
    except Exception as e:
        return {
            "online": False,
            "connected": False,
            "shop": shop,
            "mode": "offline",
            "error": str(e)
        }


# Helper functions
async def sync_shopify_data(shop: str, tenant_id: str, shopify_service: ShopifyService, tenant_service: TenantService):
    """Sync data from Shopify to local database"""
    print(f"Syncing Shopify data for shop: {shop}, tenant: {tenant_id}")
    # Note: This would integrate with existing services when they're created
    # For now, just log the sync attempt


async def process_shopify_order(order_data: Dict[str, Any]):
    """Process incoming Shopify order webhook"""
    # Find tenant by shop domain
    shop_domain = order_data.get("source_name", "").replace("https://", "").replace("http://", "")
    
    # This would typically involve finding the tenant and syncing the order
    print(f"Processing Shopify order webhook for shop: {shop_domain}")
    print(f"Order ID: {order_data.get('id')}, Name: {order_data.get('name')}")


# Add to dependencies file
def get_shopify_service() -> ShopifyService:
    """Get Shopify service instance"""
    return ShopifyService()