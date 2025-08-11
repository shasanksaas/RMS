"""
Query Handlers for CQRS Implementation
Handle queries that retrieve data without side effects
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..queries import (
    GetReturnById, GetReturnsByOrder, SearchReturns, GetReturnAnalytics,
    GetPendingDrafts, LookupOrderForReturn, GetEligibleItemsForReturn,
    GetPolicyPreview, GetReturnAuditLog
)
from ...domain.entities.return_entity import Return, ReturnDraft
from ...domain.value_objects import ReturnId, TenantId, OrderId, Email
from ...domain.services.return_eligibility_service import ReturnEligibilityService, OrderItem
from ...domain.ports.repositories import ReturnRepository, ReturnDraftRepository, OrderRepository
from ...domain.ports.services import ShopifyService, PolicyService


class GetReturnByIdHandler:
    """Handle get return by ID query"""
    
    def __init__(self, return_repository: ReturnRepository):
        self.return_repository = return_repository
    
    async def handle(self, query: GetReturnById) -> Optional[Dict[str, Any]]:
        """Get return by ID"""
        return_id = ReturnId(query.return_id)
        return_obj = await self.return_repository.get_by_id(return_id, query.tenant_id)
        
        if not return_obj:
            return None
        
        return {
            "id": return_obj.id.value,
            "tenant_id": return_obj.tenant_id.value,
            "order_id": return_obj.order_id.value,
            "status": return_obj.status.value,
            "channel": return_obj.channel.value,
            "customer_email": return_obj.customer_email.value,
            "return_method": return_obj.return_method.value,
            "estimated_refund": {
                "amount": float(return_obj.estimated_refund.amount),
                "currency": return_obj.estimated_refund.currency
            },
            "final_refund": {
                "amount": float(return_obj.final_refund.amount),
                "currency": return_obj.final_refund.currency
            } if return_obj.final_refund else None,
            "line_items": [
                {
                    "line_item_id": item.line_item_id,
                    "sku": item.sku,
                    "title": item.title,
                    "variant_title": item.variant_title,
                    "quantity": item.quantity,
                    "unit_price": {
                        "amount": float(item.unit_price.amount),
                        "currency": item.unit_price.currency
                    },
                    "reason": {
                        "code": item.reason.code,
                        "description": item.reason.description
                    },
                    "condition": item.condition,
                    "photos": item.photos,
                    "notes": item.notes
                }
                for item in return_obj.line_items
            ],
            "created_at": return_obj.created_at,
            "updated_at": return_obj.updated_at,
            "submitted_by": return_obj.submitted_by,
            "processed_by": return_obj.processed_by
        }


class SearchReturnsHandler:
    """Handle search returns query"""
    
    def __init__(self, return_repository: ReturnRepository):
        self.return_repository = return_repository
    
    async def handle(self, query: SearchReturns) -> Dict[str, Any]:
        """Search returns with pagination"""
        customer_email = Email(query.customer_email) if query.customer_email else None
        
        returns = await self.return_repository.search(
            tenant_id=query.tenant_id,
            status=query.status,
            customer_email=customer_email,
            date_from=query.date_from,
            date_to=query.date_to,
            limit=query.limit,
            offset=query.offset
        )
        
        total_count = await self.return_repository.count(
            tenant_id=query.tenant_id,
            status=query.status,
            customer_email=customer_email,
            date_from=query.date_from,
            date_to=query.date_to
        )
        
        return {
            "items": [
                {
                    "id": return_obj.id.value,
                    "order_id": return_obj.order_id.value,
                    "status": return_obj.status.value,
                    "customer_email": return_obj.customer_email.value,
                    "estimated_refund": {
                        "amount": float(return_obj.estimated_refund.amount),
                        "currency": return_obj.estimated_refund.currency
                    },
                    "created_at": return_obj.created_at,
                    "updated_at": return_obj.updated_at
                }
                for return_obj in returns
            ],
            "total_count": total_count,
            "current_page": (query.offset // query.limit) + 1,
            "total_pages": (total_count + query.limit - 1) // query.limit,
            "per_page": query.limit
        }


class GetPendingDraftsHandler:
    """Handle get pending drafts query"""
    
    def __init__(self, draft_repository: ReturnDraftRepository):
        self.draft_repository = draft_repository
    
    async def handle(self, query: GetPendingDrafts) -> Dict[str, Any]:
        """Get pending drafts for admin review"""
        drafts = await self.draft_repository.get_pending_for_tenant(query.tenant_id)
        
        # Apply pagination manually (could be moved to repository)
        total_count = len(drafts)
        start = query.offset
        end = start + query.limit
        paginated_drafts = drafts[start:end]
        
        return {
            "items": [
                {
                    "id": draft.id,
                    "order_number": draft.order_number,
                    "customer_email": draft.customer_email.value,
                    "status": draft.status,
                    "items_count": len(draft.items),
                    "photos_count": len(draft.photos),
                    "submitted_at": draft.submitted_at,
                    "customer_note": draft.customer_note
                }
                for draft in paginated_drafts
            ],
            "total_count": total_count,
            "current_page": (query.offset // query.limit) + 1,
            "total_pages": (total_count + query.limit - 1) // query.limit,
            "per_page": query.limit
        }


class LookupOrderForReturnHandler:
    """Handle order lookup for return creation"""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        shopify_service: ShopifyService
    ):
        self.order_repository = order_repository
        self.shopify_service = shopify_service
    
    async def handle(self, query: LookupOrderForReturn) -> Dict[str, Any]:
        """Lookup order for return creation - same logic as merchant dashboard"""
        
        # Primary lookup: Find order by number only (same as merchant dashboard)
        order_by_number = await self.order_repository.find_by_number(
            query.order_number, query.tenant_id
        )
        
        if order_by_number:
            serialized_order = self._serialize_order(order_by_number)
            return {
                "success": True,
                "mode": "local",
                "order": serialized_order
            }
        
        # Secondary: Try with email if provided (for validation)
        if query.customer_email:
            try:
                customer_email = Email(query.customer_email)
                order_with_email = await self.order_repository.find_by_number_and_email(
                    query.order_number, customer_email, query.tenant_id
                )
                
                if order_with_email:
                    serialized_order = self._serialize_order(order_with_email)
                    return {
                        "success": True,
                        "mode": "local",
                        "order": serialized_order
                    }
            except Exception as e:
                print(f"Email validation failed: {e}")
                pass
        
        # Last resort: Try Shopify real-time lookup (if synced data not available)
        if await self.shopify_service.is_connected(query.tenant_id):
            try:
                shopify_order = await self.shopify_service.find_order_by_number(
                    query.order_number, query.tenant_id
                )
                
                if shopify_order:
                    return {
                        "success": True,
                        "mode": "shopify",
                        "order": shopify_order
                    }
            except Exception as e:
                print(f"Shopify lookup failed: {e}")
        
        return {
            "success": False,
            "mode": "fallback",
            "message": "Order not found. Please proceed with manual entry."
        }
    
    def _serialize_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB order document to JSON-serializable format"""
        from bson import ObjectId
        from datetime import datetime
        
        def convert_value(value):
            if isinstance(value, ObjectId):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            else:
                return value
        
        return convert_value(order)


