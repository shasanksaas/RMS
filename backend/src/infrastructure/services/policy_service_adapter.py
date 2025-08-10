"""
Policy Service Adapter
Concrete implementation for policy management
"""

from datetime import datetime
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...domain.value_objects import TenantId, PolicySnapshot
from ...domain.ports.services import PolicyService as PolicyServicePort


class PolicyServiceAdapter(PolicyServicePort):
    """Adapter for policy management using MongoDB"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.tenant_settings
    
    async def get_current_policy(self, tenant_id: TenantId) -> PolicySnapshot:
        """Get current return policy for tenant"""
        settings = await self.collection.find_one({"tenant_id": tenant_id.value})
        
        if not settings:
            # Return default policy
            return self._get_default_policy()
        
        return self._build_policy_snapshot(settings)
    
    async def get_policy_at_date(
        self, 
        tenant_id: TenantId, 
        date: datetime
    ) -> PolicySnapshot:
        """Get policy that was active at specific date"""
        # For now, just return current policy
        # In a full implementation, this would query policy history
        return await self.get_current_policy(tenant_id)
    
    def _get_default_policy(self) -> PolicySnapshot:
        """Get default policy when tenant settings not found"""
        return PolicySnapshot(
            return_window_days=30,
            restock_fee_enabled=True,
            restock_fee_percent=Decimal('10.0'),
            shipping_fee_enabled=True,
            shipping_fee_amount=Decimal('5.99'),
            photo_required_reasons=['damaged', 'defective'],
            excluded_categories=['final_sale', 'gift_cards'],
            excluded_tags=['non_returnable'],
            auto_approve_threshold=Decimal('100.0'),
            eligible_outcomes=['refund', 'store_credit', 'exchange'],
            eligible_methods=['prepaid_label', 'qr_dropoff', 'in_store'],
            created_at=datetime.utcnow()
        )
    
    def _build_policy_snapshot(self, settings: dict) -> PolicySnapshot:
        """Build policy snapshot from tenant settings"""
        return_policy = settings.get('return_policy', {})
        
        return PolicySnapshot(
            return_window_days=return_policy.get('return_window_days', 30),
            restock_fee_enabled=return_policy.get('restock_fee_enabled', True),
            restock_fee_percent=Decimal(str(return_policy.get('restock_fee_percent', 10.0))),
            shipping_fee_enabled=return_policy.get('shipping_fee_enabled', True),
            shipping_fee_amount=Decimal(str(return_policy.get('shipping_fee_amount', 5.99))),
            photo_required_reasons=return_policy.get('photo_required_reasons', ['damaged', 'defective']),
            excluded_categories=return_policy.get('excluded_categories', ['final_sale', 'gift_cards']),
            excluded_tags=return_policy.get('excluded_tags', ['non_returnable']),
            auto_approve_threshold=Decimal(str(return_policy.get('auto_approve_threshold', 100.0))),
            eligible_outcomes=return_policy.get('eligible_outcomes', ['refund', 'store_credit', 'exchange']),
            eligible_methods=return_policy.get('eligible_methods', ['prepaid_label', 'qr_dropoff', 'in_store']),
            created_at=datetime.utcnow()
        )