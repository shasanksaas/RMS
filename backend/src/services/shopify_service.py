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
from ..modules.auth.service import ShopifyAuthService


class ShopifyService:
    """Service for Shopify API interactions with offline fallback"""
    
    def __init__(self, tenant_id: str = None):
        self.offline_mode = OFFLINE_MODE
        self.mock_data_path = MOCK_DATA_PATH
        self.tenant_id = tenant_id
        self.auth_service = ShopifyAuthService()  # For decrypting tokens
    
    async def is_connected(self, tenant_id: str = None) -> bool:
        """Check if this tenant has a connected Shopify integration"""
        # Use provided tenant_id or instance tenant_id
        check_tenant_id = tenant_id or self.tenant_id
        
        print(f"DEBUG is_connected: tenant_id param={tenant_id}, check_tenant_id={check_tenant_id}")
        
        if not check_tenant_id:
            print("DEBUG is_connected: No tenant_id available")
            return False
            
        try:
            # First check integrations_shopify collection
            print(f"DEBUG is_connected: Checking integrations_shopify collection")
            integration = await db.integrations_shopify.find_one({
                "tenant_id": check_tenant_id,
                "status": "connected"
            })
            if integration:
                print(f"DEBUG is_connected: Found in integrations_shopify")
                return True
                
            # Also check tenant document for shopify_integration field
            print(f"DEBUG is_connected: Checking tenants collection")
            tenant = await db.tenants.find_one({"id": check_tenant_id})
            if tenant and tenant.get('shopify_integration'):
                shopify_integration = tenant['shopify_integration']
                result = (shopify_integration.get('status') == 'connected' and 
                       shopify_integration.get('access_token') and
                       shopify_integration.get('shop_domain'))
                print(f"DEBUG is_connected: Tenant check result={result}")
                return result
                       
            print(f"DEBUG is_connected: No integration found")
            return False
        except Exception as e:
            print(f"DEBUG is_connected: Error checking Shopify connection: {e}")
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
    async def find_order_by_number(self, order_number: str, tenant_id: str = None) -> Optional[Dict[str, Any]]:
        """Real-time Shopify GraphQL lookup by order number - NO cached data"""
        use_tenant_id = tenant_id or self.tenant_id
        
        if not use_tenant_id:
            return None
            
        try:
            # Get real-time access token and shop info from integrations_shopify collection
            integration = await db.integrations_shopify.find_one({"tenant_id": use_tenant_id})
            if not integration:
                print(f"DEBUG: No integration found in integrations_shopify for {use_tenant_id}")
                return None
                
            access_token = integration.get('access_token')
            shop_domain = integration.get('shop_domain')
            
            print(f"DEBUG: Raw access_token from integrations_shopify: {access_token}")
            
            # Decrypt the access token if it's encrypted
            if access_token and access_token.startswith('gAAAAAB'):
                try:
                    access_token = self.auth_service._decrypt_secret(access_token)
                    print(f"DEBUG: Successfully decrypted access token")
                except Exception as e:
                    print(f"DEBUG: Failed to decrypt access token: {e}")
                    return None
            
            print(f"DEBUG: Found integration for {use_tenant_id}, shop_domain: {shop_domain}, has_token: {bool(access_token)}")
            
            if not access_token or not shop_domain:
                print(f"DEBUG: Missing credentials - token: {bool(access_token)}, domain: {shop_domain}")
                return None
            
            # Real-time GraphQL query to Shopify API
            graphql_url = f"https://{shop_domain}/admin/api/2024-10/graphql.json"
            
            # GraphQL query to find order by name (order number)
            query = """
            query getOrderByName($query: String!) {
                orders(first: 1, query: $query) {
                    edges {
                        node {
                            id
                            name
                            email
                            phone
                            totalPriceSet {
                                shopMoney {
                                    amount
                                    currencyCode
                                }
                            }
                            customer {
                                id
                                email
                                firstName
                                lastName
                                phone
                                displayName
                            }
                            billingAddress {
                                firstName
                                lastName
                                company
                                address1
                                address2
                                city
                                province
                                country
                                zip
                                phone
                            }
                            shippingAddress {
                                firstName
                                lastName
                                company
                                address1
                                address2
                                city
                                province
                                country
                                zip
                                phone
                            }
                            lineItems(first: 50) {
                                edges {
                                    node {
                                        id
                                        title
                                        quantity
                                        variant {
                                            id
                                            title
                                            sku
                                            price
                                        }
                                        originalUnitPriceSet {
                                            shopMoney {
                                                amount
                                                currencyCode
                                            }
                                        }
                                        product {
                                            id
                                            title
                                            productType
                                            vendor
                                        }
                                    }
                                }
                            }
                            createdAt
                            updatedAt
                            processedAt
                            displayFinancialStatus
                            displayFulfillmentStatus
                        }
                    }
                }
            }
            """
            
            # Add # prefix if not present
            search_order_number = order_number if order_number.startswith('#') else f"#{order_number}"
            
            variables = {
                "query": f"name:{search_order_number}"
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": access_token
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            # Execute real-time GraphQL query
            print(f"DEBUG: Making GraphQL query to {graphql_url} for order {search_order_number}")
            print(f"DEBUG: Headers: {headers}")
            print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(graphql_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    print(f"DEBUG: GraphQL response status: {response.status}")
                    response_text = await response.text()
                    print(f"DEBUG: GraphQL response text: {response_text}")
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            print(f"DEBUG: GraphQL response data keys: {list(data.keys()) if data else 'None'}")
                            
                            if 'errors' in data:
                                print(f"DEBUG: GraphQL errors: {data['errors']}")
                                return None
                                
                            orders = data.get('data', {}).get('orders', {}).get('edges', [])
                            print(f"DEBUG: Found {len(orders)} orders matching {search_order_number}")
                            
                            if orders:
                                order_node = orders[0]['node']
                                
                                # Transform GraphQL response to standard format
                                result = self._transform_graphql_order(order_node)
                                print(f"DEBUG: Transformed order result: {bool(result)}")
                                return result
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error: {e}")
                            return None
                    else:
                        print(f"DEBUG: Shopify API error {response.status}: {response_text}")
                        return None
                        
        except Exception as e:
            print(f"Real-time Shopify lookup error: {e}")
            return None
        
        return None
    
    def _transform_graphql_order(self, order_node: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GraphQL order response to standard format"""
        try:
            # Extract line items
            line_items = []
            for edge in order_node.get('lineItems', {}).get('edges', []):
                item_node = edge['node']
                variant = item_node.get('variant') or {}  # Handle null variants
                product = item_node.get('product') or {}  # Handle null products
                
                line_item = {
                    "id": item_node.get('id', ''),
                    "title": item_node.get('title', ''),
                    "quantity": item_node.get('quantity', 0),
                    "sku": variant.get('sku', ''),
                    "variant_title": variant.get('title', ''),
                    "variant_id": variant.get('id', ''),
                    "product_id": product.get('id', ''),
                    "product_title": product.get('title', ''),
                    "product_type": product.get('productType', ''),
                    "vendor": product.get('vendor', ''),
                    "price": float(variant.get('price', 0)) if variant.get('price') else 0.0,
                    "unit_price": float(item_node.get('originalUnitPriceSet', {}).get('shopMoney', {}).get('amount', 0)),
                    "fulfillment_status": "fulfilled"  # Default for eligible returns
                }
                line_items.append(line_item)
            
            # Extract customer information
            customer = order_node.get('customer') or {}  # Handle null customer
            billing = order_node.get('billingAddress') or {}  # Handle null billing
            shipping = order_node.get('shippingAddress') or {}  # Handle null shipping
            
            # Build standard order format
            transformed_order = {
                "id": order_node.get('id', '').replace('gid://shopify/Order/', ''),
                "order_number": order_node.get('name', '').replace('#', ''),
                "name": order_node.get('name', ''),
                "email": order_node.get('email', ''),
                "phone": order_node.get('phone', ''),
                "total_price": float(order_node.get('totalPriceSet', {}).get('shopMoney', {}).get('amount', 0)),
                "currency": order_node.get('totalPriceSet', {}).get('shopMoney', {}).get('currencyCode', 'USD'),
                "customer_id": customer.get('id', '').replace('gid://shopify/Customer/', '') if customer.get('id') else None,
                "customer_email": customer.get('email', ''),
                "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() if customer else '',
                "customer_phone": customer.get('phone', ''),
                "customer_display_name": customer.get('displayName', ''),
                "billing_address": billing,
                "shipping_address": shipping,
                "line_items": line_items,
                "financial_status": order_node.get('displayFinancialStatus', '').lower(),
                "fulfillment_status": order_node.get('displayFulfillmentStatus', '').lower(),
                "created_at": order_node.get('createdAt', ''),
                "updated_at": order_node.get('updatedAt', ''),
                "processed_at": order_node.get('processedAt', ''),
                "source": "shopify_live",  # Mark as live data
                "tenant_id": self.tenant_id
            }
            
            return transformed_order
            
        except Exception as e:
            print(f"Order transformation error: {e}")
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
    
    async def get_order_for_return(self, order_id: str, tenant_id: str = None) -> Optional[Dict[str, Any]]:
        """Get order by ID for return creation - uses real-time Shopify API"""
        use_tenant_id = tenant_id or self.tenant_id
        
        print(f"DEBUG get_order_for_return: order_id={order_id}, tenant_id={use_tenant_id}")
        
        if not use_tenant_id:
            print("DEBUG: No tenant_id provided")
            return None
        
        # First check local database
        try:
            print(f"DEBUG: Checking local database for order")
            order = await db.orders.find_one({"id": order_id, "tenant_id": use_tenant_id})
            if order:
                print(f"DEBUG: Found order in local database")
                return order
        except Exception as e:
            print(f"DEBUG: Database lookup error: {e}")
            
        # If not in database, fetch from Shopify using real-time API
        try:
            print(f"DEBUG: Fetching from Shopify API")
            # Get tenant credentials from integrations_shopify collection
            integration = await db.integrations_shopify.find_one({"tenant_id": use_tenant_id})
            if not integration:
                print(f"DEBUG: No integration found in integrations_shopify")
                return None
                
            access_token = integration.get('access_token')
            shop_domain = integration.get('shop_domain')
            
            if not access_token or not shop_domain:
                return None
            
            # Decrypt the access token if it's encrypted
            if access_token and access_token.startswith('gAAAAAB'):
                try:
                    access_token = self.auth_service._decrypt_secret(access_token)
                except Exception as e:
                    print(f"Failed to decrypt access token: {e}")
                    return None
            
            # Real-time GraphQL query to get specific order by ID
            graphql_url = f"https://{shop_domain}/admin/api/2024-10/graphql.json"
            
            query = """
            query getOrder($id: ID!) {
                order(id: $id) {
                    id
                    name
                    email
                    phone
                    totalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                    customer {
                        id
                        email
                        firstName
                        lastName
                        phone
                        displayName
                    }
                    lineItems(first: 50) {
                        edges {
                            node {
                                id
                                title
                                quantity
                                variant {
                                    id
                                    title
                                    sku
                                    price
                                }
                                originalUnitPriceSet {
                                    shopMoney {
                                        amount
                                        currencyCode
                                    }
                                }
                                product {
                                    id
                                    title
                                    productType
                                    vendor
                                }
                            }
                        }
                    }
                    createdAt
                    updatedAt
                    processedAt
                    displayFinancialStatus
                    displayFulfillmentStatus
                }
            }
            """
            
            # Convert order ID to GraphQL format
            gql_order_id = f"gid://shopify/Order/{order_id}"
            
            variables = {"id": gql_order_id}
            
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": access_token
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            # Execute real-time GraphQL query
            async with aiohttp.ClientSession() as session:
                async with session.post(graphql_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            if 'errors' in data:
                                print(f"GraphQL errors: {data['errors']}")
                                return None
                                
                            order_data = data.get('data', {}).get('order')
                            
                            if order_data:
                                # Transform GraphQL response to standard format
                                return self._transform_graphql_order(order_data)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            return None
                    else:
                        print(f"Shopify API error {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error fetching order for return: {e}")
            return None
        
        return None