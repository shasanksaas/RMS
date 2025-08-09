"""
Unit tests for TenantService
"""
import pytest
import pytest_asyncio
from datetime import datetime

from backend.src.services.tenant_service import TenantService
from backend.src.models import TenantCreate, TenantUpdate, TenantSettings


class TestTenantService:
    """Test suite for TenantService"""
    
    @pytest_asyncio.fixture
    async def tenant_service(self, test_db):
        """Create TenantService instance with test database"""
        return TenantService(test_db)
    
    @pytest_asyncio.fixture
    async def created_tenant(self, tenant_service, sample_tenant_data):
        """Create a test tenant"""
        tenant_create = TenantCreate(**sample_tenant_data)
        return await tenant_service.create_tenant(tenant_create)
    
    async def test_create_tenant_success(self, tenant_service, sample_tenant_data):
        """Test successful tenant creation"""
        tenant_create = TenantCreate(**sample_tenant_data)
        tenant = await tenant_service.create_tenant(tenant_create)
        
        assert tenant.id is not None
        assert tenant.name == sample_tenant_data["name"]
        assert tenant.domain == sample_tenant_data["domain"]
        assert tenant.is_active is True
        assert tenant.plan == "trial"
        assert isinstance(tenant.settings, dict)
        assert tenant.settings["return_window_days"] == 30
    
    async def test_get_tenant_by_id_success(self, tenant_service, created_tenant):
        """Test getting tenant by ID"""
        retrieved_tenant = await tenant_service.get_tenant_by_id(created_tenant.id)
        
        assert retrieved_tenant is not None
        assert retrieved_tenant.id == created_tenant.id
        assert retrieved_tenant.name == created_tenant.name
    
    async def test_get_tenant_by_id_not_found(self, tenant_service):
        """Test getting non-existent tenant"""
        tenant = await tenant_service.get_tenant_by_id("non-existent-id")
        assert tenant is None
    
    async def test_get_all_tenants(self, tenant_service, created_tenant):
        """Test getting all tenants"""
        tenants = await tenant_service.get_all_tenants()
        
        assert len(tenants) >= 1
        assert any(t.id == created_tenant.id for t in tenants)
    
    async def test_update_tenant_success(self, tenant_service, created_tenant):
        """Test tenant update"""
        update_data = TenantUpdate(name="Updated Tenant Name")
        updated_tenant = await tenant_service.update_tenant(created_tenant.id, update_data)
        
        assert updated_tenant is not None
        assert updated_tenant.name == "Updated Tenant Name"
        assert updated_tenant.id == created_tenant.id
    
    async def test_update_tenant_settings(self, tenant_service, created_tenant):
        """Test tenant settings update"""
        new_settings = TenantSettings(
            return_window_days=45,
            brand_color="#ff0000",
            custom_message="Custom return message"
        )
        updated_tenant = await tenant_service.update_tenant_settings(created_tenant.id, new_settings)
        
        assert updated_tenant is not None
        assert updated_tenant.settings["return_window_days"] == 45
        assert updated_tenant.settings["brand_color"] == "#ff0000"
        assert updated_tenant.settings["custom_message"] == "Custom return message"
    
    async def test_verify_tenant_exists(self, tenant_service, created_tenant):
        """Test tenant existence verification"""
        exists = await tenant_service.verify_tenant_exists(created_tenant.id)
        assert exists is True
        
        not_exists = await tenant_service.verify_tenant_exists("non-existent-id")
        assert not_exists is False
    
    async def test_deactivate_tenant(self, tenant_service, created_tenant):
        """Test tenant deactivation"""
        success = await tenant_service.deactivate_tenant(created_tenant.id)
        assert success is True
        
        # Verify tenant is no longer active
        tenant = await tenant_service.get_tenant_by_id(created_tenant.id)
        assert tenant is None  # Should not find inactive tenant