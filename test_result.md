#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
# ## user_problem_statement: {problem_statement}
# ## backend:
# ##   - task: "Task name"
# ##     implemented: true
# ##     working: true  # or false or "NA"
# ##     file: "file_path.py"
# ##     stuck_count: 0
# ##     priority: "high"  # or "medium" or "low"
# ##     needs_retesting: false
# ##     status_history:
# ##         -working: true  # or false or "NA"
# ##         -agent: "main"  # or "testing" or "user"
# ##         -comment: "Detailed comment about status"
# ##
# ## frontend:
# ##   - task: "Task name"
# ##     implemented: true
# ##     working: true  # or false or "NA"
# ##     file: "file_path.js"
# ##     stuck_count: 0
# ##     priority: "high"  # or "medium" or "low"
# ##     needs_retesting: false
# ##     status_history:
# ##         -working: true  # or false or "NA"
# ##         -agent: "main"  # or "testing" or "user"
# ##         -comment: "Detailed comment about status"
# ##
# ## metadata:
# ##   created_by: "main_agent"
# ##   version: "1.0"
# ##   test_sequence: 0
# ##   run_ui: false
# ##
# ## test_plan:
# ##   current_focus:
# ##     - "Task name 1"
# ##     - "Task name 2"
# ##   stuck_tasks:
# ##     - "Task name with persistent issues"
# ##   test_all: false
# ##   test_priority: "high_first"  # or "sequential" or "stuck_first"
# ##
# ##   - task: "Admin Impersonation for tenant-rms34 with Shopify Connection"
#    implemented: true
#    working: true
#    file: "src/controllers/tenant_admin_controller.py, integrations_shopify collection"
#    stuck_count: 0
#    priority: "high"
#    needs_retesting: false
#    status_history:
#      - working: "NA"
#        agent: "user"
#        comment: "Fix admin impersonation for tenant-rms34 to show a fully functional merchant dashboard with Shopify connection. SPECIFIC FIXES NEEDED: 1. Check tenant-rms34 Shopify connection status - verify if it has existing Shopify integration data 2. Create/Update Shopify connection for tenant-rms34 - set up proper connection with shop domain 'rms34.myshopify.com' 3. Fix Shopify OAuth redirect URL whitelisting - ensure impersonated sessions can connect to Shopify without redirect URL errors 4. Test impersonation session authentication - verify that admin impersonation tokens work with Shopify OAuth endpoints"

agent_communication:
  - agent: "main"
    message: "Added public form config under /api/public and updated middleware to bypass tenant isolation for these routes. Fixed merchant FormCustomization to read tenant_id from currentTenant and auth token from auth_token; updated file upload param to asset_type. Updated customer Start.jsx to fetch /api/public/forms config and removed any hardcoded URL fallbacks per ingress rules."
  - agent: "testing"
    message: "Backend testing completed successfully. Public form config endpoint at /api/public/forms/{tenant_id}/config is working correctly - returns proper JSON structure with config.branding, layout, and form keys without requiring authentication or tenant headers. Tenant isolation middleware properly bypasses /api/public paths while still enforcing tenant requirements for other /api routes. Fixed missing /api/public/ path in server.py security middleware skip list. CORS is working correctly with proper headers when Origin is present. All regression tests passed - no route conflicts detected."

backend:
  - task: "Move public form config under /api/public and allow through middleware"
    implemented: true
    working: true
    file: "server.py, src/middleware/tenant_isolation.py, src/controllers/public_form_config_controller.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Mounted public_form_config_router at /api/public/forms by including router with prefix /api and adding /api/public paths to TenantIsolationMiddleware public_paths."
      - working: true
        agent: "testing"
        comment: "✅ VERIFIED: Public form config endpoint at /api/public/forms/{tenant_id}/config works correctly. Returns JSON with config.branding, layout, form keys without requiring auth or X-Tenant-Id header. Tenant isolation middleware properly bypasses /api/public paths. Orders endpoint regression check passed - still requires X-Tenant-Id. CORS headers present with Origin header. Fixed missing /api/public/ in server.py skip_tenant_validation list. Minor: CORS OPTIONS method returns 405 as expected since endpoint only supports GET."
  - task: "Test backend GET /api/orders/{order_id} lookup with fallbacks for tenant-rms34"
    implemented: true
    working: true
    file: "src/controllers/orders_controller_enhanced.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "testing"
        comment: "✅ VERIFIED: Order lookup endpoint GET /api/orders/{order_id} working perfectly with robust fallback mechanisms. Successfully tested with sample numeric ID 6375150223682 (correctly returns 404 with 'Order not found' detail). Fallback lookups work via id, order_id, shopify_order_id, and order_number (with/without # prefix). All required UI keys present in response: id, order_number, customer_name, customer_email, financial_status, fulfillment_status, total_price, currency_code, line_items, created_at, updated_at, shipping_address, returns, shopify_order_url. Tenant isolation working correctly - requires X-Tenant-Id header and blocks cross-tenant access. Orders list endpoint regression test passed - still requires X-Tenant-Id header. All 36 tests passed with 100% success rate."

frontend:
  - task: "Fix FormCustomization tenant context and token usage"
    implemented: true
    working: true
    file: "src/pages/merchant/settings/FormCustomization.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Replaced currentTenantId key usage with currentTenant, corrected Authorization header to use auth_token, and fixed upload-asset field name to asset_type. URLs use REACT_APP_BACKEND_URL strictly."
  - task: "Customer Start.jsx config fetch path fix"
    implemented: true
    working: true
    file: "src/pages/customer/Start.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Fetch public form config from /api/public/forms/{tenant}/config instead of non-/api path; removed hardcoded localhost fallback."