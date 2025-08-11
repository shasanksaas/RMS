# API Reference

*Last updated: 2025-01-11*

## Endpoint Index

| Method | Path | Auth | Tenant | Purpose |
|--------|------|------|--------|---------|
| **Authentication & Setup** |
| GET | `/api/auth/shopify/install` | No | No | Start Shopify OAuth flow |
| GET | `/api/auth/shopify/callback` | No | No | OAuth callback handler |
| GET | `/api/health` | No | No | Service health check |
| **Integration Management** |
| GET | `/api/integrations/shopify/status` | No | Yes | Check Shopify connection |
| POST | `/api/integrations/shopify/resync` | No | Yes | Trigger data resync |
| GET | `/api/integrations/shopify/jobs` | No | Yes | List sync jobs |
| **Orders** |
| GET | `/api/orders/` | No | Yes | List orders with pagination |
| GET | `/api/orders/{order_id}` | No | Yes | Get specific order details |
| **Returns (Merchant)** |
| GET | `/api/returns/` | No | Yes | List returns with search/filter |
| GET | `/api/returns/{return_id}` | No | Yes | Get return details |
| **Elite Portal (Customer)** |
| POST | `/api/elite/portal/returns/lookup-order` | No | Yes | Find order for return |
| GET | `/api/elite/portal/returns/orders/{order_id}/eligible-items` | No | Yes | Get returnable items |
| POST | `/api/elite/portal/returns/policy-preview` | No | Yes | Preview return policy |
| POST | `/api/elite/portal/returns/create` | No | Yes | Create return request |
| POST | `/api/elite/portal/returns/create-draft` | No | Yes | Save draft return |
| POST | `/api/elite/portal/returns/upload-photo` | No | Yes | Upload return item photo |
| **Elite Admin (Merchant)** |
| GET | `/api/elite/admin/returns/` | No | Yes | List returns for admin |
| GET | `/api/elite/admin/returns/{return_id}` | No | Yes | Admin return details |
| POST | `/api/elite/admin/returns/{return_id}/approve` | No | Yes | Approve return |
| POST | `/api/elite/admin/returns/{return_id}/reject` | No | Yes | Reject return |
| POST | `/api/elite/admin/returns/bulk-action` | No | Yes | Bulk approve/reject |
| **Testing & Debug** |
| POST | `/api/testing/webhook` | No | No | Test webhook handling |
| POST | `/api/testing/sync/{tenant_id}` | No | No | Manual sync trigger |
| GET | `/api/testing/stores/{tenant_id}/connection` | No | No | Test store connection |

## Common Headers

### Required for Tenant APIs
```http
X-Tenant-Id: tenant-rms34
Content-Type: application/json
```

### Optional Headers
```http
X-Request-ID: unique-request-id
User-Agent: Returns-Portal/1.0
```

## Authentication APIs

### Start Shopify OAuth
```http
GET /api/auth/shopify/install?shop=rms34.myshopify.com
```

**Response:**
```json
{
  "install_url": "https://rms34.myshopify.com/admin/oauth/authorize?client_id=...&scope=read_orders,read_products&redirect_uri=..."
}
```

### OAuth Callback
```http
GET /api/auth/shopify/callback?code=auth_code&shop=rms34.myshopify.com&state=...
```

**Success Response:** Redirects to merchant dashboard
**Error Response:**
```json
{
  "error": "invalid_request",
  "error_description": "The provided authorization code is invalid"
}
```

## Integration APIs

### Check Shopify Status
```http
GET /api/integrations/shopify/status
X-Tenant-Id: tenant-rms34
```

**Response:**
```json
{
  "connected": true,
  "shop": "rms34.myshopify.com",
  "installedAt": "2025-01-10T10:30:00Z",
  "lastSyncAt": "2025-01-11T09:15:22Z",
  "webhooks": [
    {"topic": "orders/create", "status": "active"},
    {"topic": "orders/updated", "status": "active"}
  ],
  "returnCounts": {
    "total": 45,
    "last30d": 12
  },
  "syncJob": {
    "status": "completed",
    "startedAt": "2025-01-11T09:00:00Z",
    "completedAt": "2025-01-11T09:15:22Z"
  }
}
```

