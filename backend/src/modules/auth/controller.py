"""
Auth Controller for Shopify OAuth 2.0 Dynamic Connectivity
Handles authentication endpoints and store management
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query, Body
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .service import auth_service
from ...utils.exceptions import AuthenticationError, ValidationError
from ...utils.dependencies import get_current_user
from ...middleware.security import verify_tenant

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


@router.get("/callback")
async def oauth_callback(
    shop: str = Query(..., description="Shop domain"),
    code: str = Query(..., description="Authorization code from Shopify"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    hmac: Optional[str] = Query(None, description="HMAC signature from Shopify"),
    timestamp: Optional[str] = Query(None, description="Request timestamp")
):
    """
    Handle OAuth callback from Shopify
    
    This endpoint processes the callback after user authorizes the app,
    exchanges the code for an access token, and sets up the store.
    """
    try:
        result = await auth_service.handle_oauth_callback(
            shop=shop,
            code=code,
            state=state
        )
        
        # Redirect to success page with tenant info
        tenant_id = result["tenant_id"]
        shop_name = result["shop_info"].get("name", result["shop"])
        
        # In production, redirect to frontend success page
        success_url = f"https://easyreturns.preview.emergentagent.com/app/settings/integrations?connected=true&tenant={tenant_id}&shop={shop_name}"
        
        return RedirectResponse(url=success_url, status_code=302)
        
    except AuthenticationError as e:
        # Redirect to error page
        error_url = f"https://easyreturns.preview.emergentagent.com/app/settings/integrations?error=auth&message={str(e)}"
        return RedirectResponse(url=error_url, status_code=302)
    except Exception as e:
        error_url = f"https://easyreturns.preview.emergentagent.com/app/settings/integrations?error=system&message=Connection failed"
        return RedirectResponse(url=error_url, status_code=302)


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