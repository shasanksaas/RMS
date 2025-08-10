"""
Unified Return Repository
Handles data persistence for unified returns
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..config.database import db


class UnifiedReturnRepository:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.collection = db.return_requests

    async def create_return(self, return_data: Dict[str, Any]) -> str:
        """Create a new return request"""
        return_id = str(uuid.uuid4())
        
        return_record = {
            'id': return_id,
            'tenant_id': self.tenant_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **return_data
        }
        
        await self.collection.insert_one(return_record)
        return return_id

    async def get_return_by_id(self, return_id: str) -> Optional[Dict[str, Any]]:
        """Get return by ID"""
        return await self.collection.find_one({
            'id': return_id,
            'tenant_id': self.tenant_id
        })

    async def update_return(self, return_id: str, updates: Dict[str, Any]) -> bool:
        """Update return request"""
        updates['updated_at'] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {'id': return_id, 'tenant_id': self.tenant_id},
            {'$set': updates}
        )
        
        return result.modified_count > 0

    async def get_returns_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all returns for a specific order"""
        returns = await self.collection.find({
            'order_id': order_id,
            'tenant_id': self.tenant_id
        }).to_list(100)
        
        return returns

    async def get_returns_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get returns by status"""
        returns = await self.collection.find({
            'status': status,
            'tenant_id': self.tenant_id
        }).to_list(100)
        
        return returns

    async def search_returns(self, filters: Dict[str, Any], skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Search returns with pagination"""
        query = {'tenant_id': self.tenant_id}
        
        # Add filters
        if 'status' in filters and filters['status']:
            query['status'] = filters['status']
        
        if 'customer_email' in filters and filters['customer_email']:
            query['customer_email'] = {'$regex': filters['customer_email'], '$options': 'i'}
        
        if 'order_number' in filters and filters['order_number']:
            query['order_number'] = {'$regex': filters['order_number'], '$options': 'i'}
        
        if 'date_from' in filters and filters['date_from']:
            query['created_at'] = {'$gte': filters['date_from']}
        
        if 'date_to' in filters and filters['date_to']:
            if 'created_at' in query:
                query['created_at']['$lte'] = filters['date_to']
            else:
                query['created_at'] = {'$lte': filters['date_to']}
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get paginated results
        returns = await self.collection.find(query)\
                                     .sort('created_at', -1)\
                                     .skip(skip)\
                                     .limit(limit)\
                                     .to_list(limit)
        
        return {
            'returns': returns,
            'total': total,
            'page': (skip // limit) + 1,
            'per_page': limit,
            'pages': (total + limit - 1) // limit
        }

    async def get_return_statistics(self) -> Dict[str, Any]:
        """Get return statistics for the tenant"""
        pipeline = [
            {'$match': {'tenant_id': self.tenant_id}},
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1},
                'total_refund': {'$sum': '$estimated_refund'}
            }}
        ]
        
        stats = await self.collection.aggregate(pipeline).to_list(100)
        
        # Format statistics
        statistics = {
            'total_returns': 0,
            'total_refund_amount': 0.0,
            'by_status': {}
        }
        
        for stat in stats:
            status = stat['_id']
            count = stat['count']
            refund_amount = stat['total_refund']
            
            statistics['total_returns'] += count
            statistics['total_refund_amount'] += refund_amount
            statistics['by_status'][status] = {
                'count': count,
                'refund_amount': refund_amount
            }
        
        return statistics

    async def get_customer_return_history(self, customer_email: str) -> List[Dict[str, Any]]:
        """Get return history for a customer"""
        returns = await self.collection.find({
            'customer_email': customer_email,
            'tenant_id': self.tenant_id
        }).sort('created_at', -1).to_list(100)
        
        return returns

    async def delete_return(self, return_id: str) -> bool:
        """Delete a return request (soft delete by marking as cancelled)"""
        result = await self.collection.update_one(
            {'id': return_id, 'tenant_id': self.tenant_id},
            {'$set': {
                'status': 'cancelled',
                'updated_at': datetime.utcnow(),
                'cancelled_at': datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0