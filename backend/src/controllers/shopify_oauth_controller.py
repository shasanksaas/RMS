"""
Shopify OAuth Controller - Single-click OAuth endpoints
"""

import os
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from typing import Optional

from ..services.shopify_oauth_service import ShopifyOAuthService
from ..models.shopify import (
    ShopifyInstallRequest, ShopifyCallbackRequest,
    ShopifyInstallResponse, ShopifyConnectSuccessResponse, 
    ShopifyConnectionResponse
)

# Initialize router
router = APIRouter(prefix="/auth/shopify", tags=["shopify-oauth"])
security = HTTPBearer(auto_error=False)

# Initialize service
shopify_oauth = ShopifyOAuthService()

@router.get("/install", response_model=ShopifyInstallResponse)
async def initiate_shopify_install(
    shop: str = Query(..., description="Shop domain (e.g., 'rms34' or 'rms34.myshopify.com')")
):
    """
    Initiate Shopify OAuth installation flow
    
    This endpoint:
    1. Normalizes shop domain (rms34 → rms34.myshopify.com)
    2. Generates secure OAuth state
    3. Returns Shopify authorization URL
    4. Redirects user to Shopify for approval
    """
    # Check feature flag
    shopify_oauth_enabled = os.getenv('SHOPIFY_OAUTH_ENABLED', 'true').lower() == 'true'
    if not shopify_oauth_enabled:
        raise HTTPException(
            status_code=503, 
            detail={"error": "Shopify OAuth disabled", "message": "Shopify OAuth is currently disabled"}
        )
    
    try:
        install_request = ShopifyInstallRequest(shop=shop)
        install_response = await shopify_oauth.build_install_url(install_request)
        
        print(f"🚀 Shopify install initiated for shop: {install_response.shop}")
        return install_response
        
    except Exception as e:
        print(f"❌ Install initiation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/install-redirect")
async def redirect_to_shopify_install(
    shop: str = Query(..., description="Shop domain"),
    tenant_id: Optional[str] = Query(None, description="Current user's tenant ID")
):
    """
    Redirect endpoint that immediately sends user to Shopify OAuth
    Used by frontend "Login with Shopify" button
    
    Now includes current tenant context in OAuth state
    """
    # Check feature flag
    shopify_oauth_enabled = os.getenv('SHOPIFY_OAUTH_ENABLED', 'true').lower() == 'true'
    if not shopify_oauth_enabled:
        raise HTTPException(
            status_code=503, 
            detail={"error": "Shopify OAuth disabled", "message": "Shopify OAuth is currently disabled"}
        )
    
    try:        
        print(f"🔍 Install redirect - Shop: {shop}, Current Tenant: {tenant_id}")
        
        install_request = ShopifyInstallRequest(shop=shop)
        
        # Pass current tenant to OAuth service so it can be preserved in state
        install_response = await shopify_oauth.build_install_url(install_request, current_tenant_id=tenant_id)
        
        # Redirect user directly to Shopify OAuth page
        return RedirectResponse(
            url=install_response.install_url,
            status_code=302
        )
        
    except Exception as e:
        print(f"❌ Install redirect failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/callback")
