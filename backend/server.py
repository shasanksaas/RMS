from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

# Import new controllers
from src.controllers.shopify_controller import router as shopify_router
from src.controllers.enhanced_features_controller import router as enhanced_router
from src.controllers.tenant_controller import router as tenant_router
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Returns Management SaaS API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"

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

@api_router.get("/orders", response_model=List[Order])
async def get_orders(tenant_id: str = Depends(get_tenant_id)):
    orders = await db.orders.find({"tenant_id": tenant_id}).sort("created_at", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, tenant_id: str = Depends(get_tenant_id)):
    order = await db.orders.find_one({"id": order_id, "tenant_id": tenant_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

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
    
    # Apply rules engine (simplified)
    rules = await db.return_rules.find({"tenant_id": tenant_id, "is_active": True}).sort("priority", 1).to_list(100)
    for rule_data in rules:
        rule = ReturnRule(**rule_data)
        if await apply_return_rule(rule, return_request, order_obj):
            break
    
    await db.return_requests.insert_one(return_request.dict())
    return return_request

async def apply_return_rule(rule: ReturnRule, return_request: ReturnRequest, order: Order) -> bool:
    """Apply a return rule to a return request"""
    conditions = rule.conditions
    
    # Example rule conditions
    if "max_days_since_order" in conditions:
        days_since_order = (datetime.utcnow() - order.order_date).days
        if days_since_order > conditions["max_days_since_order"]:
            return_request.status = ReturnStatus.DENIED
            return_request.notes = f"Return window expired ({days_since_order} days > {conditions['max_days_since_order']} days)"
            return True
    
    if "auto_approve_reasons" in conditions:
        if return_request.reason in conditions["auto_approve_reasons"]:
            return_request.status = ReturnStatus.APPROVED
            return_request.notes = "Auto-approved based on return reason"
            return True
    
    if "require_manual_review_reasons" in conditions:
        if return_request.reason in conditions["require_manual_review_reasons"]:
            return_request.status = ReturnStatus.REQUESTED
            return_request.notes = "Requires manual review"
            return True
    
    return False

@api_router.get("/returns", response_model=List[ReturnRequest])
async def get_return_requests(tenant_id: str = Depends(get_tenant_id)):
    returns = await db.return_requests.find({"tenant_id": tenant_id}).sort("created_at", -1).to_list(1000)
    return [ReturnRequest(**ret) for ret in returns]

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
    
    # Update the return request
    update_data = {
        "status": status_update.status,
        "updated_at": datetime.utcnow()
    }
    
    if status_update.notes:
        update_data["notes"] = status_update.notes
    if status_update.tracking_number:
        update_data["tracking_number"] = status_update.tracking_number
    
    await db.return_requests.update_one(
        {"id": return_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated_return = await db.return_requests.find_one({"id": return_id, "tenant_id": tenant_id})
    return ReturnRequest(**updated_return)

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
    
    # Calculate exchange rate
    exchanges = [ret for ret in returns if ret.get("status") == ReturnStatus.EXCHANGED]
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

@api_router.get("/")
async def root():
    return {"message": "Returns Management SaaS API", "version": "1.0.0"}

# Include new routers
app.include_router(api_router)
app.include_router(shopify_router)
app.include_router(enhanced_router)

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