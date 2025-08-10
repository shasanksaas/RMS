"""
Testing Controller for Shopify Integration
Development endpoints for testing webhooks and sync
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from datetime import datetime
import json

from ..services.webhook_handlers import webhook_processor
from ..services.sync_service import sync_service
from ..modules.auth.service import auth_service

router = APIRouter(prefix="/test", tags=["testing"])


@router.post("/webhook")
async def test_webhook_processing(
    topic: str = Body(..., description="Webhook topic"),
    shop_domain: str = Body(..., description="Shop domain"),
    payload: Dict[str, Any] = Body(..., description="Webhook payload")
):
    """
    Test webhook processing without HMAC verification
    Development only - simulates webhook reception
    """
    try:
        result = await webhook_processor.process_webhook(
            topic=topic,
            shop_domain=shop_domain,
            payload=payload,
            webhook_id=f"test_{datetime.utcnow().timestamp()}"
        )
        
        return {
            "status": "success",
            "test_mode": True,
            "topic": topic,
            "shop": shop_domain,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/sync/{tenant_id}")
async def test_sync(
    tenant_id: str,
    sync_type: str = Body("manual", description="Sync type: initial, manual, incremental")
):
    """
    Test sync functionality for a specific store
    """
    try:
        result = await sync_service.trigger_sync_for_store(tenant_id, sync_type)
        
        return {
            "status": "success",
            "test_mode": True,
            "tenant_id": tenant_id,
            "sync_type": sync_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync test failed: {str(e)}")


@router.get("/stores/{tenant_id}/connection")
async def test_store_connection(tenant_id: str):
    """
    Test store connection and credentials
    """
    try:
        # Check if store exists
        connection_info = await auth_service.get_store_connection(tenant_id)
        if not connection_info:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Test GraphQL connection
        from ..services.shopify_graphql import ShopifyGraphQLFactory
        graphql_service = await ShopifyGraphQLFactory.create_service(tenant_id)
        
        if not graphql_service:
            return {
                "status": "error",
                "connection_info": connection_info,
                "graphql_service": False,
                "message": "Failed to create GraphQL service"
            }
        
        # Test a simple GraphQL query (get shop info)
        try:
            shop_query = """
            query {
                shop {
                    id
                    name
                    email
                    domain
                    myshopifyDomain
                    plan {
                        displayName
                    }
                }
            }
            """
            shop_result = await graphql_service.execute_query(shop_query)
            
            return {
                "status": "success",
                "connection_info": connection_info,
                "graphql_service": True,
                "shop_info": shop_result.get("shop", {}),
                "test_timestamp": datetime.utcnow().isoformat()
            }
        except Exception as gql_error:
            return {
                "status": "error",
                "connection_info": connection_info,
                "graphql_service": False,
                "graphql_error": str(gql_error),
                "message": "GraphQL query failed"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.post("/webhook/samples")
async def get_webhook_samples():
    """
    Get sample webhook payloads for testing
    """
    samples = {
        "orders/create": {
            "id": 12345,
            "name": "#1001",
            "email": "customer@example.com",
            "created_at": "2025-08-10T10:00:00Z",
            "updated_at": "2025-08-10T10:00:00Z",
            "financial_status": "paid",
            "fulfillment_status": "unfulfilled",
            "total_price": "99.99",
            "currency": "USD",
            "customer": {
                "id": 67890,
                "first_name": "John",
                "last_name": "Doe",
                "email": "customer@example.com"
            },
            "line_items": [
                {
                    "id": 11111,
                    "name": "Test Product",
                    "sku": "TEST-001",
                    "quantity": 1,
                    "price": "99.99"
                }
            ]
        },
        
        "returns/create": {
            "id": 54321,
            "name": "RET-001",
            "status": "requested",
            "total_quantity": 1,
            "order_id": 12345,
            "requested_at": "2025-08-10T11:00:00Z",
            "created_at": "2025-08-10T11:00:00Z",
            "updated_at": "2025-08-10T11:00:00Z",
            "return_line_items": [
                {
                    "id": 22222,
                    "quantity": 1,
                    "return_reason": "defective",
                    "return_reason_note": "Product arrived damaged"
                }
            ]
        },
        
        "app/uninstalled": {
            "id": 98765,
            "name": "Test Store",
            "domain": "test-store.myshopify.com",
            "uninstalled_at": "2025-08-10T12:00:00Z"
        }
    }
    
    return {
        "samples": samples,
        "usage": "Use these payloads with POST /test/webhook to simulate webhook events",
        "topics_supported": list(webhook_processor.handlers.keys())
    }


@router.get("/health")
async def test_service_health():
    """
    Health check for testing services
    """
    return {
        "status": "healthy",
        "services": {
            "webhook_processor": True,
            "sync_service": True,
            "auth_service": True
        },
        "supported_webhook_topics": len(webhook_processor.handlers.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }