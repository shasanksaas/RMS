# Observability & Monitoring

*Last updated: 2025-01-11*

## Monitoring Stack

### Health Checks

**System Health Endpoints:**
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-11T10:30:00Z",
  "version": "1.0.0",
  "uptime": 86400,
  "checks": {
    "database": "healthy",
    "redis": "healthy", 
    "shopify_api": "healthy"
  }
}
```

**Integration Health:**
```http
GET /api/integrations/shopify/status
X-Tenant-Id: tenant-rms34
```

**Detailed Health Check Implementation:**
```python
# controllers/health_controller.py
from datetime import datetime, timedelta
import asyncio

@router.get("/health")
async def health_check():
    """Comprehensive system health check"""
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "uptime": get_uptime_seconds(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        await db.command("ping")
        health_data["checks"]["database"] = "healthy"
    except Exception as e:
        health_data["checks"]["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    # External API connectivity
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.shopify.com/", timeout=5)
            health_data["checks"]["shopify_api"] = "healthy" if response.status_code < 500 else "degraded"
    except Exception:
        health_data["checks"]["shopify_api"] = "unhealthy"
        health_data["status"] = "degraded"
    
    return health_data
```

### Logging Architecture

**Log Levels:**
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Something unexpected happened
- **ERROR**: Serious problem occurred
- **CRITICAL**: System may be unusable

**Log Structure:**
```json
{
  "timestamp": "2025-01-11T10:30:00.123Z",
  "level": "INFO",
  "logger": "shopify_service",
  "message": "Order lookup completed",
  "tenant_id": "tenant-rms34",
  "request_id": "req_123456",
  "user_id": "customer",
  "duration_ms": 245,
  "context": {
    "order_number": "1001",
    "customer_email": "sha256_hash_of_email"
  }
}
```

**Logging Configuration:**
```python
# config/logging.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add context data if available
        if hasattr(record, 'tenant_id'):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, 'context'):
            log_data["context"] = record.context
            
        return json.dumps(log_data)

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/app/returns_app.log')
    ]
)

# Apply structured formatter
for handler in logging.root.handlers:
    handler.setFormatter(StructuredFormatter())
```

**Request Logging Middleware:**
```python
# middleware/logging.py
import time
import uuid
from fastapi import Request

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests with timing"""
    
    # Generate request ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = round((time.time() - start_time) * 1000)
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "tenant_id": getattr(request.state, 'tenant_id', None),
            "duration_ms": duration_ms,
            "status_code": response.status_code,
            "context": {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "user_agent": request.headers.get("user-agent", "")[:100]
            }
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response
```

### Metrics Collection

**Key Business Metrics:**
- Return request creation rate
- Order lookup success rate
- Return approval/rejection rates
- Average processing time
- Customer satisfaction scores

**Technical Metrics:**
- API response times
- Database query performance
- Error rates by endpoint
- Memory and CPU usage
- Queue depths

**Metrics Implementation:**
```python
# services/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Business metrics
return_requests_total = Counter(
    'return_requests_total',
    'Total number of return requests created',
    ['tenant_id', 'status']
)

order_lookups_total = Counter(
    'order_lookups_total',
    'Total number of order lookups',
    ['tenant_id', 'status', 'mode']  # success/failure, shopify/fallback
)

# Technical metrics
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'Time spent processing API requests',
    ['method', 'endpoint', 'status_code']
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Time spent on database queries',
    ['collection', 'operation']
)

# Usage example
def track_return_creation(tenant_id: str, success: bool):
    status = 'success' if success else 'failure'
    return_requests_total.labels(
        tenant_id=tenant_id,
        status=status
    ).inc()

@contextmanager
def track_api_duration(method: str, endpoint: str, status_code: int):
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        api_request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(duration)
```

## Error Tracking

### Error Categories

**Application Errors:**
- Validation failures (400 errors)
- Authentication failures (401 errors)  
- Authorization failures (403 errors)
- Not found errors (404 errors)
- Server errors (500 errors)

**Integration Errors:**
- Shopify API failures
- Database connectivity issues
- External service timeouts
- Webhook processing failures

**Business Logic Errors:**
- Policy evaluation failures
- Return creation failures
- Order lookup failures
- Email notification failures

### Error Logging

**Error Context Capture:**
```python
# utils/error_handling.py
import traceback
import sys
from typing import Dict, Any

class ErrorCapture:
    @staticmethod
    def capture_exception(e: Exception, context: Dict[str, Any] = None) -> Dict:
        """Capture detailed error information"""
        
        error_data = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc(),
            "python_version": sys.version,
            "context": context or {}
        }
        
        return error_data
    
    @staticmethod
    def log_error(e: Exception, logger: logging.Logger, context: Dict[str, Any] = None):
        """Log error with full context"""
        
        error_data = ErrorCapture.capture_exception(e, context)
        
        logger.error(
            f"Exception occurred: {error_data['error_message']}",
            extra={
                "error_type": error_data["error_type"],
                "traceback": error_data["traceback"],
                "context": error_data["context"]
            }
        )

# Usage in controllers
try:
    result = await create_return(return_data)
except Exception as e:
    ErrorCapture.log_error(e, logger, {
        "tenant_id": tenant_id,
        "order_id": return_data.get("order_id"),
        "customer_email": "***masked***"  # Don't log PII
    })
    raise HTTPException(500, "Internal server error")
```

### Error Alerting

**Alert Rules:**
```python
# monitoring/alerts.py
from dataclasses import dataclass
from typing import List
import asyncio

@dataclass
class AlertRule:
    name: str
    metric: str
    threshold: float
    duration: int  # seconds
    severity: str
    notification_channels: List[str]

# Define alert rules
ALERT_RULES = [
    AlertRule(
        name="High Error Rate",
        metric="error_rate_5min",
        threshold=0.05,  # 5% error rate
        duration=300,    # 5 minutes
        severity="warning",
        notification_channels=["slack", "email"]
    ),
    AlertRule(
        name="Database Connection Failures",
        metric="database_connection_failures",
        threshold=5,
        duration=60,
        severity="critical", 
        notification_channels=["slack", "pagerduty"]
    ),
    AlertRule(
        name="Shopify API Failures",
        metric="shopify_api_error_rate",
        threshold=0.1,  # 10% failure rate
        duration=600,   # 10 minutes
        severity="warning",
        notification_channels=["slack"]
    )
]

async def check_alerts():
    """Check all alert rules and send notifications"""
    for rule in ALERT_RULES:
        if await evaluate_alert_rule(rule):
            await send_alert_notification(rule)
```

## Performance Monitoring

### Response Time Tracking

**Response Time Buckets:**
- **Fast**: < 100ms (database queries, cache hits)
- **Normal**: 100-500ms (simple API calls)  
- **Slow**: 500ms-2s (complex queries, external APIs)
- **Critical**: > 2s (needs investigation)

**Performance Middleware:**
```python
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Track API performance metrics"""
    
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    
    # Record metrics
    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).observe(duration)
    
    # Log slow requests
    if duration > 2.0:
        logger.warning(
            f"Slow request detected: {request.method} {request.url.path}",
            extra={
                "duration_ms": round(duration * 1000),
                "status_code": response.status_code,
                "tenant_id": getattr(request.state, 'tenant_id', None)
            }
        )
    
    return response
