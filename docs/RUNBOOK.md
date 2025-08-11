# Operations Runbook

*Last updated: 2025-01-11*

## On-Call Quick Reference

### Emergency Contacts
- **Platform**: Emergent Support
- **Primary Developer**: Check git blame for recent changes
- **Database**: MongoDB Atlas (if external) or local MongoDB

### System Status Dashboard
```bash
# Health check endpoints
curl https://your-app.com/api/health
curl -H "X-Tenant-Id: tenant-rms34" https://your-app.com/api/integrations/shopify/status

# Service status
sudo supervisorctl status
```

## Common Issues & Fixes

### 🔴 Critical: OAuth Integration Down

**Symptoms:**
- Merchants can't connect to Shopify  
- "redirect_uri not whitelisted" errors
- 401/403 errors from Shopify API

**Immediate Actions:**
```bash
# 1. Check environment variables
cd /app/backend
cat .env | grep -E "SHOPIFY|APP_URL"

# 2. Verify APP_URL matches Shopify app settings
# Should be: https://f07a6717-33e5-45c0-b306-b76d55047333.preview.emergentagent.com

# 3. Check Shopify app configuration at:
# https://partners.shopify.com/organizations/your-org/apps/your-app/edit

# 4. Test OAuth flow
curl "https://your-app.com/api/auth/shopify/install?shop=test-store.myshopify.com"
```

**Root Cause Analysis:**
```bash
# Check recent deployments
git log --oneline -10

# Check for configuration changes
grep -r "redirect" /app/backend/src/controllers/shopify_integration_controller.py

# Verify callback endpoint
curl -I https://your-app.com/api/auth/shopify/callback
```

**Resolution Steps:**
1. **Update Shopify App Settings:**
   - Go to Shopify Partners dashboard
   - Update "App URL" and "Allowed redirection URLs"
   - Ensure no trailing slashes

2. **Fix Environment Variables:**
   ```bash
   # Update .env file
   vim /app/backend/.env
   # Restart backend
   sudo supervisorctl restart backend
   ```

3. **Clear OAuth Cache:**
   ```bash
   # Clear any cached OAuth states
   mongo returns_management --eval "db.oauth_states.deleteMany({})"
   ```

### 🔴 Critical: Webhooks Not Processing

**Symptoms:**
- New orders not appearing in system
- Webhook endpoint returning 401/500 errors
- Shopify webhook status shows failures

**Immediate Actions:**
```bash
# 1. Check webhook logs
tail -f /var/log/supervisor/backend.err.log | grep webhook

# 2. Test webhook endpoint directly
curl -X POST \
  -H "X-Shopify-Hmac-Sha256: test" \
  -H "X-Shopify-Shop-Domain: rms34.myshopify.com" \
  -H "Content-Type: application/json" \
  -d '{"test": true}' \
  https://your-app.com/api/webhooks/orders/create

# 3. Check webhook registration
curl -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/integrations/shopify/status | jq '.webhooks'
```

**HMAC Verification Debug:**
```bash
# Check HMAC secret in environment
echo $SHOPIFY_API_SECRET

# Debug HMAC calculation
python3 -c "
import hmac, hashlib, base64
payload = b'{\"test\": true}'
secret = 'your_shopify_secret'
calculated = base64.b64encode(hmac.new(secret.encode(), payload, hashlib.sha256).digest())
print(f'Calculated HMAC: {calculated.decode()}')
"
```

**Fix Steps:**
1. **Re-register webhooks:**
   ```bash
   curl -X POST -H "X-Tenant-Id: tenant-rms34" \
     https://your-app.com/api/integrations/shopify/resync
   ```

2. **Update webhook URLs:**
   ```python
   # In shopify_integration_controller.py
   webhook_urls = [
       f"{APP_URL}/api/webhooks/orders/create",
       f"{APP_URL}/api/webhooks/orders/updated", 
       f"{APP_URL}/api/webhooks/app/uninstalled"
   ]
   ```

### 🟡 High: Data Sync Issues

**Symptoms:**
- Orders/customers out of sync with Shopify
- Customer portal shows "order not found"
- Missing order data in merchant dashboard

