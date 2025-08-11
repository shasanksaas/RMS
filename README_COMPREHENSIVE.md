# 🚀 Returns Management SaaS - Complete Technical Documentation

This is the comprehensive technical documentation for the Returns Management SaaS application. Continue reading from the previous README sections, and here are the remaining critical sections:

## 📡 API Documentation

### **Complete API Reference**

#### **Base Configuration**
- **Base URL**: `http://localhost:8001/api` (Development) | `https://api.yourapp.com/api` (Production)
- **Authentication**: Multi-tenant via `X-Tenant-Id` header
- **Content-Type**: `application/json`
- **Rate Limits**: Varies by tenant plan (100/hour to 100K/hour)

### **Core API Endpoints**

#### **1. Elite Portal Returns Controller (`/backend/src/controllers/elite_portal_returns_controller.py`)**
```python
# Customer-facing return portal endpoints
POST   /api/elite/portal/returns/lookup-order     # Order lookup by number + email
POST   /api/elite/portal/returns/create          # Create return request
GET    /api/elite/portal/returns/{id}/status     # Check return status
POST   /api/elite/portal/returns/{id}/upload     # Upload photos/documents
```

**Example: Order Lookup**
```bash
curl -X POST "http://localhost:8001/api/elite/portal/returns/lookup-order" \
  -H "X-Tenant-Id: tenant-rms34" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "1001",
    "customer_email": "customer@example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "order": {
      "id": "5813364687033",
      "order_number": "1001",
      "customer_name": "John Smith",
      "total_price": "400.00",
      "line_items": [
        {
          "id": "13851721105593",
          "title": "Premium T-Shirt",
          "variant_title": "Large / Blue",
          "quantity": 1,
          "price": "400.00",
          "returnable": true
        }
      ]
    }
  }
}
```

#### **2. Enhanced Returns Controller (`/backend/src/controllers/returns_controller_enhanced.py`)**
```python
# Merchant dashboard return management
GET    /api/returns/                             # List returns (paginated, filtered)
GET    /api/returns/{id}                         # Get return details
PUT    /api/returns/{id}/status                  # Update return status
POST   /api/returns/{id}/resolve                 # Process resolution (refund/exchange)
GET    /api/returns/{id}/audit-log               # Get audit trail
POST   /api/returns/bulk-action                  # Bulk operations
```

**Example: Get Returns with Filters**
```bash
curl -X GET "http://localhost:8001/api/returns/?page=1&pageSize=25&status=requested&search=john" \
  -H "X-Tenant-Id: tenant-rms34"
```

**Response:**
```json
{
  "returns": [
    {
      "id": "539c705d-99db-4b70-a527-ac6faf05ba17",
      "order_number": "1001",
      "customer_name": "John Smith",
      "customer_email": "john@example.com",
      "status": "REQUESTED",
      "item_count": 2,
      "estimated_refund": 354.01,
      "created_at": "2025-01-20T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 25,
    "total": 157,
    "totalPages": 7,
    "hasNext": true
  }
}
```

#### **3. Shopify Integration Controller (`/backend/src/controllers/shopify_integration_controller.py`)**
```python
# Shopify OAuth and integration management
GET    /api/integrations/shopify/status         # Integration status
POST   /api/integrations/shopify/oauth/initiate # Start OAuth flow
POST   /api/integrations/shopify/oauth/callback # OAuth callback
POST   /api/integrations/shopify/sync/orders    # Manual sync orders
DELETE /api/integrations/shopify/disconnect     # Disconnect integration
GET    /api/integrations/shopify/webhooks       # Webhook status
```

#### **4. Orders Controller (`/backend/src/controllers/orders_controller_enhanced.py`)**
```python
# Order management and lookup
GET    /api/orders/                             # List orders
GET    /api/orders/{id}                         # Get order details
POST   /api/orders/lookup                       # Customer order lookup
GET    /api/orders/{id}/return-eligibility      # Check return eligibility
GET    /api/orders/search                       # Advanced order search
```

#### **5. Rules Engine Controller (`/backend/src/controllers/rules_controller.py`)**
```python
# Return rules management
GET    /api/return-rules/                       # List rules
POST   /api/return-rules/                       # Create rule
PUT    /api/return-rules/{id}                   # Update rule
DELETE /api/return-rules/{id}                   # Delete rule
POST   /api/return-rules/simulate               # Test rule logic
GET    /api/return-rules/{id}/performance       # Rule performance metrics
```

## 🎮 Controllers & Endpoints

### **Controller Architecture Overview**

```mermaid
graph TB
    Request[HTTP Request] --> Router[FastAPI Router]
    Router --> Controller[Controller Layer]
    Controller --> Service[Service Layer]
    Service --> Repository[Repository Layer]
    Repository --> Database[(MongoDB)]
    
    Controller --> Events[Domain Events]
    Events --> Handlers[Event Handlers]
    Handlers --> External[External Services]
    
    subgraph "Controllers"
        ElitePortal[Elite Portal Controller]
        Returns[Returns Controller]
        Orders[Orders Controller]
        Shopify[Shopify Integration]
        Rules[Rules Engine]
        Webhooks[Webhook Handler]
    end
```

