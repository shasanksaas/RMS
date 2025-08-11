"""
User Management Controller - Production Ready
Comprehensive user management APIs with CQRS integration
Handles all user types: merchants, customers, admins
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.models.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    LoginRequest, GoogleOAuthRequest, TokenResponse, 
    PasswordChangeRequest, UserRole, PermissionType
)
from src.services.auth_service import auth_service
from src.middleware.security import get_tenant_id
from src.config.database import db

# Setup router and security
router = APIRouter(prefix="/users", tags=["User Management"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


# === CQRS Command/Query Handlers ===

class UserCommands:
    """CQRS Commands for user write operations"""
    
    @staticmethod
    async def create_user_command(user_data: UserCreate, created_by: str = None) -> UserResponse:
        """Create user command handler"""
        return await auth_service.create_user(user_data, created_by)
    
    @staticmethod
    async def update_user_command(tenant_id: str, user_id: str, user_update: UserUpdate, updated_by: str = None) -> UserResponse:
        """Update user command handler"""
        return await auth_service.update_user(tenant_id, user_id, user_update, updated_by)
    
    @staticmethod
    async def delete_user_command(tenant_id: str, user_id: str, deleted_by: str = None) -> bool:
        """Delete user command handler"""
        # Soft delete - mark as inactive
        user_update = UserUpdate(is_active=False)
        await auth_service.update_user(tenant_id, user_id, user_update, deleted_by)
        
        # Invalidate all user sessions
        await db.sessions.update_many(
            {"tenant_id": tenant_id, "user_id": user_id},
            {"$set": {"is_active": False}}
        )
        return True
    
    @staticmethod
    async def change_password_command(tenant_id: str, user_id: str, password_data: PasswordChangeRequest, changed_by: str = None) -> bool:
        """Change password command handler"""
        # Get current user
        user = await auth_service.get_user_by_id(tenant_id, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not auth_service.verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        new_password_hash = auth_service.hash_password(password_data.new_password)
        await db.users.update_one(
            {"tenant_id": tenant_id, "user_id": user_id},
            {"$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Invalidate all existing sessions (force re-login)
        await db.sessions.update_many(
            {"tenant_id": tenant_id, "user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        return True


class UserQueries:
    """CQRS Queries for user read operations"""
    
    @staticmethod
    async def get_user_by_id_query(tenant_id: str, user_id: str) -> Optional[UserResponse]:
        """Get user by ID query handler"""
        user = await auth_service.get_user_by_id(tenant_id, user_id)
        return auth_service._user_to_response(user) if user else None
    
    @staticmethod
    async def get_users_list_query(
        tenant_id: str, 
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UserListResponse:
        """Get paginated users list query handler"""
        # Build query
        query = {"tenant_id": tenant_id}
        if role:
            query["role"] = role.value
        if is_active is not None:
            query["is_active"] = is_active
        
        # Get total count
        total_count = await db.users.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get users
        cursor = db.users.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        user_docs = await cursor.to_list(page_size)
        
        # Convert to response models
        users = [auth_service._user_to_response(user) for user in [await auth_service.get_user_by_id(tenant_id, doc["user_id"]) for doc in user_docs] if user]
        
        return UserListResponse(
            users=users,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


# === Authentication Dependency ===

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: str = Depends(get_tenant_id)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        # Verify tenant matches
        if payload.get("tenant_id") != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant access"
            )
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def check_permission(required_permission: PermissionType):
    """Check if user has required permission"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        if required_permission.value not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}"
            )
        
        return current_user
    
    return permission_checker


# === Authentication Endpoints ===

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Register new user
    
    - **tenant_id**: Tenant identifier (from header)
    - **user_data**: User registration data
    - **Returns**: Created user information
    """
    try:
        # Set tenant_id from header
        user_data.tenant_id = tenant_id
        
        # Create user using CQRS command
        user = await UserCommands.create_user_command(user_data)
        
        logger.info(f"User registered: {user.user_id} ({user.email}) for tenant {tenant_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_request: LoginRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    User login with email and password
    
    - **login_request**: Login credentials
    - **Returns**: Access token and user information
    """
    try:
        # Set tenant_id from header
        login_request.tenant_id = tenant_id
        
        # Authenticate user
        user, remember_me = await auth_service.authenticate_email_password(login_request)
        
        # Create session
        client_ip = request.client.host
        user_agent = request.headers.get("User-Agent")
        session = await auth_service.create_session(user, client_ip, user_agent, remember_me)
        
        # Return token response
        user_response = auth_service._user_to_response(user)
        token_response = TokenResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            expires_in=86400 if not remember_me else 2592000,  # 24h or 30 days
            user=user_response
        )
        
        logger.info(f"User logged in: {user.user_id} ({user.email}) for tenant {tenant_id}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login/google", response_model=TokenResponse)
