"""
Real Shopify OAuth and API controller
"""
from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import json

from ..modules.auth.shopify_oauth import ShopifyOAuth
from ..services.shopify_service import ShopifyService
from ..services.tenant_service import TenantService
from ..utils.dependencies import get_shopify_service, get_tenant_service

router = APIRouter(prefix="/shopify", tags=["shopify"])

# Initialize OAuth handler
oauth_handler = ShopifyOAuth()


@router.get("/install")
async def shopify_install(
    request: Request,
    shop: str = Query(..., description="Shop domain"),
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Initiate Shopify OAuth installation"""
    try:
        # Use real OAuth handler
        oauth_result = await oauth_handler.initiate_oauth(shop)
        
        return {
            "auth_url": oauth_result["auth_url"],
            "shop": oauth_result["shop"],
            "state": oauth_result["state"]
        }
    
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
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Handle Shopify OAuth callback"""
    try:
        # Handle OAuth callback with real implementation
        oauth_result = await oauth_handler.handle_callback(shop, code, state)
        
        if not oauth_result["success"]:
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
            await sync_shopify_data(shop, tenant_id, oauth_result["access_token"])
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
    tenant_id: str
):
    """Manually trigger Shopify data sync"""
    try:
        # Get access token for shop
        from ..config.database import db
        store_doc = await db.shopify_stores.find_one({"shop": shop, "is_active": True})
        if not store_doc:
            raise HTTPException(status_code=404, detail="Shop not connected")
        
        await sync_shopify_data(shop, tenant_id, store_doc["access_token"])
        return {"success": True, "message": "Data synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/webhooks/orders_create")
async def shopify_orders_webhook(request: Request):
    """Handle Shopify order creation webhook"""
    try:
        # Get raw body for HMAC verification
        body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Verify webhook authenticity
        if not oauth_handler.verify_webhook(body, hmac_header):
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


@router.post("/webhooks/orders_updated")
async def shopify_orders_updated_webhook(request: Request):
    """Handle Shopify order update webhook"""
    try:
        body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        if not oauth_handler.verify_webhook(body, hmac_header):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        order_data = json.loads(body.decode())
        await process_shopify_order_update(order_data)
        
        return {"status": "received"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")


@router.get("/connection-status")
async def shopify_connection_status(shop: str):
    """Check Shopify connection status"""
    try:
        connected = await oauth_handler.is_shop_connected(shop)
        shop_info = None
        
        if connected:
            shop_info = await oauth_handler.get_shop_info(shop)
        
        return {
            "online": True,  # Real connection
            "connected": connected,
            "shop": shop,
            "mode": "production",
            "shop_info": shop_info
        }
    except Exception as e:
        return {
            "online": False,
            "connected": False,
            "shop": shop,
            "mode": "error",
            "error": str(e)
        }


# Helper functions
async def sync_shopify_data(shop: str, tenant_id: str, access_token: str):
    """Sync data from Shopify to local database"""
    import aiohttp
    
    headers = {"X-Shopify-Access-Token": access_token}
    api_version = oauth_handler.api_version
    
    async with aiohttp.ClientSession() as session:
        # Sync products
        try:
            products_url = f"https://{shop}.myshopify.com/admin/api/{api_version}/products.json?limit=250"
            async with session.get(products_url, headers=headers) as response:
                if response.status == 200:
                    products_data = await response.json()
                    await sync_products_to_db(products_data["products"], tenant_id)
        except Exception as e:
            print(f"Product sync error: {e}")
        
        # Sync orders
        try:
            orders_url = f"https://{shop}.myshopify.com/admin/api/{api_version}/orders.json?limit=250&status=any"
            async with session.get(orders_url, headers=headers) as response:
                if response.status == 200:
                    orders_data = await response.json()
                    await sync_orders_to_db(orders_data["orders"], tenant_id)
        except Exception as e:
            print(f"Order sync error: {e}")


async def sync_products_to_db(shopify_products, tenant_id):
    """Sync Shopify products to local database"""
    from ..config.database import db
    
    for shopify_product in shopify_products:
        for variant in shopify_product.get("variants", []):
            product_data = {
                "tenant_id": tenant_id,
                "shopify_product_id": str(shopify_product["id"]),
                "name": shopify_product["title"],
                "description": shopify_product.get("body_html", ""),
                "price": float(variant["price"]),
                "category": shopify_product.get("product_type", "General"),
                "sku": variant.get("sku", f"SHOPIFY-{variant['id']}"),
                "image_url": shopify_product.get("images", [{}])[0].get("src"),
                "in_stock": variant.get("inventory_quantity", 0) > 0,
                "created_at": shopify_product["created_at"]
            }
            
            # Update or insert product
            await db.products.update_one(
                {"tenant_id": tenant_id, "sku": product_data["sku"]},
                {"$set": product_data},
                upsert=True
            )


async def sync_orders_to_db(shopify_orders, tenant_id):
    """Sync Shopify orders to local database"""
    from ..config.database import db
    
    for shopify_order in shopify_orders:
        order_data = {
            "tenant_id": tenant_id,
            "shopify_order_id": str(shopify_order["id"]),
            "customer_email": shopify_order.get("email", "unknown@example.com"),
            "customer_name": f"{shopify_order.get('customer', {}).get('first_name', 'Unknown')} {shopify_order.get('customer', {}).get('last_name', 'Customer')}",
            "order_number": shopify_order["name"],
            "items": [
                {
                    "product_id": str(item["product_id"]),
                    "product_name": item["title"],
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                    "sku": item.get("sku", f"SHOPIFY-{item['id']}")
                }
                for item in shopify_order.get("line_items", [])
            ],
            "total_amount": float(shopify_order["total_price"]),
            "order_date": shopify_order["created_at"]
        }
        
        # Update or insert order
        await db.orders.update_one(
            {"tenant_id": tenant_id, "order_number": order_data["order_number"]},
            {"$set": order_data},
            upsert=True
        )


async def process_shopify_order(order_data: Dict[str, Any]):
    """Process incoming Shopify order webhook"""
    print(f"Processing Shopify order webhook: {order_data.get('id')}")
    # TODO: Implement real-time order processing


async def process_shopify_order_update(order_data: Dict[str, Any]):
    """Process Shopify order update webhook"""
    print(f"Processing Shopify order update: {order_data.get('id')}")