### **Detailed Controller Implementations**

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
    Looks up customer order for return initiation
    
    Business Logic:
    1. Validate order number format
    2. Search local database first (performance)
    3. Fallback to live Shopify API if not found
    4. Verify customer email matches order
    5. Check return eligibility rules
    6. Return sanitized order data for return form
    """
    
    # Input validation
    if not request.order_number or not request.customer_email:
        raise HTTPException(status_code=400, detail="Order number and email required")
    
    # Try local database first (faster)
    order = await db.orders.find_one({
        "tenant_id": tenant_id,
        "order_number": request.order_number,
        "customer_email": {"$regex": re.escape(request.customer_email), "$options": "i"}
    })
    
    # Fallback to Shopify API for real-time data
    if not order:
        shopify_service = ShopifyService(tenant_id)
        order = await shopify_service.find_order_by_number(request.order_number)
        
        if order and order.get("customer_email", "").lower() != request.customer_email.lower():
            raise HTTPException(status_code=404, detail="Order not found or email mismatch")
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check return eligibility
    eligibility = await return_service.check_return_eligibility(order)
    
    return {
        "success": True,
        "data": {
            "order": order,
            "eligibility": eligibility,
            "return_window_days": await get_tenant_return_window(tenant_id)
        }
    }
```

#### **Enhanced Returns Controller**
**File:** `/backend/src/controllers/returns_controller_enhanced.py`
**Purpose:** Merchant dashboard return management with optimization

```python
@router.get("/")
async def get_returns(
    tenant_id: str = Depends(get_tenant_id),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize")
):
    """
    OPTIMIZED: Returns list with server-side pagination and filtering
    
    Performance Optimizations:
    1. Database indexes on tenant_id + status + created_at
    2. Batch order fetching to avoid N+1 queries
    3. Cached customer name resolution
    4. Efficient aggregation pipeline for counts
    """
    
    # Build MongoDB query
    query = {"tenant_id": tenant_id}
    
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [
            {"order_number": search_regex},
            {"customer_email": search_regex},
            {"customer_name": search_regex}
        ]
    
    if status:
        query["status"] = status.lower()
    
    # Get total count for pagination
    total = await db.returns.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    returns = await db.returns.find(query)\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(page_size)\
        .to_list(page_size)
    
    # OPTIMIZATION: Batch fetch related order data
    unique_order_ids = list(set(r.get("order_id") for r in returns if r.get("order_id")))
    orders_map = {}
    
    if unique_order_ids:
        orders = await db.orders.find({
            "id": {"$in": unique_order_ids},
            "tenant_id": tenant_id
        }).to_list(None)
        orders_map = {order["id"]: order for order in orders}
    
    # Format response with enriched data
    formatted_returns = []
    for return_req in returns:
        order = orders_map.get(return_req.get("order_id"))
        
        # Enrich with order data
        formatted_return = {
            "id": return_req["id"],
            "order_number": order.get("order_number", "") if order else "",
            "customer_name": return_req.get("customer_name", ""),
            "customer_email": return_req.get("customer_email", ""),
            "status": return_req.get("status", "").upper(),
            "item_count": len(return_req.get("line_items", [])),
            "estimated_refund": return_req.get("estimated_refund", {}).get("amount", 0),
            "created_at": return_req.get("created_at"),
            "decision": return_req.get("decision", "")
        }
        formatted_returns.append(formatted_return)
    
    return {
        "returns": formatted_returns,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size,
            "hasNext": page * page_size < total
        }
    }
```

#### **Shopify Integration Controller**
**File:** `/backend/src/controllers/shopify_integration_controller.py`
**Purpose:** OAuth flow and integration management

```python
@router.post("/oauth/initiate")
async def initiate_oauth(
    request: ShopifyOAuthInitiateRequest,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Initiates Shopify OAuth 2.0 flow with security measures
    """
    # Validate shop domain format
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', request.shop_domain):
        raise HTTPException(status_code=400, detail="Invalid shop domain format")
    
    # Generate secure state parameter (CSRF protection)
    state = secrets.token_urlsafe(32)
    
    # Store state in Redis with expiration
    await redis_client.setex(f"oauth_state:{state}", 600, tenant_id)  # 10 minutes
    
    # Required Shopify scopes
    scopes = [
        "read_orders", "write_orders",
        "read_customers", "write_customers", 
        "read_products", "read_inventory",
        "write_shipping", "read_fulfillments"
    ]
    
    # Build OAuth URL
    oauth_params = {
        "client_id": settings.SHOPIFY_API_KEY,
        "scope": ",".join(scopes),
        "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
        "state": state
    }
    
    oauth_url = f"https://{request.shop_domain}.myshopify.com/admin/oauth/authorize?" + \
                "&".join(f"{k}={v}" for k, v in oauth_params.items())
    
    return {
        "authorization_url": oauth_url,
        "state": state,
        "expires_in": 600
    }
