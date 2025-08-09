"""
Repository layer with mandatory tenant scoping for data safety
Prevents accidental cross-tenant data access
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

class TenantScopedRepository:
    """Base repository class that enforces tenant scoping on all operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name
    
    def _ensure_tenant_scope(self, query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Ensure all queries are scoped to tenant_id"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.collection_name} operations")
        
        # Clone query to avoid mutating original
        scoped_query = query.copy()
        scoped_query["tenant_id"] = tenant_id
        
        # Log query for audit (without PII)
        self._log_query_audit(scoped_query, tenant_id)
        
        return scoped_query
    
    def _log_query_audit(self, query: Dict[str, Any], tenant_id: str):
        """Log query for audit trail with PII redaction"""
        # Redact PII fields
        redacted_query = self._redact_pii(query)
        logger.info(f"DB Query - Collection: {self.collection_name}, Tenant: {tenant_id}, Query: {redacted_query}")
    
    def _redact_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from logs"""
        pii_fields = {"email", "customer_email", "customer_name", "phone", "address"}
        redacted = {}
        
        for key, value in data.items():
            if key.lower() in pii_fields:
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_pii(value)
            else:
                redacted[key] = value
                
        return redacted
    
    async def find_one(self, query: Dict[str, Any], tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find single document with tenant scoping"""
        scoped_query = self._ensure_tenant_scope(query, tenant_id)
        return await self.collection.find_one(scoped_query)
    
    async def find_many(self, query: Dict[str, Any], tenant_id: str, 
                       limit: Optional[int] = None, skip: Optional[int] = None,
                       sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents with tenant scoping"""
        scoped_query = self._ensure_tenant_scope(query, tenant_id)
        
        cursor = self.collection.find(scoped_query)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return await cursor.to_list(limit)
    
    async def count_documents(self, query: Dict[str, Any], tenant_id: str) -> int:
        """Count documents with tenant scoping"""
        scoped_query = self._ensure_tenant_scope(query, tenant_id)
        return await self.collection.count_documents(scoped_query)
    
    async def insert_one(self, document: Dict[str, Any], tenant_id: str) -> str:
        """Insert document with tenant scoping"""
        if not tenant_id:
            raise ValueError(f"tenant_id is required for {self.collection_name} insert")
        
        # Ensure tenant_id is set
        document["tenant_id"] = tenant_id
        document["created_at"] = document.get("created_at", datetime.utcnow())
        
        result = await self.collection.insert_one(document)
        
        # Log audit trail
        logger.info(f"DB Insert - Collection: {self.collection_name}, Tenant: {tenant_id}, DocId: {result.inserted_id}")
        
        return str(result.inserted_id)
    
    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], 
                        tenant_id: str, upsert: bool = False) -> bool:
        """Update single document with tenant scoping"""
        scoped_query = self._ensure_tenant_scope(query, tenant_id)
        
        # Add updated_at timestamp
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(scoped_query, update, upsert=upsert)
        
        # Log audit trail
        logger.info(f"DB Update - Collection: {self.collection_name}, Tenant: {tenant_id}, Modified: {result.modified_count}")
        
        return result.modified_count > 0
    
    async def delete_one(self, query: Dict[str, Any], tenant_id: str) -> bool:
        """Delete single document with tenant scoping"""
        scoped_query = self._ensure_tenant_scope(query, tenant_id)
        result = await self.collection.delete_one(scoped_query)
        
        # Log audit trail
        logger.info(f"DB Delete - Collection: {self.collection_name}, Tenant: {tenant_id}, Deleted: {result.deleted_count}")
        
        return result.deleted_count > 0

class ReturnsRepository(TenantScopedRepository):
    """Repository for return requests with business logic"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "return_requests")
    
    async def find_by_status(self, status: str, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Find returns by status"""
        return await self.find_many({"status": status}, tenant_id, limit=limit, 
                                   sort=[("created_at", DESCENDING)])
    
    async def find_by_customer(self, customer_email: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Find returns by customer email"""
        return await self.find_many({"customer_email": customer_email}, tenant_id,
                                   sort=[("created_at", DESCENDING)])
    
    async def get_analytics_data(self, tenant_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get returns for analytics with date filtering"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return await self.find_many(
            {"created_at": {"$gte": cutoff_date}}, 
            tenant_id,
            sort=[("created_at", DESCENDING)]
        )

class OrdersRepository(TenantScopedRepository):
    """Repository for orders"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "orders")
    
    async def find_by_order_number(self, order_number: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find order by order number"""
        return await self.find_one({"order_number": order_number}, tenant_id)
    
    async def find_by_customer_email(self, customer_email: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Find orders by customer email"""
        return await self.find_many({"customer_email": customer_email}, tenant_id,
                                   sort=[("order_date", DESCENDING)])

class TenantsRepository:
    """Special repository for tenants (not tenant-scoped since it manages tenants)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["tenants"]
    
    async def find_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find tenant by ID"""
        return await self.collection.find_one({"id": tenant_id, "is_active": True})
    
    async def update_settings(self, tenant_id: str, settings: Dict[str, Any]) -> bool:
        """Update tenant settings"""
        result = await self.collection.update_one(
            {"id": tenant_id, "is_active": True},
            {"$set": {"settings": settings, "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Tenant Settings Updated - Tenant: {tenant_id}, Modified: {result.modified_count}")
        
        return result.modified_count > 0

class AuditLogRepository(TenantScopedRepository):
    """Repository for audit logs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "audit_logs")
    
    async def log_event(self, event_type: str, resource_id: str, details: Dict[str, Any], 
                       user_id: str, tenant_id: str):
        """Log audit event"""
        audit_entry = {
            "event_type": event_type,
            "resource_id": resource_id,
            "details": self._redact_pii(details),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow()
        }
        
        await self.insert_one(audit_entry, tenant_id)

# Repository factory
class RepositoryFactory:
    """Factory to create repository instances"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def get_returns_repository(self) -> ReturnsRepository:
        return ReturnsRepository(self.db)
    
    def get_orders_repository(self) -> OrdersRepository:
        return OrdersRepository(self.db)
    
    def get_tenants_repository(self) -> TenantsRepository:
        return TenantsRepository(self.db)
    
    def get_audit_repository(self) -> AuditLogRepository:
        return AuditLogRepository(self.db)