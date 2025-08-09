"""
Rules service - handles return rules engine business logic
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ..models import ReturnRule, ReturnRuleCreate, ReturnRequest, Order
from ..config.database import db, COLLECTIONS


class RulesService:
    """Service class for return rules operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self.db = database
        self.collection = self.db[COLLECTIONS['return_rules']]
    
    async def create_rule(self, tenant_id: str, rule_data: ReturnRuleCreate) -> ReturnRule:
        """Create a new return rule"""
        rule = ReturnRule(**rule_data.dict(), tenant_id=tenant_id)
        await self.collection.insert_one(rule.dict())
        return rule
    
    async def get_tenant_rules(self, tenant_id: str) -> List[ReturnRule]:
        """Get all active rules for a tenant, sorted by priority"""
        rules = await self.collection.find({
            "tenant_id": tenant_id, 
            "is_active": True
        }).sort("priority", 1).to_list(100)
        
        return [ReturnRule(**rule) for rule in rules]
    
    async def get_rule_by_id(self, rule_id: str, tenant_id: str) -> Optional[ReturnRule]:
        """Get specific rule by ID"""
        rule_data = await self.collection.find_one({
            "id": rule_id, 
            "tenant_id": tenant_id, 
            "is_active": True
        })
        if rule_data:
            return ReturnRule(**rule_data)
        return None
    
    async def apply_rules_to_return(self, tenant_id: str, return_request: ReturnRequest, order: Order) -> ReturnRequest:
        """Apply rules engine to a return request"""
        rules = await self.get_tenant_rules(tenant_id)
        
        for rule in rules:
            if await self._evaluate_rule(rule, return_request, order):
                # Apply rule actions
                return_request = self._apply_rule_actions(rule, return_request)
                break  # Apply first matching rule only
        
        return return_request
    
    async def _evaluate_rule(self, rule: ReturnRule, return_request: ReturnRequest, order: Order) -> bool:
        """Evaluate if a rule matches the return request"""
        conditions = rule.conditions
        
        # Check return window
        if "max_days_since_order" in conditions:
            days_since_order = (datetime.utcnow() - order.order_date).days
            if days_since_order > conditions["max_days_since_order"]:
                return_request.status = "denied"
                return_request.notes = f"Return window expired ({days_since_order} days > {conditions['max_days_since_order']} days)"
                return True
        
        # Check auto-approve reasons
        if "auto_approve_reasons" in conditions:
            if return_request.reason in conditions["auto_approve_reasons"]:
                return_request.status = "approved"
                return_request.notes = "Auto-approved based on return reason"
                return True
        
        # Check manual review reasons
        if "require_manual_review_reasons" in conditions:
            if return_request.reason in conditions["require_manual_review_reasons"]:
                return_request.status = "requested"
                return_request.notes = "Requires manual review"
                return True
        
        return False
    
    def _apply_rule_actions(self, rule: ReturnRule, return_request: ReturnRequest) -> ReturnRequest:
        """Apply rule actions to return request"""
        actions = rule.actions
        
        # Auto-approve action
        if actions.get("auto_approve", False):
            return_request.status = "approved"
        
        # Generate label action (placeholder for future implementation)
        if actions.get("generate_label", False):
            return_request.notes = f"{return_request.notes or ''} [Label generation requested]"
        
        # Send notification action (placeholder for future implementation)  
        if actions.get("send_notification", False):
            return_request.notes = f"{return_request.notes or ''} [Notification sent]"
        
        return return_request
    
    async def update_rule(self, rule_id: str, tenant_id: str, update_data: dict) -> Optional[ReturnRule]:
        """Update a return rule"""
        await self.collection.update_one(
            {"id": rule_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        
        return await self.get_rule_by_id(rule_id, tenant_id)
    
    async def deactivate_rule(self, rule_id: str, tenant_id: str) -> bool:
        """Deactivate a rule"""
        result = await self.collection.update_one(
            {"id": rule_id, "tenant_id": tenant_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0