```

## 📁 Project Structure

### **Complete Directory Structure**
```
/app/
├── 📂 backend/                                 # FastAPI Backend Application
│   ├── 📂 src/
│   │   ├── 📂 config/                         # Configuration Management
│   │   │   ├── database.py                    # MongoDB connection config
│   │   │   ├── environment.py                 # Environment variable handling
│   │   │   └── settings.py                    # Application settings
│   │   │
│   │   ├── 📂 controllers/                    # API Route Controllers (12 controllers)
│   │   │   ├── elite_portal_returns_controller.py    # Customer portal API
│   │   │   ├── elite_admin_returns_controller.py     # Admin return management
│   │   │   ├── returns_controller_enhanced.py        # Merchant dashboard API
│   │   │   ├── orders_controller_enhanced.py         # Order management API
│   │   │   ├── shopify_integration_controller.py     # Shopify OAuth & integration
│   │   │   ├── webhook_controller.py                 # Webhook processing
│   │   │   ├── rules_controller.py                   # Business rules engine
│   │   │   ├── analytics_controller.py               # Analytics & reporting
│   │   │   ├── tenant_controller.py                  # Multi-tenant management
│   │   │   ├── testing_controller.py                 # Development testing endpoints
│   │   │   ├── unified_returns_controller.py         # Legacy unified API
│   │   │   └── shopify_test_controller.py            # Shopify connection testing
│   │   │
│   │   ├── 📂 services/                       # Business Logic Layer
│   │   │   ├── shopify_service.py             # Main Shopify API integration
│   │   │   ├── shopify_graphql.py             # GraphQL query service  
│   │   │   ├── tenant_service.py              # Multi-tenant operations
│   │   │   ├── return_service.py              # Return processing logic
│   │   │   ├── order_service.py               # Order management logic
│   │   │   ├── webhook_service.py             # Webhook registration/handling
│   │   │   ├── notification_service.py        # Email/SMS notifications
│   │   │   ├── analytics_service.py           # Business analytics
│   │   │   ├── rules_engine_service.py        # Rules evaluation
│   │   │   ├── ai_service.py                  # AI-powered features
│   │   │   └── integration_service.py         # Third-party integrations
│   │   │
│   │   ├── 📂 models/                         # Pydantic Data Models
│   │   │   ├── return_models.py               # Return request models
│   │   │   ├── order_models.py                # Order data models  
│   │   │   ├── tenant_models.py               # Tenant configuration models
│   │   │   ├── shopify_models.py              # Shopify-specific models
│   │   │   ├── webhook_models.py              # Webhook payload models
│   │   │   └── analytics_models.py            # Analytics data models
│   │   │
│   │   ├── 📂 infrastructure/                 # Infrastructure Layer (Hexagonal Architecture)
│   │   │   ├── 📂 repositories/               # Data Access Layer
│   │   │   │   ├── mongo_return_repository.py        # Returns data access
│   │   │   │   ├── mongo_order_repository.py         # Orders data access
│   │   │   │   ├── mongo_tenant_repository.py        # Tenants data access
│   │   │   │   └── analytics_repository.py           # Analytics data access
│   │   │   │
│   │   │   └── 📂 services/                   # External Service Adapters
│   │   │       ├── shopify_service_adapter.py        # Shopify API adapter
│   │   │       ├── email_service_adapter.py          # Email service adapter
│   │   │       ├── storage_service_adapter.py        # File storage adapter
│   │   │       └── payment_service_adapter.py        # Payment processing adapter
│   │   │
│   │   ├── 📂 domain/                         # Domain Layer (Business Logic)
│   │   │   ├── 📂 ports/                      # Interface definitions (Hexagonal)
│   │   │   │   ├── repositories.py                   # Repository interfaces
│   │   │   │   ├── services.py                       # Service interfaces
│   │   │   │   └── events.py                         # Event handler interfaces
│   │   │   │
│   │   │   ├── entities/                      # Business Entities
│   │   │   │   ├── return_entity.py                  # Return business entity
│   │   │   │   ├── order_entity.py                   # Order business entity
│   │   │   │   └── tenant_entity.py                  # Tenant business entity
│   │   │   │
│   │   │   ├── value_objects.py               # Domain value objects
│   │   │   ├── events.py                      # Domain events
│   │   │   └── exceptions.py                  # Domain-specific exceptions
│   │   │
│   │   ├── 📂 application/                    # Application Layer (CQRS)
│   │   │   ├── commands.py                    # Command definitions
│   │   │   ├── queries.py                     # Query definitions
│   │   │   │
│   │   │   └── 📂 handlers/                   # Command/Query Handlers
│   │   │       ├── command_handlers.py               # Command processing
│   │   │       ├── query_handlers.py                 # Query processing
│   │   │       ├── event_handlers.py                 # Domain event handlers
│   │   │       └── webhook_handlers.py               # Webhook event handlers
│   │   │
│   │   ├── 📂 middleware/                     # HTTP Middleware
│   │   │   ├── security.py                    # Authentication & authorization
│   │   │   ├── tenant_middleware.py           # Multi-tenant isolation
│   │   │   ├── rate_limiting.py               # API rate limiting
│   │   │   ├── logging.py                     # Request/response logging
│   │   │   └── error_handling.py              # Global error handling
│   │   │
│   │   ├── 📂 utils/                          # Utility Functions
│   │   │   ├── dependencies.py                # FastAPI dependencies
│   │   │   ├── rules_engine.py                # Business rules evaluation
│   │   │   ├── state_machine.py               # Return status state machine
│   │   │   ├── encryption.py                  # Data encryption utilities
│   │   │   ├── validation.py                  # Data validation helpers
│   │   │   ├── formatting.py                  # Data formatting utilities
│   │   │   └── constants.py                   # Application constants
│   │   │
│   │   └── 📂 modules/                        # Feature Modules
│   │       ├── 📂 auth/                       # Authentication Module
│   │       │   ├── service.py                        # OAuth service
│   │       │   ├── models.py                         # Auth data models
│   │       │   └── utils.py                          # Auth utilities
│   │       │
│   │       ├── 📂 returns/                    # Returns Management Module
│   │       │   ├── service.py                        # Return processing
│   │       │   ├── models.py                         # Return models
│   │       │   ├── validators.py                     # Return validation
│   │       │   └── state_machine.py                  # Return workflow
│   │       │
│   │       ├── 📂 orders/                     # Order Management Module
│   │       │   ├── service.py                        # Order processing
│   │       │   ├── models.py                         # Order models
│   │       │   └── sync.py                           # Order synchronization
│   │       │
│   │       ├── 📂 analytics/                  # Analytics Module
│   │       │   ├── service.py                        # Analytics processing
│   │       │   ├── models.py                         # Analytics models
│   │       │   └── aggregators.py                    # Data aggregation
│   │       │
│   │       └── 📂 integrations/               # External Integrations
│   │           ├── shopify/                          # Shopify integration
│   │           ├── stripe/                           # Payment integration
│   │           ├── sendgrid/                         # Email integration
│   │           └── aws/                              # Cloud services integration
│   │
│   ├── server.py                              # FastAPI Application Entry Point
│   ├── requirements.txt                       # Python Dependencies
│   ├── add_indexes.py                         # Database index optimization
│   └── .env                                   # Environment Configuration
│
├── 📂 frontend/                               # React Frontend Application
│   ├── 📂 src/
│   │   ├── 📂 components/                     # Reusable UI Components
│   │   │   ├── 📂 ui/                         # Base UI Components (Radix UI)
│   │   │   │   ├── button.jsx                        # Button component
│   │   │   │   ├── input.jsx                         # Input component
│   │   │   │   ├── dialog.jsx                        # Modal dialogs
│   │   │   │   ├── table.jsx                         # Data tables
│   │   │   │   ├── alert.jsx                         # Alert messages
│   │   │   │   ├── badge.jsx                         # Status badges
│   │   │   │   ├── card.jsx                          # Card containers
│   │   │   │   ├── select.jsx                        # Select dropdowns
│   │   │   │   ├── textarea.jsx                      # Text areas
│   │   │   │   └── progress.jsx                      # Progress indicators
│   │   │   │
│   │   │   ├── 📂 layout/                     # Layout Components
│   │   │   │   ├── MerchantLayout.jsx                # Main dashboard layout
│   │   │   │   ├── CustomerLayout.jsx                # Customer portal layout
│   │   │   │   ├── Sidebar.jsx                       # Navigation sidebar
│   │   │   │   ├── Header.jsx                        # Top navigation
│   │   │   │   ├── Footer.jsx                        # Footer component
│   │   │   │   └── TenantSwitcher.jsx                # Multi-tenant switcher
│   │   │   │
│   │   │   ├── 📂 forms/                      # Form Components
│   │   │   │   ├── ReturnForm.jsx                    # Return creation form
│   │   │   │   ├── OrderLookupForm.jsx               # Order search form
│   │   │   │   ├── ContactForm.jsx                   # Contact forms
│   │   │   │   └── FileUpload.jsx                    # File upload component
│   │   │   │
│   │   │   └── 📂 shared/                     # Shared Components
│   │   │       ├── SearchBar.jsx                     # Global search
│   │   │       ├── LoadingSpinner.jsx                # Loading indicators
│   │   │       ├── ErrorBoundary.jsx                 # Error handling
│   │   │       ├── Pagination.jsx                    # Pagination controls
│   │   │       └── StatusIndicator.jsx               # Status displays
│   │   │
│   │   ├── 📂 pages/                          # Page Components (Routes)
│   │   │   ├── 📂 customer/                   # Customer Portal Pages
│   │   │   │   ├── Start.jsx                         # Return initiation
│   │   │   │   ├── SelectItems.jsx                   # Item selection
│   │   │   │   ├── Resolution.jsx                    # Resolution choice
│   │   │   │   ├── Confirm.jsx                       # Final confirmation
│   │   │   │   ├── StatusTracker.jsx                 # Return tracking
│   │   │   │   └── ThankYou.jsx                      # Completion page
│   │   │   │
│   │   │   ├── 📂 merchant/                   # Merchant Dashboard Pages
│   │   │   │   ├── Dashboard.js                      # Main dashboard
│   │   │   │   ├── OrderDetail.jsx                   # Order details
│   │   │   │   │
│   │   │   │   ├── 📂 returns/                # Returns Management
│   │   │   │   │   ├── AllReturns.jsx                # Returns list view
│   │   │   │   │   ├── ReturnDetail.jsx              # Return details
│   │   │   │   │   ├── BulkActions.jsx               # Bulk operations
│   │   │   │   │   └── CreateReturn.jsx              # Manual return creation
│   │   │   │   │
│   │   │   │   ├── 📂 analytics/              # Analytics Pages
│   │   │   │   │   ├── Overview.jsx                  # Analytics overview
│   │   │   │   │   ├── Returns.jsx                   # Return analytics
│   │   │   │   │   ├── Financial.jsx                 # Financial reports
│   │   │   │   │   └── Customer.jsx                  # Customer insights
│   │   │   │   │
│   │   │   │   ├── 📂 settings/               # Settings Pages
│   │   │   │   │   ├── General.jsx                   # General settings
│   │   │   │   │   ├── Integrations.jsx              # Third-party integrations
│   │   │   │   │   ├── ReturnRules.jsx               # Business rules
│   │   │   │   │   ├── Branding.jsx                  # Brand customization
│   │   │   │   │   ├── Email.jsx                     # Email templates
│   │   │   │   │   ├── TeamAndRoles.jsx              # User management
│   │   │   │   │   └── Billing.jsx                   # Subscription billing
│   │   │   │   │
│   │   │   │   └── 📂 orders/                 # Order Management
│   │   │   │       ├── AllOrders.jsx                 # Orders list
│   │   │   │       ├── OrderDetail.jsx               # Order details
│   │   │   │       └── OrderSearch.jsx               # Advanced search
│   │   │   │
│   │   │   ├── 📂 admin/                      # Admin Panel Pages
│   │   │   │   ├── TenantManagement.jsx              # Tenant administration
│   │   │   │   ├── SystemHealth.jsx                  # System monitoring
│   │   │   │   ├── GlobalAnalytics.jsx               # Platform analytics
│   │   │   │   └── Configuration.jsx                 # Global configuration
│   │   │   │
│   │   │   └── 📂 auth/                       # Authentication Pages
│   │   │       ├── Login.jsx                         # Login page
│   │   │       ├── Signup.jsx                        # Registration
│   │   │       ├── ForgotPassword.jsx                # Password reset
│   │   │       └── OAuthCallback.jsx                 # OAuth callback handler
│   │   │
│   │   ├── 📂 hooks/                          # Custom React Hooks
│   │   │   ├── useApi.js                             # API calling hook
│   │   │   ├── useAuth.js                            # Authentication hook
│   │   │   ├── useTenant.js                          # Tenant context hook
│   │   │   ├── useWebSocket.js                       # WebSocket connection
│   │   │   ├── useLocalStorage.js                    # Local storage hook
│   │   │   ├── useDebounce.js                        # Debouncing hook
│   │   │   └── usePagination.js                      # Pagination hook
│   │   │
│   │   ├── 📂 context/                        # React Context Providers
│   │   │   ├── AuthContext.js                        # Authentication context
│   │   │   ├── TenantContext.js                      # Multi-tenant context
│   │   │   ├── ThemeContext.js                       # UI theme context
│   │   │   └── NotificationContext.js                # Notification system
│   │   │
│   │   ├── 📂 services/                       # Frontend Services
│   │   │   ├── api.js                                # API client configuration
│   │   │   ├── auth.js                               # Authentication service
│   │   │   ├── storage.js                            # Local storage service
│   │   │   ├── websocket.js                          # WebSocket service
│   │   │   └── analytics.js                          # Client-side analytics
│   │   │
│   │   ├── 📂 utils/                          # Utility Functions
│   │   │   ├── constants.js                          # Application constants
│   │   │   ├── helpers.js                            # Helper functions
│   │   │   ├── formatters.js                         # Data formatting
│   │   │   ├── validators.js                         # Form validation
│   │   │   └── date.js                               # Date utilities
│   │   │
│   │   ├── App.jsx                            # Main App Component
│   │   ├── App.css                            # Global CSS Styles
│   │   └── index.js                           # React App Entry Point
│   │
│   ├── 📂 public/                             # Static Assets
│   │   ├── index.html                                # HTML template
│   │   ├── favicon.ico                               # App favicon
│   │   ├── logo192.png                               # App logo (192px)
│   │   ├── logo512.png                               # App logo (512px)
│   │   ├── manifest.json                             # PWA manifest
│   │   └── robots.txt                                # SEO robots file
│   │
│   ├── package.json                           # Node.js Dependencies
│   ├── yarn.lock                              # Yarn Lock File
│   ├── tailwind.config.js                     # Tailwind CSS Configuration
│   ├── craco.config.js                        # CRACO Configuration
│   ├── postcss.config.js                      # PostCSS Configuration
│   ├── jsconfig.json                          # JavaScript Configuration
│   └── .env                                   # Frontend Environment Variables
│
├── 📂 docs/                                   # Documentation
│   ├── README.md                                     # Documentation index
│   ├── ARCHITECTURE.md                               # System architecture
│   ├── API.md                                        # API documentation
│   ├── DATABASE_SCHEMA.md                            # Database design
│   ├── SHOPIFY_INTEGRATION.md                        # Shopify integration guide
│   ├── SECURITY.md                                   # Security protocols
│   ├── DEPLOYMENT.md                                 # Deployment guide
│   ├── TROUBLESHOOTING.md                            # Common issues & solutions
│   ├── CONTRIBUTING.md                               # Contribution guidelines
│   ├── CHANGELOG.md                                  # Version history
│   ├── RUNBOOK.md                                    # Operations runbook
│   ├── VERIFICATION_LOG.md                           # Testing verification
│   ├── ENHANCED_FEATURES_SETUP.md                    # Advanced features setup
│   └── api.http                                      # HTTP request examples
│
├── 📂 tests/                                  # Test Suite
│   ├── 📂 unit/                               # Unit Tests
│   │   ├── test_services.py                          # Service layer tests
│   │   ├── test_controllers.py                       # Controller tests
│   │   ├── test_models.py                            # Model validation tests
│   │   └── test_utils.py                             # Utility function tests
│   │
│   ├── 📂 integration/                        # Integration Tests
│   │   ├── test_shopify_integration.py               # Shopify API tests
│   │   ├── test_database.py                          # Database integration tests
│   │   ├── test_webhooks.py                          # Webhook processing tests
│   │   └── test_auth_flow.py                         # Authentication flow tests
│   │
│   ├── 📂 e2e/                                # End-to-End Tests
│   │   ├── test_customer_flow.py                     # Customer return flow
│   │   ├── test_merchant_dashboard.py                # Merchant dashboard tests
│   │   └── test_admin_panel.py                       # Admin panel tests
│   │
│   ├── conftest.py                            # Pytest Configuration
│   ├── test_data.json                         # Test Data Fixtures
│   └── README.md                              # Testing Documentation
│
├── 📂 scripts/                                # Automation Scripts
│   ├── seed_database.py                              # Database seeding
│   ├── migrate_data.py                               # Data migration
│   ├── backup_database.py                            # Database backup
│   ├── deploy.sh                                     # Deployment script
│   ├── setup_dev_env.sh                             # Development setup
│   └── health_check.py                               # System health check
│
├── 📂 mock_data/                              # Sample Data
│   ├── orders_demo-store.json                        # Sample orders
│   ├── products_demo-store.json                      # Sample products
│   └── tenants_seed.json                             # Sample tenants
│
├── 🔧 Configuration Files
├── package.json                               # Root Package Configuration
├── yarn.lock                                  # Root Yarn Lock
├── Makefile                                   # Build Automation
├── docker-compose.yml                         # Docker Container Setup
├── Dockerfile                                 # Docker Image Definition
├── .gitignore                                 # Git Ignore Rules
├── .env.example                               # Environment Template
├── README.md                                  # Main Documentation (THIS FILE)
└── test_result.md                             # Testing Results Log

