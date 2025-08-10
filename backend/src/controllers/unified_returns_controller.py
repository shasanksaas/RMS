"""
Unified Returns Controller - Handles both admin and customer return creation
Production-ready with full validation, policy enforcement, and Shopify integration
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

from ..middleware.security import get_current_tenant_id
from ..config.database import db
from ..services.shopify_service import ShopifyService
from ..services.shopify_graphql import ShopifyGraphQLService
from ..utils.enhanced_rules_engine import EnhancedRulesEngine
from ..services.email_service import EmailService
from ..services.label_service import LabelService
from ..utils.file_upload import FileUploadService

router = APIRouter(prefix="/unified-returns", tags=["Unified Returns"])

# Enums and Models
class ReturnReason(str, Enum):
    WRONG_SIZE = "wrong_size"
    WRONG_COLOR = "wrong_color"
    DAMAGED_DEFECTIVE = "damaged_defective"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    LATE_DELIVERY = "late_delivery"
    RECEIVED_EXTRA = "received_extra"
    OTHER = "other"

class PreferredOutcome(str, Enum):
    REFUND_ORIGINAL = "refund_original"
    STORE_CREDIT = "store_credit"
    EXCHANGE = "exchange"
    REPLACEMENT = "replacement"

class ReturnMethod(str, Enum):
    PREPAID_LABEL = "prepaid_label"
    QR_DROPOFF = "qr_dropoff"
    IN_STORE = "in_store"
    CUSTOMER_SHIPS = "customer_ships"

class Channel(str, Enum):
    PORTAL = "portal"
    ADMIN = "admin"

class ReturnItemRequest(BaseModel):
    fulfillment_line_item_id: str
    quantity: int = Field(gt=0)
    reason: ReturnReason
    reason_note: Optional[str] = None
    photo_urls: List[str] = Field(default_factory=list)

class OrderLookupRequest(BaseModel):
    order_number: str
    email: str

class CreateReturnRequest(BaseModel):
    # Order identification
    order_id: Optional[str] = None  # For admin use
    shopify_order_gid: Optional[str] = None
    order_number: Optional[str] = None  # For customer lookup
    email: Optional[str] = None  # For customer lookup
    
    # Return details
    items: List[ReturnItemRequest]
    preferred_outcome: PreferredOutcome
    return_method: ReturnMethod
    return_location_id: Optional[str] = None
    customer_note: Optional[str] = None
    
    # Channel and admin overrides
    channel: Channel = Channel.PORTAL
    admin_override_approve: Optional[bool] = None
    admin_override_note: Optional[str] = None
    internal_tags: List[str] = Field(default_factory=list)
    manual_fee_override: Optional[Dict[str, float]] = None

    @validator('email')
    def validate_email_for_portal(cls, v, values):
        if values.get('channel') == Channel.PORTAL and not v:
            raise ValueError('Email required for customer portal')
        return v

    @validator('order_number')
    def validate_order_number_for_portal(cls, v, values):
        if values.get('channel') == Channel.PORTAL and not v:
            raise ValueError('Order number required for customer portal')
        return v

class PolicyPreview(BaseModel):
    within_window: bool
    days_remaining: int
    fees: Dict[str, float]
    estimated_refund: float
    restrictions: List[str]
    auto_approve_eligible: bool

class EligibleItem(BaseModel):
    fulfillment_line_item_id: str
    title: str
    variant_title: Optional[str]
    sku: str
    image_url: Optional[str]
    quantity_ordered: int
    quantity_eligible: int
    price: float
    refundable_amount: float

class OrderVerificationResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    customer_name: Optional[str] = None
    order_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    eligible_items: Optional[List[EligibleItem]] = None
    policy_preview: Optional[PolicyPreview] = None
    error: Optional[str] = None

class CreateReturnResponse(BaseModel):
    success: bool
    return_id: str
    status: str
    policy_version: str
    decision: str
    fees: Dict[str, float]
    estimated_refund: float
    label_url: Optional[str] = None
    tracking_number: Optional[str] = None
    explain_trace: List[str]
    message: str

# API Endpoints
@router.post("/order/lookup", response_model=OrderVerificationResponse)
async def lookup_order(
    lookup_request: OrderLookupRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Customer portal: Lookup order by number and email
    Returns eligible items and policy preview
    """
    try:
        # Get Shopify service for tenant
        shopify_service = ShopifyService(tenant_id)
        
        # Find order by number and verify email
        order = await shopify_service.find_order_by_number(lookup_request.order_number)
        
        if not order:
            return OrderVerificationResponse(
                success=False,
                error="Order not found. Please check your order number."
            )
        
        # Verify email matches
        order_email = order.get('email') or order.get('customer_email', '')
        if order_email.lower() != lookup_request.email.lower():
            return OrderVerificationResponse(
                success=False,
                error="Email does not match order records."
            )
        
        # Check if order is returnable
        created_at_str = order['created_at']
        if isinstance(created_at_str, str):
            # Handle both ISO formats (with and without 'Z')
            if created_at_str.endswith('Z'):
                created_at_str = created_at_str.replace('Z', '+00:00')
            order_date = datetime.fromisoformat(created_at_str)
        else:
            # Handle datetime objects
            order_date = created_at_str
        days_since_order = (datetime.utcnow() - order_date).days
        
        # Get return policy for tenant
        tenant = await db.tenants.find_one({"id": tenant_id})
        return_window = tenant.get('settings', {}).get('return_window_days', 30)
        
        within_window = days_since_order <= return_window
        days_remaining = max(0, return_window - days_since_order)
        
        # Get eligible items
        eligible_items = []
        for line_item in order.get('line_items', []):
            # Check fulfillment status and quantities
            quantity_eligible = await _calculate_eligible_quantity(line_item, tenant_id)
            
            if quantity_eligible > 0:
                eligible_items.append(EligibleItem(
                    fulfillment_line_item_id=line_item['id'],
                    title=line_item['title'],
                    variant_title=line_item.get('variant_title'),
                    sku=line_item.get('sku', ''),
                    image_url=line_item.get('image_url'),
                    quantity_ordered=line_item['quantity'],
                    quantity_eligible=quantity_eligible,
                    price=float(line_item['price']),
                    refundable_amount=float(line_item['price']) * quantity_eligible
                ))
        
        # Calculate policy preview
        policy_preview = PolicyPreview(
            within_window=within_window,
            days_remaining=days_remaining,
            fees={'restocking_fee': 0.0, 'shipping_fee': 0.0},
            estimated_refund=sum(item.refundable_amount for item in eligible_items),
            restrictions=[],
            auto_approve_eligible=within_window and len(eligible_items) > 0
        )
        
        # Add restrictions based on policy
        if not within_window:
            policy_preview.restrictions.append(f"Order is outside {return_window}-day return window")
        
        if not eligible_items:
            policy_preview.restrictions.append("No items are eligible for return")
        
        return OrderVerificationResponse(
            success=True,
            order_id=order['id'],
            order_number=order['order_number'],
            customer_name=f"{order.get('billing_address', {}).get('first_name', '')} {order.get('billing_address', {}).get('last_name', '')}".strip(),
            order_date=order_date,
            total_amount=float(order['total_price']),
            eligible_items=eligible_items,
            policy_preview=policy_preview
        )
        
    except Exception as e:
        return OrderVerificationResponse(
            success=False,
            error=f"Failed to lookup order: {str(e)}"
        )

@router.get("/order/{order_id}/eligible-items", response_model=List[EligibleItem])
async def get_eligible_items(
    order_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Admin: Get eligible items for a specific order
    """
    try:
        shopify_service = ShopifyService(tenant_id)
        order = await shopify_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        eligible_items = []
        for line_item in order.get('line_items', []):
            quantity_eligible = await _calculate_eligible_quantity(line_item, tenant_id)
            
            if quantity_eligible > 0:
                eligible_items.append(EligibleItem(
                    fulfillment_line_item_id=line_item['id'],
                    title=line_item['title'],
                    variant_title=line_item.get('variant_title'),
                    sku=line_item.get('sku', ''),
                    image_url=line_item.get('image_url'),
                    quantity_ordered=line_item['quantity'],
                    quantity_eligible=quantity_eligible,
                    price=float(line_item['price']),
                    refundable_amount=float(line_item['price']) * quantity_eligible
                ))
        
        return eligible_items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get eligible items: {str(e)}")

@router.post("/upload-photos")
async def upload_return_photos(
    files: List[UploadFile] = File(...),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Upload photos for return request
    Returns URLs for uploaded photos
    """
    try:
        file_service = FileUploadService()
        uploaded_urls = []
        
        for file in files:
            # Validate file
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
            
            # Check file size (5MB limit)
            file_content = await file.read()
            if len(file_content) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File too large: {file.filename}")
            
            # Upload to storage
            file_url = await file_service.upload_return_photo(
                file_content, 
                file.filename, 
                tenant_id
            )
            uploaded_urls.append(file_url)
        
        return {
            "success": True,
            "uploaded_files": uploaded_urls,
            "count": len(uploaded_urls)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Photo upload failed: {str(e)}")

@router.post("/policy-preview")
async def get_policy_preview(
    items: List[ReturnItemRequest],
    order_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Get policy preview for selected items before submitting return
    """
    try:
        # Get order data
        shopify_service = ShopifyService(tenant_id)
        order = await shopify_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Calculate fees and refunds
        total_refund = 0.0
        fees = {"restocking_fee": 0.0, "shipping_fee": 0.0}
        
        for item_request in items:
            line_item = next((li for li in order['line_items'] if li['id'] == item_request.fulfillment_line_item_id), None)
            if line_item:
                item_refund = float(line_item['price']) * item_request.quantity
                total_refund += item_refund
                
                # Apply restocking fee for certain reasons
                if item_request.reason in [ReturnReason.CHANGED_MIND, ReturnReason.WRONG_SIZE]:
                    fees["restocking_fee"] += item_refund * 0.10  # 10% restocking fee
        
        # Check auto-approval eligibility
        auto_approve = all(
            item.reason in [ReturnReason.DAMAGED_DEFECTIVE, ReturnReason.NOT_AS_DESCRIBED]
            for item in items
        )
        
        return {
            "estimated_refund": total_refund - sum(fees.values()),
            "fees": fees,
            "auto_approve_eligible": auto_approve,
            "total_items": len(items),
            "refund_breakdown": {
                "subtotal": total_refund,
                "fees": fees,
                "final_amount": total_refund - sum(fees.values())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy preview failed: {str(e)}")

@router.post("/create", response_model=CreateReturnResponse)
async def create_return(
    return_request: CreateReturnRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Create return request - unified endpoint for both admin and customer portals
    """
    try:
        # Validate and get order
        order = None
        if return_request.channel == Channel.PORTAL:
            # Customer portal: lookup by order number and email
            shopify_service = ShopifyService(tenant_id)
            order = await shopify_service.find_order_by_number(return_request.order_number)
            
            if not order or order.get('email', '').lower() != return_request.email.lower():
                raise HTTPException(status_code=400, detail="Invalid order number or email")
                
        else:
            # Admin: use provided order_id
            shopify_service = ShopifyService(tenant_id)
            order = await shopify_service.get_order(return_request.order_id)
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate return window
        order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
        tenant = await db.tenants.find_one({"id": tenant_id})
        return_window = tenant.get('settings', {}).get('return_window_days', 30)
        days_since_order = (datetime.utcnow() - order_date).days
        
        if days_since_order > return_window and not return_request.admin_override_approve:
            raise HTTPException(
                status_code=400, 
                detail=f"Order is outside {return_window}-day return window"
            )
        
        # Validate items and quantities
        for item_request in return_request.items:
            line_item = next(
                (li for li in order['line_items'] if li['id'] == item_request.fulfillment_line_item_id), 
                None
            )
            if not line_item:
                raise HTTPException(status_code=400, detail=f"Invalid item ID: {item_request.fulfillment_line_item_id}")
            
            eligible_qty = await _calculate_eligible_quantity(line_item, tenant_id)
            if item_request.quantity > eligible_qty:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Quantity {item_request.quantity} exceeds eligible quantity {eligible_qty} for item {line_item['title']}"
                )
            
            # Validate photo requirements
            if item_request.reason == ReturnReason.DAMAGED_DEFECTIVE and not item_request.photo_urls:
                raise HTTPException(
                    status_code=400, 
                    detail="Photos are required for damaged/defective items"
                )
        
        # Create return request
        return_id = str(uuid.uuid4())
        
        # Calculate fees and refunds
        total_refund = 0.0
        fees = {"restocking_fee": 0.0, "shipping_fee": 0.0}
        
        for item_request in return_request.items:
            line_item = next((li for li in order['line_items'] if li['id'] == item_request.fulfillment_line_item_id), None)
            item_refund = float(line_item['price']) * item_request.quantity
            total_refund += item_refund
            
            # Apply fees based on reason
            if item_request.reason in [ReturnReason.CHANGED_MIND, ReturnReason.WRONG_SIZE]:
                fees["restocking_fee"] += item_refund * 0.10
        
        # Apply manual fee overrides if admin
        if return_request.manual_fee_override and return_request.channel == Channel.ADMIN:
            fees.update(return_request.manual_fee_override)
        
        final_refund = total_refund - sum(fees.values())
        
        # Determine decision
        auto_approve = (
            return_request.admin_override_approve or
            all(item.reason in [ReturnReason.DAMAGED_DEFECTIVE, ReturnReason.NOT_AS_DESCRIBED] for item in return_request.items)
        )
        
        decision = "approved" if auto_approve else "requested"
        status = "approved" if auto_approve else "requested"
        
        # Generate label if auto-approved and method is prepaid
        label_url = None
        tracking_number = None
        
        if auto_approve and return_request.return_method == ReturnMethod.PREPAID_LABEL:
            try:
                label_service = LabelService()
                label_result = await label_service.generate_return_label(
                    order, return_request.items, tenant_id
                )
                label_url = label_result.get('label_url')
                tracking_number = label_result.get('tracking_number')
            except Exception as e:
                print(f"Label generation failed: {e}")
        
        # Save to database
        return_record = {
            "id": return_id,
            "tenant_id": tenant_id,
            "order_id": order['id'],
            "order_number": order['order_number'],
            "customer_email": order['email'],
            "customer_name": f"{order.get('billing_address', {}).get('first_name', '')} {order.get('billing_address', {}).get('last_name', '')}".strip(),
            "status": status,
            "decision": decision,
            "channel": return_request.channel.value,
            "items": [item.dict() for item in return_request.items],
            "preferred_outcome": return_request.preferred_outcome.value,
            "return_method": return_request.return_method.value,
            "return_location_id": return_request.return_location_id,
            "customer_note": return_request.customer_note,
            "admin_override_note": return_request.admin_override_note,
            "internal_tags": return_request.internal_tags,
            "fees": fees,
            "estimated_refund": final_refund,
            "label_url": label_url,
            "tracking_number": tracking_number,
            "policy_version": "1.0",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.return_requests.insert_one(return_record)
        
        # Send email notification
        try:
            email_service = EmailService()
            await email_service.send_return_requested_email(
                order['email'],
                return_record,
                order
            )
            
            if auto_approve:
                await email_service.send_return_approved_email(
                    order['email'],
                    return_record,
                    order,
                    label_url
                )
        except Exception as e:
            print(f"Email notification failed: {e}")
        
        explain_trace = [
            f"Return request created via {return_request.channel.value}",
            f"Order date: {order_date.strftime('%Y-%m-%d')} ({days_since_order} days ago)",
            f"Within return window: {days_since_order <= return_window}",
            f"Auto-approval criteria met: {auto_approve}",
            f"Total refund before fees: ${total_refund:.2f}",
            f"Fees applied: {fees}",
            f"Final refund amount: ${final_refund:.2f}"
        ]
        
        if label_url:
            explain_trace.append(f"Return label generated: {label_url}")
        
        return CreateReturnResponse(
            success=True,
            return_id=return_id,
            status=status,
            policy_version="1.0",
            decision=decision,
            fees=fees,
            estimated_refund=final_refund,
            label_url=label_url,
            tracking_number=tracking_number,
            explain_trace=explain_trace,
            message=f"Return request {decision}. {'Return label has been generated.' if label_url else 'You will receive updates via email.'}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create return: {str(e)}")

# Helper Functions
async def _calculate_eligible_quantity(line_item: Dict[str, Any], tenant_id: str) -> int:
    """
    Calculate eligible quantity for return based on fulfillment status and existing returns
    """
    try:
        # Check if item is fulfilled
        if line_item.get('fulfillment_status') != 'fulfilled':
            return 0
        
        # Check existing returns for this item
        existing_returns = await db.return_requests.find({
            "tenant_id": tenant_id,
            "items.fulfillment_line_item_id": line_item['id'],
            "status": {"$in": ["approved", "completed", "requested"]}
        }).to_list(100)
        
        returned_quantity = 0
        for return_req in existing_returns:
            for item in return_req.get('items', []):
                if item.get('fulfillment_line_item_id') == line_item['id']:
                    returned_quantity += item.get('quantity', 0)
        
        eligible_quantity = line_item['quantity'] - returned_quantity
        return max(0, eligible_quantity)
        
    except Exception:
        return 0