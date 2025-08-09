"""
Real Shopify OAuth 2.0 implementation
"""
import os
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs
import aiohttp
import secrets
from datetime import datetime, timedelta

from ...config.database import db


class ShopifyOAuth:
    """Real Shopify OAuth 2.0 handler"""
    
    def __init__(self):
        self.api_key = os.environ.get('SHOPIFY_API_KEY')
        self.api_secret = os.environ.get('SHOPIFY_API_SECRET')
        self.api_version = os.environ.get('SHOPIFY_API_VERSION', '2024-01')
        self.redirect_uri = os.environ.get('SHOPIFY_REDIRECT_URI')
        
        # Required scopes for Returns Management
        self.scopes = [
            "read_orders",
            "write_orders",
            "read_products", 
            "write_products",
            "read_customers",
            "write_customers",
            "read_inventory",
            "write_inventory",
            "read_fulfillments",
            "write_fulfillments",
            "read_returns",
            "write_returns",
            "read_refunds",
            "write_refunds",
            "read_locations",
            "read_shipping"
        ]
    
    def validate_shop_domain(self, shop: str) -> bool:
        """Validate shop domain format"""
        if not shop:
            return False
        
        # Remove .myshopify.com if present
        shop = shop.replace('.myshopify.com', '')
        
        # Check if valid shop name (alphanumeric and hyphens only)
        if not shop.replace('-', '').replace('_', '').isalnum():
            return False
            
        return len(shop) >= 3 and len(shop) <= 60
    
    def normalize_shop_domain(self, shop: str) -> str:
        """Normalize shop domain"""
        if not shop:
            return ""
            
        # Remove protocol if present
        shop = shop.replace('https://', '').replace('http://', '')
        
        # Remove .myshopify.com if present  
        shop = shop.replace('.myshopify.com', '')
        
        return shop.lower().strip()
    
    async def initiate_oauth(self, shop: str) -> Dict[str, Any]:
        """Initiate OAuth flow"""
        shop = self.normalize_shop_domain(shop)
        
        if not self.validate_shop_domain(shop):
            raise ValueError("Invalid shop domain")
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state in database for verification
        await db.oauth_states.insert_one({
            "shop": shop,
            "state": state,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        
        # Build authorization URL
        params = {
            "client_id": self.api_key,
            "scope": ",".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        
        auth_url = f"https://{shop}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "shop": shop,
            "state": state
        }
    
    async def handle_callback(self, shop: str, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for access token"""
        shop = self.normalize_shop_domain(shop)
        
        # Verify state parameter
        state_doc = await db.oauth_states.find_one({
            "shop": shop,
            "state": state,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not state_doc:
            raise ValueError("Invalid or expired state parameter")
        
        # Clean up used state
        await db.oauth_states.delete_one({"_id": state_doc["_id"]})
        
        # Exchange code for access token
        token_url = f"https://{shop}.myshopify.com/admin/oauth/access_token"
        
        token_data = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "code": code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, json=token_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OAuth token exchange failed: {error_text}")
                
                token_response = await response.json()
        
        access_token = token_response["access_token"]
        scope = token_response.get("scope", "")
        
        # Store access token securely (encrypted in production)
        await db.shopify_stores.update_one(
            {"shop": shop},
            {
                "$set": {
                    "shop": shop,
                    "access_token": access_token,  # TODO: Encrypt in production
                    "scope": scope,
                    "installed_at": datetime.utcnow(),
                    "is_active": True
                }
            },
            upsert=True
        )
        
        # Register webhooks
        await self.register_webhooks(shop, access_token)
        
        return {
            "success": True,
            "shop": shop,
            "access_token": access_token,
            "scope": scope
        }
    
    async def register_webhooks(self, shop: str, access_token: str):
        """Register required webhooks"""
        webhook_topics = [
            "orders/create",
            "orders/updated", 
            "orders/cancelled",
            "orders/fulfilled",
            "orders/partially_fulfilled",
            "orders/paid",
            "returns/create",
            "returns/requested",
            "returns/approved",
            "returns/declined",
            "returns/cancelled",
            "refunds/create",
            "fulfillments/create",
            "fulfillments/update",
            "fulfillments/cancel",
            "products/update",
            "product_variants/update",
            "inventory_levels/update"
        ]
        
        base_webhook_url = self.redirect_uri.replace('/callback', '/webhooks')
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
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
                            print(f"✅ Registered webhook: {topic}")
                        else:
                            error_text = await response.text()
                            print(f"⚠️ Failed to register webhook {topic}: {error_text}")
                except Exception as e:
                    print(f"⚠️ Error registering webhook {topic}: {e}")
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """Verify webhook HMAC signature"""
        if not self.api_secret or not hmac_header:
            return False
        
        # Remove 'sha256=' prefix if present
        hmac_header = hmac_header.replace('sha256=', '')
        
        # Calculate expected HMAC
        expected_hmac = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                data,
                digestmod=hashlib.sha256
            ).digest()
        ).decode()
        
        # Compare HMACs securely
        return hmac.compare_digest(expected_hmac, hmac_header)
    
    async def get_shop_info(self, shop: str) -> Optional[Dict[str, Any]]:
        """Get shop information"""
        store_doc = await db.shopify_stores.find_one({"shop": shop, "is_active": True})
        if not store_doc:
            return None
        
        access_token = store_doc["access_token"]
        headers = {"X-Shopify-Access-Token": access_token}
        
        async with aiohttp.ClientSession() as session:
            url = f"https://{shop}.myshopify.com/admin/api/{self.api_version}/shop.json"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def is_shop_connected(self, shop: str) -> bool:
        """Check if shop is connected"""
        store_doc = await db.shopify_stores.find_one({"shop": shop, "is_active": True})
        return store_doc is not None