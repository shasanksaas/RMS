"""
Elite Portal Returns Controller
Implements dual-mode order lookup and comprehensive return creation for customers
Uses CQRS handlers and hexagonal architecture
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..utils.dependencies import get_tenant_id
from ..application.commands import CreateReturnRequest, CreateReturnDraft
from ..application.queries import LookupOrderForReturn, GetEligibleItemsForReturn, GetPolicyPreview
from ..application.handlers.command_handlers import CreateReturnRequestHandler, CreateReturnDraftHandler
from ..application.handlers.query_handlers import (
    LookupOrderForReturnHandler, GetEligibleItemsForReturnHandler, GetPolicyPreviewHandler
)
from ..domain.entities.return_entity import ReturnChannel, ReturnMethod
from ..domain.value_objects import TenantId, OrderId, Email

# Dependency injection setup (will be configured in main application)
from ..infrastructure.services.dependency_container import get_container


router = APIRouter(prefix="/api/elite/portal/returns", tags=["Elite Portal Returns"])


# Request/Response Models
class OrderLookupRequest(BaseModel):
    order_number: str = Field(..., min_length=1)
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')


class OrderLookupResponse(BaseModel):
    success: bool
    mode: str  # "shopify", "local", "fallback"
    order: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ReturnItemRequest(BaseModel):
    line_item_id: str
    sku: str
    title: str
    variant_title: Optional[str] = None
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    reason: str
    reason_description: Optional[str] = None
    condition: str = Field(..., regex="^(new|used|damaged)$")
    photos: List[str] = Field(default_factory=list)
    notes: Optional[str] = ""


class CreateReturnRequestModel(BaseModel):
    order_id: Optional[str] = None  # For Shopify mode
    order_number: Optional[str] = None  # For fallback mode
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    return_method: str = Field(..., pattern="^(prepaid_label|qr_dropoff|in_store|customer_ships)$")
    items: List[ReturnItemRequest]
    customer_note: Optional[str] = ""


class FallbackReturnRequest(BaseModel):
    order_number: str = Field(..., min_length=1)
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    items: List[Dict[str, Any]]
    photos: List[str] = Field(default_factory=list)
    customer_note: Optional[str] = ""


class PolicyPreviewRequest(BaseModel):
    order_id: Optional[str] = None
    items: List[Dict[str, Any]]


# Routes
@router.post("/lookup-order", response_model=OrderLookupResponse)
async def lookup_order(
    request: OrderLookupRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Dual-mode order lookup for return creation
    Tries Shopify first if connected, falls back to local database
    """
    try:
        container = get_container()
        handler = container.get_lookup_order_handler()
        
        query = LookupOrderForReturn(
            order_number=request.order_number,
            customer_email=request.customer_email,
            tenant_id=TenantId(tenant_id)
        )
        
        result = await handler.handle(query)
        
        return OrderLookupResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/eligible-items")
async def get_eligible_items(
    order_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get items eligible for return from an order"""
    try:
        container = get_container()
        handler = container.get_eligible_items_handler()
        
        query = GetEligibleItemsForReturn(
            order_id=order_id,
            tenant_id=TenantId(tenant_id)
        )
        
        items = await handler.handle(query)
        
        return {
            "success": True,
            "items": items
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policy-preview")
async def get_policy_preview(
    request: PolicyPreviewRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get policy preview with fee calculation and eligibility check"""
    try:
        container = get_container()
        handler = container.get_policy_preview_handler()
        
        query = GetPolicyPreview(
            tenant_id=TenantId(tenant_id),
            order_id=request.order_id or "mock_order",
            items=request.items
        )
        
        preview = await handler.handle(query)
        
        return {
            "success": True,
            "preview": preview
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_return_request(
    request: CreateReturnRequestModel,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create return request (Shopify mode)
    For orders found via order lookup with valid Shopify integration
    """
    try:
        if not request.order_id:
            raise HTTPException(
                status_code=400, 
                detail="order_id is required for Shopify mode"
            )
        
        container = get_container()
        handler = container.get_create_return_handler()
        
        # Convert request items to command format
        line_items = []
        for item in request.items:
            line_items.append({
                "line_item_id": item.line_item_id,
                "sku": item.sku,
                "title": item.title,
                "variant_title": item.variant_title,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "reason": item.reason,
                "reason_description": item.reason_description or "",
                "condition": item.condition,
                "photos": item.photos,
                "notes": item.notes
            })
        
        command = CreateReturnRequest(
            tenant_id=TenantId(tenant_id),
            order_id=OrderId(request.order_id),
            customer_email=Email(request.customer_email),
            channel=ReturnChannel.CUSTOMER,
            return_method=ReturnMethod(request.return_method),
            line_items=line_items,
            customer_note=request.customer_note or "",
            submitted_by="customer",
            correlation_id=str(uuid.uuid4())
        )
        
        result = await handler.handle(command)
        
        return {
            "success": True,
            "return_request": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-draft")
async def create_return_draft(
    request: FallbackReturnRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create return draft (Fallback mode)
    For when Shopify integration is not available or order not found
    """
    try:
        container = get_container()
        handler = container.get_create_draft_handler()
        
        command = CreateReturnDraft(
            tenant_id=TenantId(tenant_id),
            order_number=request.order_number,
            customer_email=Email(request.customer_email),
            channel=ReturnChannel.CUSTOMER,
            items=request.items,
            photos=request.photos,
            customer_note=request.customer_note or "",
            correlation_id=str(uuid.uuid4())
        )
        
        result = await handler.handle(command)
        
        return {
            "success": True,
            "draft": result,
            "message": "Return request submitted for manual review. You will receive an email confirmation shortly."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-photo")
async def upload_return_photo(
    file: bytes,
    filename: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Upload photo for return request"""
    try:
        # Use existing file upload utility
        from ..utils.file_upload import save_file
        
        file_path = await save_file(
            file_content=file,
            filename=filename,
            folder=f"returns/{tenant_id}/photos"
        )
        
        return {
            "success": True,
            "photo_url": file_path,
            "message": "Photo uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for elite portal returns API"""
    return {
        "status": "healthy",
        "service": "Elite Portal Returns API",
        "version": "1.0.0",
        "features": [
            "dual_mode_order_lookup",
            "policy_preview",
            "return_creation",
            "fallback_mode",
            "photo_upload"
        ]
    }