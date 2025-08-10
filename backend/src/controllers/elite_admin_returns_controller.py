"""
Elite Admin Returns Controller
Implements comprehensive return management for merchants
Uses CQRS handlers and hexagonal architecture
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..utils.dependencies import get_tenant_id
from ..application.commands import ApproveReturn, RejectReturn, ProcessRefund, ApproveDraftAndConvert
from ..application.queries import (
    GetReturnById, SearchReturns, GetPendingDrafts, GetReturnAuditLog
)
from ..application.handlers.command_handlers import (
    ApproveReturnHandler, RejectReturnHandler, ApproveDraftAndConvertHandler
)
from ..application.handlers.query_handlers import (
    GetReturnByIdHandler, SearchReturnsHandler, GetPendingDraftsHandler, GetReturnAuditLogHandler
)
from ..domain.value_objects import TenantId

# Dependency injection setup
from ..infrastructure.services.dependency_container import get_container


router = APIRouter(prefix="/api/elite/admin/returns", tags=["Elite Admin Returns"])


# Request/Response Models
class ApproveReturnRequest(BaseModel):
    override_policy: bool = False
    notes: Optional[str] = ""


class RejectReturnRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class ProcessRefundRequest(BaseModel):
    refund_amount: float = Field(..., ge=0)
    refund_method: str = Field(..., regex="^(original_payment|store_credit|manual)$")


class ApproveDraftRequest(BaseModel):
    linked_order_id: str = Field(..., min_length=1)
    notes: Optional[str] = ""


# Routes
@router.get("/")
async def get_returns(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = Query(None),
    customer_email: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get returns with search and filtering"""
    try:
        container = get_container()
        handler = container.get_search_returns_handler()
        
        # Parse dates
        parsed_date_from = None
        parsed_date_to = None
        if date_from:
            parsed_date_from = datetime.fromisoformat(date_from)
        if date_to:
            parsed_date_to = datetime.fromisoformat(date_to)
        
        query = SearchReturns(
            tenant_id=TenantId(tenant_id),
            status=status,
            customer_email=customer_email,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            search_term=search,
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        result = await handler.handle(query)
        
        return {
            "success": True,
            "returns": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{return_id}")
async def get_return_by_id(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get detailed return information"""
    try:
        container = get_container()
        handler = container.get_return_by_id_handler()
        
        query = GetReturnById(
            return_id=return_id,
            tenant_id=TenantId(tenant_id)
        )
        
        return_data = await handler.handle(query)
        
        if not return_data:
            raise HTTPException(status_code=404, detail="Return not found")
        
        return {
            "success": True,
            "return": return_data
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{return_id}/approve")
async def approve_return(
    return_id: str,
    request: ApproveReturnRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Approve a return request"""
    try:
        container = get_container()
        handler = container.get_approve_return_handler()
        
        command = ApproveReturn(
            return_id=return_id,
            tenant_id=TenantId(tenant_id),
            approver="admin",  # TODO: Get from authentication context
            override_policy=request.override_policy,
            notes=request.notes or "",
            correlation_id=str(uuid.uuid4())
        )
        
        result = await handler.handle(command)
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{return_id}/reject")
async def reject_return(
    return_id: str,
    request: RejectReturnRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Reject a return request"""
    try:
        container = get_container()
        handler = container.get_reject_return_handler()
        
        command = RejectReturn(
            return_id=return_id,
            tenant_id=TenantId(tenant_id),
            rejector="admin",  # TODO: Get from authentication context
            reason=request.reason,
            correlation_id=str(uuid.uuid4())
        )
        
        result = await handler.handle(command)
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{return_id}/audit-log")
async def get_return_audit_log(
    return_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get return audit log/timeline"""
    try:
        container = get_container()
        handler = container.get_audit_log_handler()
        
        query = GetReturnAuditLog(
            return_id=return_id,
            tenant_id=TenantId(tenant_id)
        )
        
        audit_log = await handler.handle(query)
        
        return {
            "success": True,
            "audit_log": audit_log
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts/pending")
async def get_pending_drafts(
    tenant_id: str = Depends(get_tenant_id),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get pending return drafts for review"""
    try:
        container = get_container()
        handler = container.get_pending_drafts_handler()
        
        query = GetPendingDrafts(
            tenant_id=TenantId(tenant_id),
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        result = await handler.handle(query)
        
        return {
            "success": True,
            "drafts": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drafts/{draft_id}/approve")
async def approve_draft_and_convert(
    draft_id: str,
    request: ApproveDraftRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Approve draft and convert to return"""
    try:
        container = get_container()
        handler = container.get_approve_draft_handler()
        
        command = ApproveDraftAndConvert(
            draft_id=draft_id,
            tenant_id=TenantId(tenant_id),
            linked_order_id=request.linked_order_id,
            approver="admin",  # TODO: Get from authentication context
            notes=request.notes or "",
            correlation_id=str(uuid.uuid4())
        )
        
        result = await handler.handle(command)
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-approve")
async def bulk_approve_returns(
    return_ids: List[str],
    override_policy: bool = False,
    notes: str = "",
    tenant_id: str = Depends(get_tenant_id)
):
    """Bulk approve multiple returns"""
    try:
        container = get_container()
        handler = container.get_approve_return_handler()
        
        results = []
        for return_id in return_ids:
            try:
                command = ApproveReturn(
                    return_id=return_id,
                    tenant_id=TenantId(tenant_id),
                    approver="admin",  # TODO: Get from authentication context
                    override_policy=override_policy,
                    notes=notes,
                    correlation_id=str(uuid.uuid4())
                )
                
                result = await handler.handle(command)
                results.append({
                    "return_id": return_id,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "return_id": return_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for elite admin returns API"""
    return {
        "status": "healthy",
        "service": "Elite Admin Returns API",
        "version": "1.0.0",
        "features": [
            "return_management",
            "draft_approval",
            "bulk_operations",
            "audit_logs",
            "policy_overrides"
        ]
    }