"""
Shopify Webhook Handlers
Processes incoming webhooks with idempotency and proper error handling
"""

import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ..config.database import db
from ..services.shopify_graphql import ShopifyGraphQLFactory
from ..modules.auth.service import auth_service

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Main webhook processing service with idempotency"""
    
    def __init__(self):
        self.handlers = {
            # App lifecycle
            "app/uninstalled": self.handle_app_uninstalled,
            
            # Orders
            "orders/create": self.handle_order_created,
            "orders/updated": self.handle_order_updated,
            "orders/cancelled": self.handle_order_cancelled,
            "orders/fulfilled": self.handle_order_fulfilled,
            "orders/partially_fulfilled": self.handle_order_partially_fulfilled,
            "orders/paid": self.handle_order_paid,
            
            # Returns
            "returns/create": self.handle_return_created,
            "returns/update": self.handle_return_update,
            "returns/requested": self.handle_return_requested,
            "returns/approved": self.handle_return_approved,
            "returns/declined": self.handle_return_declined,
            "returns/cancelled": self.handle_return_cancelled,
            
            # Refunds
            "refunds/create": self.handle_refund_created,
            
            # Fulfillments
            "fulfillments/create": self.handle_fulfillment_created,
            "fulfillments/update": self.handle_fulfillment_updated,
            "fulfillments/cancel": self.handle_fulfillment_cancelled,
            
            # Products
            "products/update": self.handle_product_updated,
            "product_variants/update": self.handle_product_variant_updated,
            
            # Inventory
            "inventory_levels/update": self.handle_inventory_updated,
        }

    async def process_webhook(self, topic: str, shop_domain: str, payload: Dict[str, Any], 
                            webhook_id: str = None) -> Dict[str, Any]:
        """
        Process webhook with idempotency checks
        
        Args:
            topic: Webhook topic (e.g., 'orders/create')
            shop_domain: Shop domain from header
            payload: Webhook payload
            webhook_id: Unique webhook ID for idempotency
        """
        
        # Generate unique webhook identifier for deduplication
        if not webhook_id:
            webhook_id = self._generate_webhook_id(topic, shop_domain, payload)
        
        # Check if we've already processed this webhook
        existing = await db.webhook_logs.find_one({"webhook_id": webhook_id})
        if existing:
            logger.info(f"Webhook {webhook_id} already processed, skipping")
            return {"status": "duplicate", "processed_at": existing["processed_at"]}
        
        # Log webhook receipt
        log_entry = {
            "webhook_id": webhook_id,
            "topic": topic,
            "shop_domain": shop_domain,
            "tenant_id": f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com",
            "received_at": datetime.utcnow(),
            "status": "processing",
            "payload_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        }
        
        try:
            await db.webhook_logs.insert_one(log_entry)
            
            # Process the webhook
            if topic in self.handlers:
                result = await self.handlers[topic](shop_domain, payload)
                
                # Update log with success
                await db.webhook_logs.update_one(
                    {"webhook_id": webhook_id},
                    {
                        "$set": {
                            "status": "completed",
                            "processed_at": datetime.utcnow(),
                            "result": result
                        }
                    }
                )
                
                return {"status": "success", "result": result}
            else:
                logger.warning(f"No handler for webhook topic: {topic}")
                await db.webhook_logs.update_one(
                    {"webhook_id": webhook_id},
                    {
                        "$set": {
                            "status": "no_handler",
                            "processed_at": datetime.utcnow(),
                            "error": f"No handler for topic: {topic}"
                        }
                    }
                )
                return {"status": "no_handler", "topic": topic}
                
        except Exception as e:
            logger.error(f"Error processing webhook {webhook_id}: {e}")
            
            # Update log with error
            await db.webhook_logs.update_one(
                {"webhook_id": webhook_id},
                {
                    "$set": {
                        "status": "error",
                        "processed_at": datetime.utcnow(),
                        "error": str(e)
                    }
                }
            )
            
            raise e

    def _generate_webhook_id(self, topic: str, shop_domain: str, payload: Dict[str, Any]) -> str:
        """Generate unique webhook ID for idempotency"""
        # Use resource ID and timestamp for uniqueness
        resource_id = payload.get("id", "")
        updated_at = payload.get("updated_at", payload.get("created_at", ""))
        
        unique_string = f"{topic}:{shop_domain}:{resource_id}:{updated_at}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    # APP LIFECYCLE HANDLERS
    async def handle_app_uninstalled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app uninstallation - critical for cleanup"""
        logger.info(f"App uninstalled from {shop_domain}")
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        # Deactivate the store
        result = await auth_service.disconnect_store(tenant_id, "system_uninstall")
        
        # Clean up any active sessions or cached data
        await db.webhook_logs.update_many(
            {"shop_domain": shop_domain},
            {"$set": {"cleaned_up": True, "cleanup_at": datetime.utcnow()}}
        )
        
        return {
            "action": "store_deactivated",
            "tenant_id": tenant_id,
            "disconnected": result,
            "cleanup_completed": True
        }

    # ORDER HANDLERS
    async def handle_order_created(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new order creation"""
        order_data = self._transform_order_payload(payload)
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        # Upsert order
        await db.orders.update_one(
            {"order_id": order_data["order_id"], "tenant_id": tenant_id},
            {"$set": {**order_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "order_synced", "order_id": order_data["order_id"]}

    async def handle_order_updated(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order updates"""
        return await self.handle_order_created(shop_domain, payload)  # Same logic

    async def handle_order_cancelled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order cancellation"""
        order_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.orders.update_one(
            {"order_id": order_id, "tenant_id": tenant_id},
            {"$set": {"cancelled_at": payload.get("cancelled_at"), "synced_at": datetime.utcnow()}}
        )
        
        return {"action": "order_cancelled", "order_id": order_id}

    async def handle_order_fulfilled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order fulfillment"""
        order_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.orders.update_one(
            {"order_id": order_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "fulfillment_status": payload.get("fulfillment_status"),
                    "fulfilled_at": payload.get("fulfilled_at"),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "order_fulfilled", "order_id": order_id}

    async def handle_order_partially_fulfilled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle partial order fulfillment"""
        return await self.handle_order_fulfilled(shop_domain, payload)  # Same logic

    async def handle_order_paid(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order payment"""
        order_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.orders.update_one(
            {"order_id": order_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "financial_status": payload.get("financial_status"),
                    "paid_at": payload.get("paid_at"),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "order_paid", "order_id": order_id}

    # RETURN HANDLERS
    async def handle_return_created(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return creation"""
        return_data = self._transform_return_payload(payload)
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        # Upsert return
        await db.return_requests.update_one(
            {"return_id": return_data["return_id"], "tenant_id": tenant_id},
            {"$set": {**return_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "return_synced", "return_id": return_data["return_id"]}

    async def handle_return_requested(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return request"""
        return await self.handle_return_created(shop_domain, payload)  # Same logic

    async def handle_return_approved(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return approval from Shopify - Two-way sync"""
        try:
            return_id = str(payload.get("id"))
            order_id = str(payload.get("order_id", ""))
            
            # Correct tenant_id format (matches our app format)
            tenant_id = f"tenant-{shop_domain.replace('.myshopify.com', '')}"
            
            print(f"🔄 Shopify webhook: Return {return_id} approved for {tenant_id}")
            
            # Find the return in our database by order_id (since Shopify return ID might differ)
            return_query = {}
            if return_id:
                return_query["$or"] = [
                    {"shopify_return_id": return_id},
                    {"id": return_id}
                ]
            if order_id:
                if "$or" in return_query:
                    return_query["$or"].append({"order_id": order_id})
                else:
                    return_query["order_id"] = order_id
            
            return_query["tenant_id"] = tenant_id
            
            current_return = await db.returns.find_one(return_query)
            
            if not current_return:
                print(f"⚠️ No matching return found for Shopify return {return_id}, order {order_id}")
                return {"action": "return_not_found", "return_id": return_id}
            
            # Check if status is already approved (prevent loops)
            if current_return.get("status", "").lower() == "approved":
                print(f"✅ Return {current_return['id']} already approved, skipping update")
                return {"action": "no_change", "return_id": current_return["id"]}
            
            # Create audit entry for Shopify sync
            audit_entry = {
                "id": f"audit_shopify_{int(datetime.utcnow().timestamp() * 1000)}",
                "action": "status_updated_from_shopify", 
                "performed_by": "shopify_webhook",
                "timestamp": datetime.utcnow(),
                "details": {
                    "old_status": current_return.get("status", "unknown"),
                    "new_status": "approved",
                    "shopify_return_id": return_id,
                    "shopify_order_id": order_id,
                    "source": "shopify_webhook"
                },
                "description": f"Status updated to APPROVED via Shopify webhook",
                "type": "shopify_sync"
            }
            
            # Update return in our database
            update_result = await db.returns.update_one(
                {"id": current_return["id"], "tenant_id": tenant_id},
                {
                    "$set": {
                        "status": "approved",
                        "decision": "approved",
                        "decision_made_at": datetime.utcnow(),
                        "decision_made_by": "shopify",
                        "shopify_return_id": return_id,
                        "approved_at": datetime.utcnow(),
                        "synced_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"audit_log": audit_entry}
                }
            )
            
            if update_result.matched_count > 0:
                print(f"✅ Updated return {current_return['id']} status to approved from Shopify")
                return {"action": "return_approved", "return_id": current_return["id"], "shopify_return_id": return_id}
            else:
                print(f"❌ Failed to update return {current_return['id']}")
                return {"action": "update_failed", "return_id": current_return["id"]}
            
        except Exception as e:
            print(f"❌ Error handling return approved webhook: {e}")
            return {"action": "error", "error": str(e)}

    async def handle_return_declined(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return decline from Shopify - Two-way sync"""
        try:
            return_id = str(payload.get("id"))
            order_id = str(payload.get("order_id", ""))
            decline_reason = payload.get("decline_reason", "")
            
            # Correct tenant_id format (matches our app format)
            tenant_id = f"tenant-{shop_domain.replace('.myshopify.com', '')}"
            
            print(f"🔄 Shopify webhook: Return {return_id} declined for {tenant_id}")
            
            # Find the return in our database
            return_query = {}
            if return_id:
                return_query["$or"] = [
                    {"shopify_return_id": return_id},
                    {"id": return_id}
                ]
            if order_id:
                if "$or" in return_query:
                    return_query["$or"].append({"order_id": order_id})
                else:
                    return_query["order_id"] = order_id
            
            return_query["tenant_id"] = tenant_id
            
            current_return = await db.returns.find_one(return_query)
            
            if not current_return:
                print(f"⚠️ No matching return found for Shopify return {return_id}, order {order_id}")
                return {"action": "return_not_found", "return_id": return_id}
            
            # Check if status is already denied (prevent loops)
            if current_return.get("status", "").lower() in ["denied", "rejected"]:
                print(f"✅ Return {current_return['id']} already denied, skipping update")
                return {"action": "no_change", "return_id": current_return["id"]}
            
            # Create audit entry for Shopify sync
            audit_entry = {
                "id": f"audit_shopify_{int(datetime.utcnow().timestamp() * 1000)}",
                "action": "status_updated_from_shopify",
                "performed_by": "shopify_webhook",
                "timestamp": datetime.utcnow(),
                "details": {
                    "old_status": current_return.get("status", "unknown"),
                    "new_status": "denied",
                    "decline_reason": decline_reason,
                    "shopify_return_id": return_id,
                    "shopify_order_id": order_id,
                    "source": "shopify_webhook"
                },
                "description": f"Status updated to DENIED via Shopify webhook",
                "type": "shopify_sync"
            }
            
            # Update return in our database
            update_result = await db.returns.update_one(
                {"id": current_return["id"], "tenant_id": tenant_id},
                {
                    "$set": {
                        "status": "denied",
                        "decision": "denied", 
                        "decision_made_at": datetime.utcnow(),
                        "decision_made_by": "shopify",
                        "shopify_return_id": return_id,
                        "decline_reason": decline_reason,
                        "declined_at": datetime.utcnow(),
                        "synced_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {"audit_log": audit_entry}
                }
            )
            
            if update_result.matched_count > 0:
                print(f"✅ Updated return {current_return['id']} status to denied from Shopify")
                return {"action": "return_declined", "return_id": current_return["id"], "shopify_return_id": return_id}
            else:
                print(f"❌ Failed to update return {current_return['id']}")
                return {"action": "update_failed", "return_id": current_return["id"]}
            
        except Exception as e:
            print(f"❌ Error handling return declined webhook: {e}")
            return {"action": "error", "error": str(e)}

    async def handle_return_cancelled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return cancellation"""
        return_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.return_requests.update_one(
            {"return_id": return_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "return_cancelled", "return_id": return_id}

    async def handle_return_reopen(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return reopen - Shopify RMS Guide requirement"""
        return_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.return_requests.update_one(
            {"return_id": return_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "open",
                    "reopened_at": datetime.utcnow(),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "return_reopened", "return_id": return_id}

    async def handle_return_close(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return close - Shopify RMS Guide requirement"""
        return_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.return_requests.update_one(
            {"return_id": return_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "closed",
                    "closed_at": datetime.utcnow(),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "return_closed", "return_id": return_id}

    async def handle_return_update(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle return update - Shopify RMS Guide requirement"""
        return_data = self._transform_return_payload(payload)
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        # Update return with new data
        await db.return_requests.update_one(
            {"return_id": return_data["return_id"], "tenant_id": tenant_id},
            {"$set": {**return_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "return_updated", "return_id": return_data["return_id"]}

    # REFUND HANDLERS
    async def handle_refund_created(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund creation"""
        refund_data = {
            "refund_id": str(payload.get("id")),
            "order_id": str(payload.get("order_id")),
            "amount": float(payload.get("amount", 0)),
            "reason": payload.get("note"),
            "created_at": payload.get("created_at"),
            "refund_line_items": payload.get("refund_line_items", [])
        }
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.refunds.update_one(
            {"refund_id": refund_data["refund_id"], "tenant_id": tenant_id},
            {"$set": {**refund_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "refund_synced", "refund_id": refund_data["refund_id"]}

    # FULFILLMENT HANDLERS
    async def handle_fulfillment_created(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment creation"""
        fulfillment_data = {
            "fulfillment_id": str(payload.get("id")),
            "order_id": str(payload.get("order_id")),
            "status": payload.get("status"),
            "tracking_number": payload.get("tracking_number"),
            "tracking_company": payload.get("tracking_company"),
            "tracking_urls": payload.get("tracking_urls", []),
            "created_at": payload.get("created_at")
        }
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.fulfillments.update_one(
            {"fulfillment_id": fulfillment_data["fulfillment_id"], "tenant_id": tenant_id},
            {"$set": {**fulfillment_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "fulfillment_synced", "fulfillment_id": fulfillment_data["fulfillment_id"]}

    async def handle_fulfillment_updated(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment updates"""
        return await self.handle_fulfillment_created(shop_domain, payload)  # Same logic

    async def handle_fulfillment_cancelled(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment cancellation"""
        fulfillment_id = str(payload.get("id"))
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.fulfillments.update_one(
            {"fulfillment_id": fulfillment_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        return {"action": "fulfillment_cancelled", "fulfillment_id": fulfillment_id}

    # PRODUCT HANDLERS
    async def handle_product_updated(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product updates"""
        product_data = {
            "product_id": str(payload.get("id")),
            "title": payload.get("title"),
            "handle": payload.get("handle"),
            "product_type": payload.get("product_type"),
            "vendor": payload.get("vendor"),
            "status": payload.get("status"),
            "updated_at": payload.get("updated_at"),
            "variants": payload.get("variants", [])
        }
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.products.update_one(
            {"product_id": product_data["product_id"], "tenant_id": tenant_id},
            {"$set": {**product_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "product_synced", "product_id": product_data["product_id"]}

    async def handle_product_variant_updated(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product variant updates"""
        variant_data = {
            "variant_id": str(payload.get("id")),
            "product_id": str(payload.get("product_id")),
            "title": payload.get("title"),
            "sku": payload.get("sku"),
            "price": payload.get("price"),
            "inventory_quantity": payload.get("inventory_quantity"),
            "updated_at": payload.get("updated_at")
        }
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.product_variants.update_one(
            {"variant_id": variant_data["variant_id"], "tenant_id": tenant_id},
            {"$set": {**variant_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "variant_synced", "variant_id": variant_data["variant_id"]}

    # INVENTORY HANDLERS
    async def handle_inventory_updated(self, shop_domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory level updates"""
        inventory_data = {
            "inventory_item_id": str(payload.get("inventory_item_id")),
            "location_id": str(payload.get("location_id")),
            "available": payload.get("available"),
            "updated_at": payload.get("updated_at")
        }
        
        tenant_id = f"{shop_domain.replace('.myshopify.com', '')}.myshopify.com"
        
        await db.inventory_levels.update_one(
            {
                "inventory_item_id": inventory_data["inventory_item_id"],
                "location_id": inventory_data["location_id"],
                "tenant_id": tenant_id
            },
            {"$set": {**inventory_data, "tenant_id": tenant_id, "synced_at": datetime.utcnow()}},
            upsert=True
        )
        
        return {"action": "inventory_synced", "inventory_item_id": inventory_data["inventory_item_id"]}

    # HELPER METHODS
    def _transform_order_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Shopify order payload to our format"""
        customer = payload.get("customer", {})
        return {
            "order_id": str(payload.get("id")),
            "order_number": payload.get("name", "").replace("#", ""),
            "email": payload.get("email"),
            "customer_id": str(customer.get("id", "")),
            "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            "customer_email": customer.get("email"),
            "financial_status": payload.get("financial_status"),
            "fulfillment_status": payload.get("fulfillment_status"),
            "total_price": float(payload.get("total_price", 0)),
            "currency_code": payload.get("currency", "USD"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "processed_at": payload.get("processed_at"),
            "line_items": payload.get("line_items", []),
            "shipping_address": payload.get("shipping_address"),
            "billing_address": payload.get("billing_address"),
            "fulfillments": [f.get("id") for f in payload.get("fulfillments", [])],
            "raw_order_data": payload
        }

    def _transform_return_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Shopify return payload to our format"""
        return {
            "return_id": str(payload.get("id")),
            "order_id": str(payload.get("order_id", "")),
            "name": payload.get("name"),
            "status": payload.get("status", "requested"),
            "total_quantity": payload.get("total_quantity", 0),
            "requested_at": payload.get("requested_at"),
            "processed_at": payload.get("processed_at"),
            "decline_reason": payload.get("decline_reason"),
            "return_line_items": payload.get("return_line_items", []),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at")
        }


# Singleton instance
webhook_processor = WebhookProcessor()