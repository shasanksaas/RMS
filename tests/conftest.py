"""
Test configuration and fixtures
"""
import pytest
import pytest_asyncio
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

# Test database configuration
TEST_MONGO_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "test_returns_management"

@pytest_asyncio.fixture
async def test_db():
    """Create test database connection"""
    client = AsyncIOMotorClient(TEST_MONGO_URL)
    db = client[TEST_DB_NAME]
    
    yield db
    
    # Cleanup - drop test database
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing"""
    return {
        "name": "Test Tenant",
        "domain": "test-tenant.com",
        "shopify_store_url": "test-tenant.myshopify.com"
    }

@pytest.fixture  
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "Test Product",
        "description": "A test product",
        "price": 49.99,
        "category": "Electronics",
        "sku": "TEST-001"
    }

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
        "order_number": "ORD-TEST-001",
        "items": [
            {
                "product_id": "test-product-1",
                "product_name": "Test Product",
                "quantity": 2,
                "price": 49.99,
                "sku": "TEST-001"
            }
        ],
        "total_amount": 99.98,
        "order_date": datetime.utcnow()
    }

@pytest.fixture
def sample_return_data():
    """Sample return request data for testing"""
    return {
        "order_id": "test-order-1",
        "reason": "defective",
        "items_to_return": [
            {
                "product_id": "test-product-1",
                "product_name": "Test Product", 
                "quantity": 1,
                "price": 49.99,
                "sku": "TEST-001"
            }
        ],
        "notes": "Product arrived damaged"
    }

@pytest.fixture
def sample_rule_data():
    """Sample return rule data for testing"""
    return {
        "name": "Test Auto-Approve Rule",
        "description": "Auto-approve defective items for testing",
        "conditions": {
            "auto_approve_reasons": ["defective", "damaged_in_shipping"],
            "max_days_since_order": 30
        },
        "actions": {
            "auto_approve": True,
            "generate_label": True
        },
        "priority": 1
    }