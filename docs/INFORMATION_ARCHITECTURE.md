# Returns Management SaaS - Information Architecture & Implementation Plan

## 📱 **Frontend Structure** (React + React Router)

```
/frontend/src/
├── pages/                          # Route-based pages
│   ├── merchant/                   # Merchant app (/app/*)
│   │   ├── Dashboard.jsx          # /app/dashboard
│   │   ├── returns/
│   │   │   ├── AllReturns.jsx     # /app/returns
│   │   │   └── ReturnDetail.jsx   # /app/returns/:id
│   │   ├── Orders.jsx             # /app/orders
│   │   ├── Rules.jsx              # /app/rules
│   │   ├── Workflows.jsx          # /app/workflows
│   │   ├── Analytics.jsx          # /app/analytics
│   │   ├── Billing.jsx            # /app/billing
│   │   └── settings/
│   │       ├── General.jsx        # /app/settings/general
│   │       ├── Branding.jsx       # /app/settings/branding
│   │       ├── Email.jsx          # /app/settings/email
│   │       ├── Integrations.jsx   # /app/settings/integrations
│   │       └── Team.jsx           # /app/settings/team
│   ├── customer/                  # Customer portal (public)
│   │   ├── Start.jsx             # /returns/start
│   │   ├── SelectItems.jsx       # /returns/select
│   │   ├── Resolution.jsx        # /returns/resolution
│   │   ├── Confirm.jsx           # /returns/confirm
│   │   └── Status.jsx            # /returns/status/:returnId
│   └── admin/                    # Super admin
│       ├── Tenants.jsx           # /admin/tenants
│       ├── Operations.jsx        # /admin/ops
│       ├── Audit.jsx             # /admin/audit
│       ├── FeatureFlags.jsx      # /admin/flags
│       └── Catalog.jsx           # /admin/catalog
├── components/                   # Reusable components
│   ├── ui/                      # Base UI components
│   │   ├── Button.jsx
│   │   ├── Modal.jsx
│   │   ├── Table.jsx
│   │   ├── Toast.jsx
│   │   └── Skeleton.jsx
│   ├── layout/                  # Layout components
│   │   ├── MerchantLayout.jsx   # Header + nav for merchant app
│   │   ├── CustomerLayout.jsx   # Simple layout for customer portal
│   │   ├── Header.jsx           # Tenant switcher, search, profile
│   │   └── Sidebar.jsx          # Navigation sidebar
│   ├── returns/                 # Return-specific components
│   │   ├── ReturnsTable.jsx     # Filterable returns list
│   │   ├── ReturnTimeline.jsx   # Status timeline
│   │   ├── ItemPicker.jsx       # Item selection widget
│   │   └── ResolutionStep.jsx   # Resolution choice
│   ├── analytics/               # Analytics components
│   │   ├── KPICards.jsx         # Metric cards
│   │   ├── ChartsPanel.jsx      # Chart widgets
│   │   └── ExportButtons.jsx    # CSV/PDF export
│   └── billing/                 # Billing components
│       ├── PlanSelector.jsx     # Plan cards
│       ├── UsageMeter.jsx       # Usage vs limits
│       └── UpgradeCTA.jsx       # Upgrade prompt
├── hooks/                       # Custom React hooks
│   ├── useAuth.js              # Authentication state
│   ├── useTenant.js            # Tenant context
│   ├── useReturns.js           # Returns data fetching
│   └── useBilling.js           # Billing state
├── services/                   # API services
│   ├── api.js                  # Base API client
│   ├── returns.js              # Returns API calls
│   ├── analytics.js            # Analytics API calls
│   └── billing.js              # Billing API calls
├── utils/                      # Utilities
│   ├── constants.js            # App constants
│   ├── formatters.js           # Data formatters
│   └── validators.js           # Form validation
└── App.jsx                     # Main app with routing
```

## 🔧 **Backend Structure** (FastAPI + Python)

