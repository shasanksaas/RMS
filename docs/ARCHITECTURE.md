# System Architecture

*Last updated: 2025-01-11*

## Overview

This Returns Management SaaS follows **Hexagonal Architecture** (Ports & Adapters) with **CQRS** (Command Query Responsibility Segregation) patterns for clean separation of concerns and testability.

## Architecture Patterns

### Hexagonal Architecture Implementation

```mermaid
graph TB
    subgraph "External Adapters"
        HTTP[HTTP Controllers]
        Shopify[Shopify API Adapter]
        MongoDB[MongoDB Adapter]
        Email[Email Service Adapter]
    end
    
    subgraph "Application Layer (CQRS)"
        Commands[Commands]
        Queries[Queries]
        CommandHandlers[Command Handlers]
        QueryHandlers[Query Handlers]
    end
    
    subgraph "Domain Layer"
        Entities[Domain Entities]
        Services[Domain Services]
        Ports[Ports/Interfaces]
        Events[Domain Events]
    end
    
    HTTP --> CommandHandlers
    HTTP --> QueryHandlers
    CommandHandlers --> Services
    QueryHandlers --> Services
    Services --> Ports
    Ports <--> Shopify
    Ports <--> MongoDB
    Services --> Events
```

### File Structure Mapping

```
backend/src/
├── controllers/          # External HTTP Adapters
│   ├── elite_portal_returns_controller.py
│   └── returns_controller_enhanced.py
├── application/          # CQRS Application Layer
│   ├── commands.py       # Write operations
│   ├── queries.py        # Read operations
│   └── handlers/
│       ├── command_handlers.py
│       └── query_handlers.py
├── domain/              # Core Business Logic
│   ├── entities/        # Business entities
│   ├── services/        # Domain services
│   ├── ports/           # Interfaces to external world
│   ├── value_objects.py # Immutable value objects
│   └── events.py        # Domain events
└── infrastructure/      # External Adapters Implementation
    ├── repositories/    # Data persistence adapters
    └── services/        # External service adapters
```

## Multi-tenancy Design

Every operation is scoped by `tenant_id`:

```mermaid
sequenceDiagram
    participant F as Frontend
    participant M as Middleware
    participant C as Controller
    participant S as Service
    participant DB as Database
    
    F->>M: Request + X-Tenant-Id header
    M->>M: Validate tenant & extract ID
    M->>C: tenant_id as dependency
    C->>S: Pass tenant_id to service
    S->>DB: Query with tenant_id filter
    DB-->>S: Tenant-scoped results
    S-->>C: Business objects
    C-->>F: HTTP response
```

**Implementation Details:**
- `middleware/security.py`: Extracts and validates `X-Tenant-Id`
- All database queries include `{"tenant_id": tenant_id}` filter
- No cross-tenant data leakage possible

## Key Flows

### 1. Shopify OAuth Installation

```mermaid
sequenceDiagram
    participant M as Merchant
    participant F as Frontend
    participant B as Backend
    participant S as Shopify
    participant DB as Database
    
    M->>F: Click "Connect to Shopify"
    F->>B: GET /api/auth/shopify/install
    B->>B: Generate install URL with scopes
    B-->>F: Redirect to Shopify
    F->>S: OAuth authorization
    S->>B: Callback with auth code
    B->>S: Exchange code for access token
    S-->>B: Access token + shop info
    B->>DB: Store encrypted token in integrations_shopify
    B-->>F: Redirect to success page
```

**File Locations:**
- Controller: `controllers/shopify_integration_controller.py`
- Service: `services/shopify_service.py`
- Auth handling: `modules/auth/service.py`

### 2. Real-time Order Lookup (Customer Portal)

```mermaid
sequenceDiagram
    participant C as Customer
    participant F as Frontend
    participant B as Backend
    participant S as Shopify API
    participant DB as Database
    
    C->>F: Enter order number + email
    F->>B: POST /api/elite/portal/returns/lookup-order
    B->>DB: Check integrations_shopify for token
    B->>S: GraphQL query for order
    S-->>B: Live order data (customer, items, pricing)
    B->>B: Transform GraphQL response
    B-->>F: Order details + eligibility
    F->>F: Display items for return selection
```

**GraphQL Query Used:**
- `order(id: "gid://shopify/Order/{order_id}")` 
- Fields: customer, lineItems, totalPrice, createdAt
- File: `services/shopify_service.py:find_order_by_number()`

### 3. Return Creation Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant Events as Event Bus
    
    C->>F: Submit return form
    F->>B: POST /api/elite/portal/returns/create
    B->>B: CreateReturnCommand
    B->>B: CommandHandler validates & processes
    B->>DB: Save to returns collection
    B->>Events: Publish ReturnCreated event
    Events->>B: Trigger notifications/workflows
    B-->>F: Return confirmation
    F->>F: Show success page
```

**CQRS Implementation:**
- Command: `application/commands.py:CreateReturnCommand`
- Handler: `application/handlers/command_handlers.py:CreateReturnCommandHandler`
- Repository: `infrastructure/repositories/mongo_return_repository.py`

### 4. Merchant Dashboard Data Loading

```mermaid
sequenceDiagram
    participant M as Merchant
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant S as Shopify API
    
    M->>F: Visit /app/returns
    F->>B: GET /api/returns/
    B->>DB: Query returns collection with tenant_id
    B->>DB: For each return, lookup related order
    B->>S: Fetch live order numbers via GraphQL
    B->>B: Merge return + order data
    B-->>F: Returns list with live Shopify data
    F->>F: Render table with eye icons
```

**Data Enhancement:**
- Base data from `returns` collection
- Order numbers fetched live from Shopify GraphQL
- Customer names derived from Shopify customer data
- File: `controllers/returns_controller_enhanced.py`

## Event-Driven Architecture

Domain events enable loose coupling:

```mermaid
graph LR
    Command[Create Return] --> Handler[Command Handler]
    Handler --> Event[ReturnCreated Event]
    Event --> Notification[Email Notification]
    Event --> Audit[Audit Log]
    Event --> Webhook[External Webhooks]
    Event --> Analytics[Analytics Update]
```

**Event Types:**
- `ReturnCreated`: New return request submitted
- `ReturnApproved`: Merchant approved return
- `ReturnProcessed`: Refund issued
- `OrderSynced`: Shopify order data updated

**Implementation:**
- Events: `domain/events.py`
- Publishers: Domain services emit events
- Subscribers: Infrastructure services handle events

## Performance & Scalability

### Caching Strategy
- **Redis**: Session data, temporary tokens
- **Application Cache**: Shopify GraphQL responses (5 min TTL)
- **Database Indexes**: On tenant_id, created_at, status fields

### Database Design
- **Sharding**: By tenant_id for horizontal scaling
- **Read Replicas**: Analytics queries use read-only replicas
- **Connection Pooling**: MongoDB motor async driver

### API Rate Limiting
- **Shopify API**: Respects cost analysis, implements backoff
- **Public APIs**: Rate limited per tenant (100/min default)
- **File Uploads**: Chunked uploads for large files

## Security Layers

### Authentication & Authorization
1. **Shopify OAuth**: Validates merchant identity
2. **Tenant Validation**: Every request requires valid tenant_id
3. **API Scopes**: Different endpoints require different Shopify scopes
4. **Secrets Management**: All tokens encrypted at rest

### Data Protection
- **Encryption**: Access tokens encrypted with Fernet
- **PII Handling**: Customer data minimized, logged carefully
- **Audit Trail**: All data changes logged with user context

---

**Next**: See [API.md](./API.md) for detailed endpoint documentation.