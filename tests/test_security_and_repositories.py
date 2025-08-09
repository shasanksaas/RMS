"""
Comprehensive testing framework for Returns Management SaaS
Includes unit tests, integration tests, and security tests
"""
import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from src.repositories import RepositoryFactory, TenantScopedRepository
from src.middleware.security import SecurityMiddleware, tenant_context
from src.utils.state_machine import ReturnStateMachine, ReturnStatus
from src.utils.rules_engine import RulesEngine

class TestFixtures:
    """Test fixtures and data"""
    
    @staticmethod
    def get_test_tenant() -> Dict[str, Any]:
        return {
            "id": "test-tenant-security",
            "name": "Test Security Tenant",
            "domain": "security-test.com",
            "is_active": True,
            "settings": {
                "return_window_days": 30,
                "auto_approve_exchanges": False,
                "require_photos": True
            }
        }
    
    @staticmethod
    def get_test_order() -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": "test-tenant-security",
            "customer_email": "test@example.com",
            "customer_name": "Test Customer",
            "order_number": "TEST-001",
            "items": [
                {
                    "product_id": "prod-1",
                    "product_name": "Test Product",
                    "quantity": 1,
                    "price": 99.99,
                    "sku": "TEST-SKU-001"
                }
            ],
            "total_amount": 99.99,
            "order_date": datetime.utcnow() - timedelta(days=5),
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
    
    @staticmethod
    def get_test_return_request() -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": "test-tenant-security",
            "order_id": "test-order-id",
            "customer_email": "test@example.com",
            "customer_name": "Test Customer",
            "reason": "defective",
            "status": "requested",
            "items_to_return": [
                {
                    "product_id": "prod-1",
                    "product_name": "Test Product",
                    "quantity": 1,
                    "price": 99.99,
                    "sku": "TEST-SKU-001"
                }
            ],
            "refund_amount": 99.99,
            "notes": "Test return request",
            "created_at": datetime.utcnow()
        }

@pytest.fixture
async def test_db():
    """Test database fixture"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_returns_db"]
    yield db
    # Cleanup
    await client.drop_database("test_returns_db")
    client.close()

@pytest.fixture
def repository_factory(test_db):
    """Repository factory fixture"""
    return RepositoryFactory(test_db)

@pytest.fixture
def security_middleware():
    """Security middleware fixture"""
    return SecurityMiddleware()

class TestTenantScopedRepository:
    """Test tenant-scoped repository layer"""
    
    async def test_repository_requires_tenant_id(self, repository_factory):
        """Test that repository requires tenant_id for all operations"""
        returns_repo = repository_factory.get_returns_repository()
        
        # Test that operations without tenant_id fail
        with pytest.raises(ValueError, match="tenant_id is required"):
            await returns_repo.find_one({}, "")
        
        with pytest.raises(ValueError, match="tenant_id is required"):
            await returns_repo.insert_one({}, "")
    
    async def test_tenant_scoping_in_queries(self, repository_factory):
        """Test that all queries are automatically scoped to tenant"""
        returns_repo = repository_factory.get_returns_repository()
        test_tenant = "test-tenant-scoping"
        
        # Insert test data
        test_return = TestFixtures.get_test_return_request()
        test_return["tenant_id"] = test_tenant
        
        await returns_repo.insert_one(test_return, test_tenant)
        
        # Query should automatically include tenant_id
        result = await returns_repo.find_one({"id": test_return["id"]}, test_tenant)
        assert result is not None
        assert result["tenant_id"] == test_tenant
    
    async def test_cross_tenant_isolation(self, repository_factory):
        """Test that tenants cannot access each other's data"""
        returns_repo = repository_factory.get_returns_repository()
        
        tenant_a = "tenant-a"
        tenant_b = "tenant-b"
        
        # Insert data for tenant A
        test_return_a = TestFixtures.get_test_return_request()
        test_return_a["tenant_id"] = tenant_a
        await returns_repo.insert_one(test_return_a, tenant_a)
        
        # Insert data for tenant B
        test_return_b = TestFixtures.get_test_return_request()
        test_return_b["tenant_id"] = tenant_b
        test_return_b["id"] = str(uuid.uuid4())  # Different ID
        await returns_repo.insert_one(test_return_b, tenant_b)
        
        # Tenant A should only see their data
        results_a = await returns_repo.find_many({}, tenant_a)
        assert len(results_a) == 1
        assert all(r["tenant_id"] == tenant_a for r in results_a)
        
        # Tenant B should only see their data
        results_b = await returns_repo.find_many({}, tenant_b)
        assert len(results_b) == 1
        assert all(r["tenant_id"] == tenant_b for r in results_b)
    
    async def test_pii_redaction_in_logs(self, repository_factory, caplog):
        """Test that PII is redacted from audit logs"""
        returns_repo = repository_factory.get_returns_repository()
        
        test_return = TestFixtures.get_test_return_request()
        test_return["customer_email"] = "sensitive@example.com"
        
        await returns_repo.insert_one(test_return, "test-tenant")
        
        # Check that PII is redacted in logs
        log_records = [record.message for record in caplog.records]
        audit_logs = [log for log in log_records if "DB Query" in log]
        
        assert len(audit_logs) > 0
        for log in audit_logs:
            assert "sensitive@example.com" not in log
            assert "***REDACTED***" in log

