"""
User router for RISKOFF API.
Handles user profile and dashboard data.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
import re

from app.config import supabase_client
from app.utils.security import get_current_user, CurrentUser

router = APIRouter(
    prefix="/user",
    tags=["User"]
)


class ProfileUpdate(BaseModel):
    """Schema for updating profile data with validation."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    occupation: Optional[str] = None
    employer_name: Optional[str] = None
    employment_years: Optional[int] = None
    annual_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    account_balance: Optional[float] = None
    mutual_funds: Optional[float] = None
    stocks: Optional[float] = None
    fixed_deposits: Optional[float] = None
    existing_loans: Optional[int] = None
    existing_loan_amount: Optional[float] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Remove any spaces or dashes
            cleaned = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^\d{10}$', cleaned):
                raise ValueError('Phone number must be exactly 10 digits')
            return cleaned
        return v

    @field_validator('annual_income')
    @classmethod
    def validate_annual_income(cls, v):
        if v is not None and v < 50000:
            raise ValueError('Annual income must be at least ₹50,000')
        return v

    @field_validator('monthly_expenses')
    @classmethod
    def validate_monthly_expenses(cls, v):
        if v is not None and v < 0:
            raise ValueError('Monthly expenses cannot be negative')
        return v

    @field_validator('account_balance')
    @classmethod
    def validate_account_balance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Account balance cannot be negative')
        return v

    @field_validator('mutual_funds', 'stocks', 'fixed_deposits', 'existing_loan_amount')
    @classmethod
    def validate_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value cannot be negative')
        return v


@router.get("/profile")
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get the current user's profile data.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    try:
        # Get full profile from profiles table
        response = supabase_client.table("profiles").select("*").eq("id", current_user.id).execute()
        
        if not response.data:
            return {"profile_completed": False}
        
        profile = response.data[0]
        
        # Check if profile has financial data filled
        has_financial = (profile.get("annual_income") or 0) > 0
        profile["profile_completed"] = has_financial
        
        return profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/profile")
async def update_profile(profile_update: ProfileUpdate, current_user: CurrentUser = Depends(get_current_user)):
    """
    Update the current user's profile data.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    try:
        # Only include non-None values
        update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data to update"
            )
        
        response = supabase_client.table("profiles").update(update_data).eq("id", current_user.id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": "Profile updated successfully", "profile": response.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/dashboard")
async def get_dashboard(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get dashboard data for the current user.
    Financial data comes from the profiles table.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    try:
        # Get full profile with financial data
        profile_response = supabase_client.table("profiles").select("*").eq("id", current_user.id).execute()
        profile = profile_response.data[0] if profile_response.data else {}
        
        # Get user loans
        loans_response = supabase_client.table("loans").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        loans = loans_response.data or []
        
        # Get financial data from profile
        annual_income = profile.get("annual_income", 0) or 0
        monthly_expenses = profile.get("monthly_expenses", 0) or 0
        account_balance = profile.get("account_balance", 0) or 0
        mutual_funds = profile.get("mutual_funds", 0) or 0
        stocks = profile.get("stocks", 0) or 0
        fixed_deposits = profile.get("fixed_deposits", 0) or 0
        existing_loans_count = profile.get("existing_loans", 0) or 0
        
        # Calculate loan summary
        pending_loans = len([l for l in loans if l.get("status") == "PENDING"])
        approved_loans = len([l for l in loans if l.get("status") == "APPROVED"])
        rejected_loans = len([l for l in loans if l.get("status") == "REJECTED"])
        
        total_assets = account_balance + mutual_funds + stocks + fixed_deposits
        monthly_income = annual_income / 12 if annual_income else 0
        
        # Simple scoring algorithm
        score = 500  # Base score
        
        if annual_income >= 1000000:
            score += 150
        elif annual_income >= 500000:
            score += 100
        elif annual_income >= 300000:
            score += 50
            
        if total_assets >= 1000000:
            score += 100
        elif total_assets >= 500000:
            score += 75
        elif total_assets >= 100000:
            score += 50
            
        if monthly_income > 0:
            expense_ratio = monthly_expenses / monthly_income
            if expense_ratio < 0.3:
                score += 100
            elif expense_ratio < 0.5:
                score += 50
            elif expense_ratio > 0.8:
                score -= 50
                
        if existing_loans_count == 0:
            score += 50
        elif existing_loans_count <= 2:
            score += 20
        else:
            score -= 30
            
        # Cap score between 300-900
        score = max(300, min(900, score))
        
        # Mock spending breakdown
        spending_breakdown = [
            {"category": "Food & Dining", "amount": monthly_expenses * 0.3},
            {"category": "Shopping", "amount": monthly_expenses * 0.25},
            {"category": "Transportation", "amount": monthly_expenses * 0.15},
            {"category": "Bills & Utilities", "amount": monthly_expenses * 0.2},
            {"category": "Entertainment", "amount": monthly_expenses * 0.1}
        ] if monthly_expenses > 0 else []
        
        # Mock income vs expense data
        income_vs_expense = [
            {"month": "Oct", "income": monthly_income, "expenses": monthly_expenses * 0.9},
            {"month": "Nov", "income": monthly_income, "expenses": monthly_expenses * 0.95},
            {"month": "Dec", "income": monthly_income, "expenses": monthly_expenses * 1.1},
            {"month": "Jan", "income": monthly_income, "expenses": monthly_expenses}
        ] if monthly_income > 0 else []
        
        return {
            "customer_score": score,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "total_assets": total_assets,
            "account_balance": account_balance,
            "investments": {
                "mutual_funds": mutual_funds,
                "stocks": stocks,
                "fixed_deposits": fixed_deposits,
                "other": 0
            },
            "loan_summary": {
                "pending": pending_loans,
                "approved": approved_loans,
                "rejected": rejected_loans,
                "total": len(loans)
            },
            "spending_breakdown": spending_breakdown,
            "income_vs_expense": income_vs_expense,
            "expense_mismatch": False,
            "expense_mismatch_percent": 0,
            "profile_completed": annual_income > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
