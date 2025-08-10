"""
Advanced Returns Service
Handles the complete returns lifecycle
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from ..config.database import db
from ..models.return_models import (
    ReturnRequest, ReturnStatus, PreferredOutcome, 
    ReturnMethod, ExternalSyncStatus, AuditLogEntry,
    PortalChannel
)
from .rules_engine_advanced import AdvancedRulesEngine
from .label_service import LabelService
from .email_service_advanced import EmailService
from .offers_service import OffersService

logger = logging.getLogger(__name__)

class AdvancedReturnsService:
    """Advanced returns processing service"""
    
    def __init__(self):
        self.rules_engine = AdvancedRulesEngine()
        self.label_service = LabelService()
        self.email_service = EmailService()
        self.offers_service = OffersService()
    
    async def lookup_order(self, tenant_id: str, order_number: str, email: str) -> Dict[str, Any]:
        """
        Lookup order and determine eligibility
        First check local DB, then Shopify if connected
        """
        try:
            # Check local database first
            order = await db.orders.find_one({
                "tenant_id": tenant_id,
                "$or": [
                    {"order_number": order_number},
                    {"order_number": order_number.replace("#", "")}
                ],
                "customer_email": email
            })
            
            if not order:
                # If Shopify connected, try live lookup
                from .shopify_service import ShopifyService
                shopify_service = ShopifyService(tenant_id)
                
                if await shopify_service.is_connected():
                    order_data = await shopify_service.find_order_by_number_and_email(order_number, email)
                    if order_data:
                        # Save to local DB
                        order = await self._save_shopify_order(tenant_id, order_data)
            
            if not order:
                return {
                    "success": False,
                    "error": "Order not found. Please check your order number and email address."
                }
            
            # Get eligible items using rules engine
            policy = await self._get_tenant_policy(tenant_id)
            eligible_items = await self.rules_engine.get_eligible_items(order, policy)
            
            return {
                "success": True,
                "order": order,
                "eligible_items": eligible_items,
                "policy_info": {
                    "return_window_days": policy.get("return_window_days", 30),
                    "fees": policy.get("fees", {}),
                    "eligible_outcomes": policy.get("eligible_outcomes", []),
                    "eligible_methods": policy.get("eligible_methods", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Order lookup error for {tenant_id}: {e}")
            return {
                "success": False,
                "error": "Failed to lookup order. Please try again."
            }
    
    async def preview_policy(self, tenant_id: str, order_id: str, items: List[Dict], 
                           preferred_outcome: str, return_method: str) -> Dict[str, Any]:
        """Get policy preview with fees, eligibility, and explanations"""
        try:
            order = await db.orders.find_one({"id": order_id, "tenant_id": tenant_id})
            if not order:
                return {"success": False, "error": "Order not found"}
            
            policy = await self._get_tenant_policy(tenant_id)
            
            # Run rules engine
            result = await self.rules_engine.evaluate_return_request(
                order, items, preferred_outcome, return_method, policy
            )
            
            return {
                "success": True,
                "eligible": result["eligible"],
                "fees": result["fees"],
                "estimated_refund": result["estimated_refund"],
                "explanation": result["explanation"],
                "auto_approve": result["auto_approve"],
                "offers": await self.offers_service.get_applicable_offers(tenant_id, order, items)
            }
            
        except Exception as e:
            logger.error(f"Policy preview error for {tenant_id}: {e}")
            return {"success": False, "error": "Failed to preview policy"}
    
    async def create_return_request(self, tenant_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new return request"""
        try:
            # Validate order exists
            order = await db.orders.find_one({
                "id": request_data["order_id"], 
                "tenant_id": tenant_id
            })
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Get policy and run rules
            policy = await self._get_tenant_policy(tenant_id)
            evaluation = await self.rules_engine.evaluate_return_request(
                order, request_data["items"], request_data["preferred_outcome"], 
                request_data["return_method"], policy
            )
            
            if not evaluation["eligible"]:
                return {
                    "success": False,
                    "error": f"Return not eligible: {evaluation['explanation']['reason']}"
                }
            
            # Create return request
            return_id = str(uuid.uuid4())
            
            # Apply offers if selected
            promo_applied = None
            if request_data.get("offer"):
                promo_applied = await self.offers_service.apply_offer(
                    tenant_id, request_data["offer"], evaluation["estimated_refund"]
                )
            
            return_request = {
                "id": return_id,
                "tenant_id": tenant_id,
                "order_id": request_data["order_id"],
                "portal_channel": request_data.get("channel", "customer"),
                "status": "APPROVED" if evaluation["auto_approve"] else "REQUESTED",
                "preferred_outcome": request_data["preferred_outcome"],
                "reason_code": request_data["items"][0]["reason_code"],  # Primary reason
                "reason_note": request_data.get("customer_note", ""),
                "items": request_data["items"],
                "photos": request_data.get("photos", []),
                "return_method": request_data["return_method"],
                "fees_applied": evaluation["fees"],
                "estimated_refund_amount": evaluation["estimated_refund"],
                "promo_applied": promo_applied,
                "external_sync_status": "none",
                "external_ids": {},
                "audit_log": [{
                    "at": datetime.utcnow(),
                    "actor": {"type": "customer", "email": order.get("customer_email")},
                    "action": "return_requested",
                    "details": {"items_count": len(request_data["items"]), "outcome": request_data["preferred_outcome"]}
                }],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save to database
            await db.return_requests.insert_one(return_request)
            
            # If auto-approved, generate label and send emails
            if evaluation["auto_approve"]:
                await self._process_approval(tenant_id, return_id, "system")
            
            # Send notification emails
            await self.email_service.send_return_requested(tenant_id, return_request, order)
            
            return {
                "success": True,
                "return_id": return_id,
                "status": return_request["status"],
                "estimated_refund": evaluation["estimated_refund"],
                "auto_approved": evaluation["auto_approve"]
            }
            
        except Exception as e:
            logger.error(f"Create return error for {tenant_id}: {e}")
            return {"success": False, "error": "Failed to create return request"}
    
    async def approve_return(self, tenant_id: str, return_id: str, actor_id: str) -> Dict[str, Any]:
        """Approve a return request"""
        try:
            return_request = await db.return_requests.find_one({
                "id": return_id,
                "tenant_id": tenant_id
            })
            
            if not return_request:
                return {"success": False, "error": "Return not found"}
            
            if return_request["status"] != "REQUESTED":
                return {"success": False, "error": "Return cannot be approved in current status"}
            
            # Update status and audit log
            await self._update_return_status(tenant_id, return_id, "APPROVED", {
                "type": "user",
                "id": actor_id
            }, "return_approved")
            
            # Process approval (generate label, send emails)
            await self._process_approval(tenant_id, return_id, actor_id)
            
            return {"success": True, "message": "Return approved successfully"}
            
        except Exception as e:
            logger.error(f"Approve return error: {e}")
            return {"success": False, "error": "Failed to approve return"}
    
    async def decline_return(self, tenant_id: str, return_id: str, actor_id: str, reason: str) -> Dict[str, Any]:
        """Decline a return request"""
        try:
            return_request = await db.return_requests.find_one({
                "id": return_id,
                "tenant_id": tenant_id
            })
            
            if not return_request:
                return {"success": False, "error": "Return not found"}
            
            # Update status and audit log
            await self._update_return_status(tenant_id, return_id, "DECLINED", {
                "type": "user",
                "id": actor_id
            }, "return_declined", {"reason": reason})
            
            # Send notification email
            order = await db.orders.find_one({"id": return_request["order_id"], "tenant_id": tenant_id})
            await self.email_service.send_return_declined(tenant_id, return_request, order, reason)
            
            return {"success": True, "message": "Return declined successfully"}
            
        except Exception as e:
            logger.error(f"Decline return error: {e}")
            return {"success": False, "error": "Failed to decline return"}
    
    async def generate_label(self, tenant_id: str, return_id: str) -> Dict[str, Any]:
        """Generate shipping label for return"""
        try:
            return_request = await db.return_requests.find_one({
                "id": return_id,
                "tenant_id": tenant_id
            })
            
            if not return_request or return_request["status"] != "APPROVED":
                return {"success": False, "error": "Return must be approved to generate label"}
            
            # Generate label using LabelService
            order = await db.orders.find_one({"id": return_request["order_id"], "tenant_id": tenant_id})
            label_result = await self.label_service.create_return_label(
                tenant_id, return_request, order
            )
            
            if label_result["success"]:
                # Update return status
                await self._update_return_status(tenant_id, return_id, "LABEL_ISSUED", {
                    "type": "system"
                }, "label_generated", {"tracking": label_result["tracking"]})
                
                # Send label email
                await self.email_service.send_label_issued(tenant_id, return_request, order, label_result)
            
            return label_result
            
        except Exception as e:
            logger.error(f"Generate label error: {e}")
            return {"success": False, "error": "Failed to generate label"}
    
    async def process_refund(self, tenant_id: str, return_id: str, amount: float, 
                           method: str, actor_id: str) -> Dict[str, Any]:
        """Process refund for return"""
        try:
            return_request = await db.return_requests.find_one({
                "id": return_id,
                "tenant_id": tenant_id
            })
            
            if not return_request:
                return {"success": False, "error": "Return not found"}
            
            # Update return with refund details
            await db.return_requests.update_one(
                {"id": return_id, "tenant_id": tenant_id},
                {
                    "$set": {
                        "status": "REFUNDED",
                        "final_refund_amount": amount,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "audit_log": {
                            "at": datetime.utcnow(),
                            "actor": {"type": "user", "id": actor_id},
                            "action": "refund_processed",
                            "details": {"amount": amount, "method": method}
                        }
                    }
                }
            )
            
            # Send refund confirmation email
            order = await db.orders.find_one({"id": return_request["order_id"], "tenant_id": tenant_id})
            await self.email_service.send_refund_processed(tenant_id, return_request, order, amount, method)
            
            # Sync to Shopify if connected
            await self._sync_to_shopify(tenant_id, return_id, "refund", {"amount": amount})
            
            return {"success": True, "message": "Refund processed successfully"}
            
        except Exception as e:
            logger.error(f"Process refund error: {e}")
            return {"success": False, "error": "Failed to process refund"}
    
    async def _process_approval(self, tenant_id: str, return_id: str, actor_id: str):
        """Handle post-approval processing"""
        try:
            return_request = await db.return_requests.find_one({
                "id": return_id,
                "tenant_id": tenant_id
            })
            
            # Check if label is needed
            if return_request["return_method"] in ["PREPAID_LABEL", "QR_DROPOFF"]:
                # Generate label automatically
                await self.generate_label(tenant_id, return_id)
            
            # Send approval email
            order = await db.orders.find_one({"id": return_request["order_id"], "tenant_id": tenant_id})
            await self.email_service.send_return_approved(tenant_id, return_request, order)
            
            # Sync to Shopify if connected
            await self._sync_to_shopify(tenant_id, return_id, "approve", {})
            
        except Exception as e:
            logger.error(f"Process approval error: {e}")
    
    async def _update_return_status(self, tenant_id: str, return_id: str, new_status: str, 
                                   actor: Dict, action: str, details: Dict = None):
        """Update return status with audit log"""
        audit_entry = {
            "at": datetime.utcnow(),
            "actor": actor,
            "action": action,
            "details": details or {}
        }
        
        await db.return_requests.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
    
    async def _get_tenant_policy(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant policy with defaults"""
        policy = await db.policies.find_one({"tenant_id": tenant_id})
        
        if not policy:
            # Return default policy
            return {
                "return_window_days": 30,
                "window_overrides": [],
                "excluded": {"tags": ["FinalSale"], "categories": []},
                "condition_requirements": {"photo_required_reasons": ["DAMAGED", "DEFECTIVE"]},
                "fees": {
                    "restock": {"enabled": True, "percent": 10, "min_amount": 0},
                    "shipping": {
                        "enabled": True,
                        "methods": {
                            "PREPAID_LABEL": {"amount": 5.00},
                            "QR_DROPOFF": {"amount": 3.00},
                            "IN_STORE": {"amount": 0},
                            "CUSTOMER_SHIPS": {"amount": 0}
                        }
                    }
                },
                "auto_approve": {
                    "enabled": True,
                    "max_item_price": 150,
                    "max_total": 300,
                    "disallow_reasons": ["FRAUD_RISK"]
                },
                "eligible_outcomes": ["REFUND", "STORE_CREDIT", "EXCHANGE", "REPLACEMENT"],
                "eligible_methods": ["PREPAID_LABEL", "QR_DROPOFF", "IN_STORE", "CUSTOMER_SHIPS"],
                "offers": {
                    "bonus_store_credit_percent": 10,
                    "keep_item_credit_percent": 30,
                    "exchange_discount_percent": 10
                }
            }
        
        return policy
    
    async def _save_shopify_order(self, tenant_id: str, shopify_order: Dict) -> Dict:
        """Save Shopify order to local database"""
        order_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "external_id": shopify_order.get("admin_graphql_api_id"),
            "order_number": shopify_order.get("name", "").replace("#", ""),
            "customer_email": shopify_order.get("email", ""),
            "customer_name": shopify_order.get("customer", {}).get("first_name", "") + " " + 
                           shopify_order.get("customer", {}).get("last_name", ""),
            "created_at": shopify_order.get("created_at"),
            "fulfillment_status": shopify_order.get("fulfillment_status"),
            "financial_status": shopify_order.get("financial_status"),
            "currency": shopify_order.get("currency", "USD"),
            "total_amount": float(shopify_order.get("total_price", 0)),
            "items": shopify_order.get("line_items", []),
            "source": "shopify",
            "metadata": {"shopify_id": str(shopify_order.get("id"))}
        }
        
        await db.orders.insert_one(order_doc)
        return order_doc
    
    async def _sync_to_shopify(self, tenant_id: str, return_id: str, action: str, data: Dict):
        """Sync return action to Shopify if connected"""
        try:
            # Check if Shopify is connected
            integration = await db.integrations_shopify.find_one({"tenant_id": tenant_id})
            if not integration or integration.get("status") != "connected":
                # Mark as pending sync
                await db.return_requests.update_one(
                    {"id": return_id, "tenant_id": tenant_id},
                    {"$set": {"external_sync_status": "pending"}}
                )
                return
            
            # TODO: Implement actual Shopify sync based on action
            # For now, mark as synced
            await db.return_requests.update_one(
                {"id": return_id, "tenant_id": tenant_id},
                {"$set": {"external_sync_status": "synced"}}
            )
            
        except Exception as e:
            logger.error(f"Shopify sync error: {e}")
            await db.return_requests.update_one(
                {"id": return_id, "tenant_id": tenant_id},
                {"$set": {"external_sync_status": "error"}}
            )

# Singleton instance
advanced_returns_service = AdvancedReturnsService()