"""
Security middleware for tenant context injection and permission validation
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
import logging
import time

logger = logging.getLogger(__name__)

class TenantContext:
    """Thread-local tenant context"""
    def __init__(self):
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.permissions: Dict[str, bool] = {}
        self.request_id: Optional[str] = None

# Global tenant context
tenant_context = TenantContext()

class SecurityMiddleware:
    """Middleware to inject tenant context and validate permissions"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def validate_tenant_access(self, request: Request) -> str:
        """Validate and extract tenant ID from request"""
        
        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-Id")
        
        if not tenant_id:
            # Try to extract from path for admin routes
            if "/tenants/" in str(request.url):
                path_parts = str(request.url).split("/tenants/")
                if len(path_parts) > 1:
                    tenant_id = path_parts[1].split("/")[0]
        
        if not tenant_id:
            logger.warning(f"Missing tenant ID for request: {request.url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required. Please include X-Tenant-Id header."
            )
        
        # Validate tenant exists (this will be enhanced with real auth)
        if not await self._validate_tenant_exists(tenant_id):
            logger.warning(f"Invalid tenant ID: {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant access."
            )
        
        # Set tenant context
        tenant_context.tenant_id = tenant_id
        tenant_context.request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        # Log access attempt (without PII)
        logger.info(f"Tenant Access - ID: {tenant_id}, Path: {request.url.path}, Method: {request.method}")
        
        return tenant_id
    
    async def _validate_tenant_exists(self, tenant_id: str) -> bool:
        """Validate that tenant exists and is active"""
        # In a real implementation, this would check the database
        # For now, we'll use basic validation
        return tenant_id and len(tenant_id) > 0
    
    def validate_cross_tenant_access(self, resource_tenant_id: str, request_tenant_id: str):
        """Prevent cross-tenant data access"""
        if resource_tenant_id != request_tenant_id:
            logger.critical(f"SECURITY VIOLATION: Cross-tenant access attempted. Resource: {resource_tenant_id}, Request: {request_tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cross-tenant access not allowed."
            )
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not tenant_context.permissions.get(permission, False):
                    logger.warning(f"Permission denied: {permission} for tenant: {tenant_context.tenant_id}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission} required."
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator

class RateLimitingMiddleware:
    """Rate limiting middleware with exponential backoff"""
    
    def __init__(self):
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.blocked_until: Dict[str, float] = {}
    
    async def check_rate_limit(self, tenant_id: str, endpoint: str) -> bool:
        """Check if request should be rate limited"""
        current_time = time.time()
        key = f"{tenant_id}:{endpoint}"
        
        # Check if currently blocked
        if key in self.blocked_until and current_time < self.blocked_until[key]:
            retry_after = int(self.blocked_until[key] - current_time)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Clean up old entries
        if key in self.blocked_until and current_time >= self.blocked_until[key]:
            del self.blocked_until[key]
        
        # Track request count
        if key not in self.request_counts:
            self.request_counts[key] = {"count": 0, "window_start": current_time}
        
        window = self.request_counts[key]
        
        # Reset window if needed (1 minute windows)
        if current_time - window["window_start"] > 60:
            window["count"] = 0
            window["window_start"] = current_time
        
        window["count"] += 1
        
        # Check limits (per minute)
        limits = {
            "returns": 100,  # 100 requests per minute for returns endpoints
            "analytics": 50,  # 50 requests per minute for analytics
            "default": 200   # 200 requests per minute default
        }
        
        endpoint_type = "default"
        if "returns" in endpoint:
            endpoint_type = "returns"
        elif "analytics" in endpoint:
            endpoint_type = "analytics"
        
        limit = limits[endpoint_type]
        
        if window["count"] > limit:
            # Apply exponential backoff (start with 1 minute, max 15 minutes)
            backoff_minutes = min(15, 2 ** (window["count"] - limit - 1))
            self.blocked_until[key] = current_time + (backoff_minutes * 60)
            
            logger.warning(f"Rate limit exceeded for {key}. Blocked for {backoff_minutes} minutes.")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Blocked for {backoff_minutes} minutes.",
                headers={"Retry-After": str(backoff_minutes * 60)}
            )
        
        return True

class AuditMiddleware:
    """Middleware for comprehensive audit logging"""
    
    async def log_request(self, request: Request, response_status: int, duration_ms: float):
        """Log request for audit trail"""
        
        # Redact sensitive data
        headers = dict(request.headers)
        sensitive_headers = {"authorization", "x-api-key", "cookie"}
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "***REDACTED***"
        
        audit_data = {
            "tenant_id": tenant_context.tenant_id,
            "request_id": tenant_context.request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "status_code": response_status,
            "duration_ms": duration_ms,
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host if request.client else "unknown",
            "timestamp": time.time()
        }
        
        # Log security-relevant events
        if response_status == 403:
            logger.warning(f"SECURITY: Access denied - {audit_data}")
        elif response_status >= 500:
            logger.error(f"SERVER ERROR: {audit_data}")
        else:
            logger.info(f"REQUEST: {audit_data}")

# Utility functions for dependency injection
def get_current_tenant_id() -> str:
    """Get current tenant ID from context"""
    if not tenant_context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context available"
        )
    return tenant_context.tenant_id

def verify_tenant() -> str:
    """FastAPI dependency to verify tenant access"""
    return get_current_tenant_id()

def require_tenant_context():
    """Dependency to ensure tenant context is set"""
    return get_current_tenant_id()

# Global instances
security_middleware = SecurityMiddleware()
rate_limiting_middleware = RateLimitingMiddleware()
audit_middleware = AuditMiddleware()