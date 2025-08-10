"""
Enhanced Auth Service for Dynamic Shopify Store Connectivity
Implements OAuth 2.0 flow, secure credential storage, and multi-tenant support
"""

import os
import hmac
import hashlib
import base64
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode
import aiohttp
from cryptography.fernet import Fernet
import shopify
from shopify import Session

from ...config.database import db
from ...utils.exceptions import AuthenticationError, ValidationError
from ...repositories import TenantScopedRepository


class ShopifyAuthService:
    """Enhanced Shopify Authentication Service with dynamic connectivity"""
    
    def __init__(self):
        # Encryption key for securing tokens (use KMS in production)
        self.encryption_key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        if isinstance(self.encryption_key, str):
            self.encryption_key = self.encryption_key.encode()
        self.cipher = Fernet(self.encryption_key)
        
        self.api_version = "2025-07"
        self.base_redirect_uri = os.environ.get(
            'SHOPIFY_REDIRECT_URI', 
            'https://easyreturns.preview.emergentagent.com/auth/callback'
        )
        
        # Required scopes for Returns Management
        self.scopes = [
            "read_orders", "write_orders", "read_products", "write_products",
            "read_customers", "write_customers", "read_inventory", "write_inventory",
            "read_fulfillments", "write_fulfillments", "read_returns", "write_returns",
            "read_refunds", "write_refunds", "read_locations", "read_shipping"
        ]
        
        # Repository for tenant-scoped operations
        self.repo = TenantScopedRepository()
    
    def validate_shop_domain(self, shop: str) -> bool:
        """Validate shop domain format"""
        if not shop:
            return False
        
        # Normalize shop domain
        shop = self.normalize_shop_domain(shop)
        
        # Check if valid shop name (alphanumeric, hyphens, underscores)
        if not shop.replace('-', '').replace('_', '').isalnum():
            return False
            
        return 3 <= len(shop) <= 60
    
    def normalize_shop_domain(self, shop: str) -> str:
        """Normalize shop domain to standard format"""
        if not shop:
            return ""
        
        # Remove protocol and trailing slashes
        shop = shop.replace('https://', '').replace('http://', '').rstrip('/')
        
        # Remove .myshopify.com if present
        shop = shop.replace('.myshopify.com', '')
        
        return shop.lower().strip()
    
    def validate_credentials(self, api_key: str, api_secret: str) -> bool:
        """Validate API key and secret format"""
        if not api_key or not api_secret:
            return False
        
        # API key should be 32 characters hex
        if len(api_key) != 32 or not all(c in '0123456789abcdef' for c in api_key.lower()):
            return False
        
        # API secret should be 32 characters hex
        if len(api_secret) != 32 or not all(c in '0123456789abcdef' for c in api_secret.lower()):
            return False
        
        return True
    
    async def initiate_oauth(self, shop: str, api_key: str, api_secret: str, user_id: str = None) -> Dict[str, Any]:
        """
        Initiate OAuth flow with dynamic credentials
        
        Args:
            shop: Shop domain (e.g., 'demo-store')
            api_key: Shopify API Key from merchant's app
            api_secret: Shopify API Secret from merchant's app
            user_id: Optional user identifier for audit purposes
        
        Returns:
            Dict containing auth_url, shop, and state
        """
        # Validate inputs
        shop = self.normalize_shop_domain(shop)
        
        if not self.validate_shop_domain(shop):
            raise ValidationError("Invalid shop domain format")
        
        if not self.validate_credentials(api_key, api_secret):
            raise ValidationError("Invalid API credentials format")
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store OAuth state with credentials for callback verification
        await db.oauth_states.insert_one({
            "shop": shop,
            "state": state,
            "api_key": api_key,
            "api_secret": self._encrypt_secret(api_secret),
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        
        # Build authorization URL
        params = {
            "client_id": api_key,
            "scope": ",".join(self.scopes),
            "redirect_uri": self.base_redirect_uri,
            "state": state
        }
        
        auth_url = f"https://{shop}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "shop": shop,
            "state": state,
            "scopes_requested": self.scopes
        }
    
    async def handle_oauth_callback(self, shop: str, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for access token
        
        Args:
            shop: Shop domain
            code: Authorization code from Shopify
            state: State parameter for CSRF protection
        
        Returns:
            Dict with success status, shop info, and token details
        """
        shop = self.normalize_shop_domain(shop)
        
        # Retrieve and verify OAuth state
        state_doc = await db.oauth_states.find_one({
            "shop": shop,
            "state": state,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not state_doc:
            raise AuthenticationError("Invalid or expired OAuth state")
        
        # Get stored credentials
        api_key = state_doc["api_key"]
        api_secret = self._decrypt_secret(state_doc["api_secret"])
        user_id = state_doc.get("user_id")
        
        # Clean up used state
        await db.oauth_states.delete_one({"_id": state_doc["_id"]})
        
        # Exchange authorization code for access token
        token_url = f"https://{shop}.myshopify.com/admin/oauth/access_token"
        
        token_data = {
            "client_id": api_key,
            "client_secret": api_secret,
            "code": code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, json=token_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AuthenticationError(f"OAuth token exchange failed: {error_text}")
                
                token_response = await response.json()
        
        access_token = token_response["access_token"]
        scope = token_response.get("scope", "")
        
        # Verify we received all required scopes
        granted_scopes = set(scope.split(",")) if scope else set()
        required_scopes = set(self.scopes)
        
        if not required_scopes.issubset(granted_scopes):
            missing_scopes = required_scopes - granted_scopes
            raise AuthenticationError(f"Missing required scopes: {missing_scopes}")
        
        # Get shop information for tenant setup
        shop_info = await self._fetch_shop_info(shop, access_token)
        
        # Generate tenant_id (use full shop domain)
        tenant_id = f"{shop}.myshopify.com"
        
        # Store encrypted credentials and token
        store_data = {
            "tenant_id": tenant_id,
            "shop": shop,
            "api_key": api_key,
            "api_secret": self._encrypt_secret(api_secret),
            "access_token": self._encrypt_secret(access_token),
            "scope": scope,
            "shop_info": shop_info,
            "connected_by": user_id,
            "connected_at": datetime.utcnow(),
            "last_sync": None,
            "is_active": True,
            "webhook_status": "pending"
        }
        
        # Upsert store configuration
        await db.stores.update_one(
            {"tenant_id": tenant_id},
            {"$set": store_data},
            upsert=True
        )
        
        # Register webhooks in background
        try:
            await self.register_webhooks(tenant_id, shop, access_token)
            await db.stores.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"webhook_status": "registered"}}
            )
        except Exception as e:
            print(f"⚠️ Webhook registration failed for {shop}: {e}")
            await db.stores.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"webhook_status": "failed", "webhook_error": str(e)}}
            )
        
        # Trigger initial sync in background
        try:
            from ...services.sync_service import sync_service
            await sync_service.perform_initial_sync(tenant_id)
        except Exception as e:
            print(f"⚠️ Initial sync failed for {shop}: {e}")
            await db.stores.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"sync_status": "failed", "sync_error": str(e)}}
            )
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "shop": shop,
            "shop_info": shop_info,
            "scopes_granted": list(granted_scopes),
            "webhook_status": "registered",
            "connected_at": datetime.utcnow().isoformat()
        }
    
    async def register_webhooks(self, tenant_id: str, shop: str, access_token: str):
        """Register required webhooks for the connected store"""
        webhook_topics = [
            # App lifecycle - CRITICAL for cleanup
            "app/uninstalled",
            
            # Orders
            "orders/create", "orders/updated", "orders/cancelled", "orders/fulfilled",
            "orders/partially_fulfilled", "orders/paid",
            
            # Returns
            "returns/create", "returns/requested", "returns/approved", 
            "returns/declined", "returns/cancelled",
            
            # Refunds and fulfillments
            "refunds/create", "fulfillments/create", "fulfillments/update", 
            "fulfillments/cancel",
            
            # Products and inventory
            "products/update", "product_variants/update", "inventory_levels/update"
        ]
        
        base_webhook_url = self.base_redirect_uri.replace('/callback', '/webhooks')
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        registered_webhooks = []
        failed_webhooks = []
        
        async with aiohttp.ClientSession() as session:
            for topic in webhook_topics:
                webhook_url = f"{base_webhook_url}/{topic.replace('/', '_')}"
                
                webhook_data = {
                    "webhook": {
                        "topic": topic,
                        "address": webhook_url,
                        "format": "json"
                    }
                }
                
                api_url = f"https://{shop}.myshopify.com/admin/api/{self.api_version}/webhooks.json"
                
                try:
                    async with session.post(api_url, json=webhook_data, headers=headers) as response:
                        if response.status == 201:
                            webhook_result = await response.json()
                            registered_webhooks.append({
                                "topic": topic,
                                "id": webhook_result["webhook"]["id"],
                                "address": webhook_url
                            })
                            print(f"✅ Registered webhook: {topic}")
                        else:
                            error_text = await response.text()
                            failed_webhooks.append({"topic": topic, "error": error_text})
                            print(f"⚠️ Failed to register webhook {topic}: {error_text}")
                except Exception as e:
                    failed_webhooks.append({"topic": topic, "error": str(e)})
                    print(f"⚠️ Error registering webhook {topic}: {e}")
        
        # Store webhook registration results
        await db.stores.update_one(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "registered_webhooks": registered_webhooks,
                    "failed_webhooks": failed_webhooks,
                    "webhooks_registered_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "registered": len(registered_webhooks),
            "failed": len(failed_webhooks),
            "details": {
                "registered": registered_webhooks,
                "failed": failed_webhooks
            }
        }
    
    async def get_store_connection(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get store connection details by tenant_id"""
        store_doc = await db.stores.find_one({"tenant_id": tenant_id, "is_active": True})
        
        if not store_doc:
            return None
        
        # Return safe connection info (without sensitive data)
        return {
            "tenant_id": store_doc["tenant_id"],
            "shop": store_doc["shop"],
            "shop_info": store_doc.get("shop_info", {}),
            "connected_at": store_doc["connected_at"],
            "last_sync": store_doc.get("last_sync"),
            "webhook_status": store_doc.get("webhook_status", "unknown"),
            "is_active": store_doc["is_active"],
            "scopes": store_doc.get("scope", "").split(",") if store_doc.get("scope") else []
        }
    
    async def list_connected_stores(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List all connected stores (optionally filtered by user)"""
        query = {"is_active": True}
        if user_id:
            query["connected_by"] = user_id
        
        stores = []
        async for store_doc in db.stores.find(query):
            stores.append({
                "tenant_id": store_doc["tenant_id"],
                "shop": store_doc["shop"],
                "shop_name": store_doc.get("shop_info", {}).get("name", store_doc["shop"]),
                "connected_at": store_doc["connected_at"],
                "last_sync": store_doc.get("last_sync"),
                "webhook_status": store_doc.get("webhook_status", "unknown"),
                "is_active": store_doc["is_active"]
            })
        
        return stores
    
    async def disconnect_store(self, tenant_id: str, user_id: str = None) -> bool:
        """Disconnect a store and revoke access"""
        store_doc = await db.stores.find_one({"tenant_id": tenant_id, "is_active": True})
        
        if not store_doc:
            return False
        
        # Mark as inactive
        await db.stores.update_one(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "is_active": False,
                    "disconnected_at": datetime.utcnow(),
                    "disconnected_by": user_id
                }
            }
        )
        
        return True
    
    def verify_webhook(self, data: bytes, hmac_header: str, api_secret: str) -> bool:
        """Verify webhook HMAC signature"""
        if not api_secret or not hmac_header:
            return False
        
        # Remove 'sha256=' prefix if present
        hmac_header = hmac_header.replace('sha256=', '')
        
        # Calculate expected HMAC
        expected_hmac = base64.b64encode(
            hmac.new(
                api_secret.encode('utf-8'),
                data,
                digestmod=hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(expected_hmac, hmac_header)
    
    async def get_decrypted_credentials(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for internal use (admin only)"""
        store_doc = await db.stores.find_one({"tenant_id": tenant_id, "is_active": True})
        
        if not store_doc:
            return None
        
        return {
            "shop": store_doc["shop"],
            "api_key": store_doc["api_key"],
            "api_secret": self._decrypt_secret(store_doc["api_secret"]),
            "access_token": self._decrypt_secret(store_doc["access_token"])
        }
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt sensitive data"""
        if not secret:
            return ""
        return self.cipher.encrypt(secret.encode()).decode()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_secret:
            return ""
        return self.cipher.decrypt(encrypted_secret.encode()).decode()
    
    async def _fetch_shop_info(self, shop: str, access_token: str) -> Dict[str, Any]:
        """Fetch shop information from Shopify API"""
        headers = {"X-Shopify-Access-Token": access_token}
        url = f"https://{shop}.myshopify.com/admin/api/{self.api_version}/shop.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    shop_data = await response.json()
                    shop_info = shop_data.get("shop", {})
                    
                    # Return only relevant shop information
                    return {
                        "id": shop_info.get("id"),
                        "name": shop_info.get("name"),
                        "email": shop_info.get("email"),
                        "domain": shop_info.get("domain"),
                        "myshopify_domain": shop_info.get("myshopify_domain"),
                        "country_name": shop_info.get("country_name"),
                        "currency": shop_info.get("currency"),
                        "timezone": shop_info.get("iana_timezone"),
                        "plan_name": shop_info.get("plan_name"),
                        "created_at": shop_info.get("created_at")
                    }
                else:
                    return {"error": f"Failed to fetch shop info: {response.status}"}


# Singleton instance
auth_service = ShopifyAuthService()