📊 TOTAL FILES: ~200+ files across all directories
📦 TOTAL SIZE: ~15MB (excluding node_modules and __pycache__)
🏗️ ARCHITECTURE: Hexagonal + CQRS + Domain Events
🛡️ SECURITY: Multi-tenant + OAuth 2.0 + Encryption
🔗 INTEGRATIONS: Shopify + Email + Payment + Storage + AI
```

### **Key Architecture Principles**

1. **Hexagonal Architecture**: Clear separation between business logic and external concerns
2. **CQRS Pattern**: Separate read and write operations for performance
3. **Domain Events**: Event-driven architecture for loose coupling
4. **Multi-tenancy**: Complete data isolation per tenant
5. **API-First**: RESTful APIs with OpenAPI documentation
6. **Security by Design**: Authentication, authorization, and audit logging
7. **Scalable Frontend**: Component-based React architecture
8. **Test-Driven**: Comprehensive test coverage across all layers

## ⚙️ Configuration Management

### **Environment-Specific Configuration**

#### **Development Environment (`.env`)**
```bash
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management_dev

# Application Settings
DEBUG=true
TESTING=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Security Configuration
ENCRYPTION_KEY=YourBase64EncodedFernetKey32Bytes=
JWT_SECRET_KEY=your-development-jwt-secret-key
SESSION_SECRET=your-session-secret-key

