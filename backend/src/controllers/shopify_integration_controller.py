"""
Shopify Integration Status Controller
Handles integration status, sync jobs, and data management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from src.middleware.security import get_tenant_id
from src.config.database import db
from src.config.environment import env_config
from src.modules.auth.service import auth_service

router = APIRouter(prefix="/integrations/shopify", tags=["shopify-integration"])


@router.get("/status")
async def get_shopify_integration_status(tenant_id: str = Depends(get_tenant_id)):
    """
    Get Shopify integration status for the current tenant
    Returns connection status, sync status, and data counts
    """
    try:
        # First check integrations_shopify collection
        integration = await db.integrations_shopify.find_one({"tenant_id": tenant_id})
        
        # Also check tenant record for shopify_integration field (fallback)
        tenant = await db.tenants.find_one({"id": tenant_id})
        tenant_integration = tenant.get("shopify_integration") if tenant else None
        
        # Use integration data from either source
        shopify_integration = None
        if integration:
            shopify_integration = integration
        elif tenant_integration:
            shopify_integration = tenant_integration
        else:
            return {"connected": False}
        
        # Check if properly connected
        is_connected = (shopify_integration.get("status") == "connected" and 
                       shopify_integration.get("access_token") and
                       shopify_integration.get("shop_domain"))
        
        if not is_connected:
            return {"connected": False}
        
        # Get order counts
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_orders = await db.orders.count_documents({"tenant_id": tenant_id})
        recent_orders = await db.orders.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        })
        
        # Get return counts from correct 'returns' collection
        total_returns = await db.returns.count_documents({"tenant_id": tenant_id})
        recent_returns = await db.returns.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Get webhook status
        webhooks = [
            {"topic": "orders/create", "status": "active"},
            {"topic": "orders/updated", "status": "active"},
            {"topic": "fulfillments/create", "status": "active"},
            {"topic": "fulfillments/update", "status": "active"},
            {"topic": "returns/create", "status": "active"},
            {"topic": "returns/update", "status": "active"}
        ]
        
        # Get latest sync job
        latest_sync_job = await db.sync_jobs.find_one(
            {"tenant_id": tenant_id},
            sort=[("created_at", -1)]
        )
        
        return {
            "connected": True,
            "shop": tenant.get("shopify_store"),
            "installedAt": shopify_integration.get("installed_at"),
            "lastSyncAt": shopify_integration.get("last_sync"),
            "lastWebhookAt": shopify_integration.get("last_webhook_at"),
            "orderCounts": {
                "total": total_orders,
                "last30d": recent_orders
            },
            "returnCounts": {
                "total": total_returns, 
                "last30d": recent_returns
            },
            "webhooks": webhooks,
            "latestSyncJob": {
                "id": latest_sync_job.get("id") if latest_sync_job else None,
                "status": latest_sync_job.get("status") if latest_sync_job else None,
                "type": latest_sync_job.get("job_type") if latest_sync_job else None,
                "startedAt": latest_sync_job.get("created_at") if latest_sync_job else None,
                "completedAt": latest_sync_job.get("completed_at") if latest_sync_job else None
            }
        }
        
    except Exception as e:
        print(f"Error getting Shopify integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration status")


@router.post("/resync")
async def trigger_shopify_resync(tenant_id: str = Depends(get_tenant_id)):
    """
    Trigger a manual resync of Shopify data (90-day backfill)
    Returns job ID for tracking progress
    """
    try:
        # Get tenant record
        tenant = await db.tenants.find_one({"id": tenant_id})
        
        if not tenant or not tenant.get("shopify_integration"):
            raise HTTPException(status_code=400, detail="Shopify not connected")
        
        # Check for existing running sync jobs
        existing_job = await db.sync_jobs.find_one({
            "tenant_id": tenant_id,
            "status": {"$in": ["queued", "running"]}
        })
        
        if existing_job:
            return {
                "job_id": existing_job["id"],
                "message": "Sync already in progress",
                "status": existing_job["status"]
            }
        
        # Create new sync job
        job_id = f"resync-{tenant_id}-{int(datetime.utcnow().timestamp())}"
        
        sync_job = {
            "id": job_id,
            "tenant_id": tenant_id,
            "job_type": "manual_resync",
            "status": "queued",
            "created_at": datetime.utcnow(),
            "sync_config": {
                "orders_days_back": 90,
                "include_orders": True,
                "include_products": True,
                "include_returns": True
            },
            "progress": 0
        }
        
        await db.sync_jobs.insert_one(sync_job)
        
        # Start background sync immediately
        shop = tenant.get("shopify_store")
        encrypted_token = tenant["shopify_integration"]["access_token_encrypted"]
        
        # Decrypt token for sync
        from cryptography.fernet import Fernet
        import base64
        import os
        
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        if encryption_key:
            cipher = Fernet(encryption_key.encode())
            access_token = cipher.decrypt(encrypted_token.encode()).decode()
            
            # Process sync immediately instead of background task
            try:
                await auth_service._sync_orders(tenant_id, shop, access_token, days_back=30)
                
                # Update job status to completed
                await db.sync_jobs.update_one(
                    {"id": job_id},
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": datetime.utcnow(),
                            "progress": 100,
                            "message": "Manual resync completed successfully"
                        }
                    }
                )
            except Exception as e:
                await db.sync_jobs.update_one(
                    {"id": job_id},
                    {
                        "$set": {
                            "status": "failed",
                            "completed_at": datetime.utcnow(),
                            "error": str(e)
                        }
                    }
                )
        
        return {
            "job_id": job_id,
            "message": "Resync job started",
            "status": "queued"
        }
        
    except Exception as e:
        print(f"Error triggering resync: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger resync")


@router.get("/jobs")
async def get_sync_jobs(
    tenant_id: str = Depends(get_tenant_id),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get recent sync jobs for the tenant
    """
    try:
        jobs_cursor = db.sync_jobs.find(
            {"tenant_id": tenant_id}
        ).sort("created_at", -1).limit(limit)
        
        jobs = await jobs_cursor.to_list(limit)
        
        # Format jobs for response
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                "id": job["id"],
                "type": job["job_type"],
                "status": job["status"],
                "progress": job.get("progress", 0),
                "startedAt": job["created_at"].isoformat() if job.get("created_at") else None,
                "completedAt": job["completed_at"].isoformat() if job.get("completed_at") else None,
                "error": job.get("error"),
                "message": job.get("message")
            })
        
        return formatted_jobs
        
    except Exception as e:
        print(f"Error getting sync jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync jobs")