### Trigger Resync
```http
POST /api/integrations/shopify/resync
X-Tenant-Id: tenant-rms34
Content-Type: application/json

{
  "type": "full",
  "days": 90
}
```

**Response:**
```json
{
  "job_id": "sync_job_123",
  "status": "queued",
  "estimated_duration": "5-10 minutes"
}
```

## Orders APIs

### List Orders
```http
GET /api/orders/?page=1&pageSize=20&search=1001&status=fulfilled
X-Tenant-Id: tenant-rms34
```

**Response:**
```json
{
  "orders": [
    {
      "id": "5813364687033",
      "order_number": "1001",
      "customer_email": "shashankshekharofficial15@gmail.com",
      "customer_name": "Shashank Shekhar",
      "total_price": "400.00",
      "currency": "USD",
      "status": "fulfilled",
      "created_at": "2025-08-10T12:43:24Z",
      "line_items": [
        {
          "id": "13851721105593",
          "title": "TESTORDER",
          "quantity": 1,
          "price": "400.00",
          "sku": "N/A"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

### Get Order Details
```http
GET /api/orders/5813364687033
X-Tenant-Id: tenant-rms34
```

**Response:**
```json
{
  "id": "5813364687033",
  "order_number": "1001",
  "customer": {
    "email": "shashankshekharofficial15@gmail.com",
    "first_name": "Shashank",
    "last_name": "Shekhar"
  },
  "line_items": [
    {
      "id": "13851721105593",
      "title": "TESTORDER",
      "variant_title": null,
      "quantity": 1,
      "price": "400.00",
      "sku": "N/A",
      "product_id": "8553062793401"
    }
  ],
  "total_price": "400.00",
  "currency": "USD",
  "created_at": "2025-08-10T12:43:24Z",
  "fulfillment_status": "fulfilled",
  "return_window_days": 30,
  "eligible_for_return": true
}
```

## Returns APIs (Merchant)

### List Returns
```http
GET /api/returns/?page=1&pageSize=10&status=requested&search=shashank
X-Tenant-Id: tenant-rms34
```

**Response:**
```json
{
  "returns": [
    {
      "id": "ed2af19e-9626-4389-ad79-2ab509cebe67",
      "order_number": "1001",
      "order_id": "5813364687033",
      "customer_name": "Shashankshekharofficial15",
      "customer_email": "shashankshekharofficial15@gmail.com",
      "status": "REQUESTED",
      "decision": "",
      "item_count": 1,
      "estimated_refund": 354.01,
      "created_at": "2025-08-11T10:30:38.017000",
      "updated_at": "2025-08-11T10:30:38.017000"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "total": 20,
    "totalPages": 2
  }
}
```

### Get Return Details
```http
GET /api/returns/ed2af19e-9626-4389-ad79-2ab509cebe67
X-Tenant-Id: tenant-rms34
```

**Response:**
```json
{
  "id": "ed2af19e-9626-4389-ad79-2ab509cebe67",
  "order_id": "5813364687033",
  "order_number": "1001",
  "customer": {
    "name": "Shashankshekharofficial15",
    "email": "shashankshekharofficial15@gmail.com"
  },
  "status": "REQUESTED",
  "decision": "",
  "channel": "customer",
  "return_method": "customer_ships",
  "items": [
    {
      "fulfillment_line_item_id": "13851721105593",
      "title": "TESTORDER",
      "variant_title": null,
      "sku": "N/A",
      "quantity": 1,
      "price": 400.0,
      "refundable_amount": 400.0,
      "reason": "Defective",
      "condition": "damaged"
    }
  ],
  "estimated_refund": 354.01,
  "created_at": "2025-08-11T10:30:38.017000",
  "updated_at": "2025-08-11T10:30:38.017000"
}
```

## Elite Portal APIs (Customer)

### Lookup Order
```http
POST /api/elite/portal/returns/lookup-order
X-Tenant-Id: tenant-rms34
Content-Type: application/json

{
  "order_number": "1001",
  "customer_email": "shashankshekharofficial15@gmail.com"
}
```

**Success Response:**
```json
{
  "success": true,
  "mode": "shopify_live",
  "order": {
    "id": "5813364687033",
    "order_number": "1001",
    "customer": {
      "email": "shashankshekharofficial15@gmail.com",
      "first_name": "Shashank",
      "last_name": "Shekhar"
    },
    "line_items": [
      {
        "id": "13851721105593",
        "title": "TESTORDER",
        "quantity": 1,
        "unit_price": 400.00,
        "sku": "N/A"
      }
    ],
    "created_at": "2025-08-10T12:43:24Z",
    "source": "shopify_live"
  }
}
```

**Order Not Found:**
```json
{
  "success": false,
  "mode": "not_found",
  "order": null,
  "message": "Order #1001 not found in Shopify store"
}
```

### Create Return
```http
POST /api/elite/portal/returns/create
X-Tenant-Id: tenant-rms34
Content-Type: application/json

{
  "order_id": "5813364687033",
  "customer_email": "shashankshekharofficial15@gmail.com",
  "return_method": "customer_ships",
  "items": [
    {
      "line_item_id": "13851721105593",
      "quantity": 1,
      "reason": "Defective",
      "title": "TESTORDER",
      "unit_price": 400.00,
      "sku": "N/A",
      "condition": "damaged"
    }
  ],
  "reason": "Product defective",
  "resolution_type": "refund"
}
```

**Success Response:**
```json
{
  "success": true,
  "return_request": {
    "return_id": "ed2af19e-9626-4389-ad79-2ab509cebe67",
    "status": "requested",
    "estimated_refund": {
      "amount": 354.01,
      "currency": "USD"
    },
    "tracking_info": {
      "return_id": "ed2af19e-9626-4389-ad79-2ab509cebe67",
      "status_url": "/returns/status/ed2af19e-9626-4389-ad79-2ab509cebe67"
    }
  }
}
```

### Upload Photo
```http
POST /api/elite/portal/returns/upload-photo
X-Tenant-Id: tenant-rms34
Content-Type: multipart/form-data

form-data:
  file: [binary image data]
  return_id: "ed2af19e-9626-4389-ad79-2ab509cebe67"
  line_item_id: "13851721105593"
```

**Response:**
```json
{
  "success": true,
  "photo_url": "https://cdn.example.com/returns/photos/abc123.jpg",
  "photo_id": "photo_456"
}
```

## Error Responses

### Validation Errors (422)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "return_method"],
      "msg": "Field required"
    }
  ]
}
```

### Authentication Errors (401)
```json
{
  "detail": "Invalid or expired access token"
}
```

### Authorization Errors (403)
```json
{
  "detail": "Insufficient permissions for this operation"
}
```

### Not Found (404)
```json
{
  "detail": "Return request not found"
}
```

### Rate Limiting (429)
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

### Shopify API Errors (502)
```json
{
  "detail": "Shopify API unavailable",
  "shopify_errors": [
    {
      "message": "Shop is currently unavailable",
      "code": "SHOP_UNAVAILABLE"
    }
  ]
}
```

## GraphQL Queries Used

The following Shopify GraphQL queries are used internally:

### Order Lookup
```graphql
query GetOrder($id: ID!) {
  order(id: $id) {
    id
    name
    email
    createdAt
    customer {
      firstName
      lastName
      email
    }
    lineItems(first: 50) {
      edges {
        node {
          id
          title
          quantity
          variant {
            id
            title
            sku
            price
          }
          product {
            id
            title
          }
        }
      }
    }
    totalPriceSet {
      shopMoney {
        amount
        currencyCode
      }
    }
  }
}
```

Variables: `{"id": "gid://shopify/Order/5813364687033"}`

---

**Next**: See [FRONTEND_MAP.md](./FRONTEND_MAP.md) for UI component mappings.