```
/backend/src/
├── modules/                    # Feature modules
│   ├── auth/                  # Authentication & sessions
│   │   ├── __init__.py
│   │   ├── controller.py      # Auth endpoints
│   │   ├── service.py         # Auth business logic
│   │   ├── models.py          # Auth data models
│   │   └── shopify_oauth.py   # Shopify OAuth flow
│   ├── tenants/               # Tenant management
│   │   ├── __init__.py
│   │   ├── controller.py      # Tenant CRUD
│   │   ├── service.py         # Tenant logic
│   │   ├── models.py          # Tenant models
│   │   └── entitlements.py    # Plan/feature gating
│   ├── stores/                # Store profiles & tokens
│   │   ├── __init__.py
│   │   ├── controller.py      # Store management
│   │   ├── service.py         # Store logic
│   │   └── models.py          # Store models
│   ├── orders/                # Order sync & management
│   │   ├── __init__.py
│   │   ├── controller.py      # Order endpoints
│   │   ├── service.py         # Order sync logic
│   │   └── models.py          # Order models
│   ├── returns/               # Return management
│   │   ├── __init__.py
│   │   ├── controller.py      # Return endpoints
│   │   ├── service.py         # Return business logic
│   │   ├── models.py          # Return models
│   │   └── state_machine.py   # Status transitions
│   ├── rules/                 # Rules engine
│   │   ├── __init__.py
│   │   ├── controller.py      # Rules management
│   │   ├── service.py         # Rule evaluation
│   │   └── engine.py          # Rule processing logic
│   ├── workflows/             # Workflow engine (optional)
│   │   ├── __init__.py
│   │   ├── controller.py      # Workflow management
│   │   ├── service.py         # Workflow execution
│   │   └── builder.py         # Workflow builder APIs
│   ├── notifications/         # Email & notifications
│   │   ├── __init__.py
│   │   ├── controller.py      # Notification endpoints
│   │   ├── service.py         # Email service
│   │   └── templates.py       # Email templates
│   ├── billing/               # Stripe billing
│   │   ├── __init__.py
│   │   ├── controller.py      # Billing endpoints
│   │   ├── service.py         # Stripe integration
│   │   ├── webhooks.py        # Stripe webhooks
│   │   └── entitlements.py    # Feature gating
│   ├── analytics/             # Analytics & reporting
│   │   ├── __init__.py
│   │   ├── controller.py      # Analytics endpoints
│   │   ├── service.py         # Data aggregation
│   │   └── exports.py         # CSV/PDF generation
│   └── admin/                 # Super admin features
│       ├── __init__.py
│       ├── controller.py      # Admin endpoints
│       ├── service.py         # Admin operations
│       └── monitoring.py      # Health & monitoring
├── common/                    # Cross-cutting concerns
│   ├── __init__.py
│   ├── guards.py             # Auth guards
│   ├── interceptors.py       # Request/response interceptors
│   ├── errors.py             # Error handlers
│   ├── logging.py            # Structured logging
│   └── idempotency.py        # Idempotency helpers
├── adapters/                 # External integrations
│   ├── __init__.py
│   ├── shopify/
│   │   ├── live.py           # Real Shopify API
│   │   └── mock.py           # Mock Shopify API
│   ├── email/
│   │   ├── resend.py         # Resend integration
│   │   └── smtp.py           # SMTP fallback
│   ├── payments/
│   │   └── stripe.py         # Stripe integration
│   └── storage/
│       └── s3.py             # AWS S3 for labels/files
├── infra/                    # Infrastructure
│   ├── __init__.py
│   ├── database.py           # MongoDB connection
│   ├── redis.py              # Redis for caching/queues
│   └── queues.py             # Background job queues
├── config/                   # Configuration
│   ├── __init__.py
│   ├── settings.py           # App settings
│   └── schema.py             # Config validation
└── tests/                    # Test suites
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    ├── e2e/                  # End-to-end tests
    └── fixtures/             # Test data
```

