"""Authentication models for CyberCorp Server."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="Unique user identifier")
    username: EmailStr = Field(..., description="User email/username")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="User creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """User creation model."""
    username: EmailStr = Field(..., description="User email/username")
    password: str = Field(..., min_length=8, description="User password")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[EmailStr] = Field(None, description="User email/username")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")


class LoginRequest(BaseModel):
    """Login request model."""
    username: EmailStr = Field(..., description="User email/username")
    password: str = Field(..., description="User password")
    client_id: Optional[str] = Field(None, description="Client identifier")


class Token(BaseModel):
    """Token model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")
    user: User = Field(..., description="User information")


class TokenRefresh(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID")
    role: UserRole = Field(..., description="User role")
    client_id: Optional[str] = Field(None, description="Client identifier")


class AuthSession(BaseModel):
    """Authentication session model."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    client_id: Optional[str] = Field(None, description="Client identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PermissionScope(str, Enum):
    """Permission scope enumeration."""
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    WINDOWS_READ = "windows:read"
    WINDOWS_WRITE = "windows:write"
    PROCESSES_READ = "processes:read"
    PROCESSES_WRITE = "processes:write"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    ADMIN = "admin"


class Permission(BaseModel):
    """Permission model."""
    id: str = Field(..., description="Permission identifier")
    name: str = Field(..., description="Permission name")
    scope: PermissionScope = Field(..., description="Permission scope")
    description: str = Field(..., description="Permission description")


class RolePermissions(BaseModel):
    """Role permissions mapping."""
    role: UserRole = Field(..., description="User role")
    permissions: List[PermissionScope] = Field(..., description="List of permissions")


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        PermissionScope.SYSTEM_READ,
        PermissionScope.SYSTEM_WRITE,
        PermissionScope.WINDOWS_READ,
        PermissionScope.WINDOWS_WRITE,
        PermissionScope.PROCESSES_READ,
        PermissionScope.PROCESSES_WRITE,
        PermissionScope.CONFIG_READ,
        PermissionScope.CONFIG_WRITE,
        PermissionScope.ADMIN,
    ],
    UserRole.USER: [
        PermissionScope.SYSTEM_READ,
        PermissionScope.WINDOWS_READ,
        PermissionScope.WINDOWS_WRITE,
        PermissionScope.PROCESSES_READ,
        PermissionScope.PROCESSES_WRITE,
    ],
    UserRole.VIEWER: [
        PermissionScope.SYSTEM_READ,
        PermissionScope.WINDOWS_READ,
        PermissionScope.PROCESSES_READ,
    ],
}