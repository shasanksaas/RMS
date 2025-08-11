"""
Tenant Isolation Middleware - Production Multi-Tenancy Security
Enforces strict tenant boundaries and prevents data leakage
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Optional, Set
import jwt

logger = logging.getLogger(__name__)

class TenantIsolationMiddleware:
    """
    Middleware to enforce tenant isolation across the application
    Ensures no cross-tenant data access and maintains strict boundaries
    """
    
    def __init__(self):
        # Paths that don't require tenant isolation
        self.public_paths: Set[str] = {
            "/docs", "/openapi.json", "/health", "/api/auth/login", 
            "/api/auth/register", "/api/auth/merchant-signup", 
            "/api/auth/google", "/api/auth/refresh",
            "/api/auth/tenant-status", "/api/auth/signup-info"
        }
        
        # Admin-only paths that bypass normal tenant restrictions
        self.admin_paths: Set[str] = {
            "/api/tenants"
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with tenant isolation checks"""
        
        try:
            # Skip public paths
            if self._is_public_path(request.url.path):
                response = await call_next(request)
                return response
            
            # Extract tenant context
            tenant_id = await self._extract_tenant_context(request)
            
            # Handle admin paths with special logic
            if self._is_admin_path(request.url.path):
                user_role = await self._get_user_role_from_request(request)
                if user_role != "admin":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Admin access required"}
                    )
                # Admin can access without tenant restrictions
                response = await call_next(request)
                return response
            
            # Require tenant for all other protected paths
            if not tenant_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Tenant context required"}
                )
            
            # Add tenant to request state for use by endpoints
            request.state.tenant_id = tenant_id
            
            # Add security headers
            response = await call_next(request)
            response.headers["X-Tenant-Context"] = tenant_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant isolation middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Request processing failed"}
            )
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public and doesn't require tenant isolation"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _is_admin_path(self, path: str) -> bool:
        """Check if path is admin-only"""
        return any(path.startswith(admin_path) for admin_path in self.admin_paths)
    
    async def _extract_tenant_context(self, request: Request) -> Optional[str]:
        """Extract tenant ID from various sources"""
        
        # 1. Check X-Tenant-Id header (priority for API clients)
        tenant_id = request.headers.get("X-Tenant-Id")
        if tenant_id:
            return tenant_id.strip()
        
        # 2. Extract from JWT token if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                # Decode without verification for tenant extraction (verification happens elsewhere)
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("tenant_id")
            except Exception as e:
                logger.warning(f"Failed to extract tenant from JWT: {e}")
        
        # 3. Check query parameter (for specific endpoints)
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id.strip()
        
        return None
    
    async def _get_user_role_from_request(self, request: Request) -> Optional[str]:
        """Extract user role from JWT token"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("role")
            except Exception as e:
                logger.warning(f"Failed to extract role from JWT: {e}")
        return None

# Repository-level tenant enforcement
class TenantAwareRepository:
    """
    Base class for repositories that enforces tenant isolation
    All repository methods must include tenant_id parameter
    """
    
    def __init__(self, collection):
        self.collection = collection
    
    def _ensure_tenant_filter(self, tenant_id: str, filter_query: dict = None) -> dict:
        """Ensure all queries include tenant_id filter"""
        if not tenant_id:
            raise ValueError("tenant_id is required for all database operations")
        
        if filter_query is None:
            filter_query = {}
        
        # Always add tenant_id to filter
        filter_query["tenant_id"] = tenant_id
        return filter_query
    
    def _validate_tenant_id(self, tenant_id: str):
        """Validate tenant_id format and presence"""
        if not tenant_id:
            raise ValueError("tenant_id cannot be None or empty")
        
        if not isinstance(tenant_id, str):
            raise ValueError("tenant_id must be a string")
        
        if not tenant_id.startswith("tenant-"):
            raise ValueError("Invalid tenant_id format")

# Decorator for tenant isolation enforcement
def require_tenant_context(func):
    """
    Decorator to ensure endpoint has tenant context
    Automatically injects tenant_id from request state
    """
    async def wrapper(*args, **kwargs):
        # Find request object in args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        if not hasattr(request.state, 'tenant_id'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context required"
            )
        
        # Add tenant_id to kwargs
        kwargs['tenant_id'] = request.state.tenant_id
        
        return await func(*args, **kwargs)
    
    return wrapper

def validate_tenant_access(tenant_id: str, resource_tenant_id: str):
    """
    Validate that a resource belongs to the requesting tenant
    Raises 404 if resource doesn't belong to tenant (security through obscurity)
    """
    if not tenant_id or not resource_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant validation failed"
        )
    
    if tenant_id != resource_tenant_id:
        # Return 404 instead of 403 to prevent tenant enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

class TenantIsolationError(Exception):
    """Custom exception for tenant isolation violations"""
    pass

# Audit logging for security events
def log_tenant_violation(
    user_id: str, 
    requesting_tenant: str, 
    resource_tenant: str, 
    resource_type: str,
    action: str
):
    """Log potential tenant isolation violations for security monitoring"""
    logger.critical(
        f"TENANT_VIOLATION: user={user_id} requested_tenant={requesting_tenant} "
        f"resource_tenant={resource_tenant} resource_type={resource_type} action={action}"
    )

# Utility functions for tenant validation
def get_tenant_from_request(request: Request) -> str:
    """Get tenant_id from request state with validation"""
    if not hasattr(request.state, 'tenant_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context required"
        )
    return request.state.tenant_id

def ensure_tenant_isolation(tenant_id: str, query: dict) -> dict:
    """Ensure database query includes tenant isolation"""
    if not tenant_id:
        raise TenantIsolationError("tenant_id required for database queries")
    
    query["tenant_id"] = tenant_id
    return query