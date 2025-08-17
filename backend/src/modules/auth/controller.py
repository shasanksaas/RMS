"""
Auth Controller for Shopify OAuth 2.0 Dynamic Connectivity
Handles authentication endpoints and store management with automatic environment detection
"""

import os
import urllib.parse
from fastapi import APIRouter, HTTPException, Request, Depends, Query, Body
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .service import auth_service
from ...utils.exceptions import AuthenticationError, ValidationError
from ...utils.dependencies import get_current_user
from ...middleware.security import verify_tenant
from ...config.environment import env_config

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response validation
class InitiateOAuthRequest(BaseModel):
    shop: str = Field(..., description="Shop domain (e.g., 'demo-store' or 'demo-store.myshopify.com')")
    api_key: str = Field(..., description="Shopify API Key from Partner Dashboard")
    api_secret: str = Field(..., description="Shopify API Secret from Partner Dashboard")

class InitiateOAuthResponse(BaseModel):
    auth_url: str
    shop: str
    state: str
    scopes_requested: List[str]
    redirect_instructions: str = "Redirect user to auth_url to complete OAuth flow"

class CallbackResponse(BaseModel):
    success: bool
    tenant_id: str
    shop: str
    shop_info: Dict[str, Any]
    scopes_granted: List[str]
    webhook_status: str
    connected_at: str

class StoreConnectionInfo(BaseModel):
    tenant_id: str
    shop: str
    shop_info: Dict[str, Any]
    connected_at: datetime
    last_sync: Optional[datetime]
    webhook_status: str
    is_active: bool
    scopes: List[str]

class ConnectedStore(BaseModel):
    tenant_id: str
    shop: str
    shop_name: str
    connected_at: datetime
    last_sync: Optional[datetime]
    webhook_status: str
    is_active: bool


