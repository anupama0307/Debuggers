"""
Security utilities for RISKOFF API.
Provides JWT verification and user authentication via Supabase.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.config import supabase_client

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/form", auto_error=False)


class CurrentUser(BaseModel):
    """Model representing the authenticated user."""
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "user"


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> CurrentUser:
    """
    Dependency to get the current authenticated user.
    
    Verifies the JWT token with Supabase and returns user details.
    
    Args:
        token: JWT access token from Authorization header
        
    Returns:
        CurrentUser object with user details
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a valid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    
    try:
        # Verify token with Supabase
        user_response = supabase_client.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        user_metadata = user.user_metadata or {}
        
        return CurrentUser(
            id=user.id,
            email=user.email,
            full_name=user_metadata.get("full_name"),
            phone=user_metadata.get("phone"),
            role=user_metadata.get("role", "user")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[CurrentUser]:
    """
    Optional dependency to get the current user if authenticated.
    
    Returns None instead of raising exception if not authenticated.
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to require admin role.
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