class GetEligibleItemsForReturnHandler:
    """Handle get eligible items for return query"""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        return_repository: ReturnRepository
    ):
        self.order_repository = order_repository
        self.return_repository = return_repository
    
    async def handle(self, query: GetEligibleItemsForReturn) -> List[Dict[str, Any]]:
        """Get eligible items for return from an order"""
        order_id = OrderId(query.order_id)
        
        # Get order items
        items = await self.order_repository.get_eligible_items(order_id, query.tenant_id)
        
        # Get existing returns for this order to calculate already returned quantities
        existing_returns = await self.return_repository.get_by_order_id(order_id, query.tenant_id)
        
        # Calculate returned quantities
        returned_quantities = {}
        for return_obj in existing_returns:
            if return_obj.status.value not in ["declined", "canceled"]:
                for line_item in return_obj.line_items:
                    key = line_item.line_item_id
                    returned_quantities[key] = returned_quantities.get(key, 0) + line_item.quantity
        
        # Build eligible items list
        eligible_items = []
        for item in items:
            item_id = item["id"]
            original_quantity = item["quantity"]
            already_returned = returned_quantities.get(item_id, 0)
            eligible_quantity = max(0, original_quantity - already_returned)
            
            if eligible_quantity > 0:
                eligible_items.append({
                    "line_item_id": item_id,
                    "sku": item.get("sku", ""),
                    "title": item.get("title", ""),
                    "variant_title": item.get("variant_title"),
                    "original_quantity": original_quantity,
                    "eligible_quantity": eligible_quantity,
                    "unit_price": item.get("price", 0),
                    "fulfilled_at": item.get("fulfilled_at"),
                    "tags": item.get("tags", []),
                    "category": item.get("product_type", ""),
                    "product_type": item.get("product_type", "")
                })
        
        return eligible_items