async def handle_shopify_callback(
    request: Request,
    response: Response,
    code: str = Query(...),
    shop: str = Query(...), 
    state: str = Query(...),
    timestamp: str = Query(...),
    hmac: Optional[str] = Query(None)
):
    """
    Handle Shopify OAuth callback
    
    This endpoint:
    1. Verifies OAuth state and HMAC
    2. Exchanges code for access token
    3. Auto-provisions tenant based on shop
    4. Stores encrypted token
    5. Creates/updates user session
    6. Registers webhooks
    7. Queues 90-day backfill
    8. Sets session cookie and redirects to dashboard
    """
    # Check feature flag
    shopify_oauth_enabled = os.getenv('SHOPIFY_OAUTH_ENABLED', 'true').lower() == 'true'
    if not shopify_oauth_enabled:
        return RedirectResponse(
            url=f"/auth/login?error=oauth_disabled&message=Shopify OAuth is currently disabled",
            status_code=302
        )
    
    try:
        callback_request = ShopifyCallbackRequest(
            code=code,
            hmac=hmac or "",
            shop=shop,
            state=state,
            timestamp=timestamp
        )
        
        # Handle OAuth callback and get connection result
        connect_result = await shopify_oauth.handle_oauth_callback(callback_request)
        
        # Create proper JWT session for the authenticated user
        from src.services.auth_service import auth_service
        from ..config.database import get_database
        
        db = await get_database()
        
        # Find the user that was created/updated during OAuth
        user = await db.users.find_one({
            "tenant_id": connect_result.tenant_id,
            "role": "merchant"
        })
        
        if user:
            # Create JWT token for the user
            jwt_token = auth_service.create_access_token({
                "user_id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "tenant_id": user["tenant_id"]
            })
            
            print(f"✅ JWT token created for user: {user['email']}")
            
            # Set HTTP-only cookie with JWT token
            response.set_cookie(
                key="access_token",
                value=jwt_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400  # 24 hours
            )
            
            print(f"✅ Authentication cookie set for {user['email']}")
        else:
            print("⚠️ User not found after OAuth - redirecting to login")
        
        print(f"✅ Shopify connection complete for {connect_result.shop}")
        
        # Redirect to dashboard with connection success and authentication token
        # Instead of using the complex redirect_url, redirect directly to frontend dashboard
        dashboard_url = f"https://ecom-return-manager.preview.emergentagent.com/app/dashboard?connected=1&shop={connect_result.shop}&tenant_id={connect_result.tenant_id}"
        
        if user:
            # Add token to URL for frontend to handle (temporary solution)
            dashboard_url += f"&token={jwt_token}"
        
        print(f"🔄 Redirecting to: {dashboard_url}")
        
        return RedirectResponse(
            url=dashboard_url,
            status_code=302
        )
        
    except ValueError as e:
        print(f"❌ OAuth callback validation error: {e}")
        return RedirectResponse(
            url=f"/auth/login?error=oauth_invalid&message={str(e)}",
            status_code=302
        )
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return RedirectResponse(
            url=f"/auth/login?error=connection_failed&message={str(e)}",
            status_code=302
        )

@router.get("/debug/generate-state")
async def debug_generate_state(
    shop: str = Query(default="rms34", description="Shop to generate state for")
):
    """
    Debug endpoint to see what state we generate
    """
    try:
        shopify_oauth = ShopifyOAuthService()
        
        # Generate state like we do in the install flow
        state = shopify_oauth.create_oauth_state(
            shopify_oauth.normalize_shop_domain(shop)
        )
        
        # Also try to verify it immediately
        verification_result = shopify_oauth.verify_oauth_state(state)
        
        return {
            "generated_state": state,
            "state_length": len(state),
            "verification_works": verification_result is not None,
            "state_data": {
                "shop": verification_result.shop,
                "timestamp": verification_result.timestamp,
                "nonce": verification_result.nonce
            } if verification_result else None
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "traceback": str(e)
        }

@router.get("/debug/state")
async def debug_oauth_state(
    state: str = Query(..., description="State parameter to debug")
):
    """
    Debug endpoint to test OAuth state verification
    """
    try:
        shopify_oauth = ShopifyOAuthService()
        
        # Try to verify the state
        result = shopify_oauth.verify_oauth_state(state)
        
        if result:
            return {
                "valid": True,
                "state_data": {
                    "shop": result.shop,
                    "timestamp": result.timestamp,
                    "nonce": result.nonce,
                    "redirect_after": result.redirect_after
                }
            }
        else:
            return {
                "valid": False,
                "error": "State verification failed"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "traceback": str(e)
        }

