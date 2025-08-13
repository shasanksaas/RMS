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
from src.controllers.shopify_test_controller import router as shopify_test_router
from src.controllers.rules_controller import router as rules_router
from src.controllers.unified_returns_controller import router as unified_returns_router
from src.controllers.shopify_integration_controller import router as integration_router
from src.controllers.orders_controller_enhanced import router as orders_enhanced_router
from src.controllers.returns_controller_enhanced import router as returns_enhanced_router
from src.controllers.portal_returns_controller import router as portal_returns_router
from src.controllers.admin_returns_controller import router as admin_returns_router
from src.controllers.order_lookup_controller import router as order_lookup_router
from src.controllers.admin_drafts_controller import router as admin_drafts_router
# Elite-Grade Controllers
from src.controllers.elite_portal_returns_controller import router as elite_portal_router
from src.controllers.elite_admin_returns_controller import router as elite_admin_router
from src.controllers.users_controller import router as users_router
# Tenant Management Controllers
from src.controllers.tenant_controller import router as tenant_management_router
from src.controllers.public_signup_controller import router as public_signup_router

# Shopify OAuth Controllers  
from src.controllers.shopify_oauth_controller import router as shopify_oauth_router, integration_router as shopify_integration_router
from src.controllers.shopify_webhook_controller import router as shopify_webhook_router

# Admin Tenant Management Controller
from src.controllers.tenant_admin_controller import router as tenant_admin_router

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
# Import tenant isolation middleware
from src.middleware.tenant_isolation import TenantIsolationMiddleware
from src.middleware.empty_state_handler import empty_state_handler
from src.services.tenant_service_enhanced import enhanced_tenant_service

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

# Create the main app without a prefix and disable automatic redirect
app = FastAPI(title="Returns Management SaaS API", version="1.0.0", redirect_slashes=False)

@app.on_event("startup")
async def startup_db_client():
    global repository_factory
    repository_factory = RepositoryFactory(db)
    print("✅ Database connected and repository factory initialized")
    
    # Initialize environment configuration
    from src.config.environment import env_config
    await env_config.initialize()
    print("✅ Environment configuration initialized")

# Add security middleware
@app.middleware("http")
async def security_and_audit_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Skip middleware for health checks and static files
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json", "/api/", "/api/health", "/api/config"] or request.url.path.startswith("/static"):
        response = await call_next(request)
        return response
    
    # Skip tenant validation for certain endpoints
    skip_tenant_validation = [
        "/api/tenants",  # Tenant creation/listing
        "/api/admin/tenants",  # Admin tenant management
        "/api/auth/",    # Auth endpoints
        "/api/test/",    # Testing endpoints
        "/api/webhooks/", # Webhook endpoints
        "/api/enhanced/", # Enhanced features
        "/api/shopify/",   # Shopify endpoints
        "/api/shopify-test/",  # Shopify connectivity test endpoints
        "/api/elite/",   # Elite controllers
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

# Orders Management - MOVED TO orders_controller_enhanced.py
# @api_router.post("/orders", response_model=Order)
# async def create_order(order_data: OrderCreate, tenant_id: str = Depends(get_tenant_id)):
#     order = Order(**order_data.dict(), tenant_id=tenant_id)
#     await db.orders.insert_one(order.dict())
#     return order

# @api_router.get("/orders")
# Moved to orders_controller_enhanced.py for better organization
# async def get_orders(
#     tenant_id: str = Depends(get_tenant_id),
#     page: int = Query(1, ge=1, description="Page number"),
#     limit: int = Query(20, ge=1, le=100, description="Items per page"),
#     search: Optional[str] = Query(None, description="Search by customer name, email, or order number"),
#     status_filter: Optional[str] = Query(None, description="Filter by order status"),
#     date_from: Optional[str] = Query(None, description="Filter orders from date (YYYY-MM-DD)"),
#     date_to: Optional[str] = Query(None, description="Filter orders to date (YYYY-MM-DD)"),
#     sort_by: str = Query("created_at", description="Sort field"),
#     sort_order: str = Query("desc", description="Sort order (asc/desc)")
# ):
    # MOVED TO orders_controller_enhanced.py

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
    returns_cursor = db.returns.find({
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

# ALL RETURNS ROUTES MOVED TO returns_controller_enhanced.py
# This ensures the enhanced controller handles all /returns requests

# Analytics
@api_router.get("/analytics", response_model=Analytics)
async def get_analytics(tenant_id: str = Depends(get_tenant_id), days: int = 30):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get return requests in period
    returns = await db.returns.find({
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
    from datetime import datetime
    from src.config.environment import env_config
    
    # Get configuration summary
    config_summary = env_config.get_config_summary()
    
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "environment": config_summary
    }

@api_router.get("/config")
async def get_configuration():
    """Get current environment configuration for debugging"""
    from src.config.environment import env_config
    await env_config.initialize()
    
    config = env_config.get_config_summary()
    
    # Don't expose sensitive information
    return {
        "app_url": config["app_url"],
        "redirect_uri": config["redirect_uri"],
        "shopify_configured": config["shopify_configured"],
        "environment": config["environment"],
        "initialized": config["initialized"]
    }

# Include routers in the api_router first
# api_router.include_router(auth_router)  # DISABLED: Legacy auth router conflicting with Shopify OAuth
api_router.include_router(public_signup_router)  # Public merchant signup
api_router.include_router(users_router)  # User management system
api_router.include_router(tenant_management_router)  # Admin tenant management
api_router.include_router(tenant_admin_router)  # Real tenant CRUD with impersonation

# Shopify OAuth & Integration Routes (MAIN - PRODUCTION READY)
api_router.include_router(shopify_oauth_router)  # Shopify OAuth flow
api_router.include_router(shopify_integration_router)  # Shopify integration status/resync endpoints
api_router.include_router(shopify_webhook_router)  # Shopify webhooks

# Legacy routes (temporarily disabled to prevent conflicts)
# api_router.include_router(integration_router)  # OLD - conflicts with shopify_integration_router
# api_router.include_router(webhook_router)  # OLD - conflicts with shopify_webhook_router
# Testing & Development Routes
api_router.include_router(testing_router)  # Keep for development
api_router.include_router(enhanced_router)
api_router.include_router(orders_enhanced_router)
api_router.include_router(returns_enhanced_router)
api_router.include_router(portal_returns_router)
api_router.include_router(admin_returns_router)
# api_router.include_router(order_lookup_router)  # Disabled - conflicts with returns_enhanced_router prefix
api_router.include_router(admin_drafts_router)
# Elite-Grade Controllers
api_router.include_router(elite_portal_router)
api_router.include_router(elite_admin_router)
api_router.include_router(shopify_test_router)
api_router.include_router(rules_router)
api_router.include_router(unified_returns_router)

# Then include the api_router in the main app
app.include_router(api_router)

# Add CORS middleware FIRST (before tenant isolation)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant isolation middleware AFTER CORS
tenant_isolation = TenantIsolationMiddleware()
app.middleware("http")(tenant_isolation)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize dependency container and tenant service on startup"""
    from src.infrastructure.services.dependency_container import initialize_container
    initialize_container(db)
    logger.info("✅ Dependency container initialized with Elite-Grade architecture")
    
    # Initialize enhanced tenant service
    enhanced_tenant_service.db = db
    await enhanced_tenant_service.initialize()
    logger.info("✅ Enhanced tenant service initialized with strict isolation")

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