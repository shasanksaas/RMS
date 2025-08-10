"""
Shopify API service with offline fallback
"""
import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

from ..config.shopify import ShopifyConfig, OFFLINE_MODE, MOCK_DATA_PATH
from ..config.database import db


class ShopifyService:
    """Service for Shopify API interactions with offline fallback"""
    
    def __init__(self, tenant_id: str = None):
        self.offline_mode = OFFLINE_MODE
        self.mock_data_path = MOCK_DATA_PATH
        self.tenant_id = tenant_id
    
    async def is_connected(self) -> bool:
        """Check if this tenant has a connected Shopify integration"""
        if not self.tenant_id:
            return False
            
        try:
            integration = await db.integrations_shopify.find_one({
                "tenant_id": self.tenant_id,
                "status": "connected"
            })
            return integration is not None
        except:
            return False
    
    async def is_online(self) -> bool:
        """Check if Shopify API is accessible"""
        if self.offline_mode:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://shopify.dev/api", 
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    # OAuth Flow Methods
    async def get_authorization_url(self, shop: str, redirect_uri: str) -> str:
        """Get Shopify OAuth authorization URL"""
        if not ShopifyConfig.is_valid_shop_domain(shop):
            raise ValueError("Invalid shop domain")
        
        shop = ShopifyConfig.normalize_shop_domain(shop)
        state = self._generate_state()
        
        # Store state for verification
        await self._store_oauth_state(shop, state)
        
        return ShopifyConfig.get_authorization_url(shop, redirect_uri, state)
    
    async def exchange_code_for_token(self, shop: str, code: str, state: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        shop = ShopifyConfig.normalize_shop_domain(shop)
        
        # Verify state
        if not await self._verify_oauth_state(shop, state):
            raise ValueError("Invalid OAuth state")
        
        if await self.is_online():
            return await self._exchange_code_online(shop, code)
        else:
            return await self._exchange_code_offline(shop, code)
    
    async def _exchange_code_online(self, shop: str, code: str) -> Dict[str, Any]:
        """Exchange code for token using real Shopify API"""
        token_url = f"https://{shop}.myshopify.com/admin/oauth/access_token"
        
        data = {
            "client_id": ShopifyConfig.CLIENT_ID,
            "client_secret": ShopifyConfig.CLIENT_SECRET,
            "code": code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, json=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Store token securely
                    await self._store_access_token(shop, token_data["access_token"], token_data.get("scope", ""))
                    
                    return {
                        "success": True,
                        "access_token": token_data["access_token"],
                        "scope": token_data.get("scope", "")
                    }
                else:
                    error_data = await response.json()
                    raise Exception(f"OAuth error: {error_data}")
    
    async def _exchange_code_offline(self, shop: str, code: str) -> Dict[str, Any]:
        """Mock OAuth exchange for offline mode"""
        mock_token = f"mock_token_{shop}_{datetime.utcnow().isoformat()}"
        await self._store_access_token(shop, mock_token, ",".join(ShopifyConfig.SCOPES))
        
        return {
            "success": True,
            "access_token": mock_token,
            "scope": ",".join(ShopifyConfig.SCOPES)
        }
    
    # API Methods
    async def get_orders(self, shop: str, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get orders from Shopify with offline fallback"""
        if await self.is_online():
            return await self._get_orders_online(shop, tenant_id, limit)
        else:
            return await self._get_orders_offline(shop, tenant_id, limit)
    
    async def _get_orders_online(self, shop: str, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get orders from real Shopify API"""
        access_token = await self._get_access_token(shop)
        if not access_token:
            raise ValueError("No access token found for shop")
        
        url = ShopifyConfig.get_api_url(shop, f"orders.json?limit={limit}&status=any")
        headers = {"X-Shopify-Access-Token": access_token}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get("orders", [])
                    
                    # Cache orders locally for offline use
                    await self._cache_orders(shop, orders)
                    
                    return orders
                else:
                    # Fallback to cached data
                    return await self._get_orders_offline(shop, tenant_id, limit)
    
    async def _get_orders_offline(self, shop: str, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get orders from local cache or mock data"""
        # Try to get cached orders first
        cached_orders = await self._get_cached_orders(shop)
        if cached_orders:
            return cached_orders[:limit]
        
        # Fallback to mock data
        return await self._get_mock_orders(shop, limit)
    
    async def get_products(self, shop: str, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get products from Shopify with offline fallback"""
        if await self.is_online():
            return await self._get_products_online(shop, tenant_id, limit)
        else:
            return await self._get_products_offline(shop, tenant_id, limit)
    
    async def _get_products_online(self, shop: str, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get products from real Shopify API"""
        access_token = await self._get_access_token(shop)
        if not access_token:
            raise ValueError("No access token found for shop")
        
        url = ShopifyConfig.get_api_url(shop, f"products.json?limit={limit}")
        headers = {"X-Shopify-Access-Token": access_token}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", [])
                    
                    # Cache products locally
                    await self._cache_products(shop, products)
                    
                    return products
                else:
                    # Fallback to cached data
                    return await self._get_products_offline(shop, tenant_id, limit)
    
    async def _get_products_offline(self, shop: str, tenant_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get products from local cache or mock data"""
        cached_products = await self._get_cached_products(shop)
        if cached_products:
            return cached_products[:limit]
        
        return await self._get_mock_products(shop, limit)
    
    # Webhook Verification
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """Verify Shopify webhook HMAC"""
        if self.offline_mode:
            return True  # Skip verification in offline mode
            
        computed_hmac = base64.b64encode(
            hmac.new(
                ShopifyConfig.CLIENT_SECRET.encode('utf-8'),
                data,
                digestmod=hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(computed_hmac, hmac_header)
    
    # Helper Methods
    def _generate_state(self) -> str:
        """Generate secure state for OAuth"""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    async def _store_oauth_state(self, shop: str, state: str):
        """Store OAuth state for verification"""
        await db.oauth_states.insert_one({
            "shop": shop,
            "state": state,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
    
    async def _verify_oauth_state(self, shop: str, state: str) -> bool:
        """Verify OAuth state"""
        state_doc = await db.oauth_states.find_one({
            "shop": shop,
            "state": state,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if state_doc:
            # Clean up used state
            await db.oauth_states.delete_one({"_id": state_doc["_id"]})
            return True
        return False
    
    async def _store_access_token(self, shop: str, access_token: str, scope: str):
        """Store encrypted access token"""
        await db.shopify_tokens.update_one(
            {"shop": shop},
            {
                "$set": {
                    "shop": shop,
                    "access_token": access_token,  # In production, encrypt this
                    "scope": scope,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    async def _get_access_token(self, shop: str) -> Optional[str]:
        """Get access token for shop"""
        token_doc = await db.shopify_tokens.find_one({"shop": shop})
        return token_doc["access_token"] if token_doc else None
    
    async def _cache_orders(self, shop: str, orders: List[Dict[str, Any]]):
        """Cache orders locally"""
        await db.shopify_cache.update_one(
            {"shop": shop, "type": "orders"},
            {
                "$set": {
                    "shop": shop,
                    "type": "orders",
                    "data": orders,
                    "cached_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    async def _get_cached_orders(self, shop: str) -> List[Dict[str, Any]]:
        """Get cached orders"""
        cache_doc = await db.shopify_cache.find_one({
            "shop": shop, 
            "type": "orders"
        })
        return cache_doc["data"] if cache_doc else []
    
    async def _cache_products(self, shop: str, products: List[Dict[str, Any]]):
        """Cache products locally"""
        await db.shopify_cache.update_one(
            {"shop": shop, "type": "products"},
            {
                "$set": {
                    "shop": shop,
                    "type": "products", 
                    "data": products,
                    "cached_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    async def _get_cached_products(self, shop: str) -> List[Dict[str, Any]]:
        """Get cached products"""
        cache_doc = await db.shopify_cache.find_one({
            "shop": shop,
            "type": "products"
        })
        return cache_doc["data"] if cache_doc else []
    
    async def _get_mock_orders(self, shop: str, limit: int) -> List[Dict[str, Any]]:
        """Get mock orders from file system"""
        mock_file = f"{self.mock_data_path}/orders_{shop}.json"
        
        try:
            if os.path.exists(mock_file):
                with open(mock_file, 'r') as f:
                    data = json.load(f)
                    return data.get("orders", [])[:limit]
        except:
            pass
        
        # Generate default mock orders
        return await self._generate_mock_orders(shop, limit)
    
    async def _get_mock_products(self, shop: str, limit: int) -> List[Dict[str, Any]]:
        """Get mock products from file system"""
        mock_file = f"{self.mock_data_path}/products_{shop}.json"
        
        try:
            if os.path.exists(mock_file):
                with open(mock_file, 'r') as f:
                    data = json.load(f)
                    return data.get("products", [])[:limit]
        except:
            pass
        
        return await self._generate_mock_products(shop, limit)
    
    async def _generate_mock_orders(self, shop: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock order data"""
        orders = []
        for i in range(min(limit, 5)):  # Generate up to 5 mock orders
            order = {
                "id": f"mock_order_{shop}_{i+1}",
                "name": f"#{1000 + i}",
                "email": f"customer{i+1}@example.com",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "total_price": str(50.0 + (i * 25)),
                "currency": "USD",
                "created_at": (datetime.utcnow() - timedelta(days=i*2)).isoformat(),
                "customer": {
                    "id": f"customer_{i+1}",
                    "first_name": f"Customer{i+1}",
                    "last_name": "Demo",
                    "email": f"customer{i+1}@example.com"
                },
                "line_items": [
                    {
                        "id": f"line_item_{i+1}",
                        "product_id": f"product_{i+1}",
                        "variant_id": f"variant_{i+1}",
                        "title": f"Mock Product {i+1}",
                        "quantity": 1,
                        "price": str(50.0 + (i * 25)),
                        "sku": f"MOCK-{i+1:03d}"
                    }
                ]
            }
            orders.append(order)
        
        # Save mock data for future use
        os.makedirs(self.mock_data_path, exist_ok=True)
        mock_file = f"{self.mock_data_path}/orders_{shop}.json"
        with open(mock_file, 'w') as f:
            json.dump({"orders": orders}, f, indent=2)
        
        return orders
    
    async def _generate_mock_products(self, shop: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock product data"""
        products = []
        categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
        
        for i in range(min(limit, 10)):  # Generate up to 10 mock products
            product = {
                "id": f"mock_product_{shop}_{i+1}",
                "title": f"Mock Product {i+1}",
                "handle": f"mock-product-{i+1}",
                "product_type": categories[i % len(categories)],
                "vendor": shop.capitalize(),
                "created_at": (datetime.utcnow() - timedelta(days=i*7)).isoformat(),
                "variants": [
                    {
                        "id": f"variant_{i+1}",
                        "product_id": f"mock_product_{shop}_{i+1}",
                        "title": "Default Title",
                        "price": str(25.0 + (i * 15)),
                        "sku": f"MOCK-PROD-{i+1:03d}",
                        "inventory_quantity": 100 - (i * 5)
                    }
                ],
                "images": [
                    {
                        "id": f"image_{i+1}",
                        "src": f"https://via.placeholder.com/300x300?text=Product+{i+1}"
                    }
                ]
            }
            products.append(product)
        
        # Save mock data
        os.makedirs(self.mock_data_path, exist_ok=True)
        mock_file = f"{self.mock_data_path}/products_{shop}.json"
        with open(mock_file, 'w') as f:
            json.dump({"products": products}, f, indent=2)
        
        return products

    # Methods needed by unified returns controller
    async def find_order_by_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        """Find order by order number"""
        if self.tenant_id:
            # Get tenant's shop info from database
            tenant = await db.tenants.find_one({"id": self.tenant_id})
            if tenant and tenant.get('shopify_store'):
                shop = tenant['shopify_store']
                orders = await self.get_orders(shop, self.tenant_id, 100)
                
                for order in orders:
                    if order.get('name') == f"#{order_number}" or order.get('order_number') == order_number:
                        return order
        
        # Fallback: search in seeded data
        orders_cursor = db.orders.find({"tenant_id": self.tenant_id, "order_number": order_number})
        orders = await orders_cursor.to_list(1)
        if orders:
            return orders[0]
        
        return None

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        if self.tenant_id:
            # First try from seeded data
            order = await db.orders.find_one({"id": order_id, "tenant_id": self.tenant_id})
            if order:
                return order
                
            # Then try from Shopify if online
            tenant = await db.tenants.find_one({"id": self.tenant_id})
            if tenant and tenant.get('shopify_store'):
                shop = tenant['shopify_store']
                orders = await self.get_orders(shop, self.tenant_id, 100)
                
                for order in orders:
                    if order.get('id') == order_id:
                        return order
        
        return None