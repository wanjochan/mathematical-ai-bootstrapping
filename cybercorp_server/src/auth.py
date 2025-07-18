"""Authentication and authorization module for CyberCorp Server."""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models.auth import User, UserRole, PermissionScope
from .database import database_manager
from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()

class AuthManager:
    """Authentication and authorization manager."""
    
    def __init__(self):
        """Initialize auth manager."""
        self.config = get_config()
        self.secret_key = self.config.security.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = self.config.security.token_expire_minutes
        
    async def initialize(self):
        """Initialize authentication system."""
        logger.info("Initializing authentication system...")
        
        # Create default admin user if no users exist
        users = await database_manager.get_users()
        if not users:
            await self.create_default_admin()
    
    async def create_default_admin(self):
        """Create default admin user."""
        logger.info("Creating default admin user...")
        
        admin_user = User(
            username="admin",
            email="admin@cybercorp.local",
            role=UserRole.ADMIN,
            is_active=True,
            permissions=[
                PermissionScope.SYSTEM_READ,
                PermissionScope.SYSTEM_WRITE,
                PermissionScope.WINDOWS_READ,
                PermissionScope.WINDOWS_WRITE,
                PermissionScope.PROCESSES_READ,
                PermissionScope.PROCESSES_WRITE,
                PermissionScope.CONFIG_READ,
                PermissionScope.CONFIG_WRITE,
                PermissionScope.ADMIN,
            ]
        )
        
        # Set default password
        hashed_password = self.hash_password("admin123")
        
        await database_manager.create_user(admin_user, hashed_password)
        logger.info("Default admin user created (username: admin, password: admin123)")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode JWT token."""
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
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = await database_manager.get_user_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        stored_password = await database_manager.get_user_password(user.id)
        if not stored_password:
            return None
        
        if not self.verify_password(password, stored_password):
            return None
        
        return user
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        payload = self.decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = await database_manager.get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        
        return user
    
    def require_permission(self, permission: PermissionScope):
        """Dependency to require specific permission."""
        async def permission_dependency(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> User:
            token = credentials.credentials
            user = await self.get_current_user(token)
            
            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return user
        
        return permission_dependency
    
    def get_current_user_dependency(self):
        """Dependency to get current user."""
        async def current_user_dependency(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> User:
            token = credentials.credentials
            return await self.get_current_user(token)
        
        return current_user_dependency

# Global auth manager
auth_manager = AuthManager()

# Convenience functions
async def get_current_user(token: str) -> User:
    """Get current user from token."""
    return await auth_manager.get_current_user(token)

def require_permission(permission: PermissionScope):
    """Require specific permission."""
    return auth_manager.require_permission(permission)

def get_current_user_dependency():
    """Get current user dependency."""
    return auth_manager.get_current_user_dependency()