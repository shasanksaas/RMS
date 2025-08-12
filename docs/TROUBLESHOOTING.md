# Troubleshooting Guide

*Last updated: 2025-01-11*

## Common Error Patterns

### OAuth & Authentication Errors

#### ❌ `invalid_request: redirect_uri not whitelisted`

**Full Error:**
```
error=invalid_request&error_description=The+redirect_uri+is+not+whitelisted
```

**Root Cause:**
Shopify app configuration doesn't match the callback URL being used.

**Debugging:**
```bash
# Check current APP_URL
echo $APP_URL
cat /app/backend/.env | grep APP_URL

# Check what URL is being generated
curl "http://localhost:8001/api/auth/shopify/install?shop=rms34.myshopify.com"
```

**Solution:**
1. **Update Shopify App Settings:**
   - Go to https://partners.shopify.com
   - Find your app and click "Edit"
   - Set "App URL": `https://returnportal.preview.emergentagent.com/app`
   - Set "Allowed redirection URLs": `https://returnportal.preview.emergentagent.com/api/auth/shopify/callback`
   - **Important**: No trailing slashes!

2. **Update Environment:**
   ```bash
   # Update backend/.env
   APP_URL=https://returnportal.preview.emergentagent.com
   
   # Restart backend
   sudo supervisorctl restart backend
   ```

#### ❌ `invalid_request: matching hosts`

**Error Message:**
```
The redirect_uri is not allowed. The redirect_uri host must match the app URL host.
```

**Cause:**
Domain mismatch between app URL and callback URL.

**Fix:**
```bash
# Ensure both URLs use same domain
APP_URL=https://returnportal.preview.emergentagent.com

# Callback should be:
# https://returnportal.preview.emergentagent.com/api/auth/shopify/callback
```

#### ❌ `401 Unauthorized` from Shopify API

**Symptoms:**
- GraphQL queries return 401
- Order lookup fails with authentication error
- Integration status shows disconnected

**Debug Steps:**
```bash
# 1. Check stored access token
mongo returns_management --eval "
  db.integrations_shopify.findOne({tenant_id: 'tenant-rms34'}, {access_token: 1});
"

# 2. Test token decryption
cd /app/backend
python3 -c "
from src.modules.auth.service import AuthService
auth = AuthService()
# Replace with actual encrypted token from database
encrypted = 'gAAAAABhk...'
try:
    decrypted = auth.decrypt_token(encrypted)
    print(f'Token valid, starts with: {decrypted[:10]}...')
except Exception as e:
    print(f'Decryption failed: {e}')
"

# 3. Test token with Shopify directly
curl -H "X-Shopify-Access-Token: shpat_..." \
  https://rms34.myshopify.com/admin/api/2024-10/shop.json
```

**Solutions:**
1. **Re-authenticate:** Force OAuth flow again
2. **Check encryption key:** Ensure `ENCRYPTION_KEY` hasn't changed
3. **Verify scopes:** App might need re-authorization for new scopes

### Database & Collection Errors

#### ❌ Collection Mismatch: "Return not found"

**Symptoms:**
- Returns created successfully but don't appear in merchant dashboard
- API returns empty results
- Customer portal works but merchant view is empty

**Debug:**
```bash
# Check which collections have data
mongo returns_management --eval "
  print('returns collection:', db.returns.count());
  print('return_requests collection:', db.return_requests.count());
  
  // Show sample documents
  db.returns.findOne();
  db.return_requests.findOne();
"

# Check what API is querying
grep -r "return_requests\|\.returns" /app/backend/src/controllers/
```

**Fix:**
Ensure all controllers use the same collection name:
```python
# In controllers/returns_controller_enhanced.py
# Should use 'returns' collection:
returns = await db.returns.find(query).sort(sort_field, sort_direction)

# NOT 'return_requests':
# returns = await db.return_requests.find(query)  # ❌ Wrong
```

#### ❌ "Not Found" API Errors (404)

**Common Cases:**
- `GET /api/returns/{return_id}` returns 404
- Return exists in database but API can't find it

**Debug:**
```bash
# 1. Check if return exists
mongo returns_management --eval "
  db.returns.findOne({id: 'ed2af19e-9626-4389-ad79-2ab509cebe67'});
"

# 2. Check tenant ID in request
curl -v -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/returns/ed2af19e-9626-4389-ad79-2ab509cebe67

# 3. Verify endpoint registration
grep -r "returns/{return_id}" /app/backend/src/controllers/
```

**Common Issues:**
1. **Tenant mismatch:** Frontend using wrong tenant ID
2. **Trailing slash:** API expects `/api/returns/` but called without slash
3. **Route not registered:** Controller not included in main app