# Shopify Integration
SHOPIFY_API_KEY=0ef6de8c4bf0b4a3d8f7f99b42c53695
SHOPIFY_API_SECRET=db79f6174721b7acf332b69ef8f84374
SHOPIFY_API_VERSION=2025-07
SHOPIFY_REDIRECT_URI=http://localhost:3000/auth/shopify/callback
SHOPIFY_WEBHOOK_SECRET=your-webhook-secret

# External Services (Optional)
EMAIL_SERVICE_PROVIDER=sendgrid  # sendgrid, ses, smtp
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USERNAME=test
SMTP_PASSWORD=test

# File Storage
STORAGE_PROVIDER=local  # local, s3, gcs
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=returns-attachments-dev

# AI/ML Services
OPENAI_API_KEY=sk-your-openai-api-key
AI_FEATURES_ENABLED=false

# Performance & Monitoring
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your-sentry-dsn
ANALYTICS_ENABLED=true
PERFORMANCE_MONITORING=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=1000  # requests per hour
```

#### **Production Environment (`.env.production`)**
```bash
# Database Configuration - NEVER modify in production
MONGO_URL=mongodb://prod-cluster.mongodb.net:27017/returns_management_prod?ssl=true&authSource=admin
DB_NAME=returns_management_prod

# Application Settings
DEBUG=false
TESTING=false
LOG_LEVEL=WARN
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Security Configuration - CRITICAL: Use strong, unique keys
ENCRYPTION_KEY=GeneratedStrongFernetKeyForProductionUse=
JWT_SECRET_KEY=production-jwt-secret-minimum-32-characters
SESSION_SECRET=production-session-secret-minimum-32-characters

