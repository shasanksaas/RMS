"""
Unit tests for ReturnsService
"""
import pytest
import pytest_asyncio
from datetime import datetime

from backend.src.services.returns_service import ReturnsService
from backend.src.models import ReturnRequestCreate, ReturnStatusUpdate


class TestReturnsService:
    """Test suite for ReturnsService"""
    
    @pytest_asyncio.fixture
    async def returns_service(self, test_db):
        """Create ReturnsService instance with test database"""
        return ReturnsService(test_db)
    
    @pytest_asyncio.fixture
    async def created_return(self, returns_service, sample_return_data):
        """Create a test return request"""
        tenant_id = "test-tenant-123"
        return_create = ReturnRequestCreate(**sample_return_data)
        return await returns_service.create_return_request(
            tenant_id, return_create, "test@example.com", "Test Customer"
        )
    
    async def test_create_return_request_success(self, returns_service, sample_return_data):
        """Test successful return request creation"""
        tenant_id = "test-tenant-123"
        return_create = ReturnRequestCreate(**sample_return_data)
        return_request = await returns_service.create_return_request(
            tenant_id, return_create, "test@example.com", "Test Customer"
        )
        
        assert return_request.id is not None
        assert return_request.tenant_id == tenant_id
        assert return_request.order_id == sample_return_data["order_id"]
        assert return_request.reason == sample_return_data["reason"]
        assert return_request.customer_email == "test@example.com"
        assert return_request.customer_name == "Test Customer"
        assert return_request.refund_amount == 49.99  # From sample data
        assert return_request.status == "requested"
    
    async def test_get_tenant_returns(self, returns_service, created_return):
        """Test getting returns for a tenant"""
        returns = await returns_service.get_tenant_returns(created_return.tenant_id)
        
        assert len(returns) >= 1
        assert any(r.id == created_return.id for r in returns)
    
    async def test_get_return_by_id_success(self, returns_service, created_return):
        """Test getting return by ID"""
        return_request = await returns_service.get_return_by_id(
            created_return.id, created_return.tenant_id
        )
        
        assert return_request is not None
        assert return_request.id == created_return.id
        assert return_request.tenant_id == created_return.tenant_id
    
    async def test_get_return_by_id_not_found(self, returns_service):
        """Test getting non-existent return"""
        return_request = await returns_service.get_return_by_id("non-existent", "test-tenant")
        assert return_request is None
    
    async def test_update_return_status(self, returns_service, created_return):
        """Test updating return status"""
        status_update = ReturnStatusUpdate(
            status="approved",
            notes="Approved by admin",
            tracking_number="TRK123456"
        )
        
        updated_return = await returns_service.update_return_status(
            created_return.id, created_return.tenant_id, status_update
        )
        
        assert updated_return is not None
        assert updated_return.status == "approved"
        assert updated_return.notes == "Approved by admin"
        assert updated_return.tracking_number == "TRK123456"
        assert updated_return.updated_at > updated_return.created_at
    
    async def test_get_returns_by_status(self, returns_service, created_return):
        """Test filtering returns by status"""
        # Update return status first
        status_update = ReturnStatusUpdate(status="approved")
        await returns_service.update_return_status(
            created_return.id, created_return.tenant_id, status_update
        )
        
        # Get approved returns
        approved_returns = await returns_service.get_returns_by_status(
            created_return.tenant_id, "approved"
        )
        
        assert len(approved_returns) >= 1
        assert all(r.status == "approved" for r in approved_returns)
        assert any(r.id == created_return.id for r in approved_returns)
    
    async def test_get_customer_returns(self, returns_service, created_return):
        """Test getting returns for specific customer"""
        customer_returns = await returns_service.get_customer_returns(
            created_return.tenant_id, created_return.customer_email
        )
        
        assert len(customer_returns) >= 1
        assert any(r.id == created_return.id for r in customer_returns)
        assert all(r.customer_email == created_return.customer_email for r in customer_returns)
    
    async def test_search_returns(self, returns_service, created_return):
        """Test searching returns by customer info"""
        # Search by customer name
        name_results = await returns_service.search_returns(
            created_return.tenant_id, "Test Customer"
        )
        
        assert len(name_results) >= 1
        assert any(r.id == created_return.id for r in name_results)
        
        # Search by email
        email_results = await returns_service.search_returns(
            created_return.tenant_id, "test@example.com"
        )
        
        assert len(email_results) >= 1
        assert any(r.id == created_return.id for r in email_results)