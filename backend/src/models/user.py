"""
User Management Data Models - Production Ready
Pydantic v2.x models for comprehensive user management with MongoDB integration
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from bson import ObjectId


class UserRole(str, Enum):
    """User role enumeration with strict validation"""
    MERCHANT = "merchant"
    CUSTOMER = "customer" 
    ADMIN = "admin"


class AuthProvider(str, Enum):
    """Authentication provider types"""
    SHOPIFY = "shopify"
    GOOGLE = "google"
    EMAIL = "email"


class PermissionType(str, Enum):
    """Permission types for RBAC"""
    # Return management permissions
    VIEW_RETURNS = "view_returns"
    MANAGE_RETURNS = "manage_returns"
    CREATE_RETURN = "create_return"
    
    # Analytics permissions  
    VIEW_ANALYTICS = "view_analytics"
    VIEW_REPORTS = "view_reports"
    
    # Admin permissions
    ADMIN_SETTINGS = "admin_settings"
    MANAGE_TENANTS = "manage_tenants"
    VIEW_ALL_RETURNS = "view_all_returns"
    MANAGE_USERS = "manage_users"
    
    # Shopify specific
    SHOPIFY_INTEGRATION = "shopify_integration"


# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.MERCHANT: [
        PermissionType.VIEW_RETURNS,
        PermissionType.MANAGE_RETURNS, 
        PermissionType.VIEW_ANALYTICS,
        PermissionType.VIEW_REPORTS,
        PermissionType.SHOPIFY_INTEGRATION
    ],
    UserRole.CUSTOMER: [
        PermissionType.VIEW_RETURNS,
        PermissionType.CREATE_RETURN
    ],
    UserRole.ADMIN: [
        PermissionType.ADMIN_SETTINGS,
        PermissionType.MANAGE_TENANTS,
        PermissionType.VIEW_ALL_RETURNS,
        PermissionType.MANAGE_USERS,
        PermissionType.VIEW_RETURNS,
        PermissionType.MANAGE_RETURNS,
        PermissionType.VIEW_ANALYTICS,
        PermissionType.VIEW_REPORTS
    ]
}


class UserBase(BaseModel):
    """Base user model with common fields"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    tenant_id: str = Field(..., description="Shopify shop domain for multi-tenancy")
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    auth_provider: AuthProvider = Field(default=AuthProvider.EMAIL, description="Authentication provider")
    permissions: List[PermissionType] = Field(default_factory=list, description="User permissions")
    is_active: bool = Field(default=True, description="User active status")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")

    @validator('permissions', pre=True, always=True)
    def set_default_permissions(cls, v, values):
        """Automatically set permissions based on role if not provided"""
        if not v and 'role' in values:
            return ROLE_PERMISSIONS.get(values['role'], [])
        return v


class UserCreate(UserBase):
    """User creation model with password"""
    password: Optional[str] = Field(None, min_length=8, description="Password (required for email auth)")
    confirm_password: Optional[str] = Field(None, description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_requirements(cls, v, values):
        """Validate password strength for email auth"""
        if values.get('auth_provider') == AuthProvider.EMAIL and not v:
            raise ValueError('Password is required for email authentication')
        return v


class UserUpdate(BaseModel):
    """User update model - partial updates"""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    permissions: Optional[List[PermissionType]] = None
    is_active: Optional[bool] = None
    profile_image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """User response model - excludes sensitive data"""
    user_id: str = Field(..., description="Unique user identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    
    # Computed fields
    full_name: Optional[str] = Field(None, description="Full name computed from first + last")
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name


class UserDB(UserBase):
    """Database user model with encrypted fields"""
    user_id: str = Field(..., description="Unique user identifier")
    password_hash: Optional[str] = Field(None, description="Bcrypt hashed password")
    shopify_access_token: Optional[str] = Field(None, description="Fernet encrypted Shopify token")
    google_user_id: Optional[str] = Field(None, description="Google OAuth user ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0, description="Failed login attempt counter")
    account_locked_until: Optional[datetime] = Field(None, description="Account lockout expiry")


class SessionDB(BaseModel):
    """Session model for JWT token management"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str = Field(..., description="Unique session identifier")
    tenant_id: str = Field(..., description="Tenant identifier") 
    user_id: str = Field(..., description="User identifier")
    session_token: str = Field(..., description="JWT session token")
    refresh_token: Optional[str] = Field(None, description="Refresh token for extended sessions")
    expires_at: datetime = Field(..., description="Session expiry time")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    is_active: bool = Field(default=True, description="Session active status")


class LoginRequest(BaseModel):
    """Login request model"""
    model_config = ConfigDict(from_attributes=True)
    
    tenant_id: str = Field(..., description="Tenant identifier")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Extended session flag")


class GoogleOAuthRequest(BaseModel):
    """Google OAuth request model"""
    model_config = ConfigDict(from_attributes=True)
    
    tenant_id: str = Field(..., description="Tenant identifier") 
    auth_code: str = Field(..., description="Google OAuth authorization code")
    role: Optional[UserRole] = Field(default=UserRole.CUSTOMER, description="User role for new registrations")


class TokenResponse(BaseModel):
    """Authentication token response"""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=86400, description="Token expiry in seconds")  # 24 hours
    user: UserResponse = Field(..., description="User information")


class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    model_config = ConfigDict(from_attributes=True)
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class UserListResponse(BaseModel):
    """Paginated user list response"""
    model_config = ConfigDict(from_attributes=True)
    
    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total user count")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Items per page")
    total_pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")