# Shopify Integration - Production App Credentials
SHOPIFY_API_KEY=your-production-shopify-api-key
SHOPIFY_API_SECRET=your-production-shopify-api-secret
SHOPIFY_API_VERSION=2025-07
SHOPIFY_REDIRECT_URI=https://yourdomain.com/auth/shopify/callback
SHOPIFY_WEBHOOK_SECRET=production-webhook-secret

# External Services
EMAIL_SERVICE_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.production-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com

# File Storage - Production S3
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_S3_BUCKET=returns-attachments-prod

# Performance & Monitoring
REDIS_URL=redis://production-redis:6379/0
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
NEW_RELIC_LICENSE_KEY=your-new-relic-key
LOG_AGGREGATION_ENDPOINT=https://logs.yourdomain.com/webhook

# Security Headers
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'"

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=10000  # requests per hour for production
PREMIUM_RATE_LIMIT=100000  # for enterprise customers
```

### **Frontend Configuration**

#### **Frontend Environment (`.env`)**
```bash
# Backend API Configuration - NEVER modify in production
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_API_VERSION=v1

# Application Configuration
REACT_APP_NAME=Returns Management SaaS
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_CHAT_SUPPORT=false
REACT_APP_ENABLE_PWA=true
REACT_APP_ENABLE_DARK_MODE=true