**Diagnosis:**
```bash
# Check sync job status
curl -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/integrations/shopify/jobs | jq '.jobs[0]'

# Check database collections
mongo returns_management --eval "
  db.orders.count({tenant_id: 'tenant-rms34'});
  db.returns.count({tenant_id: 'tenant-rms34'});
  db.sync_jobs.find({tenant_id: 'tenant-rms34'}).limit(3);
"

# Test Shopify GraphQL access
curl -X POST \
  -H "X-Shopify-Access-Token: shpat_..." \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  https://rms34.myshopify.com/admin/api/2024-10/graphql.json
```

**Fix Steps:**
1. **Trigger manual sync:**
   ```bash
   curl -X POST -H "X-Tenant-Id: tenant-rms34" \
     -H "Content-Type: application/json" \
     -d '{"type": "full", "days": 30}' \
     https://your-app.com/api/integrations/shopify/resync
   ```

2. **Check access token:**
   ```python
   # In Python shell
   from src.modules.auth.service import AuthService
   auth = AuthService()
   
   # Test decryption
   encrypted_token = "gAAAAAB..."  # from database
   decrypted = auth.decrypt_token(encrypted_token)
   print(f"Token: {decrypted[:10]}...")
   ```

3. **Clear sync locks:**
   ```bash
   mongo returns_management --eval "
     db.sync_jobs.updateMany(
       {status: 'running', started_at: {\$lt: new Date(Date.now() - 3600000)}},
       {\$set: {status: 'failed', error: 'Timeout'}}
     );
   "
   ```

### 🟡 High: Customer Portal Errors

**Symptoms:**
- "Order not found" for valid orders
- 500 errors during return creation
- Frontend showing network errors

**Debug Steps:**
```bash
# 1. Test order lookup API
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-rms34" \
  -d '{"order_number": "1001", "customer_email": "test@example.com"}' \
  https://your-app.com/api/elite/portal/returns/lookup-order

# 2. Check tenant configuration
mongo returns_management --eval "
  db.tenants.findOne({id: 'tenant-rms34'});
  db.integrations_shopify.findOne({tenant_id: 'tenant-rms34'});
"

# 3. Test return creation
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-rms34" \
  -d '{
    "order_id": "5813364687033",
    "customer_email": "test@example.com",
    "return_method": "customer_ships",
    "items": [{"line_item_id": "123", "quantity": 1, "reason": "defective"}],
    "resolution_type": "refund"
  }' \
  https://your-app.com/api/elite/portal/returns/create
```

**Common Fixes:**
1. **Tenant ID mismatch:**
   ```javascript
   // Check frontend components for hardcoded tenant IDs
   grep -r "tenant-" /app/frontend/src/pages/
   
   // Should be: tenant-rms34 for main tenant
   ```

2. **Collection name issues:**
   ```python
   # Check if using wrong collection
   # Should be 'returns' not 'return_requests'
   grep -r "return_requests" /app/backend/src/controllers/
   ```

### 🟠 Medium: Performance Issues

**Symptoms:**
- Slow API responses (>5 seconds)
- Database timeouts
- High memory usage

**Monitoring:**
```bash
# Check system resources
top
df -h
free -m

# Check database performance
mongo returns_management --eval "db.runCommand({currentOp: true})"

# API response times
curl -w "@curl-format.txt" -o /dev/null \
  -H "X-Tenant-Id: tenant-rms34" \
  https://your-app.com/api/returns/

# Create curl-format.txt:
cat > curl-format.txt << EOF
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

**Optimization:**
```bash
# Add database indexes
mongo returns_management --eval "
  db.returns.createIndex({tenant_id: 1, created_at: -1});
  db.orders.createIndex({tenant_id: 1, order_number: 1});
"

# Clear large log files
sudo truncate -s 0 /var/log/supervisor/backend.err.log
sudo truncate -s 0 /var/log/supervisor/frontend.err.log
```

## Rollback Procedures

### Code Rollback
```bash
# 1. Check recent commits
git log --oneline -10

# 2. Rollback to previous version
git checkout HEAD~1

# 3. Restart services
sudo supervisorctl restart all

# 4. Verify rollback
curl https://your-app.com/api/health
```

### Database Rollback
```bash
# 1. Check recent schema changes
mongo returns_management --eval "
  db.schema_migrations.find().sort({created_at: -1}).limit(5);
"

# 2. Run rollback migration (if exists)
python /app/scripts/rollback_migration.py --to=previous

