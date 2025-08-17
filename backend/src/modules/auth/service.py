"""
Enhanced Auth Service for Dynamic Shopify Store Connectivity
Implements OAuth 2.0 flow, secure credential storage, and multi-tenant support
"""

import os
import hmac
import hashlib
import base64
import secrets
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode
import aiohttp
from cryptography.fernet import Fernet
import shopify
from shopify import Session

from ...config.database import db
from ...utils.exceptions import AuthenticationError, ValidationError


class ShopifyAuthService:
    """Enhanced Shopify Authentication Service with dynamic connectivity"""
    
    def __init__(self):
        # Set API version
        self.api_version = os.environ.get('SHOPIFY_API_VERSION', '2025-07')
        
        # Set base redirect URI
        self.base_redirect_uri = os.environ.get('SHOPIFY_REDIRECT_URI', 'https://shopify-sync-fix.preview.emergentagent.com/api/auth/shopify/callback')
        
        # Encryption key for securing tokens (use KMS in production)
        encryption_key_str = os.environ.get('ENCRYPTION_KEY')
        if not encryption_key_str or encryption_key_str == 'fernet-key-32-bytes-base64-encoded-here':
            # Generate a new key for development
            self.encryption_key = Fernet.generate_key()
        else:
            if isinstance(encryption_key_str, str):
                self.encryption_key = encryption_key_str.encode()
            else:
                self.encryption_key = encryption_key_str
                
        try:
            self.cipher = Fernet(self.encryption_key)
        except ValueError:
            # If key is invalid, generate a new one
            self.encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
        
        # Required scopes for Returns Management
        self.scopes = [
            "read_orders", "write_orders", "read_products", "write_products",
            "read_customers", "write_customers", "read_inventory", "write_inventory",
            "read_fulfillments", "write_fulfillments", "read_returns", "write_returns",
            "read_refunds", "write_refunds", "read_locations", "read_shipping"
        ]
        
    def generate_oauth_state(self) -> str:
        """Generate a secure random state token for CSRF protection"""
        return secrets.token_urlsafe(32)
    
    async def store_oauth_state(self, shop: str, state: str) -> None:
        """Store OAuth state token temporarily for verification"""
        # Store in database with expiration (10 minutes)
        expiry = datetime.utcnow() + timedelta(minutes=10)
        
        await db.oauth_states.insert_one({
            "shop": shop,
            "state": state,
            "created_at": datetime.utcnow(),
            "expires_at": expiry
        })
    
    async def verify_oauth_state(self, shop: str, state: str) -> bool:
        """Verify OAuth state token and remove it"""
        try:
            # Find and remove the state token
            result = await db.oauth_states.find_one_and_delete({
                "shop": shop,
                "state": state,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            return result is not None
        except Exception:
            return False
    
    async def cleanup_oauth_state(self, shop: str, state: str) -> None:
        """Clean up expired OAuth state tokens"""
        try:
            # Remove the specific state
            await db.oauth_states.delete_one({"shop": shop, "state": state})
            
            # Clean up expired states
            await db.oauth_states.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
        except Exception:
            pass  # Non-critical cleanup
    
    async def verify_shopify_hmac(self, shop: str, code: str, state: str, hmac: str, timestamp: str) -> bool:
        """Verify HMAC signature from Shopify"""
        try:
            # Get API secret
            api_secret = os.environ.get('SHOPIFY_API_SECRET')
            if not api_secret:
                return False
                
            # Build query string for HMAC verification
            query_string = f"code={code}&shop={shop}&state={state}"
            if timestamp:
                query_string += f"&timestamp={timestamp}"
            
            # Calculate expected HMAC
            expected_hmac = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare HMACs (constant time comparison)
            return hmac.compare_digest(hmac, expected_hmac)
            
        except Exception as e:
            print(f"HMAC verification error: {e}")
            return False
    
    async def exchange_code_for_token(self, shop: str, code: str) -> str:
        """Exchange authorization code for access token"""
        try:
            # Get API credentials
            api_key = os.environ.get('SHOPIFY_API_KEY')
            api_secret = os.environ.get('SHOPIFY_API_SECRET')
            
            if not api_key or not api_secret:
                raise AuthenticationError("Shopify API credentials not configured")
            
            # Shopify token exchange endpoint
            token_url = f"https://{shop}/admin/oauth/access_token"
            
            # Request payload
            payload = {
                "client_id": api_key,
                "client_secret": api_secret,
                "code": code
            }
            
            # Make token exchange request
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("access_token")
                    else:
                        error_text = await response.text()
                        raise AuthenticationError(f"Token exchange failed: {error_text}")
                        
        except Exception as e:
            raise AuthenticationError(f"Failed to exchange code for token: {str(e)}")
    
    async def get_shop_info(self, shop: str, access_token: str) -> Dict[str, Any]:
        """Get shop information using access token"""
        try:
            # Shopify shop info endpoint
            shop_url = f"https://{shop}/admin/api/{self.api_version}/shop.json"
            
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(shop_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("shop", {})
                    else:
                        error_text = await response.text()
                        print(f"Shop info request failed: {error_text}")
                        return {"name": shop, "domain": shop}  # Fallback
                        
        except Exception as e:
            print(f"Failed to get shop info: {e}")
            return {"name": shop, "domain": shop}  # Fallback
    
    async def save_shop_credentials(self, tenant_data: Dict[str, Any]) -> str:
        """Save shop credentials to database (encrypted) and return tenant ID"""
        try:
            # Generate tenant ID based on shop
            tenant_id = f"tenant-{tenant_data['shop'].replace('.myshopify.com', '').replace('.', '-').replace('_', '-')}"
            
            # Encrypt the access token
            encrypted_token = self.cipher.encrypt(tenant_data["access_token"].encode()).decode()
            
            # Prepare tenant document
            tenant_doc = {
                "id": tenant_id,
                "name": tenant_data.get("shop_info", {}).get("name", tenant_data["shop"]),
                "domain": tenant_data["shop"],
                "shopify_store": tenant_data["shop"],
                "shopify_store_url": f"https://{tenant_data['shop']}",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "settings": {
                    "return_window_days": 30,
                    "auto_approve_threshold": 100.0,
                    "notification_email": "support@example.com",
                    "brand_color": "#3b82f6"
                },
                "shopify_integration": {
                    "installed_at": tenant_data["installed_at"],
                    "provider": tenant_data["provider"],
                    "scopes": tenant_data["scopes"],
                    "access_token_encrypted": encrypted_token,
                    "shop_info": tenant_data.get("shop_info", {}),
                    "last_sync": None,
                    "webhook_status": "pending"
                },
                "is_active": True
            }
            
            # Upsert tenant document
            await db.tenants.update_one(
                {"id": tenant_id},
                {"$set": tenant_doc},
                upsert=True
            )
            
            return tenant_id
            
        except Exception as e:
            raise AuthenticationError(f"Failed to save shop credentials: {str(e)}")
    
    async def enqueue_initial_data_sync(self, tenant_id: str, shop: str, access_token: str) -> None:
        """Enqueue initial data synchronization job"""
        try:
            # Create sync job document
            sync_job = {
                "id": f"initial-sync-{tenant_id}-{int(datetime.utcnow().timestamp())}",
                "tenant_id": tenant_id,
                "shop": shop,
                "job_type": "initial_sync",
                "status": "queued",
                "created_at": datetime.utcnow(),
                "sync_config": {
                    "orders_days_back": 90,
                    "include_orders": True,
                    "include_products": True,
                    "include_customers": True,
                    "include_returns": True
                }
            }
            
            # Store job
            await db.sync_jobs.insert_one(sync_job)
            
            # For now, we'll process immediately in background
            # In production, this would use a proper job queue like Celery
            asyncio.create_task(self._process_initial_sync(tenant_id, shop, access_token))
            
        except Exception as e:
            print(f"Failed to enqueue initial sync: {e}")
    
    async def register_shopify_webhooks(self, shop: str, access_token: str) -> None:
        """Register required webhooks with Shopify"""
        try:
            # Webhook topics to register (as specified)
            webhook_topics = [
                "orders/create",
                "orders/updated", 
                "fulfillments/create",
                "fulfillments/update",
                "returns/create",
                "returns/update"
            ]
            
            # Base webhook endpoint
            webhook_base_url = "https://shopify-sync-fix.preview.emergentagent.com/api/webhooks/shopify"
            
            # Register each webhook
            for topic in webhook_topics:
                try:
                    await self._register_single_webhook(shop, access_token, topic, f"{webhook_base_url}/{topic.replace('/', '_')}")
                except Exception as e:
                    print(f"Failed to register webhook {topic}: {e}")
                    # Continue with other webhooks
                    
            print(f"Webhook registration completed for {shop}")
                    
        except Exception as e:
            print(f"Webhook registration failed: {e}")
    
    async def _register_single_webhook(self, shop: str, access_token: str, topic: str, address: str) -> None:
        """Register a single webhook with Shopify"""
        webhook_url = f"https://{shop}/admin/api/{self.api_version}/webhooks.json"
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    webhook_data = await response.json()
                    print(f"Registered webhook {topic}: {webhook_data.get('webhook', {}).get('id')}")
                else:
                    error_text = await response.text()
                    print(f"Failed to register webhook {topic}: {error_text}")
    
    async def _process_initial_sync(self, tenant_id: str, shop: str, access_token: str) -> None:
        """Process initial data synchronization in background"""
        try:
            print(f"Starting initial sync for {shop}")
            
            # Update job status
            await db.sync_jobs.update_one(
                {"tenant_id": tenant_id, "job_type": "initial_sync", "status": "queued"},
                {"$set": {"status": "running", "started_at": datetime.utcnow()}}
            )
            
            # Sync orders (last 90 days)
            await self._sync_orders(tenant_id, shop, access_token, days_back=90)
            
            # Sync products
            await self._sync_products(tenant_id, shop, access_token)
            
            # Update job status
            await db.sync_jobs.update_one(
                {"tenant_id": tenant_id, "job_type": "initial_sync", "status": "running"},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "message": "Initial sync completed successfully"
                    }
                }
            )
            
            # Update tenant sync status
            await db.tenants.update_one(
                {"id": tenant_id},
                {
                    "$set": {
                        "shopify_integration.last_sync": datetime.utcnow(),
                        "shopify_integration.webhook_status": "active"
                    }
                }
            )
            
            print(f"Initial sync completed for {shop}")
            
        except Exception as e:
            print(f"Initial sync failed for {shop}: {e}")
            
            # Update job status
            await db.sync_jobs.update_one(
                {"tenant_id": tenant_id, "job_type": "initial_sync"},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.utcnow(),
                        "error": str(e)
                    }
                }
            )
    
    async def _sync_orders(self, tenant_id: str, shop: str, access_token: str, days_back: int = 90) -> None:
        """Sync orders from Shopify"""
        try:
            # Calculate date range
            since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            
            # Shopify orders endpoint with cursor pagination
            orders_url = f"https://{shop}/admin/api/{self.api_version}/orders.json"
            
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            params = {
                "limit": 50,
                "created_at_min": since_date,
                "status": "any"
            }
            
            orders_synced = 0
            
            async with aiohttp.ClientSession() as session:
                while True:
                    async with session.get(orders_url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            orders = data.get("orders", [])
                            
                            if not orders:
                                break
                                
                            # Save orders to database
                            for order in orders:
                                await self._save_order(tenant_id, order)
                                orders_synced += 1
                            
                            # Check for pagination
                            link_header = response.headers.get("Link")
                            if link_header and "rel=\"next\"" in link_header:
                                # Extract next page cursor from Link header
                                # This is a simplified implementation
                                params["since_id"] = orders[-1]["id"]
                            else:
                                break
                        else:
                            error_text = await response.text()
                            print(f"Orders sync failed: {error_text}")
                            break
            
            print(f"Synced {orders_synced} orders for {shop}")
            
        except Exception as e:
            print(f"Orders sync error: {e}")
    
    async def _sync_products(self, tenant_id: str, shop: str, access_token: str) -> None:
        """Sync products from Shopify"""
        try:
            products_url = f"https://{shop}/admin/api/{self.api_version}/products.json"
            
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            params = {"limit": 50}
            products_synced = 0
            
            async with aiohttp.ClientSession() as session:
                while True:
                    async with session.get(products_url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            products = data.get("products", [])
                            
                            if not products:
                                break
                                
                            # Save products to database
                            for product in products:
                                await self._save_product(tenant_id, product)
                                products_synced += 1
                            
                            # Check for pagination
                            link_header = response.headers.get("Link")
                            if link_header and "rel=\"next\"" in link_header:
                                params["since_id"] = products[-1]["id"]
                            else:
                                break
                        else:
                            error_text = await response.text()
                            print(f"Products sync failed: {error_text}")
                            break
            
            print(f"Synced {products_synced} products for {shop}")
            
        except Exception as e:
            print(f"Products sync error: {e}")
    
    async def _save_order(self, tenant_id: str, order_data: Dict[str, Any]) -> None:
        """Save order to database"""
        try:
            # Transform order data for our schema - Frontend expects specific fields
            customer = order_data.get("customer") or {}
            billing_address = order_data.get("billing_address") or {}
            
            # Use customer name from customer object first, then billing address
            customer_name = ""
            if customer:
                first_name = customer.get("first_name", "")
                last_name = customer.get("last_name", "")
                customer_name = f"{first_name} {last_name}".strip()
            
            if not customer_name and billing_address:
                first_name = billing_address.get("first_name", "")
                last_name = billing_address.get("last_name", "")
                customer_name = f"{first_name} {last_name}".strip()
            
            order_doc = {
                "id": str(order_data["id"]),  # Keep for internal use
                "order_id": str(order_data["id"]),  # Frontend expects this field
                "tenant_id": tenant_id,
                "order_number": str(order_data.get("order_number", order_data.get("name", ""))).replace("#", ""),
                "shopify_order_id": str(order_data["id"]),
                "email": order_data.get("email", ""),
                "customer_email": order_data.get("email", customer.get("email", "")),
                "customer_name": customer_name,
                "customer_id": str(customer.get("id", "")) if customer else "",
                "financial_status": order_data.get("financial_status", ""),
                "fulfillment_status": order_data.get("fulfillment_status", ""),
                "total_price": float(order_data.get("total_price", 0)),
                "currency_code": order_data.get("currency", "USD"),
                "created_at": order_data.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": order_data.get("updated_at", datetime.utcnow().isoformat()),
                "processed_at": order_data.get("processed_at"),
                "line_items": order_data.get("line_items", []),
                "billing_address": order_data.get("billing_address", {}),
                "shipping_address": order_data.get("shipping_address", {}),
                "fulfillments": [f.get("id") for f in order_data.get("fulfillments", [])],
                "shopify_order_url": f"https://{order_data.get('order_status_url', '').split('/')[-1] if order_data.get('order_status_url') else 'unknown'}.myshopify.com/admin/orders/{order_data['id']}",
                "raw_order_data": order_data,  # Store complete raw data
                "synced_at": datetime.utcnow()
            }
            
            # Upsert order - use both id and order_id to ensure compatibility
            await db.orders.update_one(
                {"order_id": str(order_data["id"]), "tenant_id": tenant_id},
                {"$set": order_doc},
                upsert=True
            )
            
        except Exception as e:
            print(f"Failed to save order {order_data.get('id')}: {e}")
    
    async def verify_webhook_hmac(self, body: bytes, hmac_signature: str) -> bool:
        """Verify webhook HMAC signature from Shopify"""
        try:
            # Get API secret
            api_secret = os.environ.get('SHOPIFY_API_SECRET')
            if not api_secret:
                return False
            
            # Calculate expected HMAC
            expected_hmac = base64.b64encode(
                hmac.new(
                    api_secret.encode('utf-8'),
                    body,
                    hashlib.sha256
                ).digest()
            ).decode()
            
            # Compare HMACs (constant time comparison)
            return hmac.compare_digest(hmac_signature, expected_hmac)
            
        except Exception as e:
            print(f"Webhook HMAC verification error: {e}")
            return False

    async def _save_product(self, tenant_id: str, product_data: Dict[str, Any]) -> None:
        """Save product to database"""
        try:
            # Transform product data for our schema
            product_doc = {
                "id": str(product_data["id"]),
                "tenant_id": tenant_id,
                "shopify_product_id": str(product_data["id"]),
                "title": product_data.get("title", ""),
                "handle": product_data.get("handle", ""),
                "vendor": product_data.get("vendor", ""),
                "product_type": product_data.get("product_type", ""),
                "status": product_data.get("status", ""),
                "variants": product_data.get("variants", []),
                "images": product_data.get("images", []),
                "raw_product_data": product_data,  # Store complete raw data
                "created_at": product_data.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": product_data.get("updated_at", datetime.utcnow().isoformat()),
                "synced_at": datetime.utcnow()
            }
            
            # Upsert product
            await db.products.update_one(
                {"id": str(product_data["id"]), "tenant_id": tenant_id},
                {"$set": product_doc},
                upsert=True
            )
            
        except Exception as e:
            print(f"Failed to save product {product_data.get('id')}: {e}")

    async def _process_resync(self, tenant_id: str, shop: str, access_token: str, job_id: str) -> None:
        """Process manual resync job"""
        try:
            print(f"Starting manual resync job {job_id} for {shop}")
            
            # Update job status
            await db.sync_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "running", "started_at": datetime.utcnow(), "progress": 10}}
            )
            
            # Sync orders (last 90 days)
            await self._sync_orders(tenant_id, shop, access_token, days_back=90)
            
            await db.sync_jobs.update_one(
                {"id": job_id},
                {"$set": {"progress": 70}}
            )
            
            # Sync products
            await self._sync_products(tenant_id, shop, access_token)
            
            await db.sync_jobs.update_one(
                {"id": job_id},
                {"$set": {"progress": 90}}
            )
            
            # Update job status
            await db.sync_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "progress": 100,
                        "message": "Manual resync completed successfully"
                    }
                }
            )
            
            # Update tenant sync status
            await db.tenants.update_one(
                {"id": tenant_id},
                {
                    "$set": {
                        "shopify_integration.last_sync": datetime.utcnow()
                    }
                }
            )
            
            print(f"Manual resync job {job_id} completed for {shop}")
            
        except Exception as e:
            print(f"Manual resync job {job_id} failed for {shop}: {e}")
            
            # Update job status
            await db.sync_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.utcnow(),
                        "error": str(e),
                        "message": f"Resync failed: {str(e)}"
                    }
                }
            )
    
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
            "webhook_status": "pending",
            "sync_status": "pending"
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
            # Don't await this - let it run in background
            asyncio.create_task(sync_service.perform_initial_sync(tenant_id))
            await db.stores.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"sync_status": "in_progress"}}
            )
        except Exception as e:
            print(f"⚠️ Initial sync trigger failed for {shop}: {e}")
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
        # Complete webhook topics per Shopify RMS Guide
        webhook_topics = [
            # Order webhooks
            "orders/create",
            "orders/updated",
            "orders/cancelled",
            "orders/fulfilled",
            "orders/partially_fulfilled",
            "orders/paid",
            
            # Return webhooks - Shopify RMS Guide requirements
            "returns/approve",
            "returns/cancel", 
            "returns/close",
            "returns/decline",
            "returns/reopen",
            "returns/request",
            "returns/update",
            
            # Related webhooks
            "refunds/create",
            "app/uninstalled"
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