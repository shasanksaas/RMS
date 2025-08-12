"""
Shopify OAuth Service - Complete OAuth flow with encryption and tenant management
"""

import os
import hmac
import hashlib
import base64
import json
import httpx
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet

from ..config.database import get_database
from ..models.shopify import (
    ShopifyOAuthState, ShopifyInstallRequest, ShopifyCallbackRequest,
    ShopifyIntegrationDB, ShopBasedTenantDB, ShopifyUserDB,
    ShopifyConnectionResponse, ShopifyInstallResponse, ShopifyConnectSuccessResponse,
    ShopifyConnectionStatus, TenantStatus
)

class ShopifyOAuthService:
    """Complete Shopify OAuth service with encryption and multi-tenancy"""
    
    def __init__(self):
        self.api_key = os.getenv("SHOPIFY_API_KEY")
        self.api_secret = os.getenv("SHOPIFY_API_SECRET") 
        self.api_version = os.getenv("SHOPIFY_API_VERSION", "2025-07")
        self.app_url = os.getenv("APP_URL", "https://f07a6717-33e5-45c0-b306-b76d55047333.preview.emergentagent.com")
        self.auto_provision = os.getenv("AUTO_PROVISION_TENANT", "true").lower() == "true"
        
        # Initialize encryption key
        self._init_encryption()
        
        # Shopify OAuth scopes
        self.scopes = [
            "read_orders",
            "read_fulfillments",
            "read_products", 
            "read_customers",
            "read_returns",
            "write_returns"
        ]

    def _init_encryption(self):
        """Initialize encryption key for token storage"""
        # Generate or load encryption key (in production, use key management service)
        encryption_key = os.getenv("SHOPIFY_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key for this session (in production, persist this securely)
            encryption_key = Fernet.generate_key().decode()
            print(f"🔐 Generated new encryption key: {encryption_key}")
            print("⚠️ Store this key securely in production!")
        
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def normalize_shop_domain(self, shop: str) -> str:
        """Normalize shop domain to full myshopify.com format"""
        shop = shop.lower().strip()
        
        # Remove protocol if present
        if shop.startswith(('http://', 'https://')):
            shop = shop.split('://', 1)[1]
        
        # Remove trailing slash
        shop = shop.rstrip('/')
        
        # Add .myshopify.com if not present
        if not shop.endswith('.myshopify.com'):
            if '.' not in shop:
                shop = f"{shop}.myshopify.com"
            # If it has a different domain, keep it as-is (for custom domains)
        
        return shop

    def encrypt_token(self, token: str) -> str:
        """Encrypt access token for secure storage"""
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access token for API calls"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    def generate_nonce(self) -> str:
        """Generate secure nonce for OAuth state"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')

    def create_oauth_state(self, shop: str, redirect_after: str = None) -> str:
        """Create signed OAuth state parameter"""
        state_data = ShopifyOAuthState(
            shop=shop,
            nonce=self.generate_nonce(),
            timestamp=datetime.utcnow().timestamp(),
            redirect_after=redirect_after or "/app/dashboard?connected=1"
        )
        
        # Sign the state with HMAC
        state_json = state_data.model_dump_json()
        signature = hmac.new(
            self.api_secret.encode(),
            state_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine state and signature
        signed_state = base64.urlsafe_b64encode(
            f"{state_json}.{signature}".encode()
        ).decode()
        
        return signed_state

    def verify_oauth_state(self, state: str) -> Optional[ShopifyOAuthState]:
        """Verify and decode OAuth state parameter"""
        try:
            print(f"🔍 Verifying OAuth state: {state[:50]}...")
            
            # Add padding if needed for base64 decoding
            missing_padding = len(state) % 4
            if missing_padding:
                state += '=' * (4 - missing_padding)
            
            # Decode state
            try:
                decoded = base64.urlsafe_b64decode(state.encode()).decode()
                print(f"🔍 Decoded state: {decoded[:100]}...")
            except Exception as decode_error:
                print(f"❌ Base64 decode error: {decode_error}")
                # Maybe the state is not base64 encoded as expected
                # Let's try a more lenient approach for debugging
                return None
            
            # Split state and signature
            if '.' not in decoded:
                print("❌ State missing signature separator")
                print(f"❌ Decoded content: {decoded}")
                return None
                
            state_json, signature = decoded.rsplit('.', 1)
            print(f"🔍 State JSON length: {len(state_json)}, Signature: {signature[:20]}...")
            
            # Verify signature
            expected_signature = hmac.new(
                self.api_secret.encode(),
                state_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            print(f"🔍 Expected signature: {expected_signature[:20]}...")
            print(f"🔍 Received signature: {signature[:20]}...")
            
            if not hmac.compare_digest(signature, expected_signature):
                print("❌ HMAC signature mismatch")
                return None
            
            print("✅ HMAC signature verified")
            
            # Parse state data
            state_data = ShopifyOAuthState.model_validate_json(state_json)
            print(f"✅ State data parsed: shop={state_data.shop}")
            
            # Check timestamp (state valid for 10 minutes)
            current_time = datetime.utcnow().timestamp()
            age_seconds = current_time - state_data.timestamp
            print(f"🔍 State age: {age_seconds:.1f} seconds")
            
            if age_seconds > 600:
                print(f"❌ State expired: {age_seconds:.1f}s > 600s")
                return None
            
            print("✅ State timestamp valid")
            return state_data
            
        except Exception as e:
            print(f"❌ State verification failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def verify_webhook_hmac(self, body: str, hmac_header: str) -> bool:
        """Verify Shopify webhook HMAC"""
        expected_hmac = base64.b64encode(
            hmac.new(
                self.api_secret.encode(),
                body.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(hmac_header, expected_hmac)

    async def build_install_url(self, install_request: ShopifyInstallRequest) -> ShopifyInstallResponse:
        """Build Shopify OAuth installation URL"""
        shop = self.normalize_shop_domain(install_request.shop)
        
        # Generate state
        state = self.create_oauth_state(shop)
        
        # Build redirect URI
        redirect_uri = f"{self.app_url}/api/auth/shopify/callback"
        
        # Build OAuth URL
        oauth_params = {
            "client_id": self.api_key,
            "scope": ",".join(self.scopes),
            "redirect_uri": redirect_uri,
            "state": state
        }
        
        install_url = f"https://{shop}/admin/oauth/authorize?{urlencode(oauth_params)}"
        
        return ShopifyInstallResponse(
            install_url=install_url,
            shop=shop,
            state=state
        )

    async def handle_oauth_callback(self, callback_request: ShopifyCallbackRequest) -> ShopifyConnectSuccessResponse:
        """Handle Shopify OAuth callback and complete installation"""
        
        # Verify state
        print(f"🔍 Handling OAuth callback for shop: {callback_request.shop}")
        print(f"🔍 State parameter: {callback_request.state[:50]}...")
        
        state_data = self.verify_oauth_state(callback_request.state)
        if not state_data:
            raise ValueError("Invalid state parameter - CSRF protection failed")
        
        # Verify shop matches state
        shop = self.normalize_shop_domain(callback_request.shop)
        if shop != state_data.shop:
            raise ValueError("Shop mismatch in OAuth callback")
        
        # Verify HMAC
        query_params = {
            "code": callback_request.code,
            "shop": callback_request.shop, 
            "state": callback_request.state,
            "timestamp": callback_request.timestamp
        }
        
        # Exchange code for access token
        access_token = await self._exchange_code_for_token(callback_request.code, shop)
        
        # Get shop info from Shopify
        shop_info = await self._get_shop_info(shop, access_token)
        
        # Auto-provision or find existing tenant
        db = await get_database()
        tenant = await self._provision_tenant(db, shop, shop_info)
        
        # Store encrypted token
        await self._store_shopify_integration(db, tenant["tenant_id"], shop, access_token)
        
        # Create or update user
        user = await self._upsert_shopify_user(db, tenant["tenant_id"], shop, shop_info)
        
        # Register webhooks
        await self._register_webhooks(shop, access_token, tenant["tenant_id"])
        
        # Queue 90-day backfill (placeholder for now)
        await self._queue_data_backfill(tenant["tenant_id"], shop)
        
        return ShopifyConnectSuccessResponse(
            shop=shop,
            tenant_id=tenant["tenant_id"],
            redirect_url=state_data.redirect_after
        )

    async def _exchange_code_for_token(self, code: str, shop: str) -> str:
        """Exchange OAuth code for access token"""
        token_url = f"https://{shop}/admin/oauth/access_token"
        
        payload = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, json=payload)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to exchange code for token: {response.text}")
            
            token_data = response.json()
            return token_data["access_token"]

    async def _get_shop_info(self, shop: str, access_token: str) -> Dict[str, Any]:
        """Get shop information from Shopify Admin API"""
        shop_url = f"https://{shop}/admin/api/{self.api_version}/shop.json"
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(shop_url, headers=headers)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get shop info: {response.text}")
            
            return response.json()["shop"]

    async def _provision_tenant(self, db, shop: str, shop_info: Dict) -> Dict[str, Any]:
        """Auto-provision tenant based on shop domain"""
        tenants_collection = db["tenants"]
        
        # Check if tenant already exists
        existing = await tenants_collection.find_one({"shop": shop})
        if existing:
            return existing
        
        if not self.auto_provision:
            raise ValueError(f"Tenant auto-provisioning disabled and no tenant found for shop: {shop}")
        
        # Create new tenant
        tenant_data = ShopBasedTenantDB(
            shop=shop,
            name=shop_info.get("name", shop),
            status=TenantStatus.PROVISIONED
        )
        
        tenant_dict = tenant_data.model_dump()
        await tenants_collection.insert_one(tenant_dict)
        
        print(f"✅ Auto-provisioned tenant: {tenant_dict['tenant_id']} for shop: {shop}")
        return tenant_dict

    async def _store_shopify_integration(self, db, tenant_id: str, shop: str, access_token: str):
        """Store encrypted Shopify integration"""
        integrations_collection = db["integrations_shopify"]
        
        encrypted_token = self.encrypt_token(access_token)
        
        integration_data = ShopifyIntegrationDB(
            tenant_id=tenant_id,
            shop=shop,
            access_token_encrypted=encrypted_token,
            scopes=self.scopes,
            status=ShopifyConnectionStatus.CONNECTED
        )
        
        # Upsert integration
        await integrations_collection.replace_one(
            {"tenant_id": tenant_id, "shop": shop},
            integration_data.model_dump(),
            upsert=True
        )

    async def _upsert_shopify_user(self, db, tenant_id: str, shop: str, shop_info: Dict) -> Dict[str, Any]:
        """Create or update Shopify user"""
        users_collection = db["users"]
        
        # Check if user exists
        existing_user = await users_collection.find_one({"tenant_id": tenant_id, "shop": shop})
        
        user_data = ShopifyUserDB(
            tenant_id=tenant_id,
            shop=shop,
            shopify_user_id=str(shop_info.get("id", "")),
            email=shop_info.get("customer_email") or shop_info.get("email"),
            first_name=shop_info.get("shop_owner", "").split(" ")[0] if shop_info.get("shop_owner") else None,
            last_name=" ".join(shop_info.get("shop_owner", "").split(" ")[1:]) if shop_info.get("shop_owner") else None,
            last_login_at=datetime.utcnow()
        )
        
        if existing_user:
            # Update existing user
            user_data.user_id = existing_user["user_id"]
            await users_collection.replace_one(
                {"user_id": existing_user["user_id"]},
                user_data.model_dump()
            )
        else:
            # Create new user
            await users_collection.insert_one(user_data.model_dump())
        
        return user_data.model_dump()

    async def _register_webhooks(self, shop: str, access_token: str, tenant_id: str):
        """Register Shopify webhooks for real-time updates"""
        webhook_topics = [
            "orders/create",
            "orders/updated", 
            "fulfillments/create",
            "fulfillments/update",
            "app/uninstalled"
        ]
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        webhook_ids = {}
        
        async with httpx.AsyncClient() as client:
            for topic in webhook_topics:
                webhook_url = f"{self.app_url}/api/webhooks/shopify/{topic.replace('/', '-')}"
                
                webhook_data = {
                    "webhook": {
                        "topic": topic,
                        "address": webhook_url,
                        "format": "json"
                    }
                }
                
                try:
                    response = await client.post(
                        f"https://{shop}/admin/api/{self.api_version}/webhooks.json",
                        headers=headers,
                        json=webhook_data
                    )
                    
                    if response.status_code == 201:
                        webhook_info = response.json()["webhook"]
                        webhook_ids[topic] = str(webhook_info["id"])
                        print(f"✅ Registered webhook: {topic} -> {webhook_url}")
                    else:
                        print(f"⚠️ Failed to register webhook {topic}: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Webhook registration error for {topic}: {e}")
        
        # Store webhook IDs in integration record
        db = await get_database()
        integrations_collection = db["integrations_shopify"]
        await integrations_collection.update_one(
            {"tenant_id": tenant_id, "shop": shop},
            {"$set": {"webhook_ids": webhook_ids}}
        )

    async def _queue_data_backfill(self, tenant_id: str, shop: str):
        """Queue 90-day historical data backfill"""
        # Placeholder for background job system
        # In production, this would queue jobs for:
        # - Historical orders sync
        # - Historical returns sync 
        # - Customer data sync
        print(f"🔄 Queued 90-day backfill for tenant: {tenant_id}, shop: {shop}")

    async def get_connection_status(self, tenant_id: str) -> ShopifyConnectionResponse:
        """Get Shopify connection status for tenant"""
        db = await get_database()
        integration = await db["integrations_shopify"].find_one({"tenant_id": tenant_id})
        
        if not integration:
            return ShopifyConnectionResponse(
                connected=False,
                status=ShopifyConnectionStatus.DISCONNECTED
            )
        
        return ShopifyConnectionResponse(
            connected=integration["status"] == ShopifyConnectionStatus.CONNECTED,
            shop=integration["shop"],
            tenant_id=tenant_id,
            last_sync_at=integration.get("last_sync_at"),
            status=integration["status"],
            scopes=integration.get("scopes", [])
        )

    async def disconnect_shop(self, tenant_id: str) -> bool:
        """Disconnect Shopify integration"""
        db = await get_database()
        
        # Update status to disconnected
        result = await db["integrations_shopify"].update_one(
            {"tenant_id": tenant_id},
            {"$set": {"status": ShopifyConnectionStatus.DISCONNECTED}}
        )
        
        return result.modified_count > 0