```

### Database Performance

**Query Performance Tracking:**
```python
# utils/database.py
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def track_db_query(collection: str, operation: str):
    """Track database query performance"""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        database_query_duration.labels(
            collection=collection,
            operation=operation
        ).observe(duration)
        
        # Log slow queries
        if duration > 1.0:
            logger.warning(
                f"Slow database query: {collection}.{operation}",
                extra={"duration_ms": round(duration * 1000)}
            )

# Usage
async def get_returns(tenant_id: str):
    async with track_db_query("returns", "find"):
        return await db.returns.find({"tenant_id": tenant_id}).to_list(100)
```

### Memory & Resource Monitoring

**Resource Usage Tracking:**
```python
# monitoring/resources.py
import psutil
import asyncio

class ResourceMonitor:
    def __init__(self):
        self.cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('memory_usage_percent', 'Memory usage percentage') 
        self.disk_usage = Gauge('disk_usage_percent', 'Disk usage percentage')
    
    async def collect_metrics(self):
        """Collect system resource metrics"""
        while True:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_usage.set(disk_percent)
            
            # Alert on high resource usage
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 85:
                logger.warning(f"High memory usage: {memory.percent}%")
            if disk_percent > 90:
                logger.error(f"High disk usage: {disk_percent}%")
            
            await asyncio.sleep(60)  # Collect every minute

# Start resource monitoring
monitor = ResourceMonitor()
asyncio.create_task(monitor.collect_metrics())
```

## Distributed Tracing

### Request Tracing

**Trace Context Propagation:**
```python
# middleware/tracing.py
import uuid
from contextvars import ContextVar

# Context variables for trace propagation
trace_id: ContextVar[str] = ContextVar('trace_id')
span_id: ContextVar[str] = ContextVar('span_id')

@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    """Add tracing context to requests"""
    
    # Generate or extract trace ID
    trace_id_val = request.headers.get('X-Trace-Id', str(uuid.uuid4()))
    span_id_val = str(uuid.uuid4())[:8]
    
    # Set context variables
    trace_id.set(trace_id_val)
    span_id.set(span_id_val)
    
    # Process request
    response = await call_next(request)
    
    # Add trace headers to response
    response.headers["X-Trace-Id"] = trace_id_val
    response.headers["X-Span-Id"] = span_id_val
    
    return response