### Frontend API Communication

#### ❌ Mixed Content Errors (HTTPS/HTTP)

**Error in Browser:**
```
Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure resource 'http://...'. This request has been blocked.
```

**Debug:**
```bash
# Check environment variables
cat /app/frontend/.env
# Should show: REACT_APP_BACKEND_URL=https://...

# Check for hardcoded HTTP URLs in code
grep -r "http://" /app/frontend/src/
```

**Fix:**
```javascript
// Remove hardcoded fallbacks in components
// ❌ Wrong:
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ✅ Correct:
const backendUrl = process.env.REACT_APP_BACKEND_URL;
```

#### ❌ "Failed to fetch" / Network Errors

**Symptoms:**
- Frontend shows "Failed to load data"
- Network tab shows failed requests
- CORS errors in console

**Debug:**
```bash
# 1. Test API directly
curl -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/returns/

# 2. Check if backend is running
sudo supervisorctl status backend

# 3. Check backend logs
tail -f /var/log/supervisor/backend.err.log

# 4. Verify frontend environment
cd /app/frontend
echo $REACT_APP_BACKEND_URL
```

**Solutions:**
1. **Restart services:**
   ```bash
   sudo supervisorctl restart all
   ```

2. **Clear browser cache:**
   - Hard refresh (Ctrl+Shift+R)
   - Clear localStorage
   - Disable cache in DevTools

3. **Check CORS settings:**
   ```python
   # In backend/server.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # For development
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Tenant & Multi-tenancy Issues

#### ❌ Missing X-Tenant-Id Header

**Error:**
```json
{
  "detail": "X-Tenant-Id header is required"
}
```

**Debug:**
```bash
# Check middleware configuration
grep -A 10 -B 5 "X-Tenant-Id" /app/backend/src/middleware/security.py

# Test with correct header
curl -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/returns/
```

**Fix:**
Ensure all frontend API calls include tenant header:
```javascript
// Add to all fetch calls
const headers = {
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'tenant-rms34'  // Use correct tenant ID
};
```

#### ❌ Wrong Tenant ID in Frontend

**Symptoms:**
- APIs return empty results
- "Not found" errors for existing data
- Integration status shows disconnected

**Debug:**
```bash
# Check what tenant IDs exist
mongo returns_management --eval "
  db.tenants.distinct('id');
  db.integrations_shopify.distinct('tenant_id');
"

# Verify frontend tenant configuration
grep -r "tenant-" /app/frontend/src/pages/
```

**Fix:**
Update hardcoded tenant IDs in frontend components:
```javascript
// Should be consistent across all components
const tenantId = 'tenant-rms34';  // Main connected tenant
```

### Shopify Integration Issues

#### ❌ GraphQL Query Errors

**Error Response:**
```json
{
  "errors": [
    {
      "message": "Field 'lineItems' doesn't exist on type 'Order'",
      "extensions": {"code": "INVALID_FIELD"}
    }
  ]
}
```

**Cause:**
GraphQL schema changes or API version mismatch.

**Fix:**
```python
# Check API version in use
API_VERSION = "2024-10"

# Update GraphQL query to match API version
query = """
query GetOrder($id: ID!) {
  order(id: $id) {
    id
    name
    lineItems(first: 50) {  # Correct field name
      edges {
        node {
          id
          title
          quantity
        }
      }
    }
  }
}
"""
```

#### ❌ Webhook HMAC Verification Failed

**Error in Logs:**
```
ERROR: Webhook HMAC verification failed
```

**Debug:**
```bash
# 1. Check HMAC secret
echo $SHOPIFY_API_SECRET

# 2. Test HMAC calculation
python3 -c "
import hmac, hashlib, base64
payload = b'{\"test\": \"data\"}'
secret = 'your_secret_here'
calculated = base64.b64encode(hmac.new(secret.encode(), payload, hashlib.sha256).digest())
print(f'Expected HMAC: {calculated.decode()}')
"

# 3. Check webhook logs
grep -A 5 -B 5 "HMAC" /var/log/supervisor/backend.err.log
```

**Fix:**
1. **Verify secret:** Ensure `SHOPIFY_API_SECRET` matches app settings
2. **Check payload:** Webhook payload must be verified before parsing
3. **Update verification logic:**
   ```python
   def verify_webhook_hmac(payload: bytes, hmac_header: str) -> bool:
       calculated_hmac = hmac.new(
           SHOPIFY_API_SECRET.encode('utf-8'),
           payload,  # Raw bytes, not parsed JSON
           hashlib.sha256
       ).digest()
       
       expected_hmac = base64.b64encode(calculated_hmac)
       provided_hmac = hmac_header.encode('utf-8')
       
       return hmac.compare_digest(expected_hmac, provided_hmac)
   ```

### Performance & Timeout Issues

#### ❌ Database Query Timeouts

**Error:**
```
pymongo.errors.ServerSelectionTimeoutError: timed out
```

**Debug:**
```bash
# Check database connection
mongo returns_management --eval "db.runCommand({ping: 1})"

