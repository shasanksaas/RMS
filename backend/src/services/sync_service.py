"""
Shopify Sync Service
Handles initial backfill and ongoing synchronization
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..config.database import db
from ..services.shopify_graphql import ShopifyGraphQLFactory
from ..modules.auth.service import auth_service

logger = logging.getLogger(__name__)


class ShopifySyncService:
    """Service for syncing Shopify data with backfill and ongoing updates"""
    
    def __init__(self):
        self.batch_size = 50
        self.max_backfill_days = 90  # Only sync last 90 days on initial install
        
    async def perform_initial_sync(self, tenant_id: str) -> Dict[str, Any]:
        """
        Perform initial backfill sync for a newly connected store
        
        Args:
            tenant_id: Store tenant ID (shop.myshopify.com)
        
        Returns:
            Dict with sync results
        """
        logger.info(f"Starting initial sync for {tenant_id}")
        
        # Get GraphQL service
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            raise Exception("Failed to create GraphQL service")
        
        sync_results = {
            "tenant_id": tenant_id,
            "started_at": datetime.utcnow(),
            "orders": {"synced": 0, "errors": 0},
            "products": {"synced": 0, "errors": 0},
            "returns": {"synced": 0, "errors": 0},
            "customers": {"synced": 0, "errors": 0}
        }
        
        try:
            # Update sync status
            await self._update_sync_status(tenant_id, "in_progress", "Starting initial sync")
            
            # Sync products first (needed for order line items)
            products_result = await self._sync_products(graphql_service, tenant_id)
            sync_results["products"] = products_result
            logger.info(f"Products sync completed for {tenant_id}: {products_result}")
            
            # Sync recent orders (last 90 days)
            orders_result = await self._sync_recent_orders(graphql_service, tenant_id)
            sync_results["orders"] = orders_result
            logger.info(f"Orders sync completed for {tenant_id}: {orders_result}")
            
            # Sync existing returns
            returns_result = await self._sync_returns(graphql_service, tenant_id)
            sync_results["returns"] = returns_result
            logger.info(f"Returns sync completed for {tenant_id}: {returns_result}")
            
            # Update sync completion
            sync_results["completed_at"] = datetime.utcnow()
            sync_results["duration_seconds"] = (sync_results["completed_at"] - sync_results["started_at"]).total_seconds()
            
            await self._update_sync_status(
                tenant_id, 
                "completed", 
                f"Initial sync completed. Orders: {orders_result['synced']}, Products: {products_result['synced']}, Returns: {returns_result['synced']}"
            )
            
            # Store sync results
            await db.sync_logs.insert_one({
                "tenant_id": tenant_id,
                "sync_type": "initial_backfill",
                "results": sync_results,
                "completed_at": datetime.utcnow()
            })
            
            logger.info(f"Initial sync completed for {tenant_id}: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Initial sync failed for {tenant_id}: {e}")
            await self._update_sync_status(tenant_id, "failed", f"Initial sync failed: {str(e)}")
            raise e

    async def _sync_products(self, graphql_service, tenant_id: str) -> Dict[str, Any]:
        """Sync all active products"""
        synced_count = 0
        error_count = 0
        cursor = None
        
        try:
            while True:
                # Get batch of products
                result = await graphql_service.get_products(
                    limit=self.batch_size,
                    cursor=cursor
                )
                
                products = result.get("products", {}).get("edges", [])
                if not products:
                    break
                
                # Process each product
                for product_edge in products:
                    try:
                        product = product_edge["node"]
                        product_data = self._transform_product_data(product, tenant_id)
                        
                        # Upsert product
                        await db.products.update_one(
                            {"product_id": product_data["product_id"], "tenant_id": tenant_id},
                            {"$set": product_data},
                            upsert=True
                        )
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing product {product.get('id')}: {e}")
                        error_count += 1
                
                # Check for next page
                page_info = result.get("products", {}).get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Products sync error for {tenant_id}: {e}")
            error_count += 1
        
        return {"synced": synced_count, "errors": error_count}

    async def _sync_recent_orders(self, graphql_service, tenant_id: str) -> Dict[str, Any]:
        """Sync orders from the last 90 days"""
        synced_count = 0
        error_count = 0
        cursor = None
        
        # Query for recent orders
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_backfill_days)
        query_filter = f"created_at:>={cutoff_date.strftime('%Y-%m-%d')}"
        
        try:
            while True:
                # Get batch of orders
                result = await graphql_service.get_orders(
                    limit=self.batch_size,
                    cursor=cursor,
                    query_filter=query_filter
                )
                
                orders = result.get("orders", {}).get("edges", [])
                if not orders:
                    break
                
                # Process each order
                for order_edge in orders:
                    try:
                        order = order_edge["node"]
                        order_data = self._transform_order_data(order, tenant_id)
                        
                        # Upsert order
                        await db.orders.update_one(
                            {"order_id": order_data["order_id"], "tenant_id": tenant_id},
                            {"$set": order_data},
                            upsert=True
                        )
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing order {order.get('id')}: {e}")
                        error_count += 1
                
                # Check for next page
                page_info = result.get("orders", {}).get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Orders sync error for {tenant_id}: {e}")
            error_count += 1
        
        return {"synced": synced_count, "errors": error_count}

    async def _sync_returns(self, graphql_service, tenant_id: str) -> Dict[str, Any]:
        """Sync existing returns"""
        synced_count = 0
        error_count = 0
        cursor = None
        
        try:
            while True:
                # Get batch of returns
                result = await graphql_service.get_returns(
                    limit=self.batch_size,
                    cursor=cursor
                )
                
                returns = result.get("returns", {}).get("edges", [])
                if not returns:
                    break
                
                # Process each return
                for return_edge in returns:
                    try:
                        return_data_raw = return_edge["node"]
                        return_data = self._transform_return_data(return_data_raw, tenant_id)
                        
                        # Upsert return
                        await db.return_requests.update_one(
                            {"return_id": return_data["return_id"], "tenant_id": tenant_id},
                            {"$set": return_data},
                            upsert=True
                        )
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing return {return_data_raw.get('id')}: {e}")
                        error_count += 1
                
                # Check for next page
                page_info = result.get("returns", {}).get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Returns sync error for {tenant_id}: {e}")
            error_count += 1
        
        return {"synced": synced_count, "errors": error_count}

    async def trigger_sync_for_store(self, tenant_id: str, sync_type: str = "manual") -> Dict[str, Any]:
        """
        Trigger a sync for a specific store
        
        Args:
            tenant_id: Store tenant ID
            sync_type: Type of sync (initial, manual, scheduled)
        """
        # Check if store exists and is active
        store = await auth_service.get_store_connection(tenant_id)
        if not store:
            raise Exception("Store not found or inactive")
        
        # Check for ongoing sync
        ongoing_sync = await db.stores.find_one({
            "tenant_id": tenant_id,
            "sync_status": "in_progress"
        })
        
        if ongoing_sync:
            raise Exception("Sync already in progress for this store")
        
        # Start sync based on type
        if sync_type == "initial":
            return await self.perform_initial_sync(tenant_id)
        else:
            # For manual/scheduled syncs, do incremental sync
            return await self._perform_incremental_sync(tenant_id)

    async def _perform_incremental_sync(self, tenant_id: str) -> Dict[str, Any]:
        """Perform incremental sync (only recent changes)"""
        logger.info(f"Starting incremental sync for {tenant_id}")
        
        # Get last sync time
        last_sync = await db.stores.find_one({"tenant_id": tenant_id})
        last_sync_time = last_sync.get("last_sync") if last_sync else datetime.utcnow() - timedelta(hours=24)
        
        # Get GraphQL service
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        if not graphql_service:
            raise Exception("Failed to create GraphQL service")
        
        sync_results = {
            "tenant_id": tenant_id,
            "sync_type": "incremental",
            "started_at": datetime.utcnow(),
            "last_sync_time": last_sync_time,
            "orders": {"synced": 0, "errors": 0},
            "returns": {"synced": 0, "errors": 0}
        }
        
        try:
            await self._update_sync_status(tenant_id, "in_progress", "Starting incremental sync")
            
            # Sync orders updated since last sync
            query_filter = f"updated_at:>={last_sync_time.strftime('%Y-%m-%dT%H:%M:%S')}"
            orders_result = await self._sync_orders_with_filter(graphql_service, tenant_id, query_filter)
            sync_results["orders"] = orders_result
            
            # Sync recent returns
            returns_result = await self._sync_returns(graphql_service, tenant_id)
            sync_results["returns"] = returns_result
            
            # Update completion
            sync_results["completed_at"] = datetime.utcnow()
            
            await self._update_sync_status(
                tenant_id,
                "completed",
                f"Incremental sync completed. Orders: {orders_result['synced']}, Returns: {returns_result['synced']}"
            )
            
            # Update last sync time
            await db.stores.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"last_sync": datetime.utcnow()}}
            )
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Incremental sync failed for {tenant_id}: {e}")
            await self._update_sync_status(tenant_id, "failed", f"Incremental sync failed: {str(e)}")
            raise e

    async def _sync_orders_with_filter(self, graphql_service, tenant_id: str, query_filter: str) -> Dict[str, Any]:
        """Sync orders with a specific filter"""
        synced_count = 0
        error_count = 0
        cursor = None
        
        try:
            while True:
                result = await graphql_service.get_orders(
                    limit=self.batch_size,
                    cursor=cursor,
                    query_filter=query_filter
                )
                
                orders = result.get("orders", {}).get("edges", [])
                if not orders:
                    break
                
                for order_edge in orders:
                    try:
                        order = order_edge["node"]
                        order_data = self._transform_order_data(order, tenant_id)
                        
                        await db.orders.update_one(
                            {"order_id": order_data["order_id"], "tenant_id": tenant_id},
                            {"$set": order_data},
                            upsert=True
                        )
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing order {order.get('id')}: {e}")
                        error_count += 1
                
                page_info = result.get("orders", {}).get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Filtered orders sync error: {e}")
            error_count += 1
        
        return {"synced": synced_count, "errors": error_count}

    async def _update_sync_status(self, tenant_id: str, status: str, message: str):
        """Update sync status in database"""
        await db.stores.update_one(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "sync_status": status,
                    "sync_message": message,
                    "sync_updated_at": datetime.utcnow()
                }
            }
        )

    def _transform_product_data(self, product: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Transform GraphQL product data to our format"""
        variants = []
        for variant_edge in product.get("variants", {}).get("edges", []):
            variant = variant_edge["node"]
            variants.append({
                "variant_id": variant.get("id"),
                "title": variant.get("title"),
                "sku": variant.get("sku"),
                "price": variant.get("price"),
                "inventory_quantity": variant.get("inventoryQuantity"),
                "available_for_sale": variant.get("availableForSale")
            })
        
        return {
            "product_id": product.get("id"),
            "title": product.get("title"),
            "handle": product.get("handle"),
            "status": product.get("status"),
            "product_type": product.get("productType"),
            "vendor": product.get("vendor"),
            "tags": product.get("tags", []),
            "variants": variants,
            "created_at": product.get("createdAt"),
            "updated_at": product.get("updatedAt"),
            "tenant_id": tenant_id,
            "synced_at": datetime.utcnow()
        }

    def _transform_order_data(self, order: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Transform GraphQL order data to our format"""
        customer = order.get("customer", {})
        line_items = []
        
        for item_edge in order.get("lineItems", {}).get("edges", []):
            item = item_edge["node"]
            line_items.append({
                "line_item_id": item.get("id"),
                "name": item.get("name"),
                "sku": item.get("sku"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "product_id": item.get("product", {}).get("id"),
                "variant_id": item.get("variant", {}).get("id")
            })
        
        return {
            "order_id": order.get("id"),
            "order_number": order.get("name"),
            "email": order.get("email"),
            "customer_id": customer.get("id"),
            "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
            "customer_email": customer.get("email"),
            "financial_status": order.get("financialStatus"),
            "fulfillment_status": order.get("fulfillmentStatus"),
            "total_price": order.get("totalPrice"),
            "currency_code": order.get("currencyCode"),
            "line_items": line_items,
            "billing_address": order.get("billingAddress"),
            "shipping_address": order.get("shippingAddress"),
            "fulfillments": [f.get("id") for f in order.get("fulfillments", [])],
            "created_at": order.get("createdAt"),
            "updated_at": order.get("updatedAt"),
            "processed_at": order.get("processedAt"),
            "tenant_id": tenant_id,
            "synced_at": datetime.utcnow()
        }

    def _transform_return_data(self, return_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Transform GraphQL return data to our format"""
        order = return_data.get("order", {})
        customer = order.get("customer", {})
        
        return_line_items = []
        for item_edge in return_data.get("returnLineItems", {}).get("edges", []):
            item = item_edge["node"]
            fulfillment_item = item.get("fulfillmentLineItem", {})
            line_item = fulfillment_item.get("lineItem", {})
            
            return_line_items.append({
                "return_line_item_id": item.get("id"),
                "quantity": item.get("quantity"),
                "return_reason": item.get("returnReason"),
                "return_reason_note": item.get("returnReasonNote"),
                "line_item_id": line_item.get("id"),
                "product_name": line_item.get("name"),
                "sku": line_item.get("sku"),
                "price": line_item.get("price")
            })
        
        return {
            "return_id": return_data.get("id"),
            "name": return_data.get("name"),
            "status": return_data.get("status", "requested"),
            "total_quantity": return_data.get("totalQuantity"),
            "order_id": order.get("id"),
            "order_number": order.get("name"),
            "customer_id": customer.get("id"),
            "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
            "customer_email": customer.get("email"),
            "return_line_items": return_line_items,
            "requested_at": return_data.get("requestedAt"),
            "processed_at": return_data.get("processedAt"),
            "decline_reason": return_data.get("declineReason"),
            "refunds": [{"refund_id": r.get("id"), "amount": r.get("totalRefunded", {}).get("amount")} 
                       for r in return_data.get("refunds", [])],
            "tenant_id": tenant_id,
            "synced_at": datetime.utcnow()
        }


# Singleton instance
sync_service = ShopifySyncService()