# Usage in services
def log_with_trace(message: str, **kwargs):
    """Log message with trace context"""
    logger.info(message, extra={
        "trace_id": trace_id.get(None),
        "span_id": span_id.get(None),
        **kwargs
    })
```

### Cross-Service Tracing

**External API Tracing:**
```python
# services/shopify_service.py
import httpx

async def make_shopify_request(url: str, **kwargs):
    """Make Shopify API request with tracing"""
    
    # Propagate trace context
    headers = kwargs.get('headers', {})
    headers.update({
        'X-Trace-Id': trace_id.get('unknown'),
        'X-Parent-Span-Id': span_id.get('unknown')
    })
    kwargs['headers'] = headers
    
    # Create new span
    current_span = str(uuid.uuid4())[:8]
    
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(**kwargs)
            
        duration = time.perf_counter() - start_time
        
        # Log trace
        log_with_trace(
            f"Shopify API call completed",
            span_id=current_span,
            duration_ms=round(duration * 1000),
            status_code=response.status_code,
            url=url
        )
        
        return response
        
    except Exception as e:
        duration = time.perf_counter() - start_time
        
        # Log error trace
        log_with_trace(
            f"Shopify API call failed",
            span_id=current_span,
            duration_ms=round(duration * 1000),
            error=str(e),
            url=url
        )
        raise
```

## Log Analysis

### Log Queries

**Common Log Analysis Patterns:**
```bash
# Error analysis
grep -E "ERROR|CRITICAL" /var/log/app/returns_app.log | tail -50

# Performance analysis
grep "duration_ms" /var/log/app/returns_app.log | \
  jq -r 'select(.duration_ms > 1000) | "\(.timestamp) \(.message) \(.duration_ms)ms"'

# Tenant activity analysis
grep "tenant-rms34" /var/log/app/returns_app.log | \
  jq -r '"\(.timestamp) \(.level) \(.message)"' | \
  tail -100

# API endpoint analysis
grep "POST /api/elite/portal/returns/create" /var/log/app/returns_app.log | \
  jq -r 'select(.status_code >= 400)'
```

### Log Aggregation Queries

**Business Intelligence from Logs:**
```bash
# Return creation success rate
grep "return_requests_total" /var/log/app/returns_app.log | \
  jq -s 'group_by(.status) | map({status: .[0].status, count: length})'

# Most common error types  
grep '"level":"ERROR"' /var/log/app/returns_app.log | \
  jq -r '.error_type' | sort | uniq -c | sort -nr

# Response time percentiles
grep "duration_ms" /var/log/app/returns_app.log | \
  jq -r '.duration_ms' | sort -n | \
  awk '{a[NR]=$1} END {
    print "P50:", a[int(NR*0.5)]
    print "P95:", a[int(NR*0.95)]  
    print "P99:", a[int(NR*0.99)]
  }'
```

## Dashboards & Visualization

### Key Metrics Dashboard

**Business Metrics:**
- Daily return requests created
- Return approval/rejection rates
- Average processing time
- Customer satisfaction scores
- Revenue impact of returns

**Technical Metrics:**
- API response times (P50, P95, P99)
- Error rates by endpoint
- Database query performance
- System resource usage
- External API dependency status

**Security Metrics:**
- Failed authentication attempts
- Unusual access patterns
- Security event frequency
- Compliance violations

### Alert Dashboard

**Alert Status Overview:**
- Active alerts by severity
- Alert resolution time
- Most frequent alerts
- Alert trends over time

**Sample Dashboard Query:**
```python
# Dashboard data endpoint
@router.get("/api/admin/dashboard/metrics")
async def get_dashboard_metrics(
    timeframe: str = "24h",
    tenant_id: str = Depends(get_tenant_id)
):
    """Get dashboard metrics for specified timeframe"""
    
    since = datetime.now() - timedelta(hours=int(timeframe.rstrip('h')))
    
    # Business metrics
    return_stats = await db.returns.aggregate([
        {"$match": {
            "tenant_id": tenant_id,
            "created_at": {"$gte": since}
        }},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "avg_amount": {"$avg": "$estimated_refund.amount"}
        }}
    ]).to_list(10)
    
    # Error metrics from logs
    error_stats = await get_error_stats(tenant_id, since)
    
    # Performance metrics  
    performance_stats = await get_performance_stats(since)
    
    return {
        "timeframe": timeframe,
        "returns": return_stats,
        "errors": error_stats,
        "performance": performance_stats,
        "last_updated": datetime.now()
    }
```

---

**Next**: See [CONTRIBUTING.md](./CONTRIBUTING.md) for development workflow.