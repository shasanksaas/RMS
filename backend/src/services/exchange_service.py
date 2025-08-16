"""
Exchange Service for handling exchange-related business logic
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.config.database import db
from src.services.shopify_service import ShopifyService


class ExchangeService:
    """Business logic for exchange operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.shopify_service = ShopifyService(tenant_id)
    
    async def validate_exchange_eligibility(self, order_id: str, customer_email: str) -> Dict[str, Any]:
        """Validate if customer can create exchange for this order"""
        try:
            # Get order
            order = await db.orders.find_one({
                "id": order_id,
                "tenant_id": self.tenant_id
            })
            
            if not order:
                return {
                    "eligible": False,
                    "reason": "Order not found"
                }
            
            # Check customer email
            if order.get("customer_email", "").lower() != customer_email.lower():
                return {
                    "eligible": False,
                    "reason": "Customer email does not match order"
                }
            
            # Check if order is within exchange window (example: 30 days)
            order_date = order.get("created_at")
            if order_date:
                if isinstance(order_date, str):
                    try:
                        order_date = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                    except:
                        order_date = datetime.utcnow()
                
                days_since_order = (datetime.utcnow() - order_date).days
                if days_since_order > 30:  # 30-day exchange window
                    return {
                        "eligible": False,
                        "reason": f"Exchange window expired ({days_since_order} days ago)"
                    }
            
            # Check if there are already exchanges for this order
            existing_exchanges = await db.exchanges.find({
                "order_id": order_id,
                "tenant_id": self.tenant_id,
                "status": {"$nin": ["cancelled", "rejected"]}
            }).to_list(10)
            
            if len(existing_exchanges) >= 2:  # Max 2 exchanges per order
                return {
                    "eligible": False,
                    "reason": "Maximum number of exchanges reached for this order"
                }
            
            return {
                "eligible": True,
                "order": order,
                "existing_exchanges": len(existing_exchanges)
            }
            
        except Exception as e:
            print(f"Exchange eligibility validation error: {e}")
            return {
                "eligible": False,
                "reason": "Failed to validate eligibility"
            }
    
    async def calculate_exchange_totals(self, returned_items: List[Dict], exchange_items: List[Dict]) -> Dict[str, Any]:
        """Calculate totals for exchange transaction"""
        try:
            returned_total = 0.0
            exchange_total = 0.0
            
            # Calculate returned items total
            for item in returned_items:
                price = float(item.get("price", 0))
                quantity = int(item.get("quantity", 1))
                returned_total += price * quantity
            
            # Calculate exchange items total and validate availability
            exchange_details = []
            for item in exchange_items:
                variant_id = item.get("variant_id")
                quantity = int(item.get("quantity", 1))
                
                # Get variant details and validate
                variant = await self.shopify_service.get_variant(variant_id)
                if not variant:
                    raise ValueError(f"Variant {variant_id} not found")
                
                price = float(variant.get("price", 0))
                inventory = variant.get("inventory_quantity", 0)
                
                if inventory < quantity:
                    raise ValueError(f"Insufficient inventory for {variant.get('title', variant_id)}")
                
                item_total = price * quantity
                exchange_total += item_total
                
                exchange_details.append({
                    "variant_id": variant_id,
                    "title": variant.get("title"),
                    "product_title": variant.get("product_title"),
                    "price": price,
                    "quantity": quantity,
                    "total": item_total,
                    "available_inventory": inventory
                })
            
            price_difference = exchange_total - returned_total
            
            return {
                "returned_total": returned_total,
                "exchange_total": exchange_total,
                "price_difference": price_difference,
                "requires_payment": price_difference > 0,
                "refund_due": price_difference < 0,
                "exchange_details": exchange_details,
                "calculation_valid": True
            }
            
        except Exception as e:
            print(f"Exchange calculation error: {e}")
            return {
                "calculation_valid": False,
                "error": str(e)
            }
    
    async def create_exchange_record(self, exchange_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create exchange record in database"""
        try:
            exchange_id = f"EXC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
            
            exchange_record = {
                "id": exchange_id,
                "type": "exchange",
                "tenant_id": self.tenant_id,
                "order_id": exchange_data["order_id"],
                "customer_email": exchange_data["customer_email"],
                "status": "pending_approval",
                "processing_status": "awaiting_merchant_review",
                "returned_items": exchange_data["returned_items"],
                "exchange_items": exchange_data["exchange_items"],
                "price_difference": exchange_data["price_difference"],
                "requires_payment": exchange_data["requires_payment"],
                "refund_due": exchange_data["refund_due"],
                "customer_note": exchange_data.get("customer_note", ""),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "audit_trail": [{
                    "action": "exchange_created",
                    "timestamp": datetime.utcnow(),
                    "actor": "customer",
                    "details": {
                        "returned_items_count": len(exchange_data["returned_items"]),
                        "exchange_items_count": len(exchange_data["exchange_items"]),
                        "price_difference": exchange_data["price_difference"]
                    }
                }]
            }
            
            # Insert into database
            result = await db.exchanges.insert_one(exchange_record)
            
            if not result.inserted_id:
                raise Exception("Failed to insert exchange record")
            
            return {
                "success": True,
                "exchange_id": exchange_id,
                "status": "pending_approval",
                "created_at": exchange_record["created_at"].isoformat()
            }
            
        except Exception as e:
            print(f"Create exchange record error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_exchange_status(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        """Get exchange status and details"""
        try:
            exchange = await db.exchanges.find_one({
                "id": exchange_id,
                "tenant_id": self.tenant_id
            })
            
            if not exchange:
                return None
            
            # Get related order
            order = await db.orders.find_one({
                "id": exchange["order_id"],
                "tenant_id": self.tenant_id
            })
            
            # Format response
            return {
                "id": exchange["id"],
                "order_id": exchange["order_id"],
                "order_number": order.get("order_number") if order else None,
                "status": exchange["status"],
                "processing_status": exchange["processing_status"],
                "price_difference": exchange["price_difference"],
                "requires_payment": exchange.get("requires_payment", False),
                "refund_due": exchange.get("refund_due", False),
                "created_at": exchange["created_at"].isoformat() if isinstance(exchange["created_at"], datetime) else exchange["created_at"],
                "updated_at": exchange["updated_at"].isoformat() if isinstance(exchange["updated_at"], datetime) else exchange["updated_at"],
                "returned_items": exchange["returned_items"],
                "exchange_items": exchange["exchange_items"],
                "customer_note": exchange.get("customer_note", ""),
                "audit_trail": exchange.get("audit_trail", [])
            }
            
        except Exception as e:
            print(f"Get exchange status error: {e}")
            return None
    
    async def approve_exchange(self, exchange_id: str, merchant_notes: str = "") -> Dict[str, Any]:
        """Approve exchange request (merchant action)"""
        try:
            # Get exchange
            exchange = await db.exchanges.find_one({
                "id": exchange_id,
                "tenant_id": self.tenant_id
            })
            
            if not exchange:
                raise Exception("Exchange not found")
            
            if exchange.get("status") != "pending_approval":
                raise Exception("Exchange is not pending approval")
            
            # Update exchange status
            update_data = {
                "status": "approved",
                "processing_status": "preparing_new_order",
                "updated_at": datetime.utcnow(),
                "approved_at": datetime.utcnow(),
                "merchant_notes": merchant_notes
            }
            
            # Add audit entry
            audit_entry = {
                "action": "exchange_approved",
                "timestamp": datetime.utcnow(),
                "actor": "merchant",
                "details": {
                    "notes": merchant_notes
                }
            }
            
            # Update database
            result = await db.exchanges.update_one(
                {"id": exchange_id, "tenant_id": self.tenant_id},
                {
                    "$set": update_data,
                    "$push": {"audit_trail": audit_entry}
                }
            )
            
            if result.matched_count == 0:
                raise Exception("Failed to update exchange")
            
            # TODO: In production, this would:
            # 1. Create new Shopify order for exchange items
            # 2. Process payment if needed
            # 3. Send confirmation email
            # 4. Reserve inventory
            
            return {
                "success": True,
                "status": "approved",
                "message": "Exchange approved successfully"
            }
            
        except Exception as e:
            print(f"Approve exchange error: {e}")
            return {
                "success": False,
                "error": str(e)
            }