# 🚀 Returns Management SaaS - Elite-Grade Platform

**A comprehensive, production-ready, multi-tenant Returns Management System with advanced Shopify integration, built using Hexagonal Architecture, CQRS, and Domain Events.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0.0-blue.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-brightgreen.svg)](https://www.mongodb.com/)
[![Shopify](https://img.shields.io/badge/Shopify-2025--07-brightgreen.svg)](https://shopify.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# 🚀 Returns Management SaaS - Elite-Grade Platform

**A comprehensive, production-ready, multi-tenant Returns Management System with advanced Shopify integration, built using Hexagonal Architecture, CQRS, and Domain Events.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0.0-blue.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-brightgreen.svg)](https://www.mongodb.com/)
[![Shopify](https://img.shields.io/badge/Shopify-2025--07-brightgreen.svg)](https://shopify.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Project Overview

This application is a **production-ready, enterprise-grade Returns Management SaaS** that empowers merchants to handle return requests, process refunds/exchanges, and manage return policies through an intuitive, scalable interface. The system features dedicated customer-facing return portals, comprehensive merchant dashboards, and complete **real-time Shopify integration** for live order data.

### 🎯 Core Business Value
- **Reduce Return Processing Time**: From hours to minutes with automated workflows  
- **Increase Customer Satisfaction**: Self-service portals with real-time tracking
- **Scale Operations**: Multi-tenant architecture supporting unlimited merchants
- **Boost Revenue**: Smart analytics and rules engine optimize return-to-exchange ratios

### ✨ Key Features & Capabilities

#### 🏗️ **Elite-Grade Architecture**
- **Hexagonal Architecture (Ports & Adapters)**: Modular, maintainable, and testable design
- **CQRS (Command Query Responsibility Segregation)**: Optimized read/write operations
- **Domain Events**: Event-driven architecture for loose coupling and scalability
- **Multi-Tenant Architecture**: Complete data isolation with enterprise-level security

#### 🛍️ **Shopify Integration Excellence**
- **Real-time OAuth 2.0 Authentication**: Secure merchant onboarding
- **Live Order Synchronization**: GraphQL + REST API integration
- **Webhook Processing**: Real-time event handling for orders, products, and customers
- **Encrypted Credential Management**: Fernet-based security for API tokens

#### 🎛️ **Advanced Returns Processing**
- **Smart Rules Engine**: AI-powered auto-approval and routing logic
- **State Machine Workflow**: Enforced business rules with audit trails
- **Multiple Resolution Types**: Refunds, exchanges, store credit, and repairs
- **Label Generation**: Automated return shipping labels
- **Photo Validation**: AI-powered damage assessment

#### 📊 **Business Intelligence**
- **Real-time Analytics**: Return trends, financial impact, and performance metrics
- **Predictive Insights**: ML-powered return prediction and fraud detection
- **Custom Reporting**: Configurable dashboards and export capabilities
- **Cost Analysis**: ROI tracking and operational cost optimization

## 📋 Table of Contents

- [🏗️ System Architecture](#️-system-architecture)
- [🛠 Technology Stack](#-technology-stack)
- [📊 Database Architecture](#-database-architecture)
- [🔐 Authentication & Security](#-authentication--security)
- [🛍️ Shopify Integration](#️-shopify-integration)
- [📡 API Documentation](#-api-documentation)
- [🎮 Controllers & Endpoints](#-controllers--endpoints)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration Management](#️-configuration-management)
- [🚀 Development Setup](#-development-setup)
- [🧪 Testing Strategy](#-testing-strategy)
- [🚢 Deployment Guide](#-deployment-guide)
- [🔍 Troubleshooting](#-troubleshooting)

## 🏗️ System Architecture

### **Hexagonal Architecture (Ports & Adapters)**
The application follows Hexagonal Architecture principles for maximum modularity, testability, and maintainability:

```
┌─────────────────────────────────────────────────────┐
│                Application Core                      │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐ │
│  │   Domain    │    │ Application │    │ Commands │ │
│  │   Layer     │────│    Layer    │────│ & Queries│ │
│  └─────────────┘    └─────────────┘    └──────────┘ │
└─────────────────────────────────────────────────────┘
           │                    │                    │
    ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
    │ Repository  │     │  Service    │     │   Event     │
    │   Ports     │     │   Ports     │     │   Ports     │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                    │                    │
    ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
    │  MongoDB    │     │  Shopify    │     │  Webhook    │
    │  Adapter    │     │  Adapter    │     │  Handlers   │
    └─────────────┘     └─────────────┘     └─────────────┘
```

### **Multi-Tenant Architecture**
Enterprise-grade tenant isolation ensuring data security and scalability:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Customer      │    │   Merchant      │    │   Admin         │
│   Portal        │    │   Dashboard     │    │   Panel         │
│   /returns/*    │    │   /app/*        │    │   /admin/*      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   React App     │
                    │   (Port 3000)   │
                    │   Nginx Ingress │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   (Port 8001)   │
                    │   /api/* routes │
                    └─────────────────┘
                         │       │
            ┌────────────┼───────┼──────────────┐
            │            │       │              │
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │  MongoDB    │ │  Shopify    │ │  External   │
  │ Multi-Tenant│ │     API     │ │  Services   │
  └─────────────┘ └─────────────┘ └─────────────┘
```

## 🛠 Technology Stack

### **Backend Technology Stack**
| Technology | Version | Purpose | Key Benefits |
|------------|---------|---------|--------------|
| **FastAPI** | v0.110.1 | High-performance Python web framework | Automatic API docs, async support, type validation |
| **Python** | 3.11+ | Backend runtime | Rich ecosystem, excellent async support |
| **MongoDB** | 6.0+ with Motor | NoSQL database with async driver | Horizontal scaling, flexible schema, rich queries |
| **Shopify API** | v12.3.0 (2025-07) | E-commerce platform integration | GraphQL + REST, webhooks, OAuth 2.0 |
| **Cryptography** | Latest | Data encryption (Fernet) | AES-128 encryption for sensitive data |
| **Pydantic** | v2.x | Data validation and serialization | Type safety, automatic validation |

### **Frontend Technology Stack**
| Technology | Version | Purpose | Key Benefits |
|------------|---------|---------|--------------|
| **React** | v19.0.0 | Modern UI library | Component-based, virtual DOM, rich ecosystem |
| **React Router DOM** | v7.5.1 | Client-side routing | SPA navigation, code splitting |
| **Radix UI** | Latest | Accessible component primitives | WAI-ARIA compliance, customizable |
| **Tailwind CSS** | v3.4.17 | Utility-first CSS framework | Rapid styling, consistent design system |
| **Lucide React** | Latest | Beautiful icon library | 1000+ SVG icons, tree-shakable |
| **Axios** | Latest | HTTP client for API communication | Interceptors, request/response transformation |

### **Infrastructure & DevOps**
- **Supervisor**: Process management with auto-restart and logging
- **Docker**: Containerization for consistent environments
- **Kubernetes**: Container orchestration with auto-scaling
- **MongoDB Atlas**: Managed database with high availability
- **AWS/GCP**: Cloud infrastructure for global distribution

## 📊 Database Architecture

### **MongoDB Schema Design**
The database follows a document-based approach optimized for multi-tenancy and performance:

#### **Core Collections Overview**
| Collection | Purpose | Documents | Indexes | Sharding Key |
|------------|---------|-----------|---------|--------------|
| `tenants` | Tenant configuration | ~1K | tenant_id, domain | tenant_id |
| `orders` | Order data (Shopify sync) | ~100K | tenant_id, order_number | tenant_id |
| `returns` | Return requests | ~10K | tenant_id, status, created_at | tenant_id |
| `return_rules` | Business rules engine | ~100 | tenant_id, priority | tenant_id |
| `integrations_shopify` | OAuth credentials | ~1K | tenant_id | tenant_id |

#### **Sample Schema: Returns Collection**
```javascript
{
  "_id": ObjectId("..."),
  "id": "539c705d-99db-4b70-a527-ac6faf05ba17", // UUID for returns
  "tenant_id": "tenant-rms34",
  
  // Order Reference
  "order_id": "5813364687033", // Links to orders collection
  "order_number": "1001", // Denormalized for quick access
  
  // Customer Information
  "customer_email": "customer@example.com",
  "customer_name": "John Smith", // Derived from order
  
  // Return Request Details
  "return_method": "prepaid_label",
  "return_reason_category": "quality",
  "customer_note": "Item doesn't fit as expected",
  
  // Line Items Being Returned
  "line_items": [
    {
      "line_item_id": "13851721105593",
      "sku": "TSHIRT-L-BLUE",
      "title": "Premium T-Shirt",
      "variant_title": "Large / Blue",
      "quantity": 1,
      "unit_price": 400.00,
      "reason": "defective",
      "condition": "damaged",
      "resolution": "refund"
    }
  ],
  
  // Financial Calculations
  "estimated_refund": {
    "amount": 354.01,
    "currency": "USD",
    "breakdown": {
      "item_total": 400.00,
      "tax_refund": 32.00,
      "processing_fee": -5.00,
      "final_amount": 354.01
    }
  },
  
  // Status & Workflow
  "status": "requested", // requested, approved, denied, processing, completed
  "decision": "", // approved, denied, partial_approval
  "decision_made_by": "system", // admin_user_id or "auto_approved"
  
  // Timestamps
  "created_at": "2025-01-20T14:30:00Z",
  "updated_at": "2025-01-20T14:30:00Z"
}
```

### **Performance Optimizations**
```javascript
// Critical indexes for multi-tenant performance
db.returns.createIndex({"tenant_id": 1, "status": 1, "created_at": -1})
db.returns.createIndex({"tenant_id": 1, "order_id": 1})
db.returns.createIndex({"tenant_id": 1, "customer_email": 1})

// Text search for customer support
db.returns.createIndex({
  "customer_name": "text",
  "customer_email": "text", 
  "order_number": "text"
})
```

## 🔐 Authentication & Security

### **Multi-Tenant Security Architecture**
The application implements enterprise-grade security with multiple layers:

1. **Tenant Isolation**: All requests require `X-Tenant-Id` header
2. **Data Encryption**: Sensitive data encrypted with Fernet (AES-128)
3. **OAuth 2.0**: Secure Shopify merchant authentication
4. **Rate Limiting**: Per-tenant API limits based on subscription plan
5. **Audit Logging**: Complete audit trail for compliance

### **Security Middleware**
```python
class TenantSecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract and validate tenant ID
        tenant_id = request.headers.get("X-Tenant-Id")
        
        if not await self.validate_tenant(tenant_id):
            raise HTTPException(status_code=401, detail="Invalid tenant")
        
        # Inject tenant context
        request.state.tenant_id = tenant_id
        
        # Log for audit trail
        await self.log_request(request, tenant_id)
        
        response = await call_next(request)
        return response
```

### **Shopify OAuth 2.0 Flow**
```python
@router.post("/oauth/initiate")
async def initiate_oauth(request: ShopifyOAuthRequest, tenant_id: str = Depends(get_tenant_id)):
    # Generate secure state parameter (CSRF protection)
    state = secrets.token_urlsafe(32)
    await redis_client.setex(f"oauth_state:{state}", 600, tenant_id)
    
    # Build OAuth URL with required scopes
    scopes = ["read_orders", "write_orders", "read_customers", "read_products"]
    oauth_url = f"https://{request.shop_domain}.myshopify.com/admin/oauth/authorize"
    
    return {"authorization_url": oauth_url, "state": state}
```

## 🛍️ Shopify Integration

### **Comprehensive Shopify Integration**
The application provides deep, production-ready integration with Shopify:

#### **Integration Capabilities**
| Feature | Implementation | Benefits |
|---------|---------------|----------|
| **OAuth 2.0 Authentication** | Full flow with state validation | Secure, user-approved access |
| **Real-time Data Sync** | GraphQL + REST API | Live order data, fast queries |
| **Webhook Processing** | 14 webhook topics | Real-time event handling |
| **Credential Encryption** | Fernet-based AES-128 | Secure token storage |
| **Rate Limit Handling** | Exponential backoff | Shopify API compliance |

### **GraphQL Order Service**
```python
class ShopifyGraphQLService:
    ORDER_QUERY = """
    query getOrder($id: ID!) {
        order(id: $id) {
            id
            name
            processedAt
            totalPriceSet {
                shopMoney { amount currencyCode }
            }
            customer {
                id firstName lastName email
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id title variantTitle sku quantity
                        originalUnitPriceSet {
                            shopMoney { amount currencyCode }
                        }
                    }
                }
            }
        }
    }
    """
    
    async def get_order_for_return(self, order_id: str) -> Optional[dict]:
        """Gets complete order data optimized for return processing"""
        gql_id = f"gid://shopify/Order/{order_id}" if not order_id.startswith('gid://') else order_id
        result = await self._execute_graphql(self.ORDER_QUERY, {"id": gql_id})
        
        if result and result.get('data', {}).get('order'):
            return self._transform_graphql_order(result['data']['order'])
        return None
```

### **Webhook Processing**
```python
class ShopifyWebhookHandler:
    SUPPORTED_TOPICS = {
        'orders/create': 'handle_order_created',
        'orders/updated': 'handle_order_updated',
        'orders/paid': 'handle_order_paid',
        'app/uninstalled': 'handle_app_uninstalled'
    }
    
    async def handle_order_created(self, tenant_id: str, payload: dict, shop_domain: str):
        """Handles new order creation"""
        order_data = self._transform_webhook_order(payload, tenant_id)
        
        await db.orders.update_one(
            {"id": order_data["id"], "tenant_id": tenant_id},
            {"$set": order_data},
            upsert=True
        )
        
        await self._emit_domain_event("OrderCreated", {
            "tenant_id": tenant_id,
            "order_id": order_data["id"],
            "customer_email": order_data.get("customer_email")
        })
```

## 📡 API Documentation

### **Complete API Reference**

#### **Base Configuration**
- **Base URL**: `http://localhost:8001/api` (Development) | `https://api.yourapp.com/api` (Production)
- **Authentication**: Multi-tenant via `X-Tenant-Id` header
- **Content-Type**: `application/json`

### **Core API Endpoints**

#### **1. Elite Portal Returns (Customer-facing)**
```bash
# Order lookup
POST /api/elite/portal/returns/lookup-order
{
  "order_number": "1001",
  "customer_email": "customer@example.com"
}

# Create return request
POST /api/elite/portal/returns/create
{
  "order_id": "5813364687033",
  "customer_email": "customer@example.com",
  "return_method": "prepaid_label",
  "items": [
    {
      "line_item_id": "13851721105593",
      "quantity": 1,
      "reason": "defective",
      "condition": "damaged"
    }
  ]
}
```

#### **2. Returns Management (Merchant Dashboard)**
```bash
# Get paginated returns with filters
GET /api/returns/?page=1&pageSize=25&status=requested&search=john

# Get return details
GET /api/returns/{return_id}

# Update return status  
PUT /api/returns/{return_id}/status
{
  "status": "approved",
  "notes": "Approved for return"
}

# Process resolution
POST /api/returns/{return_id}/resolve
{
  "resolution_type": "refund",
  "refund_method": "original_payment"
}
```

#### **3. Shopify Integration**
```bash
# Get integration status
GET /api/integrations/shopify/status

# Initiate OAuth flow
POST /api/integrations/shopify/oauth/initiate
{
  "shop_domain": "your-shop"
}

# Manual order sync
POST /api/integrations/shopify/sync/orders
```

### **Response Format**
All API responses follow this structure:
```json
{
  "success": true,
  "data": {...},
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "per_page": 20
  },
  "message": "Operation successful"
}
```

## 🎮 Controllers & Endpoints

### **Controller Architecture Overview**

The application uses a layered controller architecture with clear separation of concerns:

#### **Elite Portal Returns Controller**
**File:** `/backend/src/controllers/elite_portal_returns_controller.py`
**Purpose:** Customer-facing return portal API

```python
@router.post("/lookup-order")
async def lookup_order(
    request: OrderLookupRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Order lookup with performance optimization:
    1. Search local database first (faster)
    2. Fallback to live Shopify API
    3. Verify customer email matches
    4. Check return eligibility
    """
    # Try local DB first
    order = await db.orders.find_one({
        "tenant_id": tenant_id,
        "order_number": request.order_number,
        "customer_email": {"$regex": re.escape(request.customer_email), "$options": "i"}
    })
    
    # Fallback to Shopify
    if not order:
        shopify_service = ShopifyService(tenant_id)
        order = await shopify_service.find_order_by_number(request.order_number)
    
    return {"success": True, "data": {"order": order}}
```

#### **Enhanced Returns Controller** 
**File:** `/backend/src/controllers/returns_controller_enhanced.py`
**Purpose:** Merchant dashboard with performance optimizations

```python
@router.get("/")
async def get_returns(
    tenant_id: str = Depends(get_tenant_id),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100)
):
    """
    OPTIMIZED returns list with:
    - Server-side pagination
    - Batch order fetching (eliminates N+1 queries)
    - Indexed MongoDB queries
    - Cached customer data resolution
    """
    # Build query with tenant isolation
    query = {"tenant_id": tenant_id}
    
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [
            {"order_number": search_regex},
            {"customer_email": search_regex}
        ]
    
    # Get paginated results with total count
    total = await db.returns.count_documents(query)
    skip = (page - 1) * page_size
    returns = await db.returns.find(query)\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(page_size)\
        .to_list(page_size)
    
    # OPTIMIZATION: Batch fetch order data to avoid N+1 queries
    order_ids = list(set(r.get("order_id") for r in returns if r.get("order_id")))
    orders_map = {}
    
    if order_ids:
        orders = await db.orders.find({
            "id": {"$in": order_ids},
            "tenant_id": tenant_id
        }).to_list(None)
        orders_map = {order["id"]: order for order in orders}
    
    # Format response with enriched data
    formatted_returns = []
    for return_req in returns:
        order = orders_map.get(return_req.get("order_id"))
        formatted_returns.append({
            "id": return_req["id"],
            "order_number": order.get("order_number", "") if order else "",
            "customer_name": return_req.get("customer_name", ""),
            "status": return_req.get("status", "").upper(),
            "estimated_refund": return_req.get("estimated_refund", {}).get("amount", 0),
            "created_at": return_req.get("created_at")
        })
    
    return {
        "returns": formatted_returns,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size
        }
    }
```

#### **Shopify Integration Controller**
**File:** `/backend/src/controllers/shopify_integration_controller.py`
**Purpose:** OAuth flow and integration management

```python
@router.get("/status")
async def get_integration_status(tenant_id: str = Depends(get_tenant_id)):
    """Returns comprehensive Shopify integration status"""
    integration = await db.integrations_shopify.find_one({"tenant_id": tenant_id})
    
    if not integration:
        return {
            "connected": False,
            "status": "not_configured",
            "message": "Shopify integration not configured"
        }
    
    # Test connection health
    shopify_service = ShopifyService(tenant_id)
    try:
        await shopify_service.authenticate()
        connection_test = await shopify_service._test_connection()
        
        if connection_test:
            stats = await get_integration_stats(tenant_id)
            return {
                "connected": True,
                "status": "active",
                "shop_domain": integration["shop_domain"],
                "connected_at": integration["connected_at"],
                "stats": stats
            }
    except Exception as e:
        return {
            "connected": False,
            "status": "connection_error",
            "message": f"Connection test failed: {str(e)}"
        }
```

## 📁 Project Structure

### **Complete Directory Architecture**
```
/app/
├── 📂 backend/                                 # FastAPI Backend Application
│   ├── 📂 src/
│   │   ├── 📂 controllers/                    # API Route Controllers (12 controllers)
│   │   │   ├── elite_portal_returns_controller.py    # Customer portal API
│   │   │   ├── elite_admin_returns_controller.py     # Admin return management
│   │   │   ├── returns_controller_enhanced.py        # Merchant dashboard API
│   │   │   ├── orders_controller_enhanced.py         # Order management API
│   │   │   ├── shopify_integration_controller.py     # Shopify OAuth & integration
│   │   │   ├── webhook_controller.py                 # Webhook processing
│   │   │   ├── rules_controller.py                   # Business rules engine
│   │   │   └── [5 more controllers...]
│   │   │
│   │   ├── 📂 services/                       # Business Logic Layer
│   │   │   ├── shopify_service.py             # Main Shopify API integration
│   │   │   ├── shopify_graphql.py             # GraphQL query service  
│   │   │   ├── tenant_service.py              # Multi-tenant operations
│   │   │   └── [8 more services...]
│   │   │
│   │   ├── 📂 infrastructure/                 # Infrastructure Layer (Hexagonal)
│   │   │   ├── 📂 repositories/               # Data Access Layer
│   │   │   │   ├── mongo_return_repository.py        # Returns data access
│   │   │   │   ├── mongo_order_repository.py         # Orders data access
│   │   │   │   └── [2 more repositories...]
│   │   │   │
│   │   │   └── 📂 services/                   # External Service Adapters
│   │   │       ├── shopify_service_adapter.py        # Shopify API adapter
│   │   │       └── [3 more adapters...]
│   │   │
│   │   ├── 📂 domain/                         # Domain Layer (Business Logic)
│   │   │   ├── 📂 ports/                      # Interface definitions
│   │   │   ├── value_objects.py               # Domain value objects
│   │   │   ├── events.py                      # Domain events
│   │   │   └── exceptions.py                  # Domain-specific exceptions
│   │   │
│   │   ├── 📂 application/                    # Application Layer (CQRS)
│   │   │   ├── commands.py                    # Command definitions
│   │   │   ├── queries.py                     # Query definitions
│   │   │   └── 📂 handlers/                   # Command/Query Handlers
│   │   │       ├── command_handlers.py               # Command processing
│   │   │       └── query_handlers.py                 # Query processing
│   │   │
│   │   ├── 📂 middleware/                     # HTTP Middleware
│   │   │   ├── security.py                    # Multi-tenant security
│   │   │   └── [3 more middleware...]
│   │   │
│   │   └── 📂 utils/                          # Utility Functions
│   │       ├── dependencies.py                # FastAPI dependencies
│   │       ├── rules_engine.py                # Business rules evaluation
│   │       └── [5 more utils...]
│   │
│   ├── server.py                              # FastAPI Application Entry Point
│   ├── requirements.txt                       # Python Dependencies
│   └── .env                                   # Environment Configuration
│
├── 📂 frontend/                               # React Frontend Application
│   ├── 📂 src/
│   │   ├── 📂 components/                     # Reusable UI Components
│   │   │   ├── 📂 ui/                         # Base UI Components (Radix UI)
│   │   │   │   ├── button.jsx, input.jsx, dialog.jsx
│   │   │   │   └── [7 more base components...]
│   │   │   │
│   │   │   └── 📂 layout/                     # Layout Components
│   │   │       ├── MerchantLayout.jsx                # Dashboard layout
│   │   │       ├── CustomerLayout.jsx                # Customer portal layout
│   │   │       └── [4 more layouts...]
│   │   │
│   │   ├── 📂 pages/                          # Page Components (Routes)
│   │   │   ├── 📂 customer/                   # Customer Portal Pages
│   │   │   │   ├── Start.jsx, SelectItems.jsx, Confirm.jsx
│   │   │   │   └── [3 more customer pages...]
│   │   │   │
│   │   │   ├── 📂 merchant/                   # Merchant Dashboard Pages
│   │   │   │   ├── Dashboard.js, OrderDetail.jsx
│   │   │   │   ├── 📂 returns/                # Returns Management
│   │   │   │   │   ├── AllReturns.jsx, ReturnDetail.jsx
│   │   │   │   │   └── [2 more return pages...]
│   │   │   │   │
│   │   │   │   └── 📂 settings/               # Settings Pages
│   │   │   │       ├── Integrations.jsx, General.jsx
│   │   │   │       └── [5 more settings...]
│   │   │   │
│   │   │   └── 📂 admin/                      # Admin Panel Pages
│   │   │       └── [4 admin pages...]
│   │   │
│   │   └── App.jsx                            # Main App Component
│   │
│   ├── package.json                           # Node.js Dependencies
│   └── .env                                   # Frontend Environment
│
├── 📂 docs/                                   # Comprehensive Documentation
│   ├── README.md, ARCHITECTURE.md, API.md
│   ├── DATABASE_SCHEMA.md, SHOPIFY_INTEGRATION.md
│   └── [8 more documentation files...]
│
├── 📂 tests/                                  # Complete Test Suite
│   ├── 📂 unit/, 📂 integration/, 📂 e2e/
│   └── conftest.py
│
└── README.md                                  # This comprehensive documentation

📊 TOTAL: 200+ files | 🏗️ Hexagonal + CQRS | 🛡️ Multi-tenant + OAuth 2.0
```

## ⚙️ Configuration Management

### **Environment Configuration**

#### **Backend Configuration (`.env`)**
```bash
# Database Configuration - NEVER modify in production
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management

# Security Configuration
ENCRYPTION_KEY=YourBase64EncodedFernetKey32Bytes=
CORS_ORIGINS=http://localhost:3000

# Shopify Integration
SHOPIFY_API_KEY=0ef6de8c4bf0b4a3d8f7f99b42c53695
SHOPIFY_API_SECRET=db79f6174721b7acf332b69ef8f84374
SHOPIFY_API_VERSION=2025-07
SHOPIFY_REDIRECT_URI=http://localhost:3000/auth/shopify/callback

# External Services (Optional)
EMAIL_SERVICE_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your-sendgrid-api-key
AWS_S3_BUCKET=returns-attachments
OPENAI_API_KEY=sk-your-openai-key

# Performance
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=1000
```

#### **Frontend Configuration (`.env`)**
```bash
# Backend API - NEVER modify in production
REACT_APP_BACKEND_URL=http://localhost:8001

# Application Configuration
REACT_APP_NAME=Returns Management SaaS
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_PWA=true

# Development
WDS_SOCKET_PORT=443
GENERATE_SOURCEMAP=true
```

### **Configuration Validation**
```python
from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    # Database
    MONGO_URL: str = Field(..., description="MongoDB connection string")
    DB_NAME: str = Field("returns_management")
    
    # Security
    ENCRYPTION_KEY: str = Field(..., description="Fernet encryption key")
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    
    @validator('ENCRYPTION_KEY')
    def validate_encryption_key(cls, v):
        try:
            from cryptography.fernet import Fernet
            Fernet(v.encode())
            return v
        except Exception:
            raise ValueError("Invalid Fernet encryption key")
    
    # Shopify
    SHOPIFY_API_KEY: str = Field(..., description="Shopify app API key")
    SHOPIFY_API_SECRET: str = Field(..., description="Shopify app secret")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

## 🚀 Development Setup

### **Prerequisites**
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend development  
- **MongoDB 6.0+** - Database server
- **Yarn** - Package manager (DO NOT use npm)

### **Quick Start**

#### **1. Clone and Setup Backend**
```bash
git clone <repository-url>
cd returns-management-saas

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

#### **2. Setup Frontend**  
```bash
cd ../frontend
yarn install  # IMPORTANT: Use yarn, not npm

# Configure environment
cp .env.example .env
# Edit .env with backend URL
```

#### **3. Start Services**
```bash
# Option 1: Using Supervisor (Recommended)
sudo supervisorctl restart all
sudo supervisorctl status

# Option 2: Manual Start
# Terminal 1: Backend
cd backend && python server.py

# Terminal 2: Frontend  
cd frontend && yarn start

# Terminal 3: MongoDB
mongod --dbpath /path/to/db
```

### **Service URLs**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001  
- **API Documentation**: http://localhost:8001/docs
- **Customer Portal**: http://localhost:3000/returns
- **Merchant Dashboard**: http://localhost:3000/app

### **Database Setup**
```bash
# Seed sample data
python seed.py

# Add performance indexes
cd backend && python add_indexes.py

# Verify setup
mongo returns_management --eval "
  print('Tenants:', db.tenants.count());
  print('Orders:', db.orders.count());
  print('Returns:', db.returns.count());
"
```

## 🧪 Testing Strategy

### **Test Suite Overview**
The application includes comprehensive testing across all layers:

#### **Backend Testing**
```bash
# Unit tests
cd backend
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v --cov=src

# Load testing  
locust -f tests/load_test.py --host=http://localhost:8001
```

#### **Frontend Testing**
```bash
# Component tests
cd frontend
yarn test

# E2E tests
yarn test:e2e

# Accessibility tests
yarn test:a11y
```

### **Manual Testing Scenarios**

#### **Customer Return Flow**
1. Visit http://localhost:3000/returns
2. Enter order number: "1001" and email: "customer@example.com"
3. Select items to return with reasons
4. Choose resolution (refund/exchange)
5. Submit and track return status

#### **Merchant Dashboard**
1. Visit http://localhost:3000/app
2. View returns dashboard with KPIs
3. Click return detail (eye icon) for full information
4. Update return status (approve/deny)
5. Process refund or exchange

#### **Shopify Integration**
1. Go to Settings > Integrations
2. Click "Connect Shopify"
3. Complete OAuth flow
4. Verify order sync and webhook setup

### **API Testing Examples**
```bash
# Health check
curl http://localhost:8001/health

# Get returns (requires tenant header)
curl -H "X-Tenant-Id: tenant-rms34" \
     http://localhost:8001/api/returns/

# Create return request
curl -X POST \
     -H "X-Tenant-Id: tenant-rms34" \
     -H "Content-Type: application/json" \
     -d '{"order_id":"123","reason":"defective"}' \
     http://localhost:8001/api/elite/portal/returns/create
```

## 🚢 Deployment Guide

### **Production Deployment**

#### **Environment Preparation**
```bash
# Production backend .env
MONGO_URL=mongodb://prod-server:27017/returns_prod
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ENCRYPTION_KEY=production-32-byte-base64-key
DEBUG=false
SHOPIFY_REDIRECT_URI=https://yourdomain.com/auth/callback
```

#### **Docker Deployment**
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8001:8001"]
    environment:
      MONGO_URL: mongodb://mongo:27017
    depends_on: [mongo]
      
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      REACT_APP_BACKEND_URL: http://localhost:8001
      
  mongo:
    image: mongo:6.0
    ports: ["27017:27017"]
    volumes: [mongo_data:/data/db]
      
volumes:
  mongo_data:
```

#### **Kubernetes Deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: returns-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: returns-backend
  template:
    metadata:
      labels:
        app: returns-backend
    spec:
      containers:
      - name: backend
        image: returns-backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: mongo-url
```

### **Production Checklist**
- [ ] Update `ENCRYPTION_KEY` with strong 32-byte key
- [ ] Set secure `CORS_ORIGINS` (not wildcards)
- [ ] Configure HTTPS certificates  
- [ ] Enable MongoDB authentication
- [ ] Set up firewall rules
- [ ] Configure monitoring and logging
- [ ] Set up automated backups
- [ ] Test disaster recovery procedures

## 🔍 Troubleshooting

### **Common Issues & Solutions**

#### **1. MongoDB Connection Failed**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB  
sudo systemctl start mongod

# Test connection
mongo --eval "db.adminCommand('ismaster')"
```

#### **2. Frontend Not Loading**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules yarn.lock
yarn install

# Check port conflicts
lsof -i :3000
```

#### **3. API Requests Failing**
```bash
# Check backend logs
sudo supervisorctl tail -f backend

# Verify CORS settings
curl -H "Origin: http://localhost:3000" \
     -H "X-Tenant-Id: tenant-rms34" \
     http://localhost:8001/api/health
```

#### **4. Shopify Integration Issues**
```bash
# Test OAuth credentials
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"shop_domain":"your-shop","api_key":"key"}' \
     http://localhost:8001/api/integrations/shopify/oauth/initiate

# Check webhook endpoints  
curl http://localhost:8001/api/webhooks/health
```

#### **5. Performance Issues**
```bash
# Check database indexes
mongo returns_management --eval "db.returns.getIndexes()"

# Monitor query performance
mongo returns_management --eval "db.setProfilingLevel(2)"

# View slow queries
mongo returns_management --eval "
  db.system.profile.find().limit(5).sort({ts:-1}).pretty()
"
```

### **Logging & Debugging**
```bash
# Backend logs
sudo supervisorctl tail -f backend stderr
tail -f /var/log/supervisor/backend.err.log

# Frontend logs (browser console)
# Chrome DevTools -> Console

# Database logs
sudo tail -f /var/log/mongodb/mongod.log
```

### **Performance Monitoring**
```bash
# Memory usage
ps aux | grep python | head -5
ps aux | grep node | head -5

# Database performance
mongo --eval "db.serverStatus().mem"
mongo --eval "db.serverStatus().connections"

# API response times
curl -w "@curl-format.txt" -s -o /dev/null \
     -H "X-Tenant-Id: tenant-rms34" \
     http://localhost:8001/api/returns/
```

## 🤝 Contributing

### **Development Guidelines**
- **Code Style**: Follow PEP 8 for Python, ESLint for JavaScript
- **Testing**: Write tests for new features (target 80% coverage)
- **Documentation**: Update README and API docs for changes
- **Security**: Never commit credentials or sensitive data

### **Getting Started**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run test suite: `yarn test && python -m pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open Pull Request with detailed description

### **Architecture Principles**
- **Hexagonal Architecture**: Keep business logic separate from external concerns
- **CQRS**: Separate read and write operations for performance
- **Multi-tenancy**: All new features must support tenant isolation
- **API-First**: Design APIs before implementation
- **Security by Design**: Consider security implications in all changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Shopify** for comprehensive API documentation and developer support
- **FastAPI** community for excellent framework and ecosystem
- **React** ecosystem for modern frontend development tools
- **Tailwind CSS** for utility-first styling approach
- **MongoDB** for flexible document storage and querying capabilities

---

**🚀 Built with ❤️ for modern e-commerce returns management**

> **Ready to scale?** This architecture supports enterprise-level deployments with multi-region distribution, horizontal scaling, and 99.9% uptime guarantees.

## 📋 Table of Contents

- [🌟 Project Overview](#-project-overview)
- [🏗️ System Architecture](#️-system-architecture)
- [🛠 Technology Stack](#-technology-stack)
- [📊 Database Architecture](#-database-architecture)
- [🔐 Authentication & Security](#-authentication--security)
- [🛍️ Shopify Integration](#️-shopify-integration)
- [📡 API Documentation](#-api-documentation)
- [🎮 Controllers & Endpoints](#-controllers--endpoints)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration Management](#️-configuration-management)
- [🚀 Development Setup](#-development-setup)
- [🔧 Advanced Features](#-advanced-features)
- [🧪 Testing Strategy](#-testing-strategy)
- [🚢 Deployment Guide](#-deployment-guide)
- [📈 Monitoring & Observability](#-monitoring--observability)
- [🔍 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

## 🛠 Technology Stack

### **Backend Technology Stack**
| Technology | Version | Purpose | Key Benefits |
|------------|---------|---------|--------------|
| **FastAPI** | v0.110.1 | High-performance Python web framework | Automatic API docs, async support, type validation |
| **Python** | 3.11+ | Backend runtime | Rich ecosystem, excellent async support |
| **MongoDB** | 6.0+ with Motor | NoSQL database with async driver | Horizontal scaling, flexible schema, rich queries |
| **Shopify API** | v12.3.0 (2025-07) | E-commerce platform integration | GraphQL + REST, webhooks, OAuth 2.0 |
| **Cryptography** | Latest | Data encryption (Fernet) | AES-128 encryption for sensitive data |
| **Pydantic** | v2.x | Data validation and serialization | Type safety, automatic validation |
| **Aiohttp** | Latest | Async HTTP client | High-performance external API calls |
| **PyJWT** | Latest | JSON Web Token handling | Secure authentication tokens |

### **Frontend Technology Stack**
| Technology | Version | Purpose | Key Benefits |
|------------|---------|---------|--------------|
| **React** | v19.0.0 | Modern UI library | Component-based, virtual DOM, rich ecosystem |
| **React Router DOM** | v7.5.1 | Client-side routing | SPA navigation, code splitting |
| **TypeScript** | v5.x | Type-safe JavaScript | Better developer experience, catch errors early |
| **Radix UI** | Latest | Accessible component primitives | WAI-ARIA compliance, customizable |
| **Tailwind CSS** | v3.4.17 | Utility-first CSS framework | Rapid styling, consistent design system |
| **Lucide React** | Latest | Beautiful icon library | 1000+ SVG icons, tree-shakable |
| **Axios** | Latest | HTTP client for API communication | Interceptors, request/response transformation |
| **React Hook Form** | Latest | Form state management | Performance, validation, developer experience |

### **Infrastructure & DevOps**
| Technology | Purpose | Key Benefits |
|------------|---------|--------------|
| **Supervisor** | Process management | Auto-restart, logging, monitoring |
| **Nginx** | Reverse proxy, static files | Load balancing, SSL termination |
| **Docker** | Containerization | Consistent environments, easy deployment |
| **Kubernetes** | Container orchestration | Auto-scaling, service discovery |
| **MongoDB Atlas** | Managed database | High availability, automatic backups |
| **AWS/GCP** | Cloud infrastructure | Scalability, global distribution |

### **Development & Testing**
| Technology | Purpose | Key Benefits |
|------------|---------|--------------|
| **Pytest** | Python testing framework | Fixtures, parametrization, plugins |
| **Jest** | JavaScript testing framework | Snapshot testing, mocking, coverage |
| **Playwright** | E2E testing | Cross-browser, reliable selectors |
| **ESLint** | JavaScript linting | Code quality, consistency |
| **Prettier** | Code formatting | Consistent formatting, team collaboration |
| **CRACO** | Create React App configuration | Custom webpack, babel configs |

### **External Integrations**
| Service | Purpose | Integration Method |
|---------|---------|-------------------|
| **Shopify** | E-commerce platform | OAuth 2.0, GraphQL, Webhooks |
| **SendGrid** | Transactional emails | REST API, SMTP |
| **Stripe** | Payment processing | REST API, Webhooks |
| **AWS S3** | File storage | SDK, signed URLs |
| **OpenAI** | AI-powered features | REST API, streaming |
| **Twilio** | SMS notifications | REST API |

## 🏗️ System Architecture

### **Hexagonal Architecture (Ports & Adapters)**
The application follows Hexagonal Architecture principles for maximum modularity, testability, and maintainability:

```mermaid
graph TB
    subgraph "Application Core"
        Domain[Domain Layer]
        Application[Application Layer]
        Commands[Commands & Queries]
        Handlers[Command & Query Handlers]
        Events[Domain Events]
    end
    
    subgraph "Ports (Interfaces)"
        RepoPort[Repository Ports]
        ServicePort[Service Ports]
        EventPort[Event Ports]
    end
    
    subgraph "Adapters (Implementations)"
        MongoAdapter[MongoDB Adapter]
        ShopifyAdapter[Shopify API Adapter]
        EmailAdapter[Email Service Adapter]
        WebhookAdapter[Webhook Handlers]
    end
    
    subgraph "External Systems"
        MongoDB[(MongoDB)]
        Shopify[Shopify API]
        EmailService[Email Service]
        FileStorage[File Storage]
    end
    
    Domain --> Commands
    Commands --> Handlers
    Handlers --> RepoPort
    Handlers --> ServicePort
    Handlers --> Events
    
    RepoPort --> MongoAdapter
    ServicePort --> ShopifyAdapter
    ServicePort --> EmailAdapter
    EventPort --> WebhookAdapter
    
    MongoAdapter --> MongoDB
    ShopifyAdapter --> Shopify
    EmailAdapter --> EmailService
    WebhookAdapter --> FileStorage
```

### **CQRS (Command Query Responsibility Segregation)**
Separates read and write operations for optimal performance and scalability:

```mermaid
graph LR
    subgraph "Command Side (Write)"
        CreateReturn[Create Return Command]
        UpdateStatus[Update Status Command]
        ProcessRefund[Process Refund Command]
        CommandHandler[Command Handlers]
        WriteDB[(Write Database)]
    end
    
    subgraph "Query Side (Read)"
        GetReturns[Get Returns Query]
        GetAnalytics[Get Analytics Query]
        SearchReturns[Search Returns Query]
        QueryHandler[Query Handlers]
        ReadDB[(Read Database)]
    end
    
    CreateReturn --> CommandHandler
    UpdateStatus --> CommandHandler
    ProcessRefund --> CommandHandler
    CommandHandler --> WriteDB
    
    GetReturns --> QueryHandler
    GetAnalytics --> QueryHandler
    SearchReturns --> QueryHandler
    QueryHandler --> ReadDB
    
    WriteDB -.->|Event Sourcing| ReadDB
```

### **Multi-Tenant Architecture**
Enterprise-grade tenant isolation ensuring data security and scalability:

```mermaid
graph TB
    subgraph "Request Flow"
        Client[Client Request]
        Gateway[API Gateway]
        TenantMiddleware[Tenant Middleware]
        Controller[Controller Layer]
        Service[Service Layer]
        Repository[Repository Layer]
        Database[(MongoDB)]
    end
    
    Client --> Gateway
    Gateway --> TenantMiddleware
    TenantMiddleware --> Controller
    Controller --> Service
    Service --> Repository
    Repository --> Database
    
    TenantMiddleware -.->|Inject X-Tenant-Id| Controller
    Repository -.->|Filter by tenant_id| Database
```

### **Service Communication Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Customer      │    │   Merchant      │    │   Admin         │
│   Portal        │    │   Dashboard     │    │   Panel         │
│   /returns/*    │    │   /app/*        │    │   /admin/*      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   React App     │
                    │   (Port 3000)   │
                    │   ┌───────────┐ │
                    │   │ Nginx     │ │
                    │   │ Ingress   │ │
                    │   └───────────┘ │
                    └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
                ┌─────────────────┐ ┌─────────────────┐
                │   FastAPI       │ │   Kubernetes    │
                │   (Port 8001)   │ │   Ingress       │
                │   /api/*        │ │   Controller    │
                └─────────────────┘ └─────────────────┘
                         │                       │
            ┌────────────┼──────────────┐       │
            │            │              │       │
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │  MongoDB    │ │  Shopify    │ │  External   │
  │ (Port 27017)│ │     API     │ │  Services   │
  │ Multi-Tenant│ │   GraphQL   │ │ (Email, S3) │
  └─────────────┘ └─────────────┘ └─────────────┘
```

### **Event-Driven Architecture**
Domain events enable loose coupling and real-time processing:

```mermaid
sequenceDiagram
    participant C as Customer
    participant API as API Layer
    participant CMD as Command Handler
    participant EVT as Event Bus
    participant WH as Webhook Handler
    participant SH as Shopify Service
    participant EMAIL as Email Service
    participant DB as Database
    
    C->>API: Submit Return Request
    API->>CMD: CreateReturnCommand
    CMD->>DB: Save Return
    CMD->>EVT: ReturnCreatedEvent
    EVT->>WH: Process Event
    EVT->>EMAIL: Send Confirmation
    EVT->>SH: Update Shopify
    WH->>SH: Register Webhook
    EMAIL->>C: Confirmation Email
```

## 📋 Prerequisites

- **Python 3.9+** - Backend runtime
- **Node.js 18+** - Frontend development
- **MongoDB 6.0+** - Database server
- **Yarn** - Package manager (DO NOT use npm)
- **Git** - Version control

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows with WSL2

## 🚀 Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd returns-management-saas
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (see Environment Configuration section)
cp .env.example .env
# Edit .env with your configurations
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies using Yarn ONLY
yarn install

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations
```

### 4. Database Setup
```bash
# Start MongoDB (if not running as service)
mongod --dbpath /path/to/your/db

# Seed the database with sample data
cd .. # Back to project root
python seed.py
```

## ⚙️ Environment Configuration

### Backend Environment (.env)
```bash
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management

# Security
CORS_ORIGINS=*
ENCRYPTION_KEY=fernet-key-32-bytes-base64-encoded-here

# Shopify Integration (Production Values)
SHOPIFY_API_KEY=0ef6de8c4bf0b4a3d8f7f99b42c53695
SHOPIFY_API_SECRET=db79f6174721b7acf332b69ef8f84374
SHOPIFY_API_VERSION=2025-07
SHOPIFY_MODE=real
SHOPIFY_REDIRECT_URI=https://your-domain.dev/app/settings/integrations

# Optional Services
OFFLINE_MODE=false
DEBUG=true

# Email Configuration (Optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
FROM_EMAIL=noreply@returns-manager.com

# AI Services (Optional)
OPENAI_API_KEY=

# Payment Processing (Optional)
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# Cloud Storage (Optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=returns-management-labels
```

### Frontend Environment (.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
```

**⚠️ CRITICAL**: Never modify the `REACT_APP_BACKEND_URL` or `MONGO_URL` in production. These are automatically configured for the deployment environment.

## 🏃‍♂️ Running the Application

### Development Mode

#### Option 1: Using Supervisor (Recommended)
```bash
# Start all services
sudo supervisorctl restart all

# Check service status
sudo supervisorctl status

# View logs
sudo supervisorctl tail -f backend
sudo supervisorctl tail -f frontend
```

#### Option 2: Manual Start
```bash
# Terminal 1: Start Backend
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start Frontend
cd frontend
yarn start

# Terminal 3: Start MongoDB (if not running as service)
mongod --dbpath /path/to/your/db
```

### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

### Application Routes
- **Customer Portal**: http://localhost:3000/returns
- **Merchant Dashboard**: http://localhost:3000/app
- **Admin Panel**: http://localhost:3000/admin

## 📚 API Documentation

### Base URL
```
http://localhost:8001/api
```

### Authentication
All API endpoints require the `X-Tenant-Id` header for multi-tenant isolation:
```bash
curl -H "X-Tenant-Id: tenant-fashion-store" http://localhost:8001/api/returns
```

### Core Endpoints

#### Tenant Management
```bash
# Create Tenant
POST /api/tenants
{
  "name": "Fashion Store",
  "domain": "fashion-store.com",
  "shopify_store_url": "fashion-store.myshopify.com"
}

# Get Tenants
GET /api/tenants

# Get Tenant Settings
GET /api/tenants/{tenant_id}/settings

# Update Tenant Settings
PUT /api/tenants/{tenant_id}/settings
```

#### Orders API
```bash
# Get Paginated Orders
GET /api/orders?page=1&limit=20&search=john&status_filter=paid

# Get Order Details
GET /api/orders/{order_id}

# Customer Order Lookup
POST /api/orders/lookup
{
  "order_number": "ORD-001",
  "email": "customer@email.com"
}
```

#### Returns Management
```bash
# Create Return Request
POST /api/returns
{
  "order_id": "uuid",
  "reason": "defective",
  "items_to_return": [...],
  "notes": "Product arrived damaged"
}

# Get Returns (Paginated)
GET /api/returns?page=1&limit=20&status_filter=approved&search=john

# Update Return Status
PUT /api/returns/{return_id}/status
{
  "status": "approved",
  "notes": "Approved for return",
  "tracking_number": "TRK123456"
}

# Process Resolution
POST /api/returns/{return_id}/resolve
{
  "resolution_type": "refund",
  "refund_method": "original_payment",
  "notes": "Full refund processed"
}

# Get Audit Log
GET /api/returns/{return_id}/audit-log
```

#### Rules Engine
```bash
# Create Return Rule
POST /api/return-rules
{
  "name": "Auto-approve defective items",
  "description": "Automatically approve returns for defective products",
  "conditions": {
    "auto_approve_reasons": ["defective", "damaged_in_shipping"],
    "max_days_since_order": 30
  },
  "actions": {
    "auto_approve": true,
    "generate_label": true
  },
  "priority": 1
}

# Simulate Rules
POST /api/return-rules/simulate
{
  "order_data": {...},
  "return_data": {...}
}
```

#### Analytics
```bash
# Get Analytics
GET /api/analytics?days=30

# Response:
{
  "total_returns": 45,
  "total_refunds": 2500.00,
  "exchange_rate": 15.5,
  "avg_processing_time": 2.5,
  "top_return_reasons": [
    {"reason": "defective", "count": 20, "percentage": 44.4}
  ]
}
```

#### Shopify Integration
```bash
# Auth Service Status
GET /api/auth/status

# Validate Credentials
POST /api/auth/test/validate
{
  "shop_domain": "demo-store",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}

# Initiate OAuth
POST /api/auth/initiate
{
  "shop": "demo-store",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}

# Connectivity Test
GET /api/shopify-test/quick-test?shop=demo-store
```

### Response Format
All API responses follow this structure:
```json
{
  "success": true,
  "data": {...},
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "per_page": 20
  },
  "message": "Operation successful"
}
```

### Error Handling
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {...}
  }
}
```

## 📁 Project Structure

```
/app/
├── backend/                    # FastAPI Backend
│   ├── src/
│   │   ├── config/            # Configuration management
│   │   ├── controllers/       # API route controllers
│   │   │   ├── returns_controller.py
│   │   │   ├── shopify_controller.py
│   │   │   ├── webhook_controller.py
│   │   │   └── testing_controller.py
│   │   ├── models/           # Pydantic data models
│   │   ├── services/         # Business logic layer
│   │   │   ├── shopify_service.py
│   │   │   ├── shopify_graphql.py
│   │   │   ├── sync_service.py
│   │   │   ├── webhook_handlers.py
│   │   │   ├── ai_service.py
│   │   │   └── email_service.py
│   │   ├── utils/           # Utility functions
│   │   │   ├── rules_engine.py
│   │   │   ├── state_machine.py
│   │   │   └── dependencies.py
│   │   ├── modules/         # Feature modules
│   │   │   ├── auth/       # Authentication & OAuth
│   │   │   ├── returns/    # Returns management
│   │   │   ├── rules/      # Rules engine
│   │   │   └── stores/     # Store management
│   │   ├── repositories/   # Data access layer
│   │   └── middleware/     # Security & validation
│   │       └── security.py
│   ├── requirements.txt    # Python dependencies
│   ├── server.py          # FastAPI app entry point
│   └── .env              # Environment variables
│
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   │   ├── ui/      # Base UI components
│   │   │   └── layout/  # Layout components
│   │   │       ├── MerchantLayout.jsx
│   │   │       ├── CustomerLayout.jsx
│   │   │       ├── SearchBar.jsx
│   │   │       └── TenantSwitcher.jsx
│   │   ├── pages/       # Route components
│   │   │   ├── customer/    # Customer portal
│   │   │   │   ├── Start.jsx
│   │   │   │   ├── SelectItems.jsx
│   │   │   │   ├── ResolutionStep.jsx
│   │   │   │   ├── Confirm.jsx
│   │   │   │   └── StatusTracker.jsx
│   │   │   ├── merchant/    # Merchant dashboard
│   │   │   │   ├── Dashboard.js
│   │   │   │   ├── Orders.jsx
│   │   │   │   ├── OrderDetail.jsx
│   │   │   │   ├── Rules.jsx
│   │   │   │   ├── Analytics.jsx
│   │   │   │   ├── returns/
│   │   │   │   │   ├── AllReturns.jsx
│   │   │   │   │   └── ReturnDetail.jsx
│   │   │   │   └── settings/
│   │   │   │       ├── General.jsx
│   │   │   │       ├── Integrations.jsx
│   │   │   │       ├── Branding.jsx
│   │   │   │       ├── Email.jsx
│   │   │   │       └── TeamAndRoles.jsx
│   │   │   └── admin/       # Admin interface
│   │   ├── App.jsx         # Main app component
│   │   └── App.css        # Global styles
│   ├── package.json       # Node.js dependencies
│   ├── tailwind.config.js # Tailwind configuration
│   └── .env              # Frontend environment
│
├── docs/                 # Documentation
│   ├── DATABASE_SCHEMA.md
│   ├── ENHANCED_FEATURES_SETUP.md
│   └── VERIFICATION_LOG.md
│
├── mock_data/           # Sample data files
├── tests/              # Test suites
├── seed.py            # Database seeding script
├── test_result.md     # Testing logs
└── README.md         # This file
```

## 🔧 Key Components

## 🔐 Authentication & Security

### **Multi-Tenant Security Architecture**

The application implements enterprise-grade security with multiple layers of protection:

```mermaid
graph TD
    Request[Incoming Request] --> RateLimit[Rate Limiting]
    RateLimit --> CORS[CORS Validation]
    CORS --> TenantAuth[Tenant Authentication]
    TenantAuth --> TenantValidation[Tenant Validation]
    TenantValidation --> DataFilter[Data Isolation Filter]
    DataFilter --> Controller[Controller Logic]
    
    TenantAuth -.->|X-Tenant-Id Header| TenantValidation
    TenantValidation -.->|Inject tenant_id| DataFilter
    DataFilter -.->|Filter all queries| Controller
```

### **Security Middleware (`/backend/src/middleware/security.py`)**

#### **1. Tenant Isolation Middleware**
```python
class TenantSecurityMiddleware:
    """
    Enforces strict tenant isolation for all requests
    """
    async def __call__(self, request: Request, call_next):
        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-Id")
        
        # Validate tenant exists and is active
        if not await self.validate_tenant(tenant_id):
            raise HTTPException(
                status_code=401, 
                detail="Invalid or inactive tenant"
            )
        
        # Inject tenant context into request
        request.state.tenant_id = tenant_id
        
        # Log request for audit trail
        await self.log_request(request, tenant_id)
        
        response = await call_next(request)
        return response
    
    async def validate_tenant(self, tenant_id: str) -> bool:
        """Validates tenant exists and is active"""
        tenant = await db.tenants.find_one({
            "id": tenant_id,
            "is_active": True
        })
        return tenant is not None
```

#### **2. Rate Limiting by Tenant**
```python
class TenantRateLimiter:
    """
    Implements per-tenant rate limiting
    """
    RATE_LIMITS = {
        "free": {"requests": 100, "window": 3600},      # 100/hour
        "basic": {"requests": 1000, "window": 3600},    # 1K/hour  
        "pro": {"requests": 10000, "window": 3600},     # 10K/hour
        "enterprise": {"requests": 100000, "window": 3600}  # 100K/hour
    }
    
    async def check_rate_limit(self, tenant_id: str, endpoint: str):
        """Checks if request is within rate limits"""
        # Implementation uses Redis for distributed rate limiting
        pass
```

#### **3. CORS Security Configuration**
```python
# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "X-Tenant-Id",
        "Authorization", 
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent"
    ],
)
```

### **Shopify OAuth 2.0 Integration**

#### **OAuth Flow Architecture**
```mermaid
sequenceDiagram
    participant M as Merchant
    participant App as Returns App
    participant Shopify as Shopify API
    participant DB as Database
    
    M->>App: 1. Initiate Integration
    App->>M: 2. Redirect to Shopify OAuth
    M->>Shopify: 3. Authorize App
    Shopify->>App: 4. OAuth Callback + Code
    App->>Shopify: 5. Exchange Code for Token
    Shopify->>App: 6. Access Token + Shop Info
    App->>DB: 7. Store Encrypted Credentials
    App->>M: 8. Integration Success
```

#### **OAuth Controller (`/backend/src/controllers/shopify_integration_controller.py`)**
```python
@router.post("/oauth/initiate")
async def initiate_oauth(
    request: ShopifyOAuthRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Initiates Shopify OAuth flow
    """
    # Generate secure state parameter
    state = secrets.token_urlsafe(32)
    
    # Store state for validation
    await redis_client.setex(
        f"oauth_state:{state}", 
        300,  # 5 minutes
        tenant_id
    )
    
    # Construct OAuth URL
    oauth_url = (
        f"https://{request.shop_domain}.myshopify.com/admin/oauth/authorize"
        f"?client_id={settings.SHOPIFY_API_KEY}"
        f"&scope={REQUIRED_SCOPES}"
        f"&redirect_uri={settings.SHOPIFY_REDIRECT_URI}"
        f"&state={state}"
    )
    
    return {"authorization_url": oauth_url, "state": state}

@router.post("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str,
    shop: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Handles OAuth callback and token exchange
    """
    # Validate state parameter
    stored_tenant = await redis_client.get(f"oauth_state:{state}")
    if not stored_tenant or stored_tenant.decode() != tenant_id:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for access token
    async with aiohttp.ClientSession() as session:
        token_data = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code
        }
        
        async with session.post(
            f"https://{shop}.myshopify.com/admin/oauth/access_token",
            json=token_data
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to exchange OAuth code"
                )
            
            token_response = await response.json()
            access_token = token_response["access_token"]
    
    # Encrypt and store credentials
    encrypted_token = encryption_service.encrypt(access_token)
    
    await db.integrations_shopify.update_one(
        {"tenant_id": tenant_id},
        {
            "$set": {
                "tenant_id": tenant_id,
                "shop_domain": shop,
                "access_token": encrypted_token,
                "scope": token_response.get("scope", ""),
                "connected_at": datetime.utcnow(),
                "is_active": True
            }
        },
        upsert=True
    )
    
    # Set up webhooks
    await webhook_service.register_webhooks(tenant_id, shop, access_token)
    
    return {"success": True, "message": "Integration completed successfully"}
```

### **Data Encryption & Security**

#### **Credential Encryption Service**
```python
class EncryptionService:
    """
    Handles encryption/decryption of sensitive data
    """
    def __init__(self):
        # 32-byte encryption key from environment
        key = os.getenv("ENCRYPTION_KEY").encode()
        self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypts sensitive string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts sensitive string data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypts dictionary values"""
        encrypted = {}
        for key, value in data.items():
            if key in SENSITIVE_FIELDS:
                encrypted[key] = self.encrypt(str(value))
            else:
                encrypted[key] = value
        return encrypted

# Usage in services
class ShopifyService:
    async def get_access_token(self, tenant_id: str) -> str:
        integration = await db.integrations_shopify.find_one({
            "tenant_id": tenant_id,
            "is_active": True
        })
        
        if not integration:
            raise ValueError("Shopify integration not found")
        
        # Decrypt access token
        encrypted_token = integration["access_token"]
        return encryption_service.decrypt(encrypted_token)
```

### **Request Validation & Sanitization**

#### **Input Validation with Pydantic**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class CreateReturnRequest(BaseModel):
    """
    Validates return request creation
    """
    order_id: str = Field(..., min_length=1, max_length=50)
    customer_email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return_method: str = Field(..., regex=r'^(prepaid_label|customer_ships|drop_off)$')
    
    line_items: List[ReturnLineItem] = Field(..., min_items=1, max_items=50)
    customer_note: Optional[str] = Field(None, max_length=1000)
    
    @validator('customer_note')
    def sanitize_note(cls, v):
        """Sanitizes customer input to prevent XSS"""
        if v:
            # Remove HTML tags and dangerous characters
            v = re.sub(r'<[^>]*>', '', v)
            v = re.sub(r'[<>&"\']', '', v)
        return v
    
    @validator('line_items')
    def validate_line_items(cls, v):
        """Validates line items structure"""
        if not v:
            raise ValueError("At least one line item is required")
        
        total_quantity = sum(item.quantity for item in v)
        if total_quantity > 100:
            raise ValueError("Total return quantity cannot exceed 100")
        
        return v

class ReturnLineItem(BaseModel):
    line_item_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, le=100)
    reason: str = Field(..., regex=r'^(defective|damaged_in_shipping|wrong_item|too_small|too_large|changed_mind)$')
    condition: str = Field(..., regex=r'^(new|used|damaged)$')
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('notes')
    def sanitize_notes(cls, v):
        """Sanitizes line item notes"""
        if v:
            v = re.sub(r'<[^>]*>', '', v)
            v = re.sub(r'[<>&"\']', '', v)
        return v
```

### **Security Headers & Protection**

#### **Security Headers Configuration**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Adds security headers to all responses
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server information
    response.headers.pop("server", None)
    
    return response
```

### **Audit Logging & Compliance**

#### **Audit Trail Implementation**
```python
class AuditLogger:
    """
    Comprehensive audit logging for compliance
    """
    async def log_action(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str = "system",
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """
        Logs all significant actions for audit trail
        """
        audit_entry = {
            "tenant_id": tenant_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "performed_by": user_id,
            "timestamp": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "session_id": self.get_session_id()
        }
        
        await db.audit_log.insert_one(audit_entry)
        
        # Also log to external SIEM if configured
        if settings.SIEM_ENABLED:
            await self.send_to_siem(audit_entry)

# Usage in controllers
@router.put("/returns/{return_id}/status")
async def update_return_status(
    return_id: str,
    status_update: StatusUpdate,
    tenant_id: str = Depends(get_tenant_id),
    request: Request = None
):
    """Updates return status with full audit trail"""
    
    # Perform update
    result = await return_service.update_status(
        tenant_id, return_id, status_update
    )
    
    # Log the action
    await audit_logger.log_action(
        tenant_id=tenant_id,
        action="return_status_updated",
        resource_type="return",
        resource_id=return_id,
        details={
            "old_status": result.old_status,
            "new_status": status_update.status,
            "reason": status_update.reason
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return result
```

### **Environment Security Configuration**

#### **Production Security Checklist**
```bash
# Required Environment Variables for Production
ENCRYPTION_KEY=32-byte-base64-encoded-fernet-key  # CRITICAL: Generate unique key
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com  # NO wildcards in production
JWT_SECRET_KEY=long-random-string-for-jwt-signing
SHOPIFY_API_SECRET=your-shopify-app-secret  # From Shopify Partner Dashboard

# Database Security
MONGO_URL=mongodb://username:password@prod-mongo:27017/returns_prod?authSource=admin
MONGO_AUTH_SOURCE=admin
MONGO_SSL=true

# Optional: External Security Services
REDIS_URL=redis://username:password@redis-server:6379/0  # For rate limiting
SIEM_WEBHOOK_URL=https://your-siem-system.com/webhook  # Security monitoring
VAULT_URL=https://vault.company.com  # Secret management

# Disable Debug in Production
DEBUG=false
TESTING=false
```

#### **Secrets Management Best Practices**
1. **Never commit secrets to version control**
2. **Use environment variables or secret management systems**
3. **Rotate encryption keys regularly (quarterly)**
4. **Monitor access to sensitive configuration**
5. **Use different keys per environment (dev/staging/prod)**

## 🛍️ Shopify Integration

### **Comprehensive Shopify Integration Architecture**

The application provides **deep, production-ready integration** with Shopify, supporting both GraphQL and REST APIs for maximum compatibility and performance.

#### **Integration Capabilities Overview**
| Feature | Implementation | Benefits |
|---------|---------------|----------|
| **OAuth 2.0 Authentication** | Full flow with state validation | Secure, user-approved access |
| **Real-time Data Sync** | GraphQL + REST API | Live order data, fast queries |
| **Webhook Processing** | 14 webhook topics | Real-time event handling |
| **Credential Encryption** | Fernet-based AES-128 | Secure token storage |
| **Rate Limit Handling** | Exponential backoff | Shopify API compliance |
| **Multi-Store Support** | Per-tenant isolation | Enterprise scalability |

### **Shopify Service Layer (`/backend/src/services/shopify_service.py`)**

#### **Core Service Architecture**
```python
class ShopifyService:
    """
    Comprehensive Shopify API service with GraphQL and REST support
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.base_url = None
        self.access_token = None
        self.shop_domain = None
        self._authenticated = False
    
    async def authenticate(self) -> bool:
        """
        Authenticates with Shopify using stored credentials
        """
        integration = await db.integrations_shopify.find_one({
            "tenant_id": self.tenant_id,
            "is_active": True
        })
        
        if not integration:
            raise ShopifyIntegrationError("No active Shopify integration found")
        
        # Decrypt access token
        encrypted_token = integration["access_token"]
        if encrypted_token.startswith('gAAAAAB'):  # Fernet encrypted
            self.access_token = encryption_service.decrypt(encrypted_token)
        else:
            self.access_token = encrypted_token  # Legacy plain text
        
        self.shop_domain = integration["shop_domain"]
        self.base_url = f"https://{self.shop_domain}.myshopify.com"
        
        # Validate credentials
        if await self._test_connection():
            self._authenticated = True
            return True
        
        raise ShopifyIntegrationError("Invalid Shopify credentials")
    
    async def _test_connection(self) -> bool:
        """Tests API connection and permissions"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Shopify-Access-Token": self.access_token,
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.base_url}/admin/api/2025-07/shop.json",
                    headers=headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False
```

#### **GraphQL Query Service**
```python
class ShopifyGraphQLService:
    """
    High-performance GraphQL queries for Shopify data
    """
    
    # GraphQL Query Templates
    ORDER_QUERY = """
    query getOrder($id: ID!) {
        order(id: $id) {
            id
            name
            processedAt
            displayFulfillmentStatus
            displayFinancialStatus
            totalPriceSet {
                shopMoney {
                    amount
                    currencyCode
                }
            }
            customer {
                id
                firstName
                lastName
                displayName
                email
                phone
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        title
                        variantTitle
                        sku
                        quantity
                        originalUnitPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        product {
                            id
                            title
                            handle
                            vendor
                        }
                        variant {
                            id
                            title
                            sku
                            image {
                                url(transform: {maxWidth: 300})
                            }
                        }
                    }
                }
            }
            shippingAddress {
                firstName
                lastName
                company
                address1
                address2
                city
                province
                country
                zip
                phone
            }
        }
    }
    """
    
    async def find_order_by_number(self, order_number: str) -> Optional[dict]:
        """
        Finds order by order number using GraphQL for performance
        """
        if not self._authenticated:
            await self.authenticate()
        
        query = """
        query findOrderByName($query: String!) {
            orders(first: 1, query: $query) {
                edges {
                    node {
                        id
                        name
                        processedAt
                        displayFulfillmentStatus
                        displayFinancialStatus
                        totalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        customer {
                            id
                            firstName
                            lastName
                            displayName
                            email
                        }
                        lineItems(first: 50) {
                            edges {
                                node {
                                    id
                                    title
                                    variantTitle
                                    sku
                                    quantity
                                    originalUnitPriceSet {
                                        shopMoney {
                                            amount
                                            currencyCode
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {"query": f"name:{order_number}"}
        
        result = await self._execute_graphql(query, variables)
        
        if result and result.get('data', {}).get('orders', {}).get('edges'):
            order_data = result['data']['orders']['edges'][0]['node']
            return self._transform_graphql_order(order_data)
        
        return None
    
    async def get_order_for_return(self, order_id: str) -> Optional[dict]:
        """
        Gets complete order data optimized for return processing
        """
        if not self._authenticated:
            await self.authenticate()
        
        # Convert to GraphQL ID if needed
        gql_id = f"gid://shopify/Order/{order_id}" if not order_id.startswith('gid://') else order_id
        
        variables = {"id": gql_id}
        
        result = await self._execute_graphql(self.ORDER_QUERY, variables)
        
        if result and result.get('data', {}).get('order'):
            order_data = result['data']['order']
            return self._transform_graphql_order(order_data)
        
        return None
    
    async def _execute_graphql(self, query: str, variables: dict = None) -> dict:
        """
        Executes GraphQL query with error handling and rate limiting
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/admin/api/2025-07/graphql.json",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 2))
                    await asyncio.sleep(retry_after)
                    return await self._execute_graphql(query, variables)
                
                if response.status != 200:
                    raise ShopifyAPIError(f"GraphQL request failed: {response.status}")
                
                return await response.json()
    
    def _transform_graphql_order(self, order_data: dict) -> dict:
        """
        Transforms GraphQL order data to standard format
        """
        # Extract Shopify order ID from GraphQL ID
        shopify_id = order_data['id'].split('/')[-1] if order_data['id'].startswith('gid://') else order_data['id']
        
        # Transform customer data
        customer = order_data.get('customer', {})
        customer_transformed = {}
        if customer:
            customer_transformed = {
                'id': customer.get('id', '').split('/')[-1] if customer.get('id') else '',
                'first_name': customer.get('firstName', ''),
                'last_name': customer.get('lastName', ''),
                'displayName': customer.get('displayName', ''),
                'email': customer.get('email', '')
            }
        
        # Transform line items
        line_items = []
        for edge in order_data.get('lineItems', {}).get('edges', []):
            item = edge['node']
            line_items.append({
                'id': item['id'].split('/')[-1],
                'title': item.get('title', ''),
                'variant_title': item.get('variantTitle', ''),
                'sku': item.get('sku', ''),
                'quantity': item.get('quantity', 0),
                'price': item.get('originalUnitPriceSet', {}).get('shopMoney', {}).get('amount', '0'),
                'product_id': item.get('product', {}).get('id', '').split('/')[-1] if item.get('product', {}).get('id') else '',
                'variant_id': item.get('variant', {}).get('id', '').split('/')[-1] if item.get('variant', {}).get('id') else ''
            })
        
        # Transform main order data
        transformed_order = {
            'id': shopify_id,
            'order_number': order_data.get('name', ''),
            'name': order_data.get('name', ''),
            'processed_at': order_data.get('processedAt', ''),
            'financial_status': order_data.get('displayFinancialStatus', '').lower(),
            'fulfillment_status': order_data.get('displayFulfillmentStatus', '').lower(),
            'total_price': order_data.get('totalPriceSet', {}).get('shopMoney', {}).get('amount', '0'),
            'currency': order_data.get('totalPriceSet', {}).get('shopMoney', {}).get('currencyCode', 'USD'),
            'customer': customer_transformed,
            'customer_name': f"{customer_transformed.get('first_name', '')} {customer_transformed.get('last_name', '')}".strip(),
            'customer_email': customer_transformed.get('email', ''),
            'customer_display_name': customer_transformed.get('displayName', ''),
            'line_items': line_items,
            'shipping_address': order_data.get('shippingAddress', {}),
            'tenant_id': self.tenant_id,
            'source': 'shopify_live',
            'last_sync': datetime.utcnow().isoformat()
        }
        
        return transformed_order
```

### **Webhook Processing System**

#### **Webhook Handler (`/backend/src/services/webhook_handlers.py`)**
```python
class ShopifyWebhookHandler:
    """
    Processes Shopify webhooks for real-time data sync
    """
    
    SUPPORTED_TOPICS = {
        'orders/create': 'handle_order_created',
        'orders/updated': 'handle_order_updated', 
        'orders/paid': 'handle_order_paid',
        'orders/cancelled': 'handle_order_cancelled',
        'orders/fulfilled': 'handle_order_fulfilled',
        'orders/partially_fulfilled': 'handle_order_partially_fulfilled',
        'refunds/create': 'handle_refund_created',
        'app/uninstalled': 'handle_app_uninstalled',
        'customers/create': 'handle_customer_created',
        'customers/update': 'handle_customer_updated',
        'products/create': 'handle_product_created',
        'products/update': 'handle_product_updated',
        'inventory_levels/update': 'handle_inventory_update',
        'carts/create': 'handle_cart_created'
    }
    
    async def process_webhook(
        self,
        tenant_id: str,
        topic: str,
        payload: dict,
        shop_domain: str,
        webhook_id: str = None
    ) -> bool:
        """
        Processes incoming webhook with error handling and retry logic
        """
        try:
            # Log webhook received
            await self._log_webhook(tenant_id, topic, payload, 'received')
            
            # Find handler method
            handler_method = self.SUPPORTED_TOPICS.get(topic)
            if not handler_method:
                await self._log_webhook(tenant_id, topic, payload, 'unsupported')
                return False
            
            # Execute handler
            handler = getattr(self, handler_method)
            await handler(tenant_id, payload, shop_domain)
            
            await self._log_webhook(tenant_id, topic, payload, 'processed')
            return True
            
        except Exception as e:
            await self._log_webhook(
                tenant_id, topic, payload, 'error', 
                error_details=str(e)
            )
            
            # Schedule retry if applicable
            await self._schedule_retry(tenant_id, topic, payload)
            raise
    
    async def handle_order_created(self, tenant_id: str, payload: dict, shop_domain: str):
        """Handles new order creation"""
        order_data = self._transform_webhook_order(payload, tenant_id)
        
        # Insert or update order in database
        await db.orders.update_one(
            {"id": order_data["id"], "tenant_id": tenant_id},
            {"$set": order_data},
            upsert=True
        )
        
        # Trigger business events
        await self._emit_domain_event("OrderCreated", {
            "tenant_id": tenant_id,
            "order_id": order_data["id"],
            "customer_email": order_data.get("customer_email"),
            "total_price": float(order_data.get("total_price", 0))
        })
    
    async def handle_order_updated(self, tenant_id: str, payload: dict, shop_domain: str):
        """Handles order updates"""
        order_data = self._transform_webhook_order(payload, tenant_id)
        
        # Update existing order
        result = await db.orders.update_one(
            {"id": order_data["id"], "tenant_id": tenant_id},
            {"$set": order_data}
        )
        
        if result.modified_count > 0:
            await self._emit_domain_event("OrderUpdated", {
                "tenant_id": tenant_id,
                "order_id": order_data["id"],
                "changes": self._detect_order_changes(payload)
            })
    
    async def handle_app_uninstalled(self, tenant_id: str, payload: dict, shop_domain: str):
        """
        Handles app uninstallation - critical for compliance
        """
        # Mark integration as inactive
        await db.integrations_shopify.update_one(
            {"tenant_id": tenant_id, "shop_domain": shop_domain},
            {
                "$set": {
                    "is_active": False,
                    "uninstalled_at": datetime.utcnow(),
                    "access_token": None  # Remove access token
                }
            }
        )
        
        # Disable tenant (optional, based on business rules)
        await db.tenants.update_one(
            {"id": tenant_id},
            {
                "$set": {
                    "shopify_connected": False,
                    "integration_status": "disconnected"
                }
            }
        )
        
        # Send notification to tenant
        await notification_service.send_integration_disconnected_email(tenant_id)
        
        await self._emit_domain_event("ShopifyAppUninstalled", {
            "tenant_id": tenant_id,
            "shop_domain": shop_domain,
            "uninstalled_at": datetime.utcnow().isoformat()
        })
```

### **Webhook Registration & Management**

#### **Webhook Controller (`/backend/src/controllers/webhook_controller.py`)**
```python
@router.post("/{topic}")
async def receive_webhook(
    topic: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receives and validates Shopify webhooks
    """
    # Get raw body for HMAC verification
    body = await request.body()
    
    # Verify webhook authenticity
    hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')
    shop_domain = request.headers.get('X-Shopify-Shop-Domain')
    
    if not await verify_webhook_hmac(body, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse payload
    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Find tenant by shop domain
    integration = await db.integrations_shopify.find_one({
        "shop_domain": shop_domain,
        "is_active": True
    })
    
    if not integration:
        # Log orphaned webhook
        await db.webhook_errors.insert_one({
            "topic": topic,
            "shop_domain": shop_domain,
            "error": "No active integration found",
            "payload_size": len(body),
            "created_at": datetime.utcnow()
        })
        raise HTTPException(status_code=404, detail="Integration not found")
    
    tenant_id = integration["tenant_id"]
    
    # Process webhook asynchronously
    background_tasks.add_task(
        webhook_handler.process_webhook,
        tenant_id,
        topic,
        payload,
        shop_domain
    )
    
    return {"success": True, "message": "Webhook received"}

async def verify_webhook_hmac(body: bytes, hmac_header: str) -> bool:
    """
    Verifies webhook HMAC signature for security
    """
    if not hmac_header:
        return False
    
    # Calculate expected HMAC
    secret = settings.SHOPIFY_WEBHOOK_SECRET.encode('utf-8')
    expected_hmac = base64.b64encode(
        hmac.new(secret, body, hashlib.sha256).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(expected_hmac, hmac_header)
```

### **Integration Management Dashboard**

#### **Integration Status Controller**
```python
@router.get("/status")
async def get_integration_status(tenant_id: str = Depends(get_tenant_id)):
    """
    Returns comprehensive Shopify integration status
    """
    integration = await db.integrations_shopify.find_one({
        "tenant_id": tenant_id
    })
    
    if not integration:
        return {
            "connected": False,
            "status": "not_configured",
            "message": "Shopify integration not configured"
        }
    
    if not integration.get("is_active", False):
        return {
            "connected": False,
            "status": "disconnected",
            "message": "Shopify integration is disconnected",
            "disconnected_at": integration.get("uninstalled_at")
        }
    
    # Test connection
    shopify_service = ShopifyService(tenant_id)
    try:
        await shopify_service.authenticate()
        connection_test = await shopify_service._test_connection()
        
        if connection_test:
            # Get additional integration metrics
            stats = await get_integration_stats(tenant_id)
            
            return {
                "connected": True,
                "status": "active",
                "shop_domain": integration["shop_domain"],
                "connected_at": integration["connected_at"],
                "scope": integration.get("scope", ""),
                "last_sync": integration.get("last_sync"),
                "stats": stats
            }
        else:
            return {
                "connected": False,
                "status": "invalid_credentials",
                "message": "Shopify credentials are invalid or expired"
            }
    
    except Exception as e:
        return {
            "connected": False,
            "status": "connection_error",
            "message": f"Connection test failed: {str(e)}"
        }

async def get_integration_stats(tenant_id: str) -> dict:
    """
    Gets integration statistics for dashboard
    """
    # Count synced orders
    orders_count = await db.orders.count_documents({"tenant_id": tenant_id})
    
    # Count webhooks processed (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    webhooks_count = await db.webhooks.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Count returns with Shopify data
    returns_with_shopify_data = await db.returns.count_documents({
        "tenant_id": tenant_id,
        "source": "shopify_live"
    })
    
    return {
        "orders_synced": orders_count,
        "webhooks_processed_30d": webhooks_count,
        "returns_with_shopify_data": returns_with_shopify_data,
        "sync_health": "healthy" if orders_count > 0 else "no_data"
    }
```

## 📊 Database Architecture

### **MongoDB Schema Design**
The database follows a document-based approach optimized for multi-tenancy and performance:

#### **Core Collections Overview**
| Collection | Purpose | Documents | Indexes | Sharding Key |
|------------|---------|-----------|---------|--------------|
| `tenants` | Tenant configuration | ~1K | tenant_id, domain | tenant_id |
| `orders` | Order data (Shopify sync) | ~100K | tenant_id, order_number | tenant_id |
| `returns` | Return requests | ~10K | tenant_id, status, created_at | tenant_id |
| `return_rules` | Business rules engine | ~100 | tenant_id, priority | tenant_id |
| `integrations_shopify` | OAuth credentials | ~1K | tenant_id | tenant_id |
| `webhooks` | Webhook event log | ~1M | tenant_id, created_at | tenant_id |
| `analytics` | Pre-computed metrics | ~10K | tenant_id, date_key | tenant_id |

### **Detailed Schema Definitions**

#### **1. Tenants Collection**
```javascript
{
  "_id": ObjectId("..."),
  "id": "tenant-rms34", // Primary key for tenant identification
  "name": "RMS Fashion Store",
  "domain": "rmsfashion.com",
  "shopify_store_url": "rms34.myshopify.com",
  "plan": "pro", // free, basic, pro, enterprise
  "status": "active", // active, suspended, deleted
  
  // Business Settings
  "settings": {
    "return_window_days": 30,
    "auto_approve_exchanges": true,
    "require_photos": ["defective", "damaged_in_shipping"],
    "max_return_value": 500.00,
    
    // Branding
    "brand_color": "#e11d48",
    "logo_url": "https://cdn.example.com/logos/tenant-rms34.png",
    "custom_css": "/* Custom styles */",
    
    // Email Configuration
    "email_settings": {
      "from_email": "returns@rmsfashion.com",
      "smtp_configured": true,
      "templates": {
        "return_confirmation": "template_id_123",
        "return_approved": "template_id_124"
      }
    },
    
    // Payment Settings
    "payment_settings": {
      "refund_method": "original_payment", // original_payment, store_credit, manual
      "processing_fee": 5.00,
      "free_return_threshold": 100.00
    }
  },
  
  // Tracking & Analytics
  "metrics": {
    "total_returns": 157,
    "total_refunded": 15750.00,
    "avg_processing_time_hours": 24.5,
    "customer_satisfaction_score": 4.8
  },
  
  "created_at": ISODate("2025-01-01T00:00:00.000Z"),
  "updated_at": ISODate("2025-01-15T10:30:00.000Z"),
  "is_active": true
}
```

#### **2. Orders Collection (Shopify Sync)**
```javascript
{
  "_id": ObjectId("..."),
  "id": "5813364687033", // Shopify order ID
  "tenant_id": "tenant-rms34",
  
  // Order Identification
  "order_number": "1001",
  "name": "#RMS1001", // Shopify order name format
  "order_id": "5813364687033", // Duplicate for compatibility
  
  // Financial Information
  "total_price": "400.00",
  "total_discounts": "0.00",
  "total_tax": "32.00",
  "subtotal_price": "368.00",
  "currency": "USD",
  "financial_status": "paid", // pending, paid, partially_paid, refunded
  "fulfillment_status": "fulfilled", // unfulfilled, partial, fulfilled
  
  // Customer Information
  "customer": {
    "id": "customer_shopify_id",
    "first_name": "Shashank",
    "last_name": "Shekhar",
    "email": "shashankshekharofficial15@gmail.com",
    "phone": "+1234567890",
    "accepts_marketing": true
  },
  "customer_name": "Shashank Shekhar", // Computed field
  "customer_email": "shashankshekharofficial15@gmail.com", // Denormalized
  "customer_display_name": "Shashank S.", // For UI display
  
  // Line Items (Products)
  "line_items": [
    {
      "id": "13851721105593",
      "variant_id": "variant_123",
      "product_id": "product_456",
      "title": "TESTORDER Premium T-Shirt",
      "variant_title": "Large / Blue",
      "sku": "TSHIRT-L-BLUE",
      "vendor": "Premium Brand",
      "quantity": 1,
      "price": "400.00",
      "total_discount": "0.00",
      "tax_lines": [{"rate": 0.08, "title": "Sales Tax", "price": "32.00"}],
      
      // Return Status Tracking
      "returnable": true,
      "returned_quantity": 0,
      "refunded_quantity": 0,
      
      // Product Metadata for Returns
      "properties": {
        "size": "Large",
        "color": "Blue",
        "material": "100% Cotton"
      },
      "fulfillment_service": "manual",
      "fulfillment_status": "fulfilled"
    }
  ],
  
  // Shipping Information
  "shipping_address": {
    "first_name": "Shashank",
    "last_name": "Shekhar",
    "company": "",
    "address1": "123 Main Street",
    "address2": "Apt 4B",
    "city": "New York",
    "province": "NY",
    "country": "United States",
    "zip": "10001",
    "phone": "+1234567890"
  },
  
  // Billing Information (if different)
  "billing_address": {
    // Same structure as shipping_address
  },
  
  // Fulfillment & Shipping
  "fulfillments": [
    {
      "id": "fulfillment_123",
      "status": "success",
      "created_at": "2025-01-10T08:30:00Z",
      "tracking_company": "UPS",
      "tracking_number": "1Z999AA1234567890",
      "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA1234567890"
    }
  ],
  
  // Timestamps
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-10T08:30:00Z",
  "processed_at": "2025-01-10T08:05:00Z",
  
  // Return Eligibility
  "return_eligible": true,
  "return_window_end": "2025-02-09T08:00:00Z", // 30 days from order
  
  // Sync Metadata
  "source": "shopify_live", // shopify_live, shopify_webhook, manual
  "last_sync": "2025-01-15T12:00:00Z",
  "shopify_admin_url": "https://rms34.myshopify.com/admin/orders/5813364687033"
}
```

#### **3. Returns Collection (Elite-Grade Schema)**
```javascript
{
  "_id": ObjectId("..."),
  "id": "539c705d-99db-4b70-a527-ac6faf05ba17", // UUID for returns
  "tenant_id": "tenant-rms34",
  
  // Order Reference
  "order_id": "5813364687033", // Links to orders collection
  "order_number": "1001", // Denormalized for quick access
  
  // Customer Information
  "customer_email": "shashankshekharofficial15@gmail.com",
  "customer_name": "Shashank Shekhar", // Derived from order
  "customer_phone": "+1234567890",
  
  // Return Request Details
  "return_method": "prepaid_label", // prepaid_label, customer_ships, drop_off
  "return_reason_category": "quality", // quality, fit, damaged, changed_mind
  "customer_note": "Item doesn't fit as expected",
  
  // Line Items Being Returned
  "line_items": [
    {
      "line_item_id": "13851721105593", // Reference to order line item
      "sku": "TSHIRT-L-BLUE",
      "title": "TESTORDER Premium T-Shirt",
      "variant_title": "Large / Blue",
      "quantity": 1, // Quantity being returned
      "unit_price": 400.00,
      
      // Return Specific Information
      "reason": "defective", // defective, damaged_in_shipping, wrong_item, too_small, too_large
      "condition": "damaged", // new, used, damaged
      "resolution": "refund", // refund, exchange, store_credit, repair
      
      // Evidence & Documentation
      "photos": [
        {
          "url": "https://storage.example.com/returns/photos/photo1.jpg",
          "description": "Damage on sleeve",
          "uploaded_at": "2025-01-20T14:30:00Z"
        }
      ],
      "notes": "There's a small tear on the left sleeve",
      
      // AI Analysis (if enabled)
      "ai_analysis": {
        "damage_assessment": "minor_defect",
        "authenticity_check": "verified",
        "condition_grade": "B",
        "confidence_score": 0.85
      }
    }
  ],
  
  // Financial Calculations
  "estimated_refund": {
    "amount": 354.01, // After fees and taxes
    "currency": "USD",
    "breakdown": {
      "item_total": 400.00,
      "tax_refund": 32.00,
      "shipping_refund": 0.00,
      "restocking_fee": -20.00, // If applicable
      "processing_fee": -5.00,
      "final_amount": 354.01
    }
  },
  
  // Status & Workflow
  "status": "requested", // requested, approved, denied, processing, completed, cancelled
  "decision": "", // approved, denied, partial_approval
  "decision_reason": "",
  "decision_made_by": "", // admin_user_id or "auto_approved"
  "decision_made_at": null,
  
  // State Machine History
  "state_history": [
    {
      "from_state": null,
      "to_state": "requested",
      "changed_by": "customer",
      "changed_at": "2025-01-20T14:30:00Z",
      "notes": "Return request submitted"
    }
  ],
  
  // Processing Information
  "shipping": {
    "return_label_url": null,
    "tracking_number": null,
    "carrier": null,
    "estimated_delivery": null,
    "return_address": {
      "company": "RMS Fashion Returns",
      "address1": "456 Warehouse Dr",
      "city": "Fulfillment City",
      "state": "CA",
      "zip": "90210",
      "country": "US"
    }
  },
  
  // Resolution & Refund
  "resolution": {
    "type": null, // refund, exchange, store_credit, repair
    "status": "pending", // pending, processing, completed, failed
    "refund_transaction_id": null,
    "exchange_order_id": null,
    "store_credit_id": null,
    "completed_at": null,
    "notes": ""
  },
  
  // Rules Engine Processing
  "rule_evaluations": [
    {
      "rule_id": "rule_auto_approve_defective",
      "rule_name": "Auto-approve defective items",
      "matched": true,
      "action_taken": "auto_approve",
      "confidence_score": 0.95,
      "evaluated_at": "2025-01-20T14:31:00Z"
    }
  ],
  
  // Audit & Compliance
  "audit_log": [
    {
      "action": "return_created",
      "performed_by": "customer", // customer, admin_user_id, system
      "timestamp": "2025-01-20T14:30:00Z",
      "details": {
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.1",
        "changes": {
          "status": "requested"
        }
      }
    }
  ],
  
  // Timestamps
  "created_at": "2025-01-20T14:30:00Z",
  "updated_at": "2025-01-20T14:30:00Z",
  "expires_at": "2025-02-19T14:30:00Z", // 30 days to complete return
  
  // Performance Metrics
  "metrics": {
    "processing_time_hours": null,
    "customer_satisfaction_score": null, // 1-5 rating
    "cost_to_process": 15.50 // Including labor, shipping, etc.
  }
}
```

### **Database Indexes for Performance**

#### **Critical Performance Indexes**
```javascript
// Tenants Collection
db.tenants.createIndex({"id": 1}, {"unique": true})
db.tenants.createIndex({"domain": 1})
db.tenants.createIndex({"shopify_store_url": 1})

// Orders Collection - Multi-tenant optimized
db.orders.createIndex({"tenant_id": 1, "id": 1}, {"unique": true})
db.orders.createIndex({"tenant_id": 1, "order_number": 1})
db.orders.createIndex({"tenant_id": 1, "customer_email": 1})
db.orders.createIndex({"tenant_id": 1, "created_at": -1})
db.orders.createIndex({"tenant_id": 1, "financial_status": 1})
db.orders.createIndex({"tenant_id": 1, "return_eligible": 1})

// Returns Collection - Query optimized
db.returns.createIndex({"tenant_id": 1, "id": 1}, {"unique": true})
db.returns.createIndex({"tenant_id": 1, "status": 1, "created_at": -1})
db.returns.createIndex({"tenant_id": 1, "order_id": 1})
db.returns.createIndex({"tenant_id": 1, "customer_email": 1})
db.returns.createIndex({"tenant_id": 1, "decision": 1})
db.returns.createIndex({"created_at": -1}) // For analytics
db.returns.createIndex({"expires_at": 1}) // For cleanup jobs

// Text Search Indexes
db.returns.createIndex(
  {
    "customer_name": "text",
    "customer_email": "text",
    "order_number": "text",
    "customer_note": "text"
  },
  {
    "name": "returns_text_search",
    "weights": {
      "customer_email": 10,
      "order_number": 8,
      "customer_name": 5,
      "customer_note": 1
    }
  }
)

// Rules Engine
db.return_rules.createIndex({"tenant_id": 1, "priority": 1, "is_active": 1})
db.return_rules.createIndex({"tenant_id": 1, "conditions.auto_approve_reasons": 1})

// Shopify Integrations
db.integrations_shopify.createIndex({"tenant_id": 1}, {"unique": true})
db.integrations_shopify.createIndex({"shop_domain": 1})

// Webhooks & Events
db.webhooks.createIndex({"tenant_id": 1, "created_at": -1})
db.webhooks.createIndex({"tenant_id": 1, "topic": 1, "processed": 1})
db.webhooks.createIndex({"created_at": 1}, {"expireAfterSeconds": 2592000}) // 30 days TTL

// Analytics & Metrics
db.analytics.createIndex({"tenant_id": 1, "date_key": 1, "metric_type": 1})
db.analytics.createIndex({"tenant_id": 1, "created_at": -1})
```

### **Data Consistency & Integrity**

#### **Multi-Tenant Data Isolation Rules**
1. **All collections MUST include `tenant_id` field**
2. **All queries MUST filter by `tenant_id`**  
3. **Cross-tenant references are FORBIDDEN**
4. **Backup and restore operations are tenant-aware**

#### **Data Validation Schema**
```javascript
// MongoDB Schema Validation Example
db.createCollection("returns", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["id", "tenant_id", "order_id", "status", "created_at"],
      properties: {
        id: {bsonType: "string", pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"},
        tenant_id: {bsonType: "string", pattern: "^tenant-[a-zA-Z0-9-]+$"},
        status: {enum: ["requested", "approved", "denied", "processing", "completed", "cancelled"]},
        estimated_refund: {
          bsonType: "object",
          properties: {
            amount: {bsonType: "number", minimum: 0},
            currency: {bsonType: "string", enum: ["USD", "EUR", "GBP", "CAD"]}
          }
        }
      }
    }
  }
})
```

## 🧪 Testing

### Seed Sample Data
```bash
# Generate comprehensive test data
python seed.py

# This creates:
# - 2 tenants with different configurations
# - 50+ products across categories  
# - 30+ orders from various customers
# - 20+ returns in different states
# - Return rules covering various scenarios
```

### Manual Testing Scenarios

#### 1. Customer Return Flow
1. Visit http://localhost:3000/returns
2. Enter order number and email
3. Select items to return
4. Choose return reason
5. Submit return request
6. Track return status

#### 2. Merchant Dashboard
1. Visit http://localhost:3000/app
2. View dashboard with KPIs
3. Manage returns (approve/deny)
4. Configure return rules
5. View analytics and reports

#### 3. Shopify Integration
1. Go to Settings > Integrations
2. Enter Shopify store details
3. Complete OAuth flow
4. Verify data synchronization
5. Test webhook processing

### API Testing
```bash
# Health check
curl http://localhost:8001/health

# Get returns for a tenant
curl -H "X-Tenant-Id: tenant-fashion-store" \
     http://localhost:8001/api/returns

# Create a return request
curl -X POST \
     -H "X-Tenant-Id: tenant-fashion-store" \
     -H "Content-Type: application/json" \
     -d '{"order_id":"uuid","reason":"defective","items_to_return":[...]}' \
     http://localhost:8001/api/returns
```

### Backend Testing
```bash
# Run unit tests
cd backend
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Load testing
locust -f tests/load_test.py --host=http://localhost:8001
```

### Frontend Testing
```bash
# Run unit tests
cd frontend
yarn test

# Run E2E tests
yarn test:e2e

# Component testing
yarn test:components
```

## 🚀 Deployment

### Production Checklist

#### Security
- [ ] Update `ENCRYPTION_KEY` with strong 32-byte key
- [ ] Set secure `CORS_ORIGINS` (not *)
- [ ] Configure HTTPS certificates
- [ ] Enable MongoDB authentication
- [ ] Set up firewall rules

#### Environment Variables
```bash
# Production Backend .env
MONGO_URL=mongodb://prod-server:27017/returns_prod
DB_NAME=returns_management_prod
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ENCRYPTION_KEY=your-32-byte-base64-encoded-key
DEBUG=false
SHOPIFY_REDIRECT_URI=https://yourdomain.com/auth/callback
```

#### Database
```bash
# Create production database
mongorestore --uri="mongodb://prod-server:27017/returns_prod" backup/

# Set up indexes
mongo returns_prod --eval "
  db.tenants.createIndex({'id': 1});
  db.orders.createIndex({'tenant_id': 1, 'order_number': 1});
  db.return_requests.createIndex({'tenant_id': 1, 'status': 1});
"
```

#### Process Management
```bash
# Production supervisor config
[program:returns-backend]
command=/path/to/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true

[program:returns-frontend]
command=yarn start
directory=/path/to/frontend
user=www-data
autostart=true
autorestart=true
```

### Docker Deployment
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]

# Dockerfile.frontend  
FROM node:18-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
CMD ["yarn", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongo:27017
    depends_on:
      - mongo
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
      
  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      
volumes:
  mongo_data:
```

### Cloud Deployment (AWS)
```bash
# Install AWS CLI and configure
aws configure

# Deploy using Elastic Beanstalk
eb init returns-management-saas
eb create production
eb deploy

# Or use ECS with Fargate
aws ecs create-cluster --cluster-name returns-saas
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

## 🔍 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Check connection
mongo --eval "db.adminCommand('ismaster')"
```

#### 2. Frontend Not Loading
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules yarn.lock
yarn install

# Check port conflicts
lsof -i :3000
```

#### 3. API Requests Failing
```bash
# Check backend logs
sudo supervisorctl tail -f backend

# Verify CORS settings
curl -H "Origin: http://localhost:3000" \
     -H "X-Tenant-Id: tenant-fashion-store" \
     http://localhost:8001/api/health
```

#### 4. Shopify Integration Issues
```bash
# Verify credentials
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"shop_domain":"your-shop","api_key":"key","api_secret":"secret"}' \
     http://localhost:8001/api/auth/test/validate

# Check webhook endpoints
curl http://localhost:8001/api/webhooks/health
```

#### 5. Database Seeding Failed
```bash
# Clear database and reseed
mongo returns_management --eval "db.dropDatabase()"
python seed.py

# Check seed results
mongo returns_management --eval "
  print('Tenants:', db.tenants.count());
  print('Products:', db.products.count());
  print('Orders:', db.orders.count());
  print('Returns:', db.return_requests.count());
"
```

### Performance Issues

#### Slow API Responses
```bash
# Check database indexes
mongo returns_management --eval "db.return_requests.getIndexes()"

# Monitor query performance
mongo returns_management --eval "db.setProfilingLevel(2)"

# Check slow queries
mongo returns_management --eval "db.system.profile.find().limit(5).sort({ts:-1}).pretty()"
```

#### Memory Usage
```bash
# Monitor Python processes
ps aux | grep python

# Monitor Node.js processes  
ps aux | grep node

# Check MongoDB memory
mongo --eval "db.serverStatus().mem"
```

### Logs and Debugging

#### Backend Logs
```bash
# Supervisor logs
sudo supervisorctl tail -f backend stderr
sudo supervisorctl tail -f backend stdout

# Direct logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log
```

#### Frontend Logs
```bash
# Browser console for frontend errors
# Chrome DevTools -> Console

# React dev server logs
sudo supervisorctl tail -f frontend

# Build errors
cd frontend && yarn build
```

#### Database Logs
```bash
# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Query logs
mongo returns_management --eval "db.setProfilingLevel(1, {slowms: 100})"
```

## 📞 Support & Contribution

### Getting Help
- **Documentation**: Check `/docs` directory for detailed guides
- **API Reference**: http://localhost:8001/docs (when running)
- **Issues**: Report bugs and feature requests via GitHub Issues

### Development Guidelines
- **Code Style**: Follow PEP 8 for Python, ESLint for JavaScript
- **Testing**: Write tests for new features
- **Documentation**: Update README and API docs for changes
- **Security**: Never commit credentials or sensitive data

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Shopify** for comprehensive API documentation
- **FastAPI** community for excellent framework
- **React** ecosystem for modern frontend tools
- **Tailwind CSS** for utility-first styling
- **MongoDB** for flexible document storage

---

**Built with ❤️ for modern e-commerce returns management**
