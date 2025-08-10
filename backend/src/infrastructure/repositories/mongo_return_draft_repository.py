"""
MongoDB implementation of Return Draft Repository
Adapter for persistence using MongoDB
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...domain.entities.return_entity import ReturnDraft, ReturnChannel
from ...domain.value_objects import TenantId, Email
from ...domain.ports.repositories import ReturnDraftRepository


class MongoReturnDraftRepository(ReturnDraftRepository):
    """MongoDB implementation of Return Draft Repository"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.return_drafts
    
    async def save(self, draft: ReturnDraft) -> None:
        """Save or update a return draft"""
        document = {
            "id": draft.id,
            "tenant_id": draft.tenant_id.value,
            "order_number": draft.order_number,
            "customer_email": draft.customer_email.value,
            "channel": draft.channel.value,
            "status": draft.status,
            "items": draft.items,
            "photos": draft.photos,
            "customer_note": draft.customer_note,
            "submitted_at": draft.submitted_at,
            "reviewed_at": draft.reviewed_at,
            "reviewed_by": draft.reviewed_by,
            "linked_order_id": draft.linked_order_id
        }
        
        await self.collection.update_one(
            {"id": draft.id, "tenant_id": draft.tenant_id.value},
            {"$set": document},
            upsert=True
        )
    
    async def get_by_id(self, draft_id: str, tenant_id: TenantId) -> Optional[ReturnDraft]:
        """Get draft by ID"""
        document = await self.collection.find_one({
            "id": draft_id,
            "tenant_id": tenant_id.value
        })
        
        if not document:
            return None
        
        return ReturnDraft(
            id=document["id"],
            tenant_id=TenantId(document["tenant_id"]),
            order_number=document["order_number"],
            customer_email=Email(document["customer_email"]),
            channel=ReturnChannel(document["channel"]),
            status=document["status"],
            items=document.get("items", []),
            photos=document.get("photos", []),
            customer_note=document.get("customer_note", ""),
            submitted_at=document["submitted_at"],
            reviewed_at=document.get("reviewed_at"),
            reviewed_by=document.get("reviewed_by"),
            linked_order_id=document.get("linked_order_id")
        )
    
    async def get_pending_for_tenant(self, tenant_id: TenantId) -> List[ReturnDraft]:
        """Get pending drafts for admin review"""
        cursor = self.collection.find({
            "tenant_id": tenant_id.value,
            "status": "pending_validation"
        }).sort("submitted_at", -1)
        
        documents = await cursor.to_list(length=None)
        
        drafts = []
        for document in documents:
            draft = ReturnDraft(
                id=document["id"],
                tenant_id=TenantId(document["tenant_id"]),
                order_number=document["order_number"],
                customer_email=Email(document["customer_email"]),
                channel=ReturnChannel(document["channel"]),
                status=document["status"],
                items=document.get("items", []),
                photos=document.get("photos", []),
                customer_note=document.get("customer_note", ""),
                submitted_at=document["submitted_at"],
                reviewed_at=document.get("reviewed_at"),
                reviewed_by=document.get("reviewed_by"),
                linked_order_id=document.get("linked_order_id")
            )
            drafts.append(draft)
        
        return drafts
    
    async def delete(self, draft_id: str, tenant_id: TenantId) -> None:
        """Delete draft after conversion to return"""
        await self.collection.delete_one({
            "id": draft_id,
            "tenant_id": tenant_id.value
        })