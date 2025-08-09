# Returns Management SaaS - Site Map & User Journey

## 🗺️ **Site Map** (Copy to Notion/Jira)

### **Customer Return Portal** (Public - returns.yourdomain.com)
```
📱 Customer Portal (/returns)
├── 🚀 Start Return (/returns/start)
│   ├── Order lookup (number + email)
│   ├── Validation & error handling
│   └── → Select Items
├── 📦 Select Items (/returns/select)  
│   ├── Item list with quantities
│   ├── Return reasons per item
│   └── → Choose Resolution
├── 💰 Choose Resolution (/returns/resolution)
│   ├── Refund option
│   ├── Exchange suggestions
│   ├── Store credit (with bonus)
│   └── → Confirm & Submit
├── ✅ Confirm & Submit (/returns/confirm)
│   ├── Review details
│   ├── Policy acceptance
│   └── → Status Tracking
└── 📊 Status Tracking (/returns/status/:returnId)
    ├── Timeline view
    ├── Label download
    └── Email updates
```

### **Merchant App** (Embedded in Shopify + Standalone)
```
🏪 Merchant Dashboard (/app)
├── 📈 Dashboard (/app/dashboard)
│   ├── KPI cards (returns, revenue impact)
│   ├── Recent activity
│   └── Quick actions
├── 📋 Returns Management
│   ├── 📄 All Returns (/app/returns)
│   │   ├── Filters (status, date, customer)
│   │   ├── Search & sorting
│   │   ├── Bulk actions
│   │   └── Export options
│   └── 🔍 Return Detail (/app/returns/:id)
│       ├── Customer info & order details
│       ├── Timeline & audit trail
│       ├── Action buttons (approve, deny, resolve)
│       └── Rule explanation
├── 🛒 Orders (/app/orders)
│   ├── Synced order list
│   ├── Return eligibility status
│   └── Link to create return
├── ⚙️ Rules Engine (/app/rules)
│   ├── Rule builder interface
│   ├── Simulation tool
│   ├── Test scenarios
│   └── Rule priority management
├── 🔄 Workflows (/app/workflows) [Feature Flag]
│   ├── Workflow list
│   ├── Builder canvas (/app/workflows/:id)
│   ├── Trigger configuration
│   └── Analytics
├── 📊 Analytics (/app/analytics)
│   ├── Configurable dashboard
│   ├── Time period filters
│   ├── Export tools (CSV, PDF)
│   └── Performance metrics
├── 💳 Billing (/app/billing)
│   ├── Current plan & usage
│   ├── Plan comparison
│   ├── Upgrade/downgrade
│   └── Payment history
└── ⚙️ Settings
    ├── 🏢 General (/app/settings/general)
    │   ├── Store info
    │   ├── Return policies
    │   └── Notification preferences
    ├── 🎨 Branding (/app/settings/branding)
    │   ├── Logo upload
    │   ├── Color customization
    │   └── Custom messages
    ├── 📧 Email (/app/settings/email)
    │   ├── SMTP/Resend setup
    │   ├── Template customization
    │   └── Test sending
    ├── 🔌 Integrations (/app/settings/integrations)
    │   ├── Shopify connection
    │   ├── Stripe setup
    │   └── Third-party apps
    └── 👥 Team & Roles (/app/settings/team) [Feature Flag]
        ├── User management
        ├── Role assignment
        └── Permission matrix
```

### **Super Admin** (Internal - admin.yourdomain.com)
```
🔧 Super Admin (/admin)
├── 🏢 Tenants (/admin/tenants)
│   ├── Tenant list & health
│   ├── Plan assignments
│   └── Support actions
├── ⚡ Operations (/admin/ops)
│   ├── System health
│   ├── Queue monitoring
│   └── Performance metrics
├── 📋 Audit & Logs (/admin/audit)
│   ├── Security events
│   ├── API usage
│   └── Error tracking
├── 🚩 Feature Flags (/admin/flags)
│   ├── Flag management
│   ├── Rollout controls
│   └── A/B testing
└── 📚 Templates Catalog (/admin/catalog)
    ├── Email templates
    ├── Workflow templates
    └── Rule presets
```

## 🎯 **Core User Journeys** (Step-by-Step)

### **Journey A: Customer Creates Return** ⭐
```
1. 📱 Customer visits returns.store.com/returns/start
2. 🔍 Enters Order #ORD-12345 + Email: customer@email.com
3. ✅ System validates → Shows order details
4. 📦 Customer selects items + quantities + reasons
5. 💰 Chooses resolution: "Refund to original payment"
6. ⚙️ Rules engine evaluates → "Auto-approved" 
7. ✅ Confirmation screen → Return #RET-67890 created
8. 📧 Email sent with return label
9. 📊 Customer can track at /returns/status/RET-67890
```

**Edge Cases Handled:**
- ❌ Wrong order/email → "Order not found" + retry option
- ⏰ Outside return window → "Policy message" + manual review option
- 🚫 Excluded item → "Not eligible" with explanation

