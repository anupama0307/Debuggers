"""
Pydantic schemas for data validation.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ============ User Schemas ============
class UserSignup(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    phone: str = Field(..., min_length=10, max_length=15, description="User's phone number")
    password: str = Field(..., min_length=8, description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone": "1234567890",
                "password": "securepassword123"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# ============ Loan Schemas ============
class LoanApplication(BaseModel):
    """Schema for loan application submission."""
    amount: float = Field(..., gt=0, description="Loan amount requested")
    tenure_months: int = Field(..., ge=1, le=360, description="Loan tenure in months")
    income: float = Field(..., gt=0, description="Monthly income")
    expenses: float = Field(..., ge=0, description="Monthly expenses")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 50000.00,
                "tenure_months": 24,
                "income": 75000.00,
                "expenses": 30000.00
            }
        }


class RiskResult(BaseModel):
    """Schema for risk assessment result."""
    score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    status: str = Field(..., description="Risk status: LOW, MEDIUM, HIGH")
    reasons: List[str] = Field(default_factory=list, description="Reasons for the risk score")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 75.5,
                "status": "MEDIUM",
                "reasons": ["Debt-to-income ratio is moderate", "Short credit history"]
            }
        }


# ============ Receipt Schemas ============
class ReceiptData(BaseModel):
    """Schema for parsed receipt data."""
    merchant: Optional[str] = Field(None, description="Merchant name")
    amount: Optional[float] = Field(None, description="Transaction amount")
    date: Optional[str] = Field(None, description="Transaction date")
    category: Optional[str] = Field(None, description="Expense category")


# ============ Zudu Voice Agent Schemas ============
class ZuduResponse(BaseModel):
    """Schema for Zudu voice agent response."""
    text: str = Field(..., description="Text response for voice synthesis")
    loan_status: Optional[str] = Field(None, description="Current loan status")
    amount_due: Optional[float] = Field(None, description="Amount due")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Your loan of 50000 rupees is approved. Next EMI of 2500 is due on January 15th.",
                "loan_status": "APPROVED",
                "amount_due": 2500.00
            }
        }


# ============ Admin Schemas ============
class LoanStatusUpdate(BaseModel):
    """Schema for admin loan status update."""
    loan_id: str = Field(..., description="Loan ID")
    status: str = Field(..., description="New status: PENDING, APPROVED, REJECTED")
    remarks: Optional[str] = Field(None, description="Admin remarks")
