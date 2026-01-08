"""
Authentication router for RISKOFF API.
Handles user signup, login, and session management.
"""

from fastapi import APIRouter, HTTPException, status
from app.config import supabase_client
from app.schemas import UserSignup, UserLogin

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup):
    """
    Register a new user with Supabase Auth.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
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

        if auth_response.user:
            return {
                "message": "User registered successfully",
                "user_id": auth_response.user.id,
                "email": auth_response.user.email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(user: UserLogin):
    """
    Authenticate user and return session tokens.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })

        if auth_response.user:
            return {
                "message": "Login successful",
                "user_id": auth_response.user.id,
                "email": auth_response.user.email,
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def logout():
    """
    Sign out the current user.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        supabase_client.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