@router.post("/initiate", response_model=InitiateOAuthResponse)
async def initiate_oauth(request: InitiateOAuthRequest):
    """
    Initiate OAuth flow with dynamic Shopify credentials
    
    This endpoint accepts merchant-provided API credentials and initiates 
    the OAuth flow for dynamic store connectivity.
    """
    try:
        result = await auth_service.initiate_oauth(
            shop=request.shop,
            api_key=request.api_key,
            api_secret=request.api_secret
        )
        
        return InitiateOAuthResponse(
            **result,
            redirect_instructions="Redirect user to auth_url to complete OAuth flow"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth initiation failed: {str(e)}")


@router.get("/shopify/install")
async def shopify_oauth_install(
    request: Request,
    shop: str = Query(..., description="Shop domain (e.g., rms34.myshopify.com)")
):
    """
    Shopify OAuth Install Route with Dynamic URL Detection
    Automatically detects the correct APP_URL and builds redirect_uri
    
    Usage: GET /api/auth/shopify/install?shop=rms34.myshopify.com
    """
    try:
        # Ensure environment config is initialized
        await env_config.initialize()
        
        # Update APP_URL from request if needed (for dynamic environments)
        request_host = request.headers.get('host')
        request_scheme = 'https' if request.headers.get('x-forwarded-proto') == 'https' or request.url.scheme == 'https' else 'http'
        if request_host:
            env_config.update_app_url_from_request(request_host, request_scheme)
        
        # Validate shop domain
        if not shop:
            raise HTTPException(status_code=400, detail="Shop domain is required")
            
        # Normalize shop domain to ensure it ends with .myshopify.com
        if not shop.endswith('.myshopify.com'):
            shop = f"{shop}.myshopify.com"
        
        # Validate shop domain format
        if not shop.replace('.myshopify.com', '').replace('-', '').replace('_', '').isalnum():
            raise HTTPException(status_code=400, detail="Invalid shop domain format")
        
        # Get Shopify credentials from environment config
        shopify_credentials = env_config.get_shopify_credentials()
        api_key = shopify_credentials.get('api_key')
        
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Shopify API key not configured. Set SHOPIFY_API_KEY environment variable."
            )
        
        # Get scopes and redirect URI from environment config
        scopes = env_config.get_shopify_scopes()
        redirect_uri = env_config.get_oauth_redirect_uri()
        
        # Log the URLs being used for debugging
        print(f"🔗 OAuth Install Request:")
        print(f"   APP_URL: {env_config.get_app_url()}")
        print(f"   Redirect URI: {redirect_uri}")
        print(f"   Shop: {shop}")
        
        # Generate and store CSRF state token
        state = auth_service.generate_oauth_state()
        await auth_service.store_oauth_state(shop, state)
        
        # Build Shopify authorization URL
        auth_url = f"https://{shop}/admin/oauth/authorize"
        params = {
            "client_id": api_key,
            "scope": scopes,
            "redirect_uri": redirect_uri,
            "state": state,
            "grant_options[]": "offline"  # Request offline access
        }
        
        # Build query string
        query_params = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        full_auth_url = f"{auth_url}?{query_params}"
        
        # 302 redirect to Shopify authorize URL
        return RedirectResponse(url=full_auth_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ OAuth installation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth installation failed: {str(e)}")


@router.get("/shopify/callback")
async def shopify_oauth_callback(
    request: Request,
    shop: str = Query(..., description="Shop domain"),
    code: str = Query(..., description="Authorization code from Shopify"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    hmac: Optional[str] = Query(None, description="HMAC signature from Shopify"),
    timestamp: Optional[str] = Query(None, description="Request timestamp")
):
    """
    Shopify OAuth Callback Route with Dynamic URL Detection
    Processes the callback after user authorizes the app
    
    Usage: This is called automatically by Shopify after user approval
    """
    try:
        # Ensure environment config is initialized
        await env_config.initialize()
        
        # Update APP_URL from request if needed
        request_host = request.headers.get('host')
        request_scheme = 'https' if request.headers.get('x-forwarded-proto') == 'https' or request.url.scheme == 'https' else 'http'
        if request_host:
            env_config.update_app_url_from_request(request_host, request_scheme)
        
        print(f"🔄 OAuth Callback:")
        print(f"   APP_URL: {env_config.get_app_url()}")
        print(f"   Shop: {shop}")
        print(f"   State: {state}")
        
        # Verify HMAC signature for security
        if hmac:
            await auth_service.verify_shopify_hmac(shop, code, state, hmac, timestamp)
        
        # Verify CSRF state token
        if not await auth_service.verify_oauth_state(shop, state):
            raise HTTPException(status_code=400, detail="Invalid state parameter - CSRF protection")
        
        # Exchange code for access token
        access_token = await auth_service.exchange_code_for_token(shop, code)
        
        # Get shop information using the access token
        shop_info = await auth_service.get_shop_info(shop, access_token)
        
        # Persist credentials by tenant (encrypted)
        tenant_data = {
            "shop": shop,
            "access_token": access_token,  # Will be encrypted by service
            "scopes": env_config.get_shopify_scopes(),
            "installed_at": datetime.utcnow().isoformat(),
            "provider": "shopify",
            "shop_info": shop_info
        }
        
        tenant_id = await auth_service.save_shop_credentials(tenant_data)
        
        # Clean up state token
        await auth_service.cleanup_oauth_state(shop, state)
        
        # Immediate data bootstrap - enqueue background job
        await auth_service.enqueue_initial_data_sync(tenant_id, shop, access_token)
        
        # Register webhooks
        await auth_service.register_shopify_webhooks(shop, access_token)
        
        # 302 redirect to integrations page with success (using dynamic APP_URL)
        app_url = env_config.get_app_url()
        success_url = f"{app_url}/app/settings/integrations?connected=1&shop={shop}"
        
        print(f"✅ OAuth Success - Redirecting to: {success_url}")
        
        return RedirectResponse(url=success_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        
        # Build error URL using dynamic APP_URL
        app_url = env_config.get_app_url()
        error_url = f"{app_url}/app/settings/integrations?error=1&message=Connection failed"
        
        return RedirectResponse(url=error_url, status_code=302)


@router.get("/callback")
async def oauth_callback(
    shop: str = Query(..., description="Shop domain"),
    code: str = Query(..., description="Authorization code from Shopify"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    hmac: Optional[str] = Query(None, description="HMAC signature from Shopify"),
    timestamp: Optional[str] = Query(None, description="Request timestamp")
):
    """
    Legacy OAuth callback - redirects to new Shopify callback
    Maintains backward compatibility
    """
    # Redirect to the new Shopify-specific callback
    query_params = f"?shop={shop}&code={code}&state={state}"
    if hmac:
        query_params += f"&hmac={hmac}"
    if timestamp:
        query_params += f"&timestamp={timestamp}"
        
    callback_url = f"/api/auth/shopify/callback{query_params}"
    full_callback_url = f"https://ecom-return-manager.preview.emergentagent.com{callback_url}"
    
    return RedirectResponse(url=full_callback_url, status_code=302)


@router.get("/callback/json", response_model=CallbackResponse)
async def oauth_callback_json(
    shop: str = Query(..., description="Shop domain"),
    code: str = Query(..., description="Authorization code from Shopify"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    JSON version of OAuth callback for API clients
    """
    try:
        result = await auth_service.handle_oauth_callback(
            shop=shop,
            code=code,
            state=state
        )
        return CallbackResponse(**result)
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.get("/stores", response_model=List[ConnectedStore])
async def list_connected_stores(
    user_id: Optional[str] = Query(None, description="Filter by user who connected the store")
):
    """
    List all connected Shopify stores
    """
    try:
        stores = await auth_service.list_connected_stores(user_id=user_id)
        return [ConnectedStore(**store) for store in stores]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list stores: {str(e)}")


@router.get("/stores/{tenant_id}", response_model=StoreConnectionInfo)
async def get_store_connection(
    tenant_id: str,
    current_tenant: str = Depends(verify_tenant)
):
    """
    Get detailed connection information for a specific store
    """
    # Verify tenant access
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this store")
    
    try:
        connection_info = await auth_service.get_store_connection(tenant_id)
        
        if not connection_info:
            raise HTTPException(status_code=404, detail="Store connection not found")
        
        return StoreConnectionInfo(**connection_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get store info: {str(e)}")


@router.post("/stores/{tenant_id}/disconnect")
async def disconnect_store(
    tenant_id: str,
    user_id: Optional[str] = Body(None, description="User performing the disconnect"),
    current_tenant: str = Depends(verify_tenant)
):
    """
    Disconnect a Shopify store and revoke access
    """
    # Verify tenant access
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this store")
    
    try:
        success = await auth_service.disconnect_store(tenant_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Store connection not found")
        
        return {
            "success": True,
            "message": f"Store {tenant_id} disconnected successfully",
            "disconnected_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect store: {str(e)}")


@router.post("/stores/{tenant_id}/webhooks/register")
async def register_webhooks(
    tenant_id: str,
    current_tenant: str = Depends(verify_tenant)
):
    """
    Re-register webhooks for a connected store
    """
    # Verify tenant access
    if current_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this store")
    
    try:
        credentials = await auth_service.get_decrypted_credentials(tenant_id)
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Store credentials not found")
        
        result = await auth_service.register_webhooks(
            tenant_id=tenant_id,
            shop=credentials["shop"],
            access_token=credentials["access_token"]
        )
        
        return {
            "success": True,
            "message": f"Webhook registration completed",
            "registered": result["registered"],
            "failed": result["failed"],
            "details": result["details"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register webhooks: {str(e)}")


@router.get("/status")
async def auth_status():
    """
    Get authentication service status
    """
    return {
        "service": "shopify_auth",
        "status": "operational",
        "api_version": "2025-07",
        "redirect_uri": auth_service.base_redirect_uri,
        "required_scopes": auth_service.scopes,
        "encryption": "fernet" if auth_service.encryption_key else "none",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test/validate")
async def validate_credentials(request: InitiateOAuthRequest):
    """
    Test endpoint to validate credentials format without initiating OAuth
    """
    try:
        shop = auth_service.normalize_shop_domain(request.shop)
        
        validations = {
            "shop_domain": {
                "value": shop,
                "valid": auth_service.validate_shop_domain(request.shop),
                "normalized": shop
            },
            "api_key": {
                "value": request.api_key[:8] + "..." if len(request.api_key) > 8 else request.api_key,
                "valid": auth_service.validate_credentials(request.api_key, request.api_secret),
                "length": len(request.api_key)
            },
            "api_secret": {
                "value": request.api_secret[:8] + "..." if len(request.api_secret) > 8 else request.api_secret,
                "valid": auth_service.validate_credentials(request.api_key, request.api_secret),
                "length": len(request.api_secret)
            }
        }
        
        all_valid = all(validation["valid"] for validation in validations.values())
        
        return {
            "overall_valid": all_valid,
            "validations": validations,
            "ready_for_oauth": all_valid,
            "potential_auth_url": f"https://{shop}.myshopify.com/admin/oauth/authorize" if shop else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat()
    }