class GetPolicyPreviewHandler:
    """Handle get policy preview query"""
    
    def __init__(
        self,
        policy_service: PolicyService,
        eligibility_service: ReturnEligibilityService,
        order_repository: OrderRepository
    ):
        self.policy_service = policy_service
        self.eligibility_service = eligibility_service
        self.order_repository = order_repository
    
    async def handle(self, query: GetPolicyPreview) -> Dict[str, Any]:
        """Get policy preview for return"""
        # Get current policy
        policy = await self.policy_service.get_current_policy(query.tenant_id)
        
        # Get order data
        order_id = OrderId(query.order_id)
        order = await self.order_repository.get_by_id(order_id, query.tenant_id)
        
        if not order:
            raise ValueError("Order not found")
        
        # Convert order items to domain objects
        order_items = []
        for item in order.get("line_items", []):
            order_item = OrderItem(
                id=item["id"],
                sku=item.get("sku", ""),
                title=item.get("title", ""),
                variant_title=item.get("variant_title"),
                quantity=item["quantity"],
                unit_price=item["price"],
                fulfilled_at=item.get("fulfilled_at"),
                tags=item.get("tags", []),
                category=item.get("product_type", ""),
                product_type=item.get("product_type", "")
            )
            order_items.append(order_item)
        
        # Check eligibility
        result = self.eligibility_service.check_eligibility(
            order_items=order_items,
            requested_items=query.items,
            order_date=datetime.fromisoformat(order["created_at"]),
            policy=policy
        )
        
        return {
            "eligible": result.eligible,
            "auto_approve": result.auto_approve,
            "estimated_refund": {
                "amount": float(result.estimated_refund.amount),
                "currency": result.estimated_refund.currency
            },
            "fees": result.fees,
            "reasons": result.reasons,
            "warnings": result.warning_messages,
            "policy_summary": {
                "return_window_days": policy.return_window_days,
                "restock_fee_percent": float(policy.restock_fee_percent) if policy.restock_fee_enabled else 0,
                "shipping_fee": float(policy.shipping_fee_amount) if policy.shipping_fee_enabled else 0
            }
        }


class GetReturnAuditLogHandler:
    """Handle get return audit log query"""
    
    def __init__(self, return_repository: ReturnRepository):
        self.return_repository = return_repository
    
    async def handle(self, query: GetReturnAuditLog) -> List[Dict[str, Any]]:
        """Get return audit log"""
        return_id = ReturnId(query.return_id)
        return_obj = await self.return_repository.get_by_id(return_id, query.tenant_id)
        
        if not return_obj:
            raise ValueError("Return not found")
        
        return [
            {
                "timestamp": entry.timestamp,
                "actor": entry.actor,
                "action": entry.action,
                "details": entry.details,
                "correlation_id": entry.correlation_id
            }
            for entry in return_obj.audit_log
        ]