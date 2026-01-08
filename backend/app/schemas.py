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


class LoanCreate(BaseModel):
    """Schema for creating a new loan application (Member 3 spec)."""
    amount: float = Field(..., gt=0, description="Loan amount requested")
    tenure_months: int = Field(..., ge=1, le=360, description="Loan tenure in months")
    monthly_income: float = Field(..., gt=0, description="Monthly income")
    monthly_expenses: float = Field(..., ge=0, description="Monthly expenses")
    purpose: str = Field(..., min_length=3, max_length=200, description="Purpose of the loan")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 100000.00,
                "tenure_months": 24,
                "monthly_income": 75000.00,
                "monthly_expenses": 30000.00,
                "purpose": "Business expansion"
            }
        }


class LoanResponse(BaseModel):
    """Schema for loan application response with risk assessment."""
    id: int = Field(..., description="Loan ID")
    status: str = Field(..., description="Loan status: APPROVED, REJECTED, PENDING")
    risk_score: float = Field(..., description="Risk score (0-100)")
    max_approved_amount: Optional[float] = Field(None, description="Maximum approved loan amount")
    emi: float = Field(..., description="Calculated EMI amount")
    ai_explanation: str = Field(..., description="AI-generated explanation")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "status": "APPROVED",
                "risk_score": 25.0,
                "max_approved_amount": 100000.00,
                "emi": 8884.88,
                "ai_explanation": "Congratulations! Your loan has been approved based on your strong financial profile."
            }
        }


class RiskResult(BaseModel):
    """Schema for risk assessment result."""
    score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    status: str = Field(..., description="Risk status: APPROVED, REJECTED")
    emi: float = Field(..., description="Calculated EMI amount")
    reasons: List[str] = Field(default_factory=list, description="Reasons for the risk score")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 25.0,
                "status": "APPROVED",
                "emi": 8884.88,
                "reasons": ["Healthy debt-to-income ratio"]
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
    voice_text: str = Field(..., description="Text response for voice synthesis")
    data: Optional[dict] = Field(default_factory=dict, description="Additional data payload")

    class Config:
        json_schema_extra = {
            "example": {
                "voice_text": "Hello John. Your loan of 50000 rupees is currently Approved.",
                "data": {"loan_status": "APPROVED", "amount": 50000, "emi": 2500.00}
            }
        }


# ============ Admin Schemas ============
class LoanStatusUpdate(BaseModel):
    """Schema for admin loan status update."""
    loan_id: str = Field(..., description="Loan ID")
    status: str = Field(..., description="New status: PENDING, APPROVED, REJECTED")
    remarks: Optional[str] = Field(None, description="Admin remarks")


# ============ AI Agent Schemas ============
class ChatRequest(BaseModel):
    """Schema for AI Agent chat request."""
    query: str = Field(..., min_length=1, max_length=1000, description="User's query to the AI agent")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is my loan status?"
            }
        }


class ChatResponse(BaseModel):
    """Schema for AI Agent chat response."""
    response: str = Field(..., description="AI-generated response")
    suggested_action: Optional[str] = Field(None, description="Suggested next action for the user")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your loan of ₹100,000 has been approved! Your monthly EMI is ₹8,884.88.",
                "suggested_action": "Visit our branch to complete the documentation."
            }
        }