# Check slow queries
mongo returns_management --eval "
  db.setProfilingLevel(2, {slowms: 1000});
  // Run some queries
  db.system.profile.find().sort({ts: -1}).limit(5);
"

# Check indexes
mongo returns_management --eval "
  db.returns.getIndexes();
  db.orders.getIndexes();
"
```

**Fix:**
Add missing indexes:
```bash
mongo returns_management --eval "
  db.returns.createIndex({tenant_id: 1, created_at: -1});
  db.returns.createIndex({tenant_id: 1, status: 1});
  db.orders.createIndex({tenant_id: 1, order_number: 1});
"
```

#### ❌ API Response Times > 5 seconds

**Debug:**
```bash
# Measure API response times
curl -w "@curl-format.txt" -o /dev/null \
  -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/returns/

# Check database query performance
mongo returns_management --eval "
  db.returns.find({tenant_id: 'tenant-rms34'}).explain('executionStats');
"
```

**Optimization:**
1. **Add pagination:** Limit large result sets
2. **Use projections:** Only fetch needed fields
3. **Cache results:** Cache expensive operations
4. **Optimize queries:** Add compound indexes

### File Upload Issues

#### ❌ Photo Upload Fails

**Error:** `413 Request Entity Too Large`

**Fix:**
```python
# Increase file size limits in FastAPI
from fastapi import FastAPI, File, UploadFile

@app.post("/upload")
async def upload_file(file: UploadFile = File(..., max_size=10*1024*1024)):  # 10MB
    # Process file
```

**Error:** `422 Validation Error`

**Debug:**
```bash
# Check file upload endpoint
curl -X POST \
  -H "X-Tenant-Id: tenant-rms34" \
  -F "file=@test.jpg" \
  -F "return_id=test123" \
  https://your-app.com/api/elite/portal/returns/upload-photo
```

## Error Monitoring & Logging

### Log Analysis Commands

```bash
# Find all errors in last hour
grep -E "ERROR|Exception" /var/log/supervisor/backend.err.log | \
  awk -v date="$(date -d '1 hour ago' '+%Y-%m-%d %H:')" '$0 > date'

# Count error types
grep "ERROR" /var/log/supervisor/backend.err.log | \
  awk '{print $4}' | sort | uniq -c | sort -nr

# Find slow API calls
grep "response_time" /var/log/supervisor/backend.out.log | \
  awk '$NF > 3000' | tail -10

# Database connection errors
grep "connection" /var/log/supervisor/backend.err.log | tail -20
```

### Setting Up Alerts

```bash
# Create alert script
cat > /app/scripts/error_monitor.sh << 'EOF'
#!/bin/bash
ERROR_COUNT=$(grep -c "ERROR" /var/log/supervisor/backend.err.log | tail -100)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "High error rate: $ERROR_COUNT errors in last 100 lines"
    # Send notification (email, Slack, etc.)
fi
EOF

# Add to crontab for regular monitoring
crontab -e
# Add: */5 * * * * /app/scripts/error_monitor.sh
```

### Debug Mode

```bash
# Enable debug logging
echo "DEBUG=true" >> /app/backend/.env
sudo supervisorctl restart backend

# View debug logs
tail -f /var/log/supervisor/backend.out.log | grep DEBUG

# Disable when done
sed -i 's/DEBUG=true/DEBUG=false/' /app/backend/.env
```

## Recovery Procedures

### Emergency Reset
```bash
# If system is completely broken:
1. Stop all services
   sudo supervisorctl stop all

2. Restore from backup
   mongorestore --drop /backup/latest/returns_management

3. Reset configuration
   cp /app/backend/.env.backup /app/backend/.env

4. Clear logs
   sudo truncate -s 0 /var/log/supervisor/*.log

5. Restart everything
   sudo supervisorctl start all

6. Verify system health
   curl https://your-app.com/api/health
```

### Data Recovery
```bash
# If data corruption detected:
1. Stop writes to database
2. Identify last known good backup
3. Calculate data loss window
4. Restore from backup
5. Replay any critical transactions
6. Verify data integrity
```

---

**Next**: See [SECURITY.md](./SECURITY.md) for security guidelines.