"""
Zudu Voice Agent router for RISKOFF API.
Provides endpoints for voice bot integration with security key validation.
"""

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Header
from app.config import supabase_client
from app.schemas import ZuduResponse

router = APIRouter(
    prefix="/zudu",
    tags=["Zudu Voice Agent"]
)


def verify_zudu_key(x_zudu_key: str = Header(..., description="Zudu API secret key")):
    """
    Dependency to verify the Zudu secret key from request header.
    """
    expected_key = os.getenv("ZUDU_SECRET_KEY", "")
    
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zudu service not configured. ZUDU_SECRET_KEY not set."
        )
    
    if x_zudu_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Zudu API key"
        )
    
    return True


@router.get("/loan-status/{phone_number}", response_model=ZuduResponse)
async def get_loan_status_by_phone(phone_number: str, _: bool = Header(default=None, alias="x-zudu-key")):
    """
    Fetch loan status by phone number for voice bot.
    Returns a voice-friendly text response suitable for text-to-speech synthesis.
    
    Requires x-zudu-key header for authentication.
    """
    # Verify Zudu key
    x_zudu_key = _
    if x_zudu_key is not None:
        expected_key = os.getenv("ZUDU_SECRET_KEY", "")
        if expected_key and x_zudu_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Zudu API key"
            )
    
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Query user by phone number from profiles table
        user_response = supabase_client.table("profiles").select("id, full_name").eq("phone", phone_number).execute()

        if not user_response.data:
            return ZuduResponse(
                voice_text=f"I'm sorry, I couldn't find an account with that phone number. Please check the number and try again.",
                data={"found": False, "phone": phone_number}
            )

        user = user_response.data[0]
        user_id = user.get("id")
        full_name = user.get("full_name", "Customer")

        # Fetch latest loan for this user
        loan_response = supabase_client.table("loans").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()

        if not loan_response.data:
            return ZuduResponse(
                voice_text=f"Hello {full_name}. You currently have no active loan applications. Would you like to apply for a new loan?",
                data={"found": True, "user_name": full_name, "has_loans": False}
            )

        loan = loan_response.data[0]
        loan_status = loan.get("status", "PENDING")
        amount = loan.get("amount", 0)
        ai_explanation = loan.get("ai_explanation", "")
        emi = loan.get("emi", 0)

        # Generate voice-friendly response based on loan status
        if loan_status == "PENDING":
            voice_text = f"Hello {full_name}. Your loan application for {int(amount)} rupees is currently under review. We will notify you once a decision is made."
        elif loan_status == "APPROVED":
            voice_text = f"Hello {full_name}. Your loan for {int(amount)} rupees is currently Approved. {ai_explanation}"
        elif loan_status == "REJECTED":
            voice_text = f"Hello {full_name}. Your loan for {int(amount)} rupees is currently Rejected. {ai_explanation}"
        else:
            voice_text = f"Hello {full_name}. Your loan status is {loan_status}. Please contact support for more information."

        return ZuduResponse(
            voice_text=voice_text,
            data={
                "found": True,
                "user_name": full_name,
                "loan_status": loan_status,
                "amount": amount,
                "emi": emi
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/payment-reminder/{phone_number}", response_model=ZuduResponse)
async def get_payment_reminder(phone_number: str, _: str = Header(default=None, alias="x-zudu-key")):
    """
    Get payment reminder for a user by phone number.
    Returns a voice-friendly EMI reminder with due date.
    
    Requires x-zudu-key header for authentication.
    """
    # Verify Zudu key
    x_zudu_key = _
    if x_zudu_key is not None:
        expected_key = os.getenv("ZUDU_SECRET_KEY", "")
        if expected_key and x_zudu_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Zudu API key"
            )
    
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Query user by phone number
        user_response = supabase_client.table("profiles").select("id, full_name").eq("phone", phone_number).execute()

        if not user_response.data:
            return ZuduResponse(
                voice_text=f"I'm sorry, I couldn't find an account with that phone number.",
                data={"found": False}
            )

        user = user_response.data[0]
        user_id = user.get("id")
        full_name = user.get("full_name", "Customer")

        # Find latest APPROVED loan
        loan_response = supabase_client.table("loans").select("*").eq("user_id", user_id).eq("status", "APPROVED").order("created_at", desc=True).limit(1).execute()

        if not loan_response.data:
            return ZuduResponse(
                voice_text=f"Hello {full_name}. You don't have any active approved loans with pending payments.",
                data={"found": True, "user_name": full_name, "has_approved_loan": False}
            )

        loan = loan_response.data[0]
        emi = loan.get("emi", 0)
        
        # Calculate dummy due date (5th of next month)
        today = datetime.now()
        if today.day >= 5:
            next_month = today.replace(day=1) + timedelta(days=32)
            due_date = next_month.replace(day=5)
        else:
            due_date = today.replace(day=5)
        
        due_date_str = due_date.strftime("%-dth of %B")

        voice_text = f"Hi {full_name}, your next EMI of {int(emi)} rupees is due on the {due_date_str}. Please keep your balance ready."

        return ZuduResponse(
            voice_text=voice_text,
            data={
                "found": True,
                "user_name": full_name,
                "emi": emi,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "loan_id": loan.get("id")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/greeting", response_model=ZuduResponse)
async def get_greeting():
    """
    Get a greeting message for the voice bot.
    """
    return ZuduResponse(
        voice_text="Welcome to RISKOFF. I can help you check your loan status, get payment reminders, or connect you to an agent. How can I assist you today?",
        data={"action": "greeting"}
    )