# External Service Keys (Client-side)
REACT_APP_GOOGLE_ANALYTICS_ID=GA-XXXX-XXXX
REACT_APP_SENTRY_DSN=https://your-frontend-sentry-dsn
REACT_APP_INTERCOM_APP_ID=your-intercom-app-id

# Development Configuration
WDS_SOCKET_PORT=443  # Required for development proxy
GENERATE_SOURCEMAP=true
```

### **Configuration Loading and Validation**

#### **Backend Configuration Handler (`/backend/src/config/environment.py`)**
```python
from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application configuration with validation and type safety
    """
    
    # Core Application
    APP_NAME: str = "Returns Management SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(False, description="Enable debug mode")
    TESTING: bool = Field(False, description="Enable testing mode")
    LOG_LEVEL: str = Field("INFO", regex="^(DEBUG|INFO|WARN|ERROR|CRITICAL)$")
    
    # Database
    MONGO_URL: str = Field(..., description="MongoDB connection string")
    DB_NAME: str = Field("returns_management", description="Database name")
    
    # Security
    ENCRYPTION_KEY: str = Field(..., description="Fernet encryption key (32 bytes base64)")
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="JWT signing key")
    SESSION_SECRET: str = Field(..., min_length=32, description="Session encryption key")
    CORS_ORIGINS: List[str] = Field(default_factory=list, description="Allowed CORS origins")
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @validator('ENCRYPTION_KEY')
    def validate_encryption_key(cls, v):
        """Validates Fernet key format"""
        try:
            from cryptography.fernet import Fernet
            Fernet(v.encode())
            return v
        except Exception:
            raise ValueError("Invalid Fernet encryption key format")
    
    # Shopify Integration
    SHOPIFY_API_KEY: str = Field(..., description="Shopify app API key")
    SHOPIFY_API_SECRET: str = Field(..., description="Shopify app API secret")
    SHOPIFY_API_VERSION: str = Field("2025-07", description="Shopify API version")
    SHOPIFY_REDIRECT_URI: str = Field(..., description="OAuth redirect URI")
    SHOPIFY_WEBHOOK_SECRET: Optional[str] = Field(None, description="Webhook verification secret")
    
    @validator('SHOPIFY_REDIRECT_URI')
    def validate_redirect_uri(cls, v):
        """Ensures redirect URI uses HTTPS in production"""
        if not cls.DEBUG and not v.startswith('https://'):
            raise ValueError("Redirect URI must use HTTPS in production")
        return v
    
    # External Services
    EMAIL_SERVICE_PROVIDER: str = Field("smtp", regex="^(smtp|sendgrid|ses)$")
    SENDGRID_API_KEY: Optional[str] = None
    SMTP_HOST: str = Field("localhost", description="SMTP server host")
    SMTP_PORT: int = Field(587, ge=1, le=65535)
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = Field("noreply@returns-manager.com", regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # File Storage
    STORAGE_PROVIDER: str = Field("local", regex="^(local|s3|gcs)$")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = Field("us-east-1")
    AWS_S3_BUCKET: Optional[str] = None
    
    # AI/ML Services
    OPENAI_API_KEY: Optional[str] = None
    AI_FEATURES_ENABLED: bool = Field(False)
    
    @validator('AI_FEATURES_ENABLED')
    def validate_ai_config(cls, v, values):
        """Requires OpenAI key when AI features are enabled"""
        if v and not values.get('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY required when AI_FEATURES_ENABLED=true")
        return v
    
    # Performance & Monitoring
    REDIS_URL: Optional[str] = Field(None, description="Redis connection string")
    SENTRY_DSN: Optional[str] = None
    ANALYTICS_ENABLED: bool = Field(True)
    PERFORMANCE_MONITORING: bool = Field(False)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(True)
    DEFAULT_RATE_LIMIT: int = Field(1000, ge=10, description="Default requests per hour")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True
        
    @classmethod
    def load_from_env(cls) -> 'Settings':
        """
        Loads settings with environment-specific overrides
        """
        # Check for environment-specific config files
        env = os.getenv('ENVIRONMENT', 'development')
        env_files = [
            '.env',  # Base configuration
            f'.env.{env}',  # Environment-specific overrides
            f'.env.local'  # Local developer overrides (git ignored)
        ]
        
        # Load configuration with file precedence
        settings = cls(_env_file=[f for f in env_files if Path(f).exists()])
        
        # Validate configuration for current environment
        settings._validate_environment_config()
        
        return settings
    
    def _validate_environment_config(self):
        """
        Validates configuration based on environment
        """
        if not self.DEBUG:  # Production validations
            # Ensure secure settings in production
            required_production_vars = [
                'ENCRYPTION_KEY', 'JWT_SECRET_KEY', 'SHOPIFY_API_SECRET'
            ]
            
            for var in required_production_vars:
                if not getattr(self, var):
                    raise ValueError(f"{var} is required in production")
            
            # Validate CORS origins are not wildcards
            if '*' in self.CORS_ORIGINS:
                raise ValueError("Wildcard CORS origins not allowed in production")
    
    def get_database_url(self) -> str:
        """Returns formatted database URL"""
        return f"{self.MONGO_URL}/{self.DB_NAME}"
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Checks if a feature is enabled"""
        feature_map = {
            'ai': self.AI_FEATURES_ENABLED,
            'analytics': self.ANALYTICS_ENABLED,
            'rate_limiting': self.RATE_LIMIT_ENABLED,
            'monitoring': self.PERFORMANCE_MONITORING
        }
        return feature_map.get(feature.lower(), False)

# Global settings instance
settings = Settings.load_from_env()

# Export commonly used settings
DATABASE_URL = settings.get_database_url()
IS_DEVELOPMENT = settings.DEBUG
IS_TESTING = settings.TESTING
```

This comprehensive documentation provides everything needed to understand, develop, deploy, and scale the Returns Management SaaS application. The architecture supports enterprise-level requirements while maintaining developer productivity and system reliability.