@router.get("/status", response_model=ShopifyConnectionResponse)
async def get_shopify_connection_status(
    tenant_id: str = Query(..., description="Tenant ID to check connection for")
):
    """
    Get Shopify connection status for a tenant
    
    Returns:
    - Connection status (connected/disconnected)
    - Shop domain
    - Last sync time
    - Available scopes
    """
    try:
        print(f"🔍 Checking Shopify status for tenant: {tenant_id}")
        
        # Get database connection
        from ..config.database import get_database
        db = await get_database()
        
        # Query integration directly with detailed logging
        integration = await db["integrations_shopify"].find_one({"tenant_id": tenant_id})
        print(f"📊 Integration found: {integration is not None}")
        
        if not integration:
            print(f"📊 No integration found for tenant {tenant_id}")
            return ShopifyConnectionResponse(
                connected=False,
                status="disconnected",
                tenant_id=tenant_id,
                shop=None,
                last_sync_at=None,
                scopes=[]
            )
        
        # Extract data safely
        shop_domain = integration.get("shop", integration.get("shop_domain"))
        status = integration.get("status", "disconnected")
        connected = status == "connected"
        
        print(f"📊 Integration status: {status}, shop: {shop_domain}, connected: {connected}")
        
        response = ShopifyConnectionResponse(
            connected=connected,
            status=status,
            tenant_id=tenant_id,
            shop=shop_domain,
            shop_domain=shop_domain,
            last_sync_at=integration.get("last_sync_at"),
            scopes=integration.get("scopes", [])
        )
        
        print(f"✅ Status response created successfully for {tenant_id}")
        return response
        
    except Exception as e:
        print(f"❌ Status check failed for tenant {tenant_id}: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        
        # Return a safe fallback response instead of crashing
        return ShopifyConnectionResponse(
            connected=False,
            status="error",
            tenant_id=tenant_id,
            shop=None,
            last_sync_at=None,
            scopes=[],
            error=str(e)
        )

@router.post("/disconnect")
async def disconnect_shopify_store(
    tenant_id: str = Query(..., description="Tenant ID to disconnect")
):
    """
    Disconnect Shopify integration
    
    This endpoint:
    1. Marks integration as disconnected
    2. Keeps audit trail
    3. Clears session (if needed)
    4. Returns success status
    """
    try:
        success = await shopify_oauth.disconnect_shop(tenant_id)
        
        if success:
            return {"success": True, "message": "Store disconnected successfully"}
        else:
            raise HTTPException(status_code=404, detail="No connection found to disconnect")
            
    except Exception as e:
        print(f"❌ Disconnect failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect store")

# === Session Management Endpoints ===

@router.get("/session")
async def get_current_session(
    request: Request
):
    """
    Get current Shopify session information
    
    In production, this would decode the HttpOnly JWT session cookie
    For now, returns basic tenant info based on session
    """
    # Placeholder for session retrieval
    # In production, decode JWT from HttpOnly cookie
    return {
        "authenticated": False,
        "provider": "shopify",
        "tenant_id": None,
        "shop": None,
        "user_role": None
    }

@router.post("/session/create")
async def create_shopify_session(
    request: Request,
    response: Response,
    tenant_id: str,
    shop: str
):
    """
    Create authenticated session after successful OAuth
    
    This would typically:
    1. Generate JWT with tenant context
    2. Set HttpOnly, Secure, SameSite=Lax cookie
    3. Include tenant_id, shop, user_role in payload
    """
    # Placeholder for session creation
    # In production, create HttpOnly JWT session cookie
    
    session_data = {
        "tenant_id": tenant_id,
        "shop": shop,
        "user_role": "merchant_owner",
        "provider": "shopify",
        "created_at": "timestamp"
    }
    
    return {"success": True, "session": session_data}

@router.delete("/session")
async def destroy_shopify_session(
    request: Request,
    response: Response
):
    """
    Destroy current Shopify session (logout)
    
    This would:
    1. Clear HttpOnly session cookie
    2. Invalidate JWT token
    3. Return success status
    """
    # Placeholder for session destruction
    return {"success": True, "message": "Session destroyed"}

# === Admin-only endpoints ===

@router.get("/admin/connections")
async def list_all_shopify_connections():
    """
    Admin endpoint: List all Shopify connections across all tenants
    
    Requires admin role verification
    """
    # TODO: Add admin authentication check
    try:
        from ..config.database import get_database
        db = await get_database()
        
        connections = await db["integrations_shopify"].find(
            {}, 
            {"access_token_encrypted": 0}  # Don't expose encrypted tokens
        ).to_list(length=100)
        
        return {"connections": connections}
        
    except Exception as e:
        print(f"❌ Admin connections list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list connections")

@router.get("/admin/tenant/{tenant_id}")
async def get_tenant_shopify_details(tenant_id: str):
    """
    Admin endpoint: Get detailed Shopify integration info for specific tenant
    
    Requires admin role verification
    """
    # TODO: Add admin authentication check
    try:
        status = await shopify_oauth.get_connection_status(tenant_id)
        return status
        
    except Exception as e:
        print(f"❌ Admin tenant details failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant details")

# Integration endpoints that the frontend Integrations screen expects - MOVED TO shopify_integration_controller.py
integration_router = APIRouter(prefix="/integrations/shopify-oauth", tags=["shopify-oauth-integration"])

# Status endpoint moved to shopify_integration_controller.py for comprehensive status
# This avoids route conflicts and provides better integration status info

@integration_router.post("/disconnect")
async def disconnect_shopify_integration(request: Request):
    """
    Disconnect Shopify integration for the current tenant
    
    Removes integration data and allows reconnection
    """
    # Get tenant from X-Tenant-Id header
    current_tenant = request.headers.get("X-Tenant-Id")
    if not current_tenant:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    try:
        # Use the shopify oauth service to disconnect
        success = await shopify_oauth.disconnect_shop(current_tenant)
        
        if success:
            return {
                "success": True,
                "message": "Shopify integration disconnected successfully",
                "tenant_id": current_tenant
            }
        else:
            return {
                "success": False,
                "message": "No Shopify integration found to disconnect",
                "tenant_id": current_tenant
            }
        
    except Exception as e:
        print(f"❌ Disconnect failed for {current_tenant}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Shopify integration: {str(e)}"
        )

@integration_router.post("/resync")
async def trigger_shopify_resync(
    request: Request
):
    """
    Trigger manual Shopify data resync for the current tenant
    
    Used by the frontend Integrations screen "Resync" button
    """
    # Get tenant from X-Tenant-Id header (sent by frontend)
    current_tenant = request.headers.get("X-Tenant-Id")
    if not current_tenant:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    # Check feature flag
    shopify_oauth_enabled = os.getenv('SHOPIFY_OAUTH_ENABLED', 'true').lower() == 'true'
    if not shopify_oauth_enabled:
        raise HTTPException(
            status_code=503,
            detail="Shopify integration is currently disabled"
        )
    
    try:
        # Check if tenant has Shopify connection
        status = await shopify_oauth.get_connection_status(current_tenant)
        
        if not status.connected:
            raise HTTPException(
                status_code=400,
                detail="Shopify integration not connected. Please connect first."
            )
        
        # Trigger actual data sync by calling shopify_oauth service
        await shopify_oauth._queue_data_backfill(current_tenant, status.shop)
        
        print(f"🔄 Manual resync completed for tenant: {current_tenant}")
        
        return {
            "success": True,
            "message": "Data resync initiated successfully",
            "tenant_id": current_tenant,
            "job_id": f"sync_{current_tenant}_{int(time.time())}",  # Add job_id that frontend expects
            "sync_initiated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Integration resync failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to trigger resync: {str(e)}"
        )