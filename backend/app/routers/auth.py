"""
Authentication router for RISKOFF API.
Handles user signup, login, and session management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.config import supabase_client
from app.schemas import UserSignup, UserLogin
from app.utils.security import get_current_user, CurrentUser

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""
    message: str
    user_id: str
    email: str
    full_name: Optional[str] = None
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup) -> AuthResponse:
    """
    Register a new user with Supabase Auth.
    
    Args:
        user: UserSignup model with email, password, phone, full_name
        
    Returns:
        AuthResponse with tokens and user details
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        # Create user in Supabase Auth
        auth_response = supabase_client.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name,
                    "phone": user.phone
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        # Check if email confirmation is required
        if not auth_response.session:
            return {
                "message": "Registration successful. Please check your email to confirm your account.",
                "user_id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": user.full_name,
                "access_token": "",
                "refresh_token": "",
                "token_type": "bearer"
            }

        return AuthResponse(
            message="User registered successfully",
            user_id=auth_response.user.id,
            email=auth_response.user.email,
            full_name=user.full_name,
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e).lower()
        
        # Handle common errors gracefully
        if "already registered" in error_message or "already exists" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )
        elif "invalid email" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        elif "password" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements (min 6 characters)"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )


@router.post("/login")
async def login(user: UserLogin) -> AuthResponse:
    """
    Authenticate user and return session tokens.
    
    Args:
        user: UserLogin model with email and password
        
    Returns:
        AuthResponse with access_token and refresh_token
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_metadata = auth_response.user.user_metadata or {}

        return AuthResponse(
            message="Login successful",
            user_id=auth_response.user.id,
            email=auth_response.user.email,
            full_name=user_metadata.get("full_name"),
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e).lower()
        
        if "invalid" in error_message or "credentials" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        elif "not confirmed" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please confirm your email address before logging in"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}"
            )


@router.post("/login/form")
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()) -> AuthResponse:
    """
    OAuth2 compatible login endpoint for Swagger UI.
    Uses form data instead of JSON body.
    """
    user = UserLogin(email=form_data.username, password=form_data.password)
    return await login(user)


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """
    Sign out the current user.
    
    Requires valid authentication token.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        supabase_client.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh the access token using a refresh token.
    
    Args:
        refresh_token: Valid refresh token from login
        
    Returns:
        New access_token and refresh_token
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        auth_response = supabase_client.auth.refresh_session(refresh_token)
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role
    }
