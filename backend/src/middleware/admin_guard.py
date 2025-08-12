"""
Admin Guard Middleware
Provides admin-only access control for platform administration endpoints
"""

from fastapi import HTTPException, Depends, status
from src.controllers.tenant_controller import get_current_user
from src.models.user import User
import logging

logger = logging.getLogger(__name__)

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user has admin role
    Raises 403 if user is not a platform admin
    """
    if not current_user:
        logger.warning("Admin access attempted without authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user {current_user.email} with role {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Only platform administrators can access this resource."
        )
    
    logger.info(f"Admin access granted to {current_user.email}")
    return current_user

async def require_admin_or_impersonation(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to allow admin or admin-impersonated sessions
    Used for merchant endpoints that admins can access via impersonation
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Allow direct admin access
    if current_user.role == "admin":
        return current_user
    
    # Allow merchant access (includes impersonated sessions)
    if current_user.role == "merchant":
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. Admin or merchant role required."
    )