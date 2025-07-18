"""Authentication router for CyberCorp Server."""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.auth import (
    LoginRequest, Token, TokenRefresh, TokenResponse, User, UserCreate,
    UserUpdate, UserRole, PermissionScope
)
from ..auth import auth_manager, get_current_user, require_permission
from ..logging_config import get_logger

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest) -> Token:
    """Authenticate user and return JWT token."""
    try:
        logger.info(f"Login attempt for user: {login_request.username}")
        
        # Authenticate user
        token = await auth_manager.authenticate_user(
            username=login_request.username,
            password=login_request.password,
            client_id=login_request.client_id
        )
        
        logger.info(f"User {login_request.username} logged in successfully")
        return token
        
    except Exception as e:
        logger.warning(f"Login failed for user {login_request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_refresh: TokenRefresh) -> TokenResponse:
    """Refresh JWT token."""
    try:
        logger.info("Token refresh attempt")
        
        # Refresh token
        new_token = await auth_manager.refresh_token(token_refresh.refresh_token)
        
        logger.info("Token refreshed successfully")
        return new_token
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Logout user and invalidate token."""
    try:
        logger.info(f"Logout for user: {current_user.username}")
        
        # Invalidate token
        await auth_manager.invalidate_token(credentials.credentials)
        
        logger.info(f"User {current_user.username} logged out successfully")
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user information."""
    logger.info(f"User info request for: {current_user.username}")
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
) -> User:
    """Update current user information."""
    try:
        logger.info(f"User update request for: {current_user.username}")
        
        # Update user
        updated_user = await auth_manager.update_user(current_user.id, user_update)
        
        logger.info(f"User {current_user.username} updated successfully")
        return updated_user
        
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.post("/users", response_model=User)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> User:
    """Create new user (admin only)."""
    try:
        logger.info(f"User creation request by: {current_user.username}")
        
        # Create user
        new_user = await auth_manager.create_user(user_create)
        
        logger.info(f"User {new_user.username} created successfully")
        return new_user
        
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )


@router.get("/users", response_model=list[User])
async def list_users(
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> list[User]:
    """List all users (admin only)."""
    try:
        logger.info(f"User list request by: {current_user.username}")
        
        # Get users
        users = await auth_manager.list_users()
        
        return users
        
    except Exception as e:
        logger.error(f"User list error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> User:
    """Get user by ID (admin only)."""
    try:
        logger.info(f"User get request for {user_id} by: {current_user.username}")
        
        # Get user
        user = await auth_manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> User:
    """Update user by ID (admin only)."""
    try:
        logger.info(f"User update request for {user_id} by: {current_user.username}")
        
        # Update user
        updated_user = await auth_manager.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User {user_id} updated successfully")
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission(PermissionScope.ADMIN))
) -> Dict[str, Any]:
    """Delete user by ID (admin only)."""
    try:
        logger.info(f"User delete request for {user_id} by: {current_user.username}")
        
        # Delete user
        success = await auth_manager.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User {user_id} deleted successfully")
        return {"success": True, "message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user permissions."""
    try:
        logger.info(f"Permissions request for: {current_user.username}")
        
        # Get permissions
        permissions = await auth_manager.get_user_permissions(current_user.id)
        
        return {
            "user_id": current_user.id,
            "role": current_user.role,
            "permissions": permissions
        }
        
    except Exception as e:
        logger.error(f"Permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve permissions"
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user active sessions."""
    try:
        logger.info(f"Sessions request for: {current_user.username}")
        
        # Get sessions
        sessions = await auth_manager.get_user_sessions(current_user.id)
        
        return {
            "user_id": current_user.id,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )