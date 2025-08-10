from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
import time

# Import new controllers
from src.controllers.shopify_controller import router as shopify_router
from src.controllers.enhanced_features_controller import router as enhanced_router
from src.modules.auth.controller import router as auth_router
from src.controllers.webhook_controller import router as webhook_router
from src.controllers.testing_controller import router as testing_router
from src.controllers.returns_controller import router as returns_router
from src.controllers.shopify_test_controller import router as shopify_test_router
from src.controllers.rules_controller import router as rules_router
from src.controllers.unified_returns_controller import router as unified_returns_router
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import json

# Import new utilities
from src.utils.state_machine import ReturnStateMachine, ReturnResolutionHandler, ReturnResolutionType
from src.utils.rules_engine import RulesEngine

# Import repository layer and security
from src.repositories import RepositoryFactory
from src.middleware.security import (
    SecurityMiddleware, 
    RateLimitingMiddleware, 
    AuditMiddleware,
    tenant_context,
    get_current_tenant_id
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize repositories and middleware
repository_factory = None
security_middleware = SecurityMiddleware()
rate_limiting_middleware = RateLimitingMiddleware()  
audit_middleware = AuditMiddleware()

# Create the main app without a prefix
app = FastAPI(title="Returns Management SaaS API", version="1.0.0")

@app.on_event("startup")
async def startup_db_client():
    global repository_factory
    repository_factory = RepositoryFactory(db)
    print("✅ Database connected and repository factory initialized")

# Add security middleware
@app.middleware("http")
async def security_and_audit_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Skip middleware for health checks and static files
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json", "/api/"] or request.url.path.startswith("/static"):
        response = await call_next(request)
        return response
    
    # Skip tenant validation for certain endpoints
    skip_tenant_validation = [
        "/api/tenants",  # Tenant creation/listing
        "/api/auth/",    # Auth endpoints
        "/api/test/",    # Testing endpoints
        "/api/webhooks/", # Webhook endpoints
        "/api/enhanced/", # Enhanced features
        "/api/shopify/",   # Shopify endpoints
        "/api/shopify-test/",  # Shopify connectivity test endpoints
        "/api/rules/field-types/options"  # Rules field types endpoint (no tenant needed)
    ]
    
    should_skip_tenant = any(request.url.path.startswith(path) for path in skip_tenant_validation)
    
    try:
        # Validate tenant access for API endpoints (except those that should skip)
        if request.url.path.startswith("/api") and not should_skip_tenant:
            tenant_id = await security_middleware.validate_tenant_access(request)
            
            # Check rate limits
            await rate_limiting_middleware.check_rate_limit(tenant_id, request.url.path)
        
        # Process request
        response = await call_next(request)
        
        # Log audit trail
        duration_ms = (time.time() - start_time) * 1000
        await audit_middleware.log_request(request, response.status_code, duration_ms)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Security middleware error: {str(e)}")
        logger.error(f"Request path: {request.url.path}")
        logger.error(f"Request method: {request.method}")
        logger.error(f"Should skip tenant: {should_skip_tenant}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal security error: {str(e)}")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Secure dependency injection
def get_repository_factory() -> RepositoryFactory:
    """Get repository factory instance"""
    if not repository_factory:
        raise HTTPException(status_code=500, detail="Repository factory not initialized")
    return repository_factory

async def get_secure_tenant_id(request: Request) -> str:
    """Secure tenant ID extraction with validation"""
    if hasattr(tenant_context, 'tenant_id') and tenant_context.tenant_id:
        return tenant_context.tenant_id
    
    # Fallback for non-middleware requests
    tenant_id = request.headers.get("X-Tenant-Id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    return tenant_id

# Enums - Updated with proper state machine statuses
class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    LABEL_ISSUED = "label_issued" 
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    RESOLVED = "resolved"

class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    WRONG_SIZE = "wrong_size"
    WRONG_COLOR = "wrong_color"
    NOT_AS_DESCRIBED = "not_as_described"
    DAMAGED_IN_SHIPPING = "damaged_in_shipping"
    CHANGED_MIND = "changed_mind"
    QUALITY_ISSUES = "quality_issues"

class PlanType(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Models
class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: str
    shopify_store_url: Optional[str] = None
    shopify_access_token: Optional[str] = None
    plan: PlanType = PlanType.TRIAL
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    shopify_product_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    sku: str
    in_stock: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    sku: str

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    shopify_order_id: Optional[str] = None
    customer_email: str
    customer_name: str
    order_number: str
    items: List[OrderItem]
    total_amount: float
    order_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReturnRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # JSON conditions for rule evaluation
    actions: Dict[str, Any]     # Actions to take when rule matches
    priority: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReturnRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_id: str
    customer_email: str
    customer_name: str
    reason: ReturnReason
    status: ReturnStatus = ReturnStatus.REQUESTED
    items_to_return: List[OrderItem]
    refund_amount: float = 0.0
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Analytics(BaseModel):
    tenant_id: str
    total_returns: int = 0
    total_refunds: float = 0.0
    exchange_rate: float = 0.0
    avg_processing_time: float = 0.0
    top_return_reasons: List[Dict[str, Any]] = Field(default_factory=list)
    period_start: datetime
    period_end: datetime

# DTOs
class TenantCreate(BaseModel):
    name: str
    domain: str
    shopify_store_url: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: str
    image_url: Optional[str] = None

class OrderCreate(BaseModel):
    customer_email: str
    customer_name: str
    order_number: str
    items: List[OrderItem]
    total_amount: float
    order_date: datetime

class ReturnRequestCreate(BaseModel):
    order_id: str
    reason: ReturnReason
    items_to_return: List[OrderItem]
    notes: Optional[str] = None

class ReturnRuleCreate(BaseModel):
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 1

class ReturnStatusUpdate(BaseModel):
    status: ReturnStatus
    notes: Optional[str] = None
    tracking_number: Optional[str] = None

class ReturnResolution(BaseModel):
    resolution_type: str  # refund, exchange, store_credit
    notes: Optional[str] = None
    refund_method: Optional[str] = "original_payment"  # stripe, manual, original_payment
    exchange_items: Optional[List[Dict[str, Any]]] = None
    
class RuleSimulationRequest(BaseModel):
    order_data: Dict[str, Any]
    return_data: Dict[str, Any]
    
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20
    search: Optional[str] = None
    status_filter: Optional[str] = "all"
    sort_by: str = "created_at"
    sort_order: str = "desc"

# Middleware for tenant context
async def get_tenant_id(x_tenant_id: str = Header(None)) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    # Verify tenant exists
    tenant = await db.tenants.find_one({"id": x_tenant_id, "is_active": True})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return x_tenant_id

# Tenant Management
@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant_data: TenantCreate):
    tenant = Tenant(**tenant_data.dict())
    tenant.settings = {
        "return_window_days": 30,
        "auto_approve_exchanges": True,
        "require_photos": False,
        "brand_color": "#3b82f6",
        "custom_message": "We're here to help with your return!"
    }
    await db.tenants.insert_one(tenant.dict())
    return tenant

@api_router.get("/tenants", response_model=List[Tenant])
async def get_tenants():
    tenants = await db.tenants.find({"is_active": True}).to_list(100)
    return [Tenant(**tenant) for tenant in tenants]

@api_router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str):
    tenant = await db.tenants.find_one({"id": tenant_id, "is_active": True})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return Tenant(**tenant)

@api_router.put("/tenants/{tenant_id}/settings")
async def update_tenant_settings(
    tenant_id: str, 
    settings: Dict[str, Any],
    current_tenant: str = Depends(get_tenant_id)
):
    """Update tenant settings"""
    
    # Verify tenant access
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Access denied to tenant settings")
    
    # Validate settings
    valid_settings = {
        "return_window_days", "auto_approve_exchanges", "require_photos",
        "brand_color", "custom_message", "restocking_fee_percent",
        "store_credit_bonus_percent", "logo_url"
    }
    
    filtered_settings = {k: v for k, v in settings.items() if k in valid_settings}
    
    if not filtered_settings:
        raise HTTPException(status_code=400, detail="No valid settings provided")
    
    # Update settings atomically
    result = await db.tenants.update_one(
        {"id": tenant_id, "is_active": True},
        {
            "$set": {
                "settings": filtered_settings,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get updated tenant
    updated_tenant = await db.tenants.find_one({"id": tenant_id})
    
    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": updated_tenant["settings"]
    }

@api_router.get("/tenants/{tenant_id}/settings")
async def get_tenant_settings(
    tenant_id: str,
    current_tenant: str = Depends(get_tenant_id)
):
    """Get tenant settings"""
    
    if tenant_id != current_tenant:
        raise HTTPException(status_code=403, detail="Access denied to tenant settings")
    
    tenant = await db.tenants.find_one({"id": tenant_id, "is_active": True})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant_id": tenant_id,
        "settings": tenant.get("settings", {}),
        "name": tenant.get("name"),
        "domain": tenant.get("domain")
    }

# Products Management
@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, tenant_id: str = Depends(get_tenant_id)):
    product = Product(**product_data.dict(), tenant_id=tenant_id)
    await db.products.insert_one(product.dict())
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(tenant_id: str = Depends(get_tenant_id)):
    products = await db.products.find({"tenant_id": tenant_id}).to_list(1000)
    return [Product(**product) for product in products]

# Orders Management
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, tenant_id: str = Depends(get_tenant_id)):
    order = Order(**order_data.dict(), tenant_id=tenant_id)
    await db.orders.insert_one(order.dict())
    return order