async def google_oauth_login(
    oauth_request: GoogleOAuthRequest,
    request: Request,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Google OAuth login
    
    - **oauth_request**: Google OAuth data
    - **Returns**: Access token and user information
    """
    try:
        # Set tenant_id from header
        oauth_request.tenant_id = tenant_id
        
        # Authenticate with Google
        user, remember_me = await auth_service.authenticate_google_oauth(oauth_request)
        
        # Create session
        client_ip = request.client.host
        user_agent = request.headers.get("User-Agent")
        session = await auth_service.create_session(user, client_ip, user_agent, remember_me)
        
        # Return token response
        user_response = auth_service._user_to_response(user)
        token_response = TokenResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            expires_in=86400,
            user=user_response
        )
        
        logger.info(f"Google OAuth login: {user.user_id} ({user.email}) for tenant {tenant_id}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth login failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    User logout - invalidate current session
    
    - **Returns**: Success message
    """
    try:
        token = credentials.credentials
        success = await auth_service.invalidate_session(token)
        
        if success:
            logger.info(f"User logged out: {current_user.get('sub')} for tenant {current_user.get('tenant_id')}")
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# === User Profile Endpoints ===

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user profile
    
    - **Returns**: Current user information
    """
    try:
        tenant_id = current_user.get("tenant_id")
        user_id = current_user.get("sub")
        
        user = await UserQueries.get_user_by_id_query(tenant_id, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user profile
    
    - **user_update**: User update data
    - **Returns**: Updated user information
    """
    try:
        tenant_id = current_user.get("tenant_id")
        user_id = current_user.get("sub")
        
        user = await UserCommands.update_user_command(tenant_id, user_id, user_update, user_id)
        
        logger.info(f"User profile updated: {user_id} for tenant {tenant_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/me/change-password")
async def change_current_user_password(
    password_data: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change current user password
    
    - **password_data**: Password change data
    - **Returns**: Success message
    """
    try:
        tenant_id = current_user.get("tenant_id")
        user_id = current_user.get("sub")
        
        success = await UserCommands.change_password_command(tenant_id, user_id, password_data, user_id)
        
        if success:
            logger.info(f"Password changed: {user_id} for tenant {tenant_id}")
            return {"message": "Password changed successfully. Please log in again."}
        else:
            raise HTTPException(status_code=400, detail="Password change failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# === Admin User Management Endpoints ===

@router.get("", response_model=UserListResponse)
async def get_users_list(
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(check_permission(PermissionType.MANAGE_USERS))
):
    """
    Get paginated list of users (Admin only)
    
    - **role**: Filter by user role
    - **is_active**: Filter by active status
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (1-100)
    - **Returns**: Paginated user list
    """
    try:
        tenant_id = current_user.get("tenant_id")
        
        users_list = await UserQueries.get_users_list_query(
            tenant_id, role, is_active, page, page_size
        )
        
        return users_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users list"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: Dict[str, Any] = Depends(check_permission(PermissionType.MANAGE_USERS))
):
    """
    Get user by ID (Admin only)
    
    - **user_id**: User identifier
    - **Returns**: User information
    """
    try:
        tenant_id = current_user.get("tenant_id")
        
        user = await UserQueries.get_user_by_id_query(tenant_id, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: str,
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(check_permission(PermissionType.MANAGE_USERS))
):
    """
    Update user by ID (Admin only)
    
    - **user_id**: User identifier  
    - **user_update**: User update data
    - **Returns**: Updated user information
    """
    try:
        tenant_id = current_user.get("tenant_id")
        updated_by = current_user.get("sub")
        
        user = await UserCommands.update_user_command(tenant_id, user_id, user_update, updated_by)
        
        logger.info(f"User updated by admin: {user_id} by {updated_by} for tenant {tenant_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: Dict[str, Any] = Depends(check_permission(PermissionType.MANAGE_USERS))
):
    """
    Delete user by ID (Admin only) - Soft delete
    
    - **user_id**: User identifier
    - **Returns**: Success message
    """
    try:
        tenant_id = current_user.get("tenant_id")
        deleted_by = current_user.get("sub")
        
        # Prevent self-deletion
        if user_id == deleted_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = await UserCommands.delete_user_command(tenant_id, user_id, deleted_by)
        
        if success:
            logger.info(f"User deleted by admin: {user_id} by {deleted_by} for tenant {tenant_id}")
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="User deletion failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


# === System Endpoints ===

@router.post("/cleanup-sessions")
async def cleanup_expired_sessions(
    current_user: Dict[str, Any] = Depends(check_permission(PermissionType.ADMIN_SETTINGS))
):
    """
    Cleanup expired sessions (Admin only)
    
    - **Returns**: Success message with cleanup count
    """
    try:
        await auth_service.cleanup_expired_sessions()
        return {"message": "Session cleanup completed successfully"}
        
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session cleanup failed"
        )