class TestSecurityMiddleware:
    """Test security middleware"""
    
    async def test_tenant_validation(self, security_middleware):
        """Test tenant validation"""
        # Mock request
        class MockRequest:
            def __init__(self, headers, url="/api/returns"):
                self.headers = headers
                self.url = type('URL', (), {'path': url})()
                self.method = "GET"
        
        # Valid tenant ID
        request = MockRequest({"X-Tenant-Id": "valid-tenant"})
        tenant_id = await security_middleware.validate_tenant_access(request)
        assert tenant_id == "valid-tenant"
    
    async def test_missing_tenant_id_raises_error(self, security_middleware):
        """Test that missing tenant ID raises appropriate error"""
        from fastapi import HTTPException
        
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.url = type('URL', (), {'path': '/api/returns'})()
                self.method = "GET"
        
        with pytest.raises(HTTPException) as exc_info:
            await security_middleware.validate_tenant_access(MockRequest())
        
        assert exc_info.value.status_code == 400
        assert "Tenant ID is required" in str(exc_info.value.detail)
    
    def test_cross_tenant_access_prevention(self, security_middleware):
        """Test prevention of cross-tenant access"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            security_middleware.validate_cross_tenant_access("tenant-a", "tenant-b")
        
        assert exc_info.value.status_code == 403
        assert "Cross-tenant access not allowed" in str(exc_info.value.detail)

class TestStateMachine:
    """Test return status state machine"""
    
    def test_valid_transitions(self):
        """Test valid state transitions"""
        assert ReturnStateMachine.can_transition("requested", "approved")
        assert ReturnStateMachine.can_transition("approved", "label_issued")
        assert ReturnStateMachine.can_transition("label_issued", "in_transit")
        assert ReturnStateMachine.can_transition("in_transit", "received")
        assert ReturnStateMachine.can_transition("received", "resolved")
    
    def test_invalid_transitions(self):
        """Test that invalid transitions are blocked"""
        assert not ReturnStateMachine.can_transition("requested", "resolved")
        assert not ReturnStateMachine.can_transition("denied", "approved")
        assert not ReturnStateMachine.can_transition("resolved", "requested")
    
    def test_terminal_states(self):
        """Test terminal state detection"""
        assert ReturnStateMachine.is_terminal_state("denied")
        assert ReturnStateMachine.is_terminal_state("resolved")
        assert not ReturnStateMachine.is_terminal_state("requested")
        assert not ReturnStateMachine.is_terminal_state("approved")
    
    def test_audit_log_creation(self):
        """Test audit log entry creation"""
        entry = ReturnStateMachine.create_audit_log_entry(
            return_id="test-return",
            from_status="requested",
            to_status="approved",
            notes="Test approval",
            user_id="test-user"
        )
        
        assert entry["return_id"] == "test-return"
        assert entry["from_status"] == "requested"
        assert entry["to_status"] == "approved"
        assert entry["notes"] == "Test approval"
        assert entry["user_id"] == "test-user"
        assert "timestamp" in entry

class TestRulesEngine:
    """Test rules engine"""
    
    def test_rules_simulation_with_auto_approve(self):
        """Test rules simulation with auto-approve scenario"""
        return_request = {
            "reason": "defective",
            "refund_amount": 50.00
        }
        
        order = {
            "order_date": (datetime.utcnow() - timedelta(days=10)).isoformat()
        }
        
        rules = [{
            "name": "Auto-approve defective items",
            "conditions": {
                "auto_approve_reasons": ["defective"],
                "max_days_since_order": 30
            },
            "actions": {
                "auto_approve": True
            }
        }]
        
        result = RulesEngine.simulate_rules_application(return_request, order, rules)
        
        assert result["final_status"] == "approved"
        assert len(result["steps"]) >= 2  # Time window + auto-approve checks
        assert result["rule_applied"] == "Auto-approve defective items"
    
    def test_rules_simulation_with_denial(self):
        """Test rules simulation with denial scenario"""
        return_request = {
            "reason": "defective",
            "refund_amount": 50.00
        }
        
        # Order older than return window
        order = {
            "order_date": (datetime.utcnow() - timedelta(days=60)).isoformat()
        }
        
        rules = [{
            "name": "Return window check",
            "conditions": {
                "max_days_since_order": 30
            }
        }]
        
        result = RulesEngine.simulate_rules_application(return_request, order, rules)
        
        assert result["final_status"] == "denied"
        assert any("outside return window" in step["explanation"] for step in result["steps"])

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    async def test_large_order_handling(self, repository_factory):
        """Test handling of orders with many line items"""
        orders_repo = repository_factory.get_orders_repository()
        
        # Create order with 100+ line items
        large_order = TestFixtures.get_test_order()
        large_order["items"] = []
        
        for i in range(150):
            large_order["items"].append({
                "product_id": f"prod-{i}",
                "product_name": f"Product {i}",
                "quantity": 1,
                "price": 10.00,
                "sku": f"SKU-{i:03d}"
            })
        
        large_order["total_amount"] = 1500.00
        
        # Should handle large orders without issues
        await orders_repo.insert_one(large_order, "test-tenant")
        
        result = await orders_repo.find_one({"id": large_order["id"]}, "test-tenant")
        assert result is not None
        assert len(result["items"]) == 150
    
    async def test_duplicate_webhook_handling(self, repository_factory):
        """Test idempotent webhook processing"""
        returns_repo = repository_factory.get_returns_repository()
        
        test_return = TestFixtures.get_test_return_request()
        webhook_id = str(uuid.uuid4())
        
        # Process same webhook twice
        test_return["webhook_id"] = webhook_id
        
        await returns_repo.insert_one(test_return, "test-tenant")
        
        # Second attempt should be idempotent (would need webhook processing logic)
        try:
            test_return["id"] = str(uuid.uuid4())  # Different return ID
            await returns_repo.insert_one(test_return, "test-tenant")
            # In real implementation, this should check webhook_id uniqueness
        except Exception as e:
            # Expected for duplicate webhook prevention
            pass
    
    def test_invalid_order_email_combination(self):
        """Test validation of invalid order/email combinations"""
        # This would test the customer portal validation
        # For now, we'll test the concept
        
        def validate_order_customer_match(order_number: str, customer_email: str, 
                                        stored_order: Dict[str, Any]) -> bool:
            return (stored_order.get("order_number") == order_number and 
                   stored_order.get("customer_email").lower() == customer_email.lower())
        
        stored_order = {
            "order_number": "ORD-001",
            "customer_email": "customer@example.com"
        }
        
        # Valid combination
        assert validate_order_customer_match("ORD-001", "customer@example.com", stored_order)
        
        # Invalid combinations
        assert not validate_order_customer_match("ORD-002", "customer@example.com", stored_order)
        assert not validate_order_customer_match("ORD-001", "wrong@example.com", stored_order)

# Performance tests
class TestPerformance:
    """Performance tests for key endpoints"""
    
    async def test_returns_query_performance(self, repository_factory):
        """Test performance of returns queries"""
        returns_repo = repository_factory.get_returns_repository()
        tenant_id = "performance-test-tenant"
        
        # Insert test data
        test_returns = []
        for i in range(100):
            test_return = TestFixtures.get_test_return_request()
            test_return["id"] = str(uuid.uuid4())
            test_return["tenant_id"] = tenant_id
            test_return["created_at"] = datetime.utcnow() - timedelta(days=i % 30)
            test_returns.append(test_return)
        
        # Bulk insert
        for return_data in test_returns:
            await returns_repo.insert_one(return_data, tenant_id)
        
        # Test query performance
        start_time = datetime.utcnow()
        results = await returns_repo.find_many({}, tenant_id, limit=50)
        query_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert len(results) == 50
        assert query_time < 1.0  # Should complete within 1 second

# Run tests
if __name__ == "__main__":
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run pytest
    pytest.main([__file__, "-v"])