## 🎫 **Implementation Tickets** 

### **Phase 1: Information Architecture Implementation**

#### **Ticket 1: Frontend Route Structure**
**Files to create/modify:**
- `frontend/src/App.jsx` - Update with new routing structure
- `frontend/src/pages/merchant/Dashboard.jsx` - Main dashboard
- `frontend/src/pages/customer/Start.jsx` - Customer portal entry
- `frontend/src/components/layout/MerchantLayout.jsx` - Merchant app layout
- `frontend/src/components/layout/Header.jsx` - Header with tenant switcher

**Acceptance Criteria:**
- [ ] All routes defined match the IA structure
- [ ] Navigation works between all pages
- [ ] Mobile-responsive design
- [ ] Tenant switcher functional in header

#### **Ticket 2: Backend Module Structure** 
**Files to create:**
- `backend/src/modules/tenants/controller.py` - Tenant management endpoints
- `backend/src/modules/stores/controller.py` - Store profile management
- `backend/src/modules/billing/controller.py` - Billing endpoints
- `backend/src/modules/workflows/controller.py` - Workflow management
- `backend/src/modules/admin/controller.py` - Super admin features

**Acceptance Criteria:**
- [ ] Module structure matches IA blueprint
- [ ] All controllers have basic CRUD endpoints
- [ ] Proper error handling and validation
- [ ] Repository pattern implemented

#### **Ticket 3: Customer Return Flow Pages**
**Files to create:**
- `frontend/src/pages/customer/Start.jsx`
- `frontend/src/pages/customer/SelectItems.jsx`  
- `frontend/src/pages/customer/Resolution.jsx`
- `frontend/src/pages/customer/Confirm.jsx`
- `frontend/src/pages/customer/Status.jsx`

**Acceptance Criteria:**
- [ ] Complete customer flow: start → select → resolution → confirm → status
- [ ] Mobile-optimized design
- [ ] Proper validation and error handling
- [ ] Integration with backend APIs

#### **Ticket 4: Merchant Returns Management**
**Files to create:**
- `frontend/src/pages/merchant/returns/AllReturns.jsx`
- `frontend/src/pages/merchant/returns/ReturnDetail.jsx`
- `frontend/src/components/returns/ReturnsTable.jsx`
- `frontend/src/components/returns/ReturnTimeline.jsx`

**Acceptance Criteria:**
- [ ] Filterable returns list (status, date, customer)
- [ ] Return detail with timeline and actions
- [ ] Status transitions with validation
- [ ] Bulk actions support

#### **Ticket 5: State Machine Implementation**
**Files to create/modify:**
- `backend/src/modules/returns/state_machine.py` - Enhanced state machine
- `backend/src/modules/returns/service.py` - Return business logic
- `backend/src/modules/returns/controller.py` - Return endpoints

**Acceptance Criteria:**
- [ ] Complete state machine: requested → approved → resolved
- [ ] Illegal transitions blocked with clear errors
- [ ] Idempotent transition handling
- [ ] Audit trail for all state changes

### **Phase 2: User Flow Implementation**

#### **Ticket 6: Onboarding Wizard**
**Files to create:**
- `frontend/src/pages/merchant/Onboarding.jsx`
- `frontend/src/components/onboarding/BrandingStep.jsx`
- `frontend/src/components/onboarding/PolicyStep.jsx`
- `frontend/src/components/onboarding/EmailStep.jsx`
- `frontend/src/components/onboarding/ShopifyStep.jsx`
- `frontend/src/components/onboarding/TestStep.jsx`

**Acceptance Criteria:**
- [ ] 5-step wizard: Brand → Policy → Email → Shopify → Test
- [ ] Each step saves progress
- [ ] < 10 minute completion time
- [ ] End-to-end return test works

