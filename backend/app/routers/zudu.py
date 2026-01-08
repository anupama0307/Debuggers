"""
Zudu Voice Agent router for RISKOFF API.
Provides endpoints for voice bot integration.
"""

from fastapi import APIRouter, HTTPException, status
from app.config import supabase_client
from app.schemas import ZuduResponse

router = APIRouter(
    prefix="/zudu",
    tags=["Zudu Voice Agent"]
)


@router.get("/loan-status/{phone}", response_model=ZuduResponse)
async def get_loan_status_by_phone(phone: str):
    """
    Fetch loan status by phone number for voice bot.
    Returns a text response suitable for text-to-speech synthesis.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Query user by phone number from profiles/users table
        user_response = supabase_client.table("profiles").select("id, full_name").eq("phone", phone).execute()

        if not user_response.data:
            return ZuduResponse(
                text=f"Sorry, we could not find an account associated with phone number {phone}. Please check the number and try again.",
                loan_status=None,
                amount_due=None
            )

        user = user_response.data[0]
        user_id = user.get("id")
        full_name = user.get("full_name", "Customer")

        # Fetch latest loan for this user
        loan_response = supabase_client.table("loans").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()

        if not loan_response.data:
            return ZuduResponse(
                text=f"Hello {full_name}, you currently have no active loan applications. Would you like to apply for a new loan?",
                loan_status=None,
                amount_due=None
            )

        loan = loan_response.data[0]
        loan_status = loan.get("status", "PENDING")
        amount = loan.get("amount", 0)
        emi = loan.get("emi_amount", 0)

        # Generate voice-friendly response based on loan status
        if loan_status == "PENDING":
            text = f"Hello {full_name}, your loan application of {amount} rupees is currently under review. We will notify you once a decision is made."
        elif loan_status == "APPROVED":
            text = f"Hello {full_name}, congratulations! Your loan of {amount} rupees has been approved. Your EMI amount is {emi} rupees."
        elif loan_status == "REJECTED":
            text = f"Hello {full_name}, we regret to inform you that your loan application of {amount} rupees was not approved. Please contact our support for more details."
        else:
            text = f"Hello {full_name}, your loan status is {loan_status}. Please contact support for more information."

        return ZuduResponse(
            text=text,
            loan_status=loan_status,
            amount_due=emi if loan_status == "APPROVED" else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/greeting")
async def get_greeting():
    """
    Get a greeting message for the voice bot.
    """
    return ZuduResponse(
        text="Welcome to RISKOFF. I can help you check your loan status or connect you to an agent. How can I assist you today?",
        loan_status=None,
        amount_due=None
    )
