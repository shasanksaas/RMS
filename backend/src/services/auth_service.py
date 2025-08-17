"""
Authentication Service - Production Ready
Handles Shopify OAuth (existing), Google OAuth, and email/password authentication
Integrates with existing system while adding comprehensive user management
"""

import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
import asyncio
import logging

# Cryptography and hashing
import bcrypt
import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

# HTTP and OAuth
import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import google.auth.exceptions

# Database and models
from motor.motor_asyncio import AsyncIOMotorClient
from src.config.database import db
from src.models.user import (
    UserDB, SessionDB, UserCreate, UserResponse, UserUpdate,
    LoginRequest, GoogleOAuthRequest, TokenResponse, 
    UserRole, AuthProvider, PermissionType, ROLE_PERMISSIONS
)

# Setup logging
logger = logging.getLogger(__name__)

# Encryption and hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Comprehensive authentication service"""
    
    def __init__(self):
        # JWT Configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24
        self.refresh_token_expire_days = 30
        
        # Encryption for sensitive data (Shopify tokens)
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            encryption_key = Fernet.generate_key().decode()
            logger.warning("ENCRYPTION_KEY not set, generated temporary key")
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        
        # Google OAuth Configuration
        self.google_client_id = "286821938662-8jjcepu96llg0v1g6maskbptmp34o15u.apps.googleusercontent.com"
        self.google_client_secret = "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"
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://ecom-return-manager.preview.emergentagent.com/auth/google/callback")
        
        # Account lockout settings
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30

    # === Password Management ===
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    # === Token Management ===
    
    def create_access_token(self, user: UserDB, remember_me: bool = False) -> str:
        """Create JWT access token with user data"""
        expire_hours = 720 if remember_me else self.access_token_expire_hours  # 30 days if remember_me
        expire = datetime.utcnow() + timedelta(hours=expire_hours)
        
        payload = {
            "sub": user.user_id,  # Subject (user ID)
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "auth_provider": user.auth_provider.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token for extended sessions"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    # === Encryption for Shopify Tokens ===
    
    def encrypt_shopify_token(self, token: str) -> str:
        """Encrypt Shopify access token for secure storage"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_shopify_token(self, encrypted_token: str) -> str:
        """Decrypt Shopify access token"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    # === Session Management ===
    
    async def create_session(self, user: UserDB, ip_address: str = None, user_agent: str = None, remember_me: bool = False) -> SessionDB:
        """Create user session with JWT token"""
        session_id = str(uuid.uuid4())
        access_token = self.create_access_token(user, remember_me)
        refresh_token = self.create_refresh_token(user.user_id) if remember_me else None
        
        expire_hours = 720 if remember_me else self.access_token_expire_hours
        expires_at = datetime.utcnow() + timedelta(hours=expire_hours)
        
        session = SessionDB(
            session_id=session_id,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store session in database
        await db.sessions.insert_one(session.model_dump())
        return session
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate user session"""
        result = await db.sessions.update_one(
            {"session_token": session_token},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (run as background task)"""
        current_time = datetime.utcnow()
        result = await db.sessions.delete_many({
            "$or": [
                {"expires_at": {"$lt": current_time}},
                {"is_active": False}
            ]
        })
        logger.info(f"Cleaned up {result.deleted_count} expired sessions")

    # === User Management ===
    
    async def create_user(self, user_data: UserCreate, created_by: str = None) -> UserResponse:
        """Create new user with comprehensive validation"""
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Check if user already exists
        existing_user = await db.users.find_one({
            "tenant_id": user_data.tenant_id,
            "email": user_data.email.lower()
        })
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Prepare user document
        user_db_data = {
            "user_id": user_id,
            "tenant_id": user_data.tenant_id,
            "email": user_data.email.lower(),
            "role": user_data.role,
            "auth_provider": user_data.auth_provider,
            "permissions": user_data.permissions or ROLE_PERMISSIONS.get(user_data.role, []),
            "is_active": user_data.is_active,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "profile_image_url": user_data.profile_image_url,
            "metadata": user_data.metadata,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "failed_login_attempts": 0
        }
        
        # Hash password if provided (for email auth)
        if user_data.password and user_data.auth_provider == AuthProvider.EMAIL:
            user_db_data["password_hash"] = self.hash_password(user_data.password)
        
        # Insert user into database
        result = await db.users.insert_one(user_db_data)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Return user response
        user_db = UserDB(**user_db_data)
        return self._user_to_response(user_db)
    
    async def get_user_by_id(self, tenant_id: str, user_id: str) -> Optional[UserDB]:
        """Get user by ID and tenant"""
        user_doc = await db.users.find_one({
            "tenant_id": tenant_id,
            "user_id": user_id
        })
        
        if user_doc:
            return UserDB(**user_doc)
        return None
    
    async def get_user_by_id_global(self, user_id: str) -> Optional[UserDB]:
        """Get user by ID across all tenants (for admin authentication)"""
        user_doc = await db.users.find_one({
            "user_id": user_id
        })
        
        if user_doc:
            return UserDB(**user_doc)
        return None
    
    async def get_user_by_email(self, tenant_id: str, email: str) -> Optional[UserDB]:
        """Get user by email and tenant"""
        user_doc = await db.users.find_one({
            "tenant_id": tenant_id,
            "email": email.lower()
        })
        
        if user_doc:
            return UserDB(**user_doc)
        return None
    
    async def update_user(self, tenant_id: str, user_id: str, user_update: UserUpdate, updated_by: str = None) -> UserResponse:
        """Update user information"""
        # Check if user exists
        existing_user = await self.get_user_by_id(tenant_id, user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        # Update fields that are provided
        for field, value in user_update.model_dump(exclude_unset=True).items():
            if field == "email" and value:
                # Check email uniqueness
                email_check = await db.users.find_one({
                    "tenant_id": tenant_id,
                    "email": value.lower(),
                    "user_id": {"$ne": user_id}
                })
                if email_check:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already exists"
                    )
                update_data["email"] = value.lower()
            else:
                update_data[field] = value
        
        # Update user
        result = await db.users.update_one(
            {"tenant_id": tenant_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Return updated user
        updated_user = await self.get_user_by_id(tenant_id, user_id)
        return self._user_to_response(updated_user)

    # === Authentication Methods ===
    
    async def authenticate_email_password(self, login_request: LoginRequest) -> Tuple[UserDB, bool]:
        """Authenticate user with email and password"""
        # Get user
        user = await self.get_user_by_email(login_request.tenant_id, login_request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check account lockout
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.account_locked_until}"
            )
        
        # Verify password
        if not user.password_hash or not self.verify_password(login_request.password, user.password_hash):
            # Increment failed attempts
            await self._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Reset failed attempts on successful login
        await self._reset_failed_attempts(user)
        
        # Update last login
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        
        return user, login_request.remember_me
    
    async def authenticate_google_oauth(self, oauth_request: GoogleOAuthRequest) -> Tuple[UserDB, bool]:
        """Authenticate or register user with Google OAuth"""
        # Exchange auth code for tokens
        google_user_info = await self._exchange_google_auth_code(oauth_request.auth_code)
        
        # Check if user exists
        existing_user = await self.get_user_by_email(oauth_request.tenant_id, google_user_info["email"])
        
        if existing_user:
            # Update Google user ID if not set
            if not existing_user.google_user_id:
                await db.users.update_one(
                    {"user_id": existing_user.user_id},
                    {"$set": {"google_user_id": google_user_info["sub"]}}
                )
            
            # Update last login
            await db.users.update_one(
                {"user_id": existing_user.user_id},
                {"$set": {"last_login_at": datetime.utcnow()}}
            )
            
            return existing_user, False
        
        else:
            # Create new user from Google OAuth
            user_create = UserCreate(
                tenant_id=oauth_request.tenant_id,
                email=google_user_info["email"],
                role=oauth_request.role,
                auth_provider=AuthProvider.GOOGLE,
                first_name=google_user_info.get("given_name"),
                last_name=google_user_info.get("family_name"),
                profile_image_url=google_user_info.get("picture"),
                metadata={"google_verified": google_user_info.get("email_verified", False)}
            )
            
            user_response = await self.create_user(user_create)
            
            # Get the created user with Google ID
            await db.users.update_one(
                {"user_id": user_response.user_id},
                {"$set": {
                    "google_user_id": google_user_info["sub"],
                    "last_login_at": datetime.utcnow()
                }}
            )
            
            created_user = await self.get_user_by_id(oauth_request.tenant_id, user_response.user_id)
            return created_user, False

    # === Shopify Integration (Existing) ===
    
    async def authenticate_shopify_oauth(self, tenant_id: str, access_token: str) -> Tuple[UserDB, bool]:
        """Authenticate merchant with existing Shopify OAuth (preserves existing functionality)"""
        # Verify Shopify token and get shop info
        shopify_user_info = await self._get_shopify_user_info(access_token)
        
        if not shopify_user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Shopify access token"
            )
        
        shop_domain = shopify_user_info.get("domain", "").replace(".myshopify.com", "")
        email = shopify_user_info.get("email", f"{shop_domain}@shopify.local")
        
        # Check if merchant exists
        existing_user = await self.get_user_by_email(tenant_id, email)
        
        if existing_user:
            # Update Shopify token
            encrypted_token = self.encrypt_shopify_token(access_token)
            await db.users.update_one(
                {"user_id": existing_user.user_id},
                {"$set": {
                    "shopify_access_token": encrypted_token,
                    "last_login_at": datetime.utcnow()
                }}
            )
            return existing_user, False
        
        else:
            # Create new merchant user
            user_create = UserCreate(
                tenant_id=tenant_id,
                email=email,
                role=UserRole.MERCHANT,
                auth_provider=AuthProvider.SHOPIFY,
                first_name=shopify_user_info.get("shop_owner", "").split()[0] if shopify_user_info.get("shop_owner") else None,
                last_name=" ".join(shopify_user_info.get("shop_owner", "").split()[1:]) if shopify_user_info.get("shop_owner") else None,
                metadata={
                    "shop_domain": shopify_user_info.get("domain"),
                    "shop_name": shopify_user_info.get("name"),
                    "plan_name": shopify_user_info.get("plan_name")
                }
            )
            
            user_response = await self.create_user(user_create)
            
            # Store encrypted Shopify token
            encrypted_token = self.encrypt_shopify_token(access_token)
            await db.users.update_one(
                {"user_id": user_response.user_id},
                {"$set": {
                    "shopify_access_token": encrypted_token,
                    "last_login_at": datetime.utcnow()
                }}
            )
            
            created_user = await self.get_user_by_id(tenant_id, user_response.user_id)
            return created_user, False

    # === Helper Methods ===
    
    def _user_to_response(self, user: UserDB) -> UserResponse:
        """Convert UserDB to UserResponse (excludes sensitive data)"""
        return UserResponse(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            auth_provider=user.auth_provider,
            permissions=user.permissions,
            is_active=user.is_active,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image_url=user.profile_image_url,
            metadata=user.metadata,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )
    
    async def _handle_failed_login(self, user: UserDB):
        """Handle failed login attempt"""
        failed_attempts = user.failed_login_attempts + 1
        update_data = {"failed_login_attempts": failed_attempts}
        
        if failed_attempts >= self.max_login_attempts:
            lockout_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            update_data["account_locked_until"] = lockout_until
        
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": update_data}
        )
    
    async def _reset_failed_attempts(self, user: UserDB):
        """Reset failed login attempts"""
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "failed_login_attempts": 0,
                "account_locked_until": None
            }}
        )
    
    async def _exchange_google_auth_code(self, auth_code: str) -> Dict[str, Any]:
        """Exchange Google auth code for user info"""
        token_url = "https://oauth2.googleapis.com/token"
        
        token_data = {
            "code": auth_code,
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "redirect_uri": self.google_redirect_uri,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Get access token
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                tokens = token_response.json()
                
                # Verify and decode ID token
                id_token_jwt = tokens.get("id_token")
                if not id_token_jwt:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No ID token received from Google"
                    )
                
                # Verify ID token
                user_info = id_token.verify_oauth2_token(
                    id_token_jwt, 
                    google_requests.Request(), 
                    self.google_client_id
                )
                
                return user_info
                
            except google.auth.exceptions.GoogleAuthError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google authentication error: {str(e)}"
                )
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange Google auth code: {str(e)}"
                )
    
    async def _get_shopify_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get Shopify user info from access token (preserves existing functionality)"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.shopify.com/shop.json",
                    headers={"X-Shopify-Access-Token": access_token}
                )
                response.raise_for_status()
                return response.json().get("shop")
            except httpx.HTTPError:
                return None


# Global auth service instance
auth_service = AuthService()