@api_router.get("/orders")
async def get_orders(
    tenant_id: str = Depends(get_tenant_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by customer name, email, or order number"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    date_from: Optional[str] = Query(None, description="Filter orders from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter orders to date (YYYY-MM-DD)"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get paginated orders with filtering and search for real Shopify data"""
    
    # Build query
    query = {"tenant_id": tenant_id}
    
    # Add search filter
    if search:
        search_pattern = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"customer_name": search_pattern},
            {"customer_email": search_pattern},
            {"order_number": search_pattern},
            {"email": search_pattern}
        ]
    
    # Add status filter  
    if status_filter and status_filter != "all":
        if status_filter == "paid":
            query["financial_status"] = "paid"
        elif status_filter == "fulfilled":
            query["fulfillment_status"] = "fulfilled"
        elif status_filter == "unfulfilled":
            query["fulfillment_status"] = {"$in": ["unfulfilled", "partial"]}
        elif status_filter == "cancelled":
            query["financial_status"] = "cancelled"
    
    # Add date filters
    if date_from or date_to:
        date_query = {}
        if date_from:
            try:
                date_query["$gte"] = datetime.fromisoformat(date_from)
            except ValueError:
                pass
        if date_to:
            try:
                date_query["$lte"] = datetime.fromisoformat(date_to + "T23:59:59")
            except ValueError:
                pass
        if date_query:
            query["created_at"] = date_query
    
    # Count total items
    total_items = await db.orders.count_documents(query)
    
    # Calculate pagination
    total_pages = (total_items + limit - 1) // limit
    skip = (page - 1) * limit
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    sort_field = sort_by if sort_by in ["created_at", "updated_at", "total_price", "order_number"] else "created_at"
    
    # Get orders
    orders_cursor = db.orders.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
    orders = await orders_cursor.to_list(length=limit)
    
    # Transform data for response
    orders_data = []
    for order in orders:
        # Handle both synced order format and legacy format
        order_data = {
            "id": order.get("order_id", order.get("id")),
            "order_number": order.get("order_number", order.get("name")),
            "customer_name": order.get("customer_name", "Unknown"),
            "customer_email": order.get("customer_email", order.get("email")),
            "financial_status": order.get("financial_status", "unknown"),
            "fulfillment_status": order.get("fulfillment_status", "unfulfilled"),
            "total_price": float(order.get("total_price", "0") or 0),
            "currency_code": order.get("currency_code", "USD"),
            "line_items": order.get("line_items", []),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            "billing_address": order.get("billing_address"),
            "shipping_address": order.get("shipping_address"),
            "fulfillments": order.get("fulfillments", []),
            "has_returns": False  # TODO: Check for linked returns
        }
        orders_data.append(order_data)
    
    return {
        "items": orders_data,
        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@api_router.get("/orders/{order_id}")
async def get_order(order_id: str, tenant_id: str = Depends(get_tenant_id)):
    """Get single order details with real Shopify data"""
    
    # Find order by either order_id or id field
    order = await db.orders.find_one({
        "$or": [
            {"order_id": order_id, "tenant_id": tenant_id},
            {"id": order_id, "tenant_id": tenant_id}
        ]
    })
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get related returns for this order
    returns_cursor = db.return_requests.find({
        "order_id": order_id,
        "tenant_id": tenant_id
    })
    returns = await returns_cursor.to_list(length=100)
    
    # Transform order data
    order_data = {
        "id": order.get("order_id", order.get("id")),
        "order_number": order.get("order_number", order.get("name")),
        "customer_name": order.get("customer_name", "Unknown"),
        "customer_email": order.get("customer_email", order.get("email")),
        "customer_id": order.get("customer_id"),
        "financial_status": order.get("financial_status", "unknown"),
        "fulfillment_status": order.get("fulfillment_status", "unfulfilled"),
        "total_price": float(order.get("total_price", "0") or 0),
        "currency_code": order.get("currency_code", "USD"),
        "line_items": order.get("line_items", []),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
        "processed_at": order.get("processed_at"),
        "billing_address": order.get("billing_address"),
        "shipping_address": order.get("shipping_address"),
        "fulfillments": order.get("fulfillments", []),
        "returns": returns,
        "shopify_order_url": f"https://{tenant_id.replace('.myshopify.com', '')}.myshopify.com/admin/orders/{order.get('order_id', order.get('id'))}"
    }
    
    return order_data

@api_router.post("/orders/lookup")
async def lookup_order(
    order_lookup: Dict[str, str],
    tenant_id: str = Header(None, alias="X-Tenant-Id")
):
    """Lookup order for customer return portal - no tenant validation needed"""
    
    order_number = order_lookup.get("order_number", "").strip()
    email = order_lookup.get("email", "").strip().lower()
    
    if not order_number or not email:
        raise HTTPException(status_code=400, detail="Order number and email are required")
    
    # Search across all tenants if no specific tenant provided
    query = {
        "$or": [
            {"customer_email": {"$regex": f"^{email}$", "$options": "i"}},
            {"email": {"$regex": f"^{email}$", "$options": "i"}}
        ],
        "$and": [
            {
                "$or": [
                    {"order_number": order_number},
                    {"name": order_number}
                ]
            }
        ]
    }
    
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    order = await db.orders.find_one(query)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify email matches (case insensitive)
    order_email = (order.get("customer_email") or order.get("email", "")).lower()
    if order_email != email:
        raise HTTPException(status_code=403, detail="Email does not match order records")
    
    # Return order data for return portal
    return {
        "id": order.get("order_id", order.get("id")),
        "order_number": order.get("order_number", order.get("name")),
        "customer_name": order.get("customer_name", "Unknown"),
        "customer_email": order.get("customer_email", order.get("email")),
        "created_at": order.get("created_at"),
        "total_price": float(order.get("total_price", "0") or 0),
        "currency_code": order.get("currency_code", "USD"),
        "line_items": order.get("line_items", []),
        "tenant_id": order.get("tenant_id"),
        "eligible_for_return": True  # TODO: Add return eligibility logic
    }

# Return Rules Engine
@api_router.post("/return-rules", response_model=ReturnRule)
async def create_return_rule(rule_data: ReturnRuleCreate, tenant_id: str = Depends(get_tenant_id)):
    rule = ReturnRule(**rule_data.dict(), tenant_id=tenant_id)
    await db.return_rules.insert_one(rule.dict())
    return rule

@api_router.get("/return-rules", response_model=List[ReturnRule])
async def get_return_rules(tenant_id: str = Depends(get_tenant_id)):
    rules = await db.return_rules.find({"tenant_id": tenant_id, "is_active": True}).sort("priority", 1).to_list(100)
    return [ReturnRule(**rule) for rule in rules]

@api_router.post("/return-rules/simulate")
async def simulate_return_rules(
    simulation_request: RuleSimulationRequest, 
    tenant_id: str = Depends(get_tenant_id)
):
    """Simulate rules application and return step-by-step explanation"""
    
    # Get rules for tenant
    rules = await db.return_rules.find({"tenant_id": tenant_id, "is_active": True}).sort("priority", 1).to_list(100)
    
    if not rules:
        return {
            "steps": [],
            "final_status": "requested",
            "final_notes": "No rules configured",
            "rule_applied": None,
            "total_rules_evaluated": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Simulate rules application
    simulation_result = RulesEngine.simulate_rules_application(
        return_request=simulation_request.return_data,
        order=simulation_request.order_data,
        rules=rules
    )
    
    return simulation_result

# Returns Management
@api_router.post("/returns", response_model=ReturnRequest)
async def create_return_request(return_data: ReturnRequestCreate, tenant_id: str = Depends(get_tenant_id)):
    # Validate order exists
    order = await db.orders.find_one({"id": return_data.order_id, "tenant_id": tenant_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_obj = Order(**order)
    
    # Calculate refund amount
    refund_amount = sum(item.price * item.quantity for item in return_data.items_to_return)
    
    # Create return request
    return_request = ReturnRequest(
        **return_data.dict(),
        tenant_id=tenant_id,
        customer_email=order_obj.customer_email,
        customer_name=order_obj.customer_name,
        refund_amount=refund_amount
    )
    
    # Apply rules engine (enhanced)
    rules = await db.return_rules.find({"tenant_id": tenant_id, "is_active": True}).sort("priority", 1).to_list(100)
    if rules:
        # Use enhanced rules engine for consistent processing
        simulation_result = RulesEngine.simulate_rules_application(
            return_request=return_request.dict(),
            order=order_obj.dict(),
            rules=rules
        )
        
        # Apply the final status from rules simulation
        return_request.status = ReturnStatus(simulation_result["final_status"])
        if simulation_result["final_notes"]:
            return_request.notes = simulation_result["final_notes"]
    
    await db.return_requests.insert_one(return_request.dict())
    
    # Create initial audit log entry
    audit_entry = ReturnStateMachine.create_audit_log_entry(
        return_id=return_request.id,
        from_status="new",
        to_status=return_request.status.value,
        notes=f"Return request created. {return_request.notes or ''}".strip(),
        user_id="customer"
    )
    await db.audit_logs.insert_one(audit_entry)
    
    return return_request


@api_router.get("/returns", response_model=Dict[str, Any])
async def get_return_requests(
    tenant_id: str = Depends(get_tenant_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: str = Query("all"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    """Get paginated and filtered return requests"""
    
    # Build filter query
    filter_query = {"tenant_id": tenant_id}
    
    # Status filter
    if status_filter != "all":
        filter_query["status"] = status_filter
    
    # Search filter
    if search:
        filter_query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"customer_email": {"$regex": search, "$options": "i"}},
            {"order_id": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count for pagination
    total_count = await db.return_requests.count_documents(filter_query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit
    
    # Build sort order
    sort_direction = -1 if sort_order == "desc" else 1
    
    # Get paginated results with stable sort (always include _id as secondary sort)
    returns_cursor = db.return_requests.find(filter_query).sort([
        (sort_by, sort_direction),
        ("_id", sort_direction)  # Stable sort
    ]).skip(skip).limit(limit)
    
    returns = await returns_cursor.to_list(limit)
    
    return {
        "items": [ReturnRequest(**ret) for ret in returns],
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": limit,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filters_applied": {
            "search": search,
            "status_filter": status_filter,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }

@api_router.get("/returns/{return_id}", response_model=ReturnRequest)
async def get_return_request(return_id: str, tenant_id: str = Depends(get_tenant_id)):
    return_req = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    return ReturnRequest(**return_req)

@api_router.put("/returns/{return_id}/status", response_model=ReturnRequest)
async def update_return_status(return_id: str, status_update: ReturnStatusUpdate, tenant_id: str = Depends(get_tenant_id)):
    return_req = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    current_status = return_req["status"]
    new_status = status_update.status.value
    
    # Validate state transition (allow idempotent updates)
    if current_status != new_status and not ReturnStateMachine.can_transition(current_status, new_status):
        valid_transitions = ReturnStateMachine.get_valid_transitions(current_status)
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid transition from {current_status} to {new_status}. Valid transitions: {valid_transitions}"
        )
    
    # Update the return request (idempotent)
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    if status_update.notes:
        update_data["notes"] = status_update.notes
    if status_update.tracking_number:
        update_data["tracking_number"] = status_update.tracking_number
    
    # Perform atomic update
    result = await db.return_requests.update_one(
        {"id": return_id, "tenant_id": tenant_id, "status": current_status},  # Include current status for concurrency
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        # Either return was already updated or not found - check which
        current_return = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
        if current_return and current_return["status"] == new_status:
            # Already updated - idempotent operation
            return ReturnRequest(**current_return)
        else:
            raise HTTPException(status_code=409, detail="Return status was modified by another request")
    
    # Create audit log entry
    audit_entry = ReturnStateMachine.create_audit_log_entry(
        return_id=return_id,
        from_status=current_status,
        to_status=new_status,
        notes=status_update.notes,
        user_id="system"  # In real app, get from authentication
    )
    await db.audit_logs.insert_one(audit_entry)
    
    updated_return = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    return ReturnRequest(**updated_return)

@api_router.post("/returns/{return_id}/resolve")
async def resolve_return(
    return_id: str, 
    resolution: ReturnResolution, 
    tenant_id: str = Depends(get_tenant_id)
):
    """Process return resolution (refund/exchange/store credit)"""
    
    # Validate return exists and is in correct state
    return_req = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    if return_req["status"] not in ["received", "approved"]:
        raise HTTPException(status_code=400, detail="Return must be received or approved before resolution")
    
    resolution_record = None
    
    # Process based on resolution type
    if resolution.resolution_type == "refund":
        resolution_record = ReturnResolutionHandler.create_refund_record(
            return_request_id=return_id,
            amount=return_req["refund_amount"],
            method=resolution.refund_method,
            notes=resolution.notes
        )
        
        # Store resolution record
        await db.resolutions.insert_one(resolution_record)
        
        # Update return status to resolved
        await db.return_requests.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": {
                "status": "resolved",
                "updated_at": datetime.utcnow(),
                "resolution_type": "refund",
                "resolution_id": resolution_record["id"]
            }}
        )
        
        message = f"{'Refund processed' if resolution.refund_method != 'manual' else 'Manual refund recorded'}"
        
    elif resolution.resolution_type == "exchange":
        if not resolution.exchange_items:
            raise HTTPException(status_code=400, detail="Exchange items required for exchange resolution")
            
        resolution_record = ReturnResolutionHandler.create_exchange_record(
            return_request_id=return_id,
            original_items=return_req["items_to_return"],
            new_items=resolution.exchange_items,
            notes=resolution.notes
        )
        
        await db.resolutions.insert_one(resolution_record)
        
        await db.return_requests.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": {
                "status": "resolved",
                "updated_at": datetime.utcnow(),
                "resolution_type": "exchange",
                "resolution_id": resolution_record["id"]
            }}
        )
        
        message = f"Exchange processed - Outbound order: {resolution_record['outbound_order_id']}"
        
    elif resolution.resolution_type == "store_credit":
        resolution_record = ReturnResolutionHandler.create_store_credit_record(
            return_request_id=return_id,
            customer_email=return_req["customer_email"],
            amount=return_req["refund_amount"],
            notes=resolution.notes
        )
        
        await db.resolutions.insert_one(resolution_record)
        
        await db.return_requests.update_one(
            {"id": return_id, "tenant_id": tenant_id},
            {"$set": {
                "status": "resolved", 
                "updated_at": datetime.utcnow(),
                "resolution_type": "store_credit",
                "resolution_id": resolution_record["id"]
            }}
        )
        
        message = "Store credit issued"
        
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution type")
    
    # Create audit log
    audit_entry = ReturnStateMachine.create_audit_log_entry(
        return_id=return_id,
        from_status=return_req["status"],
        to_status="resolved",
        notes=f"{resolution.resolution_type.title()} resolution: {message}",
        user_id="system"
    )
    await db.audit_logs.insert_one(audit_entry)
    
    return {
        "success": True,
        "message": message,
        "resolution_id": resolution_record["id"],
        "resolution_type": resolution.resolution_type
    }

@api_router.get("/returns/{return_id}/audit-log")
async def get_return_audit_log(return_id: str, tenant_id: str = Depends(get_tenant_id)):
    """Get audit log/timeline for a return request"""
    
    # Verify return exists
    return_req = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    # Get audit log entries (convert ObjectId to string for JSON serialization)
    audit_logs_cursor = db.audit_logs.find({"return_id": return_id}).sort("timestamp", 1)
    audit_logs = []
    async for log in audit_logs_cursor:
        # Convert ObjectId to string
        if '_id' in log:
            log['_id'] = str(log['_id'])
        audit_logs.append(log)
    
    return {
        "return_id": return_id,
        "timeline": audit_logs,
        "current_status": return_req["status"]
    }

# Analytics
@api_router.get("/analytics", response_model=Analytics)
async def get_analytics(tenant_id: str = Depends(get_tenant_id), days: int = 30):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get return requests in period
    returns = await db.return_requests.find({
        "tenant_id": tenant_id,
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(1000)
    
    total_returns = len(returns)
    total_refunds = sum(ret.get("refund_amount", 0) for ret in returns)
    
    # Calculate exchange rate (using resolved returns with exchange resolution)
    exchanges = [ret for ret in returns if ret.get("status") == ReturnStatus.RESOLVED and ret.get("resolution_type") == "exchange"]
    exchange_rate = (len(exchanges) / total_returns * 100) if total_returns > 0 else 0
    
    # Top return reasons
    reason_counts = {}
    for ret in returns:
        reason = ret.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    top_return_reasons = [
        {"reason": reason, "count": count, "percentage": count / total_returns * 100}
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return Analytics(
        tenant_id=tenant_id,
        total_returns=total_returns,
        total_refunds=total_refunds,
        exchange_rate=exchange_rate,
        avg_processing_time=2.5,  # Mock data
        top_return_reasons=top_return_reasons,
        period_start=start_date,
        period_end=end_date
    )

# Mock Shopify Integration
@api_router.post("/shopify/webhook/orders/create")
async def shopify_order_webhook(order_data: Dict[str, Any], x_tenant_id: str = Header(None)):
    """Mock Shopify order webhook handler"""
    if not x_tenant_id:
        return {"status": "error", "message": "X-Tenant-Id required"}
    
    # This would normally parse Shopify order data
    # For now, return success
    return {"status": "received", "order_id": order_data.get("id")}

@app.get("/_health")
async def health_check():
    """Health check endpoint for deployment verification"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@api_router.get("/")
async def root():
    return {"message": "Returns Management SaaS API", "version": "1.0.0"}

@api_router.get("/health")  
async def api_health():
    """API health check endpoint for deployment verification"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Include routers in the api_router first
api_router.include_router(auth_router)
api_router.include_router(webhook_router)
api_router.include_router(testing_router)
api_router.include_router(shopify_router)
api_router.include_router(enhanced_router)
api_router.include_router(returns_router)
api_router.include_router(shopify_test_router)
api_router.include_router(rules_router)
api_router.include_router(unified_returns_router)

# Then include the api_router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Health check endpoint (no authentication required)
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if client else "disconnected"
    }