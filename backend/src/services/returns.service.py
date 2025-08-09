"""
Returns service - handles return request business logic
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ..models import ReturnRequest, ReturnRequestCreate, ReturnStatusUpdate, Order
from ..config.database import db, COLLECTIONS


class ReturnsService:
    """Service class for return requests operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self.db = database
        self.collection = self.db[COLLECTIONS['return_requests']]
    
    async def create_return_request(self, tenant_id: str, return_data: ReturnRequestCreate, 
                                  customer_email: str, customer_name: str) -> ReturnRequest:
        """Create a new return request"""
        # Calculate refund amount
        refund_amount = sum(item.price * item.quantity for item in return_data.items_to_return)
        
        return_request = ReturnRequest(
            **return_data.dict(),
            tenant_id=tenant_id,
            customer_email=customer_email,
            customer_name=customer_name,
            refund_amount=refund_amount
        )
        
        await self.collection.insert_one(return_request.dict())
        return return_request
    
    async def get_tenant_returns(self, tenant_id: str, limit: int = 1000) -> List[ReturnRequest]:
        """Get all return requests for a tenant"""
        returns = await self.collection.find({
            "tenant_id": tenant_id
        }).sort("created_at", -1).limit(limit).to_list(limit)
        
        return [ReturnRequest(**ret) for ret in returns]
    
    async def get_return_by_id(self, return_id: str, tenant_id: str) -> Optional[ReturnRequest]:
        """Get specific return request by ID"""
        return_data = await self.collection.find_one({
            "id": return_id, 
            "tenant_id": tenant_id
        })
        if return_data:
            return ReturnRequest(**return_data)
        return None
    
    async def update_return_status(self, return_id: str, tenant_id: str, 
                                 status_update: ReturnStatusUpdate) -> Optional[ReturnRequest]:
        """Update return request status"""
        update_data = {
            "status": status_update.status,
            "updated_at": datetime.utcnow()
        }
        
        if status_update.notes:
            update_data["notes"] = status_update.notes
        if status_update.tracking_number:
            update_data["tracking_number"] = status_update.tracking_number
        
        await self.collection.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        
        return await self.get_return_by_id(return_id, tenant_id)
    
    async def get_returns_by_status(self, tenant_id: str, status: str) -> List[ReturnRequest]:
        """Get return requests filtered by status"""
        returns = await self.collection.find({
            "tenant_id": tenant_id,
            "status": status
        }).sort("created_at", -1).to_list(1000)
        
        return [ReturnRequest(**ret) for ret in returns]
    
    async def get_customer_returns(self, tenant_id: str, customer_email: str) -> List[ReturnRequest]:
        """Get all return requests for a specific customer"""
        returns = await self.collection.find({
            "tenant_id": tenant_id,
            "customer_email": customer_email
        }).sort("created_at", -1).to_list(100)
        
        return [ReturnRequest(**ret) for ret in returns]
    
    async def search_returns(self, tenant_id: str, search_term: str) -> List[ReturnRequest]:
        """Search return requests by customer name or email"""
        returns = await self.collection.find({
            "tenant_id": tenant_id,
            "$or": [
                {"customer_name": {"$regex": search_term, "$options": "i"}},
                {"customer_email": {"$regex": search_term, "$options": "i"}},
                {"order_id": {"$regex": search_term, "$options": "i"}}
            ]
        }).sort("created_at", -1).to_list(100)
        
        return [ReturnRequest(**ret) for ret in returns]