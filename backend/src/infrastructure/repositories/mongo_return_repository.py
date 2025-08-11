"""
MongoDB implementation of Return Repository
Adapter for persistence using MongoDB
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ...domain.entities.return_entity import Return, ReturnStatus, ReturnChannel, ReturnMethod, ReturnLineItem
from ...domain.value_objects import ReturnId, TenantId, OrderId, Email, Money, ReturnReason, PolicySnapshot, AuditEntry
from ...domain.ports.repositories import ReturnRepository


class MongoReturnRepository(ReturnRepository):
    """MongoDB implementation of Return Repository"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.returns
    
    async def save(self, return_obj: Return) -> None:
        """Save or update a return"""
        try:
            print(f"DEBUG save: Converting return {return_obj.id.value} to document")
            document = self._to_document(return_obj)
            print(f"DEBUG save: Document keys: {list(document.keys())}")
            
            # Upsert based on return ID
            print(f"DEBUG save: Upserting to database")
            result = await self.collection.update_one(
                {"id": return_obj.id.value, "tenant_id": return_obj.tenant_id.value},
                {"$set": document},
                upsert=True
            )
            print(f"DEBUG save: Upsert result - matched: {result.matched_count}, modified: {result.modified_count}, upserted: {result.upserted_id}")
        except Exception as e:
            print(f"DEBUG save: Error during save: {e}")
            raise
    
    async def get_by_id(self, return_id: ReturnId, tenant_id: TenantId) -> Optional[Return]:
        """Get return by ID"""
        document = await self.collection.find_one({
            "id": return_id.value,
            "tenant_id": tenant_id.value
        })
        
        if not document:
            return None
        
        return self._from_document(document)
    
    async def get_by_order_id(self, order_id: OrderId, tenant_id: TenantId) -> List[Return]:
        """Get returns for an order"""
        cursor = self.collection.find({
            "order_id": order_id.value,
            "tenant_id": tenant_id.value
        })
        
        documents = await cursor.to_list(length=None)
        return [self._from_document(doc) for doc in documents]
    
    async def search(
        self, 
        tenant_id: TenantId,
        status: Optional[str] = None,
        customer_email: Optional[Email] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Return]:
        """Search returns with filters"""
        query = {"tenant_id": tenant_id.value}
        
        if status:
            query["status"] = status
        
        if customer_email:
            query["customer_email"] = customer_email.value
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query
        
        cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
        documents = await cursor.to_list(length=None)
        
        return [self._from_document(doc) for doc in documents]
    
    async def count(
        self, 
        tenant_id: TenantId,
        status: Optional[str] = None,
        customer_email: Optional[Email] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """Count returns with filters"""
        query = {"tenant_id": tenant_id.value}
        
        if status:
            query["status"] = status
        
        if customer_email:
            query["customer_email"] = customer_email.value
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query
        
        return await self.collection.count_documents(query)
    
    def _to_document(self, return_obj: Return) -> Dict[str, Any]:
        """Convert Return entity to MongoDB document"""
        return {
            "id": return_obj.id.value,
            "tenant_id": return_obj.tenant_id.value,
            "order_id": return_obj.order_id.value,
            "channel": return_obj.channel.value,
            "status": return_obj.status.value,
            "customer_email": return_obj.customer_email.value,
            "return_method": return_obj.return_method.value,
            "line_items": [
                {
                    "line_item_id": item.line_item_id,
                    "sku": item.sku,
                    "title": item.title,
                    "variant_title": item.variant_title,
                    "quantity": item.quantity,
                    "unit_price": {
                        "amount": str(item.unit_price.amount),
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
            "policy_snapshot": {
                "return_window_days": return_obj.policy_snapshot.return_window_days,
                "restock_fee_enabled": return_obj.policy_snapshot.restock_fee_enabled,
                "restock_fee_percent": str(return_obj.policy_snapshot.restock_fee_percent),
                "shipping_fee_enabled": return_obj.policy_snapshot.shipping_fee_enabled,
                "shipping_fee_amount": str(return_obj.policy_snapshot.shipping_fee_amount),
                "photo_required_reasons": return_obj.policy_snapshot.photo_required_reasons,
                "excluded_categories": return_obj.policy_snapshot.excluded_categories,
                "excluded_tags": return_obj.policy_snapshot.excluded_tags,
                "auto_approve_threshold": str(return_obj.policy_snapshot.auto_approve_threshold),
                "eligible_outcomes": return_obj.policy_snapshot.eligible_outcomes,
                "eligible_methods": return_obj.policy_snapshot.eligible_methods,
                "created_at": return_obj.policy_snapshot.created_at
            },
            "estimated_refund": {
                "amount": str(return_obj.estimated_refund.amount),
                "currency": return_obj.estimated_refund.currency
            },
            "final_refund": {
                "amount": str(return_obj.final_refund.amount),
                "currency": return_obj.final_refund.currency
            } if return_obj.final_refund else None,
            "created_at": return_obj.created_at,
            "updated_at": return_obj.updated_at,
            "submitted_by": return_obj.submitted_by,
            "processed_by": return_obj.processed_by,
            "audit_log": [
                {
                    "timestamp": entry.timestamp,
                    "actor": entry.actor,
                    "action": entry.action,
                    "details": entry.details,
                    "correlation_id": entry.correlation_id
                }
                for entry in return_obj.audit_log
            ]
        }
    
    def _from_document(self, document: Dict[str, Any]) -> Return:
        """Convert MongoDB document to Return entity"""
        # Convert line items
        line_items = []
        for item_data in document.get("line_items", []):
            line_item = ReturnLineItem(
                line_item_id=item_data["line_item_id"],
                sku=item_data["sku"],
                title=item_data["title"],
                variant_title=item_data.get("variant_title"),
                quantity=item_data["quantity"],
                unit_price=Money(
                    item_data["unit_price"]["amount"],
                    item_data["unit_price"]["currency"]
                ),
                reason=ReturnReason(
                    item_data["reason"]["code"],
                    item_data["reason"]["description"]
                ),
                condition=item_data["condition"],
                photos=item_data.get("photos", []),
                notes=item_data.get("notes", "")
            )
            line_items.append(line_item)
        
        # Convert policy snapshot
        policy_data = document["policy_snapshot"]
        policy_snapshot = PolicySnapshot(
            return_window_days=policy_data["return_window_days"],
            restock_fee_enabled=policy_data["restock_fee_enabled"],
            restock_fee_percent=policy_data["restock_fee_percent"],
            shipping_fee_enabled=policy_data["shipping_fee_enabled"],
            shipping_fee_amount=policy_data["shipping_fee_amount"],
            photo_required_reasons=policy_data["photo_required_reasons"],
            excluded_categories=policy_data["excluded_categories"],
            excluded_tags=policy_data["excluded_tags"],
            auto_approve_threshold=policy_data["auto_approve_threshold"],
            eligible_outcomes=policy_data["eligible_outcomes"],
            eligible_methods=policy_data["eligible_methods"],
            created_at=policy_data["created_at"]
        )
        
        # Convert audit log
        audit_log = []
        for entry_data in document.get("audit_log", []):
            audit_entry = AuditEntry(
                timestamp=entry_data["timestamp"],
                actor=entry_data["actor"],
                action=entry_data["action"],
                details=entry_data["details"],
                correlation_id=entry_data.get("correlation_id")
            )
            audit_log.append(audit_entry)
        
        # Create return entity
        return_obj = Return(
            id=ReturnId(document["id"]),
            tenant_id=TenantId(document["tenant_id"]),
            order_id=OrderId(document["order_id"]),
            channel=ReturnChannel(document["channel"]),
            status=ReturnStatus(document["status"]),
            customer_email=Email(document["customer_email"]),
            line_items=line_items,
            return_method=ReturnMethod(document["return_method"]),
            policy_snapshot=policy_snapshot,
            estimated_refund=Money(
                document["estimated_refund"]["amount"],
                document["estimated_refund"]["currency"]
            ),
            final_refund=Money(
                document["final_refund"]["amount"],
                document["final_refund"]["currency"]
            ) if document.get("final_refund") else None,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            submitted_by=document.get("submitted_by"),
            processed_by=document.get("processed_by"),
            audit_log=audit_log
        )
        
        return return_obj