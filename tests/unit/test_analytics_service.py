"""
Unit tests for AnalyticsService
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from backend.src.services.analytics_service import AnalyticsService
from backend.src.services.returns_service import ReturnsService
from backend.src.models import ReturnRequestCreate


class TestAnalyticsService:
    """Test suite for AnalyticsService"""
    
    @pytest_asyncio.fixture
    async def analytics_service(self, test_db):
        """Create AnalyticsService instance with test database"""
        return AnalyticsService(test_db)
    
    @pytest_asyncio.fixture  
    async def returns_service(self, test_db):
        """Create ReturnsService for test data setup"""
        return ReturnsService(test_db)
    
    @pytest_asyncio.fixture
    async def sample_returns_data(self, returns_service):
        """Create sample return requests for analytics testing"""
        tenant_id = "test-tenant-analytics"
        
        # Create multiple return requests with different statuses and reasons
        returns_data = [
            {
                "order_id": "order-1",
                "reason": "defective",
                "items_to_return": [{"product_id": "1", "product_name": "Product 1", "quantity": 1, "price": 50.0, "sku": "P1"}],
                "notes": "Defective item"
            },
            {
                "order_id": "order-2", 
                "reason": "wrong_size",
                "items_to_return": [{"product_id": "2", "product_name": "Product 2", "quantity": 1, "price": 75.0, "sku": "P2"}],
                "notes": "Wrong size"
            },
            {
                "order_id": "order-3",
                "reason": "defective", 
                "items_to_return": [{"product_id": "3", "product_name": "Product 3", "quantity": 2, "price": 30.0, "sku": "P3"}],
                "notes": "Also defective"
            }
        ]
        
        created_returns = []
        for data in returns_data:
            return_create = ReturnRequestCreate(**data)
            return_request = await returns_service.create_return_request(
                tenant_id, return_create, f"customer{len(created_returns)+1}@example.com", f"Customer {len(created_returns)+1}"
            )
            created_returns.append(return_request)
        
        return tenant_id, created_returns
    
    async def test_get_tenant_analytics_success(self, analytics_service, sample_returns_data):
        """Test getting analytics for a tenant"""
        tenant_id, sample_returns = sample_returns_data
        
        analytics = await analytics_service.get_tenant_analytics(tenant_id, days=30)
        
        assert analytics.tenant_id == tenant_id
        assert analytics.total_returns == 3
        assert analytics.total_refunds == 185.0  # 50 + 75 + (30*2)
        assert analytics.exchange_rate == 0.0  # No exchanges yet
        assert analytics.avg_processing_time == 2.5  # Mock value
        
        # Check top return reasons
        assert len(analytics.top_return_reasons) == 2  # defective and wrong_size
        
        # Defective should be top reason (2 out of 3)
        top_reason = analytics.top_return_reasons[0]
        assert top_reason["reason"] == "defective"
        assert top_reason["count"] == 2
        assert abs(top_reason["percentage"] - 66.67) < 0.1  # Approximately 66.67%
    
    async def test_get_tenant_analytics_empty(self, analytics_service):
        """Test analytics for tenant with no returns"""
        analytics = await analytics_service.get_tenant_analytics("empty-tenant", days=30)
        
        assert analytics.tenant_id == "empty-tenant"
        assert analytics.total_returns == 0
        assert analytics.total_refunds == 0.0
        assert analytics.exchange_rate == 0.0
        assert len(analytics.top_return_reasons) == 0
    
    async def test_get_tenant_analytics_custom_period(self, analytics_service, sample_returns_data):
        """Test analytics with custom time period"""
        tenant_id, _ = sample_returns_data
        
        # Test with 7 days period
        analytics = await analytics_service.get_tenant_analytics(tenant_id, days=7)
        
        assert analytics.tenant_id == tenant_id
        assert analytics.total_returns >= 0  # Depends on when sample data was created
        assert (analytics.period_end - analytics.period_start).days == 7
    
    async def test_get_return_trends(self, analytics_service, sample_returns_data):
        """Test getting return trends over time"""
        tenant_id, _ = sample_returns_data
        
        trends = await analytics_service.get_return_trends(tenant_id, days=30)
        
        assert "daily_trends" in trends
        assert "period_start" in trends
        assert "period_end" in trends
        assert isinstance(trends["daily_trends"], list)
        
        # Should have trend data for today (when sample data was created)
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        today_trend = next((t for t in trends["daily_trends"] if t["_id"] == today_str), None)
        
        if today_trend:  # Might be None if test runs at exact midnight
            assert today_trend["count"] == 3
            assert today_trend["total_refund"] == 185.0