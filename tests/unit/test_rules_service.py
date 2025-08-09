"""
Unit tests for RulesService
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from backend.src.services.rules_service import RulesService
from backend.src.models import ReturnRuleCreate, ReturnRequest, Order, OrderItem


class TestRulesService:
    """Test suite for RulesService"""
    
    @pytest_asyncio.fixture
    async def rules_service(self, test_db):
        """Create RulesService instance with test database"""
        return RulesService(test_db)
    
    @pytest_asyncio.fixture
    async def created_rule(self, rules_service, sample_rule_data):
        """Create a test rule"""
        tenant_id = "test-tenant-123"
        rule_create = ReturnRuleCreate(**sample_rule_data)
        return await rules_service.create_rule(tenant_id, rule_create)
    
    async def test_create_rule_success(self, rules_service, sample_rule_data):
        """Test successful rule creation"""
        tenant_id = "test-tenant-123"
        rule_create = ReturnRuleCreate(**sample_rule_data)
        rule = await rules_service.create_rule(tenant_id, rule_create)
        
        assert rule.id is not None
        assert rule.tenant_id == tenant_id
        assert rule.name == sample_rule_data["name"]
        assert rule.conditions == sample_rule_data["conditions"]
        assert rule.actions == sample_rule_data["actions"]
        assert rule.is_active is True
    
    async def test_get_tenant_rules(self, rules_service, created_rule):
        """Test getting rules for a tenant"""
        rules = await rules_service.get_tenant_rules(created_rule.tenant_id)
        
        assert len(rules) >= 1
        assert any(r.id == created_rule.id for r in rules)
        # Rules should be sorted by priority
        priorities = [r.priority for r in rules]
        assert priorities == sorted(priorities)
    
    async def test_apply_rules_auto_approve(self, rules_service, created_rule):
        """Test rule application for auto-approval"""
        # Create test return request and order
        order = Order(
            id="test-order",
            tenant_id=created_rule.tenant_id,
            customer_email="test@example.com",
            customer_name="Test Customer",
            order_number="ORD-001",
            items=[OrderItem(product_id="1", product_name="Test", quantity=1, price=50.0, sku="TST-001")],
            total_amount=50.0,
            order_date=datetime.utcnow() - timedelta(days=5)  # 5 days ago
        )
        
        return_request = ReturnRequest(
            id="test-return",
            tenant_id=created_rule.tenant_id,
            order_id=order.id,
            customer_email=order.customer_email,
            customer_name=order.customer_name,
            reason="defective",  # This should trigger auto-approval
            items_to_return=order.items,
            refund_amount=50.0
        )
        
        # Apply rules
        updated_return = await rules_service.apply_rules_to_return(
            created_rule.tenant_id, return_request, order
        )
        
        assert updated_return.status == "approved"
        assert "Auto-approved" in updated_return.notes
    
    async def test_apply_rules_expired_window(self, rules_service):
        """Test rule application for expired return window"""
        # Create rule with 30-day window
        tenant_id = "test-tenant-expired"
        rule_data = {
            "name": "Expired Window Test",
            "description": "Test expired returns",
            "conditions": {"max_days_since_order": 30},
            "actions": {},
            "priority": 1
        }
        rule_create = ReturnRuleCreate(**rule_data)
        await rules_service.create_rule(tenant_id, rule_create)
        
        # Create order from 45 days ago (expired)
        order = Order(
            id="test-order-expired",
            tenant_id=tenant_id,
            customer_email="test@example.com",
            customer_name="Test Customer", 
            order_number="ORD-002",
            items=[OrderItem(product_id="1", product_name="Test", quantity=1, price=50.0, sku="TST-001")],
            total_amount=50.0,
            order_date=datetime.utcnow() - timedelta(days=45)  # 45 days ago
        )
        
        return_request = ReturnRequest(
            id="test-return-expired",
            tenant_id=tenant_id,
            order_id=order.id,
            customer_email=order.customer_email,
            customer_name=order.customer_name,
            reason="defective",
            items_to_return=order.items,
            refund_amount=50.0
        )
        
        # Apply rules
        updated_return = await rules_service.apply_rules_to_return(
            tenant_id, return_request, order
        )
        
        assert updated_return.status == "denied"
        assert "expired" in updated_return.notes.lower()
    
    async def test_get_rule_by_id(self, rules_service, created_rule):
        """Test getting specific rule by ID"""
        rule = await rules_service.get_rule_by_id(created_rule.id, created_rule.tenant_id)
        
        assert rule is not None
        assert rule.id == created_rule.id
        assert rule.name == created_rule.name
    
    async def test_deactivate_rule(self, rules_service, created_rule):
        """Test rule deactivation"""
        success = await rules_service.deactivate_rule(created_rule.id, created_rule.tenant_id)
        assert success is True
        
        # Verify rule is no longer returned in active rules
        rules = await rules_service.get_tenant_rules(created_rule.tenant_id)
        assert not any(r.id == created_rule.id for r in rules)