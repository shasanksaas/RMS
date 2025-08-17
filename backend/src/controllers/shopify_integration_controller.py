"""
Shopify Integration Status Controller
Handles integration status, sync jobs, and data management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import httpx

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
        print(f"🔍 STATUS CHECK: Getting Shopify integration status for tenant: {tenant_id}")
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
            print(f"🔍 STATUS CHECK: No integration found for tenant: {tenant_id}")
            return {
                "connected": False,
                "orderCounts": {
                    "total": 0,
                    "last30d": 0
                },
                "returnCounts": {
                    "total": 0,
                    "last30d": 0
                },
                "message": "No Shopify integration connected"
            }
        
        # Check if properly connected
        is_connected = (shopify_integration.get("status") == "connected" and 
                       (shopify_integration.get("access_token_encrypted") or shopify_integration.get("access_token")) and
                       shopify_integration.get("shop_domain"))
        
        print(f"🔍 STATUS CHECK: Connection status for {tenant_id}: {is_connected}")
        
        if not is_connected:
            return {
                "connected": False,
                "orderCounts": {
                    "total": 0,
                    "last30d": 0
                },
                "returnCounts": {
                    "total": 0,
                    "last30d": 0
                },
                "message": "No Shopify integration connected"
            }
        
        # Get order counts (only from Shopify source)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_orders = await db.orders.count_documents({
            "tenant_id": tenant_id,
            "source": {"$in": ["shopify", "shopify_live"]}  # Handle both source types
        })
        recent_orders = await db.orders.count_documents({
            "tenant_id": tenant_id,
            "source": {"$in": ["shopify", "shopify_live"]},  # Handle both source types
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        })
        
        # Get return counts from correct 'returns' collection (only Shopify-related)
        total_returns = await db.returns.count_documents({
            "tenant_id": tenant_id,
            "$or": [
                {"source": {"$in": ["shopify", "returns_manager"]}},
                {"source": None}  # Include returns with no source (likely from our system)
            ]
        })
        recent_returns = await db.returns.count_documents({
            "tenant_id": tenant_id,
            "$or": [
                {"source": {"$in": ["shopify", "returns_manager"]}},
                {"source": None}
            ],
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Get webhook status from integration record (dynamic, not hardcoded)
        webhooks = []
        webhook_data = shopify_integration.get("webhooks", {})
        
        # Default webhook topics we expect
        expected_webhooks = [
            "orders/create", "orders/updated", 
            "fulfillments/create", "fulfillments/update",
            "app/uninstalled"
        ]
        
        for topic in expected_webhooks:
            webhook_info = webhook_data.get(topic.replace('/', '_'), {})
            webhooks.append({
                "topic": topic,
                "status": "active" if webhook_info.get("id") else "inactive",
                "webhook_id": webhook_info.get("id"),
                "created_at": webhook_info.get("created_at")
            })
        
        # Get latest sync job
        latest_sync_job = await db.sync_jobs.find_one(
            {"tenant_id": tenant_id},
            sort=[("created_at", -1)]
        )
        
        return {
            "connected": True,
            "shop": shopify_integration.get("shop_domain"),
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
        print(f"❌ Integration status check failed: {str(e)}")
        import traceback
        print("📊 Full traceback:")
        traceback.print_exc()
        return {
            "connected": False,
            "status": "error",
            "message": f"Error checking connection status: {str(e)}",
            "error_type": type(e).__name__
        }


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
        
        # Get integration data for sync
        integration = await db.integrations_shopify.find_one({"tenant_id": tenant_id})
        if not integration:
            raise HTTPException(status_code=400, detail="Shopify integration not found")
        
        shop = integration.get("shop_domain")
        encrypted_token = integration.get("access_token_encrypted")
        
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


@router.post("/sync-existing")
async def sync_existing_shopify_installation(
    sync_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Sync an already-installed Shopify app that's not in our database
    
    For cases where the app is installed in Shopify but not recorded in our system
    """
    try:
        shop_domain = sync_data.get("shop_domain", "").strip()
        access_token = sync_data.get("access_token", "").strip()
        
        if not shop_domain or not access_token:
            raise HTTPException(
                status_code=400,
                detail="shop_domain and access_token are required"
            )
        
        print(f"🔄 Syncing existing Shopify installation for {shop_domain}")
        
        # Normalize shop domain
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
        
        # Test the access token by making a shop API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{shop_domain}/admin/api/2025-07/shop.json",
                headers={"X-Shopify-Access-Token": access_token}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid access token or shop domain"
                )
            
            shop_info = response.json()["shop"]
        
        # Create integration record
        from src.services.shopify_oauth_service import ShopifyOAuthService
        oauth_service = ShopifyOAuthService()
        
        # Store the integration
        integration_data = {
            "tenant_id": tenant_id,
            "shop_domain": shop_domain,
            "access_token_encrypted": oauth_service.encrypt_token(access_token),
            "scopes": oauth_service.scopes,
            "status": "connected",
            "connected_at": datetime.utcnow(),
            "shop_info": {
                "name": shop_info.get("name"),
                "email": shop_info.get("email"),
                "domain": shop_info.get("domain"),
                "currency": shop_info.get("currency"),
                "timezone": shop_info.get("iana_timezone")
            }
        }
        
        # Insert or update integration
        await db.integrations_shopify.replace_one(
            {"tenant_id": tenant_id, "shop_domain": shop_domain},
            integration_data,
            upsert=True
        )
        
        # Start data backfill
        print(f"🔄 Starting data backfill for synced installation...")
        try:
            # Import the backfill method
            await oauth_service._queue_data_backfill(tenant_id, shop_domain)
        except Exception as e:
            print(f"⚠️ Backfill failed but integration synced: {e}")
        
        print(f"✅ Successfully synced existing installation for {shop_domain}")
        
        return {
            "success": True,
            "message": f"Successfully synced existing Shopify installation for {shop_domain}",
            "integration": {
                "tenant_id": tenant_id,
                "shop_domain": shop_domain,
                "status": "connected",
                "shop_name": shop_info.get("name")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error syncing existing installation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync existing installation: {str(e)}"
        )


@router.post("/resync")
async def resync_shopify_data(tenant_id: str = Depends(get_tenant_id)):
    """
    Trigger manual Shopify data resync for current tenant
    """
    try:
        print(f"🔄 Manual resync triggered for tenant: {tenant_id}")
        
        # Check if integration exists
        integration = await db.integrations_shopify.find_one({"tenant_id": tenant_id})
        
        if not integration:
            raise HTTPException(status_code=400, detail="Shopify integration not found")
        
        if integration.get("status") != "connected":
            raise HTTPException(status_code=400, detail="Shopify not connected")
        
        shop_domain = integration.get("shop_domain")
        if not shop_domain:
            raise HTTPException(status_code=400, detail="Shop domain not found")
        
        # Get access token
        encrypted_token = integration.get("access_token_encrypted")
        if not encrypted_token:
            raise HTTPException(status_code=400, detail="Access token not found")
        
        # Decrypt token
        from src.services.shopify_oauth_service import ShopifyOAuthService
        oauth_service = ShopifyOAuthService()
        access_token = oauth_service.decrypt_token(encrypted_token)
        
        # Trigger data sync
        await oauth_service._sync_shopify_orders(tenant_id, shop_domain, access_token)
        await oauth_service._sync_shopify_returns(tenant_id, shop_domain, access_token)
        
        # Update last sync timestamp
        await db.integrations_shopify.update_one(
            {"tenant_id": tenant_id},
            {"$set": {"last_sync_at": datetime.utcnow()}}
        )
        
        print(f"✅ Manual resync completed for tenant: {tenant_id}")
        
        return {
            "success": True,
            "message": "Data resync completed successfully",
            "tenant_id": tenant_id,
            "synced_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Resync failed for {tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resync data: {str(e)}"
        )


@router.post("/force-cleanup")
async def force_cleanup_shopify_data(tenant_id: str = Depends(get_tenant_id)):
    """
    Force cleanup of all Shopify-related data for tenant
    
    Use when disconnect didn't work properly or data is stuck
    """
    try:
        print(f"🧹 Force cleaning up Shopify data for tenant: {tenant_id}")
        
        # Remove any integration records
        integration_result = await db.integrations_shopify.delete_many({"tenant_id": tenant_id})
        
        # Clean up sync jobs
        sync_jobs_result = await db.sync_jobs.delete_many({"tenant_id": tenant_id})
        
        # Clean up orders (all Shopify source variations)
        orders_result = await db.orders.delete_many({
            "tenant_id": tenant_id,
            "source": {"$in": ["shopify", "shopify_live"]}
        })
        
        # Clean up returns (all variations)
        returns_result = await db.returns.delete_many({
            "tenant_id": tenant_id,
            "$or": [
                {"source": {"$in": ["shopify", "returns_manager"]}},
                {"source": None},
                {"source": {"$exists": False}}
            ]
        })
        
        print(f"✅ Force cleanup complete:")
        print(f"   Integrations cleaned: {integration_result.deleted_count}")
        print(f"   Sync jobs cleaned: {sync_jobs_result.deleted_count}")
        print(f"   Orders cleaned: {orders_result.deleted_count}")
        print(f"   Returns cleaned: {returns_result.deleted_count}")
        
        return {
            "success": True,
            "message": "Force cleanup completed successfully",
            "tenant_id": tenant_id,
            "details": {
                "integrations_cleaned": integration_result.deleted_count,
                "sync_jobs_cleaned": sync_jobs_result.deleted_count,
                "orders_cleaned": orders_result.deleted_count,
                "returns_cleaned": returns_result.deleted_count
            }
        }
        
    except Exception as e:
        print(f"❌ Force cleanup failed for {tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to force cleanup: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_shopify_integration(tenant_id: str = Depends(get_tenant_id)):
    """
    Disconnect Shopify integration for the current tenant
    
    Removes integration data completely and allows seamless reconnection
    Optionally cleans up orders/returns data for immediate count reset
    """
    try:
        print(f"🔄 Disconnecting Shopify integration for tenant: {tenant_id}")
        
        # Remove integration record entirely (allows reconnection)
        integration_result = await db.integrations_shopify.delete_one({"tenant_id": tenant_id})
        
        if integration_result.deleted_count > 0:
            # Clean up sync jobs
            sync_jobs_result = await db.sync_jobs.delete_many({"tenant_id": tenant_id})
            
            # Clean up Shopify-sourced data for immediate count reset
            orders_result = await db.orders.delete_many({
                "tenant_id": tenant_id,
                "source": {"$in": ["shopify", "shopify_live"]}  # Handle both source types
            })
            
            returns_result = await db.returns.delete_many({
                "tenant_id": tenant_id,
                "$or": [
                    {"source": {"$in": ["shopify", "returns_manager"]}},
                    {"source": None}  # Handle returns with no source set
                ]
            })
            
            print(f"✅ Disconnection complete:")
            print(f"   Integration removed: {integration_result.deleted_count > 0}")
            print(f"   Sync jobs cleaned: {sync_jobs_result.deleted_count}")
            print(f"   Orders cleaned: {orders_result.deleted_count}")
            print(f"   Returns cleaned: {returns_result.deleted_count}")
            
            return {
                "success": True,
                "message": "Shopify integration disconnected successfully",
                "tenant_id": tenant_id,
                "details": {
                    "integration_removed": integration_result.deleted_count > 0,
                    "sync_jobs_cleaned": sync_jobs_result.deleted_count,
                    "orders_cleaned": orders_result.deleted_count,
                    "returns_cleaned": returns_result.deleted_count
                }
            }
        else:
            return {
                "success": False,
                "message": "No Shopify integration found to disconnect",
                "tenant_id": tenant_id
            }
        
    except Exception as e:
        print(f"❌ Disconnect failed for {tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Shopify integration: {str(e)}"
        )