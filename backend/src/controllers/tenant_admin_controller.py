"""
Tenant Administration Controller
Real tenant CRUD operations with admin-only access and impersonation functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import jwt
import os
import logging
from typing import Optional

from src.middleware.admin_guard import require_admin
from src.models.user import UserDB as User
from src.models.tenant_admin import (
    TenantCreateRequest, 
    TenantResponse, 
    TenantListResponse,
    TenantDeleteResponse,
    ImpersonationResponse,
    AuditLogEntry
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/tenants", tags=["Admin - Tenant Management"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/returns_manager_enhanced")
client = MongoClient(MONGO_URL)
db = client.returns_management

# JWT settings for impersonation tokens
JWT_SECRET_KEY = os.environ.get("SECRET_KEY", "user-management-secret-key-change-in-production-very-secure-key")
IMPERSONATION_EXPIRY_MINUTES = 30

@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = 1,
    page_size: int = 50,
    admin_user: User = Depends(require_admin)
):
    """
    List all tenants from database (admin-only)
    Returns real tenant data, no mocks
    """
    try:
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Query tenants collection
        tenants_collection = db.tenants
        
        # Get total count
        total = tenants_collection.count_documents(
            {"archived": {"$ne": True}}  # Exclude soft-deleted tenants
        )
        
        # Get paginated tenants
        tenant_docs = list(tenants_collection.find(
            {"archived": {"$ne": True}},
            {"_id": 0}  # Exclude MongoDB _id
        ).skip(skip).limit(page_size).sort("created_at", -1))
        
        # Convert to response models
        tenants = []
        for doc in tenant_docs:
            # Add basic stats if available
            stats = {
                "orders_count": 0,
                "returns_count": 0,
                "users_count": 0
            }
            
            # Get stats from related collections
            if doc.get("tenant_id"):
                tenant_id = doc["tenant_id"]
                
                # Count orders for this tenant
                orders_count = db.orders.count_documents({"tenant_id": tenant_id})
                stats["orders_count"] = orders_count
                
                # Count returns for this tenant  
                returns_count = db.returns.count_documents({"tenant_id": tenant_id})
                stats["returns_count"] = returns_count
                
                # Count users for this tenant
                users_count = db.users.count_documents({"tenant_id": tenant_id})
                stats["users_count"] = users_count
            
            tenant_response = TenantResponse(
                tenant_id=doc.get("tenant_id", ""),
                name=doc.get("name", ""),
                shop_domain=doc.get("shop_domain"),
                connected_provider=doc.get("connected_provider"),
                created_at=doc.get("created_at", datetime.utcnow()),
                stats=stats
            )
            tenants.append(tenant_response)
        
        logger.info(f"Admin {admin_user.email} listed {len(tenants)} tenants (page {page})")
        
        return TenantListResponse(
            tenants=tenants,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenants"
        )

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreateRequest,
    admin_user: User = Depends(require_admin)
):
    """
    Create a new tenant (admin-only)
    Validates unique tenant_id and returns created record
    """
    try:
        tenants_collection = db.tenants
        
        # Check if tenant_id already exists
        existing_tenant = tenants_collection.find_one({"tenant_id": tenant_data.tenant_id})
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with ID '{tenant_data.tenant_id}' already exists"
            )
        
        # Create tenant document
        tenant_doc = {
            "tenant_id": tenant_data.tenant_id,
            "name": tenant_data.name,
            "shop_domain": tenant_data.shop_domain,
            "connected_provider": None,  # Will be set when Shopify is connected
            "created_at": datetime.utcnow(),
            "archived": False
        }
        
        # Insert into database
        result = tenants_collection.insert_one(tenant_doc)
        
        if result.inserted_id:
            # Log audit event
            await log_audit_event(
                action="TENANT_CREATED",
                admin_user=admin_user,
                tenant_id=tenant_data.tenant_id,
                details={"name": tenant_data.name, "shop_domain": tenant_data.shop_domain}
            )
            
            logger.info(f"Tenant {tenant_data.tenant_id} created by admin {admin_user.email}")
            
            return TenantResponse(
                tenant_id=tenant_doc["tenant_id"],
                name=tenant_doc["name"],
                shop_domain=tenant_doc["shop_domain"],
                connected_provider=tenant_doc["connected_provider"],
                created_at=tenant_doc["created_at"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tenant"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )

@router.delete("/{tenant_id}", response_model=TenantDeleteResponse)
async def delete_tenant(
    tenant_id: str,
    admin_user: User = Depends(require_admin)
):
    """
    Delete/archive a tenant (admin-only)
    Soft delete by default (set archived=true)
    """
    try:
        tenants_collection = db.tenants
        
        # Check if tenant exists
        tenant = tenants_collection.find_one({"tenant_id": tenant_id, "archived": {"$ne": True}})
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found"
            )
        
        # Check environment variable for hard delete
        hard_delete_allowed = os.environ.get("HARD_DELETE_ALLOWED", "false").lower() == "true"
        
        if hard_delete_allowed:
            # Hard delete - completely remove from database
            result = tenants_collection.delete_one({"tenant_id": tenant_id})
            action = "TENANT_HARD_DELETED"
            message = f"Tenant '{tenant_id}' permanently deleted"
        else:
            # Soft delete - mark as archived
            result = tenants_collection.update_one(
                {"tenant_id": tenant_id},
                {
                    "$set": {
                        "archived": True,
                        "archived_at": datetime.utcnow(),
                        "archived_by": admin_user.email
                    }
                }
            )
            action = "TENANT_ARCHIVED"
            message = f"Tenant '{tenant_id}' archived (soft deleted)"
        
        if result.modified_count > 0 or result.deleted_count > 0:
            # Log audit event
            await log_audit_event(
                action=action,
                admin_user=admin_user,
                tenant_id=tenant_id,
                details={"tenant_name": tenant["name"]}
            )
            
            logger.info(f"Tenant {tenant_id} deleted by admin {admin_user.email}")
            
            return TenantDeleteResponse(
                success=True,
                message=message,
                tenant_id=tenant_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tenant"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tenant"
        )

@router.post("/{tenant_id}/impersonate")
async def impersonate_tenant(
    tenant_id: str,
    response: Response,
    admin_user: User = Depends(require_admin)
):
    """
    Admin impersonation - create session to view tenant dashboard
    Sets secure HTTP-only cookie and redirects to merchant dashboard
    """
    try:
        tenants_collection = db.tenants
        
        # Verify tenant exists
        tenant = tenants_collection.find_one({"tenant_id": tenant_id, "archived": {"$ne": True}})
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found"
            )
        
        # Create impersonation JWT token
        impersonation_payload = {
            "sub": admin_user.user_id,  # Original admin user ID
            "tenant_id": tenant_id,
            "role": "merchant",  # Impersonate as merchant
            "act": "impersonate",  # Action type
            "orig_user_id": admin_user.user_id,
            "orig_email": admin_user.email,
            "exp": datetime.utcnow() + timedelta(minutes=IMPERSONATION_EXPIRY_MINUTES),
            "iat": datetime.utcnow()
        }
        
        impersonation_token = jwt.encode(
            impersonation_payload,
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=impersonation_token,
            max_age=IMPERSONATION_EXPIRY_MINUTES * 60,  # seconds
            httponly=True,
            secure=False,  # Allow HTTP for development
            samesite="lax",
            path="/"  # Ensure cookie is available site-wide
        )
        
        # Log audit event
        await log_audit_event(
            action="ADMIN_IMPERSONATE",
            admin_user=admin_user,
            tenant_id=tenant_id,
            details={
                "tenant_name": tenant["name"],
                "session_duration_minutes": IMPERSONATION_EXPIRY_MINUTES
            }
        )
        
        logger.info(f"Admin {admin_user.email} impersonating tenant {tenant_id}")
        
        # Redirect to merchant dashboard
        redirect_url = f"/app/dashboard?tenant={tenant_id}&impersonated=true"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error impersonating tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start impersonation session"
        )

@router.post("/end-impersonation")
async def end_impersonation(
    response: Response,
    request: Request
):
    """
    End admin impersonation session
    Clear impersonation cookie and redirect back to admin panel
    """
    try:
        # Clear the impersonation cookie
        response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # Try to get impersonation info for logging
        session_token = request.cookies.get("session_token")
        if session_token:
            try:
                payload = jwt.decode(session_token, JWT_SECRET_KEY, algorithms=["HS256"])
                tenant_id = payload.get("tenant_id")
                orig_email = payload.get("orig_email")
                
                logger.info(f"Admin {orig_email} ended impersonation of tenant {tenant_id}")
            except jwt.InvalidTokenError:
                pass  # Token was invalid, just continue
        
        # Redirect back to admin tenants page
        return RedirectResponse(url="/admin/tenants", status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        logger.error(f"Error ending impersonation: {str(e)}")
        # Still redirect even if logging fails
        return RedirectResponse(url="/admin/tenants", status_code=status.HTTP_302_FOUND)

async def log_audit_event(
    action: str,
    admin_user: User,
    tenant_id: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    Log admin action to audit trail
    """
    try:
        audit_collection = db.admin_audit_log
        
        audit_entry = {
            "action": action,
            "admin_user_id": admin_user.user_id,
            "admin_email": admin_user.email,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow(),
            "details": details or {}
        }
        
        audit_collection.insert_one(audit_entry)
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")
        # Don't raise exception for audit logging failures