# 3. Verify data integrity
mongo returns_management --eval "
  db.returns.count();
  db.orders.count();
"
```

### Configuration Rollback
```bash
# 1. Restore previous environment file
cp /app/backend/.env.backup /app/backend/.env

# 2. Restart backend
sudo supervisorctl restart backend

# 3. Verify configuration
curl https://your-app.com/api/integrations/shopify/status
```

## Monitoring & Alerts

### Key Metrics to Track
```bash
# Error rates
grep -c "ERROR" /var/log/supervisor/backend.err.log | tail -100

# Response times  
tail -f /var/log/supervisor/backend.out.log | grep "response_time"

# Database connections
mongo returns_management --eval "db.runCommand({serverStatus: 1}).connections"

# Webhook success rates
mongo returns_management --eval "
  db.webhook_events.aggregate([
    {\$group: {
      _id: '\$processed',
      count: {\$sum: 1}
    }}
  ]);
"
```

### Alert Thresholds
- **Error rate**: >5% over 5 minutes
- **Response time**: >3 seconds average
- **Database connections**: >80% of max
- **Webhook failures**: >10% over 15 minutes
- **Disk space**: >90% full

## Backup & Recovery

### Database Backup
```bash
# Create backup
mongodump --db returns_management --out /backup/$(date +%Y%m%d_%H%M%S)

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
mongodump --db returns_management --out $BACKUP_DIR
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Keep only last 7 days
find /backup -name "*.tar.gz" -mtime +7 -delete
```

### Application Backup
```bash
# Backup configuration
tar -czf /backup/config_$(date +%Y%m%d).tar.gz \
  /app/backend/.env \
  /app/frontend/.env

# Backup custom code (if modified)
tar -czf /backup/code_$(date +%Y%m%d).tar.gz \
  /app/backend/src \
  /app/frontend/src
```

### Recovery Procedures
```bash
# Restore database
tar -xzf /backup/20250111_120000.tar.gz
mongorestore --db returns_management --drop /backup/20250111_120000/returns_management

# Restore configuration  
tar -xzf /backup/config_20250111.tar.gz -C /
sudo supervisorctl restart all

# Verify restoration
curl https://your-app.com/api/health
```

## Security Incident Response

### Suspected Breach
1. **Immediate Actions:**
   ```bash
   # Rotate all API keys
   # Update SHOPIFY_API_SECRET in .env
   # Revoke Shopify app access tokens
   
   # Check for suspicious database queries
   mongo returns_management --eval "db.runCommand({currentOp: true})"
   
   # Review access logs
   grep -E "POST|DELETE|PUT" /var/log/supervisor/backend.out.log | tail -100
   ```

2. **Investigation:**
   ```bash
   # Check authentication logs
   grep -i "auth" /var/log/supervisor/backend.err.log | tail -50
   
   # Look for unusual data access
   mongo returns_management --eval "
     db.webhook_events.find({processed: false}).limit(10);
     db.returns.find().sort({created_at: -1}).limit(5);
   "
   ```

### Data Leak
1. **Identify scope:**
   ```bash
   # Check what customer data exists
   mongo returns_management --eval "
     db.returns.distinct('customer_email');
     db.orders.count({'customer.email': {\$exists: true}});
   "
   ```

2. **Notification procedures:**
   - Contact affected customers
   - Update privacy policy
   - Report to relevant authorities if required

## Maintenance Windows

### Planned Maintenance
```bash
# 1. Notify users (if public-facing)
# 2. Schedule during low usage (e.g., 2-4 AM)

# Pre-maintenance checklist
- [ ] Database backup completed
- [ ] Configuration backup completed  
- [ ] Rollback plan documented
- [ ] Test environment validated

# During maintenance
sudo supervisorctl stop all
# Perform updates/changes
sudo supervisorctl start all

# Post-maintenance validation
curl https://your-app.com/api/health
curl https://your-app.com/api/integrations/shopify/status
```

### Emergency Maintenance
```bash
# If system is down, prioritize:
1. Restore service availability
2. Preserve data integrity  
3. Document changes for later review

# Emergency contact procedure:
1. Check Emergent platform status
2. Review recent changes in git log
3. Restore from known good backup if needed
```

---

**Next**: See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for specific error solutions.