### **Journey B: Merchant Processes Return** ⭐
```
1. 🏪 Merchant opens /app/returns → Sees "New" returns
2. 🔍 Clicks return #RET-67890 → Opens detail view
3. 👁️ Reviews: customer info, items, rule explanation
4. ✅ Clicks "Approve" → Status changes to "Approved"
5. 📧 Customer gets email notification
6. 📦 Customer ships item → Status becomes "In Transit"
7. 🏢 Warehouse receives → Merchant marks "Received"
8. 💰 Merchant resolves → "Refund $49.99" 
9. ✅ Stripe processes refund → Status "Resolved"
10. 📊 Analytics updated → KPIs refreshed
```

**Guardrails:**
- 🚫 Can't resolve before receiving → Blocked with message
- 📝 All actions logged → Audit trail visible
- 🔁 Idempotent operations → Safe retries

### **Journey C: First-Time Setup** ⭐
```
1. 🚀 New merchant installs app → Onboarding wizard starts
2. 🏢 Step 1: Brand setup → Logo, colors, support email
3. 📋 Step 2: Return policy → Window (30 days), auto-approve rules
4. 📧 Step 3: Email setup → Test send to verify SMTP/Resend
5. 🛒 Step 4: Shopify connect → OAuth flow or "Use demo data"
6. 🧪 Step 5: Test return → Create sample return end-to-end
7. ✅ "Setup complete!" → Redirected to dashboard
8. ⏱️ Total time: < 10 minutes
```

### **Journey D: Billing Upgrade** ⭐
```
1. 💳 Merchant hits AI suggestion limit → Upgrade CTA shown
2. 🔍 Clicks "Upgrade" → Redirected to /app/billing
3. 📊 Sees plan comparison → Selects "Growth ($49/month)"
4. 💰 Stripe checkout → Payment processed
5. 🔄 Webhook received → Entitlements updated immediately
6. ✨ AI suggestions now available → Feature gates removed
7. 📧 Confirmation email sent → Billing cycle starts
```

## 🧪 **Testing Scenarios** (QA Checklist)

### **Smoke Tests** (Must pass before release)
- [ ] Customer can complete return flow in < 3 minutes
- [ ] Merchant can process return without errors
- [ ] All navigation links work correctly
- [ ] Mobile layout doesn't break on any page
- [ ] Cross-tenant data isolation working

### **Edge Case Tests**
- [ ] Invalid order/email handling
- [ ] Network failure recovery
- [ ] Simultaneous merchant actions
- [ ] Plan limit enforcement
- [ ] Webhook replay handling

### **Performance Tests**
- [ ] Page load times < 2s on 3G
- [ ] API response times < 300ms (reads)
- [ ] API response times < 800ms (writes)
- [ ] 100 concurrent returns processing

### **Security Tests**
- [ ] SQL injection attempts blocked
- [ ] Cross-tenant access attempts blocked  
- [ ] PII properly redacted in logs
- [ ] Rate limiting working correctly
- [ ] Authentication bypass attempts fail

## 📋 **Ready-to-Use Tickets** (Copy to Jira)

### **Epic: Customer Portal Implementation**
**Story Points: 21**

#### **Ticket 1: Customer Return Flow - Start Page**
- **Files**: `frontend/src/pages/customer/Start.jsx`
- **Acceptance**: Order lookup works, validation errors shown
- **Points**: 3

#### **Ticket 2: Customer Return Flow - Item Selection**
- **Files**: `frontend/src/pages/customer/SelectItems.jsx`
- **Acceptance**: Multi-item selection, reasons, quantities
- **Points**: 5

#### **Ticket 3: Customer Return Flow - Resolution & Confirmation**
- **Files**: `frontend/src/pages/customer/Resolution.jsx`, `Confirm.jsx`
- **Acceptance**: Resolution options, final confirmation
- **Points**: 3

#### **Ticket 4: Customer Return Flow - Status Tracking**
- **Files**: `frontend/src/pages/customer/Status.jsx`
- **Acceptance**: Timeline view, email updates
- **Points**: 2

#### **Ticket 5: Customer Portal Mobile Optimization**
- **Files**: CSS updates across customer pages
- **Acceptance**: Works on 320px+ screens
- **Points**: 2

#### **Ticket 6: Customer Portal Integration Testing**
- **Files**: E2E test suite
- **Acceptance**: Complete flow tested automatically
- **Points**: 3

#### **Ticket 7: Customer Portal Error Handling**
- **Files**: Error boundary, validation
- **Acceptance**: Friendly errors, no crashes
- **Points**: 3

---

**This structure provides:**
- ✅ **Exact site map** ready for Notion/Jira
- ✅ **Step-by-step user journeys** with success/error paths
- ✅ **Testing scenarios** with specific acceptance criteria
- ✅ **Ready-to-use tickets** with story points and file paths

The blueprint is now **dev-ready**! Should I proceed with implementing **Ticket 1: Frontend Route Structure** to establish the foundation?