#### **Ticket 7: Rules Engine with Simulation**
**Files to create/modify:**
- `backend/src/modules/rules/engine.py` - Enhanced rules engine
- `backend/src/modules/rules/controller.py` - Rules management
- `frontend/src/pages/merchant/Rules.jsx` - Rules editor

**Acceptance Criteria:**
- [ ] Rule simulation with step-by-step explanation
- [ ] Visual rule builder interface
- [ ] Test rule scenarios
- [ ] Rule priority and precedence

#### **Ticket 8: Billing Integration**
**Files to create:**
- `backend/src/modules/billing/stripe.py` - Stripe integration
- `backend/src/modules/billing/webhooks.py` - Webhook handlers
- `frontend/src/pages/merchant/Billing.jsx` - Billing dashboard
- `frontend/src/components/billing/PlanSelector.jsx` - Plan selection

**Acceptance Criteria:**
- [ ] Stripe test mode integration
- [ ] Plan upgrade/downgrade flows
- [ ] Usage limits with upgrade CTAs
- [ ] Webhook idempotency

### **Phase 3: Analytics & Admin**

#### **Ticket 9: Analytics Dashboard**
**Files to create:**
- `frontend/src/pages/merchant/Analytics.jsx`
- `frontend/src/components/analytics/KPICards.jsx`
- `frontend/src/components/analytics/ChartsPanel.jsx`
- `backend/src/modules/analytics/exports.py`

**Acceptance Criteria:**
- [ ] Configurable dashboard with saved layouts
- [ ] KPIs: return rate, exchange %, revenue saved
- [ ] CSV/PDF exports match filters
- [ ] Real-time data updates

#### **Ticket 10: Super Admin Features**
**Files to create:**
- `frontend/src/pages/admin/Tenants.jsx`
- `frontend/src/pages/admin/Operations.jsx`
- `frontend/src/pages/admin/Audit.jsx`
- `backend/src/modules/admin/monitoring.py`

**Acceptance Criteria:**
- [ ] Tenant management and health monitoring
- [ ] System-wide audit logs
- [ ] Feature flag management
- [ ] Queue health monitoring

## 🧪 **Testing Strategy**

### **Unit Tests** (per module)
- Repository layer tests
- Service logic tests  
- State machine tests
- Rules engine tests

### **Integration Tests**
- API endpoint tests
- Database integration tests
- External service mocks
- Webhook handling tests

### **E2E Tests** (Playwright)
- Complete customer return flow
- Merchant processing workflow
- Billing upgrade flow
- Multi-tenant isolation

### **Load Tests** (Locust)
- 100 RPS for 2 minutes
- Key endpoints: returns, analytics
- Performance budgets: <300ms reads, <800ms writes

## ✅ **Acceptance Checklist** (for QA)

### **Customer Portal**
- [ ] Start → select → resolution → confirm → status works on mobile
- [ ] Invalid order/email shows friendly error, no crashes
- [ ] Branding reflects merchant settings
- [ ] Offline mode shows cached data with timestamp

### **Merchant Dashboard** 
- [ ] All navigation links work correctly
- [ ] Returns list: pagination, search, filters functional
- [ ] Return detail: timeline, actions, rule explanations
- [ ] Illegal state transitions blocked with clear messages

### **Multi-Tenancy**
- [ ] Tenant switcher changes data correctly
- [ ] No cross-tenant data leakage
- [ ] Audit logs capture tenant context

### **Billing**
- [ ] Plan limits enforced with upgrade CTAs
- [ ] Stripe webhooks update entitlements within 60s
- [ ] Usage meters accurate and real-time

---

**This blueprint provides:**
1. **Exact file paths** for every component and module
2. **Specific tickets** with clear acceptance criteria  
3. **Testing strategy** aligned with requirements
4. **QA checklist** for final verification

Ready to implement! Should I start with **Ticket 1: Frontend Route Structure** to establish the navigation foundation?