"""
Loans router for RISKOFF API.
Handles loan applications and risk assessment with authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.config import supabase_client
from app.schemas import LoanCreate, LoanResponse, LoanApplication, RiskResult
from app.services.risk_engine import calculate_risk_score
from app.services import audit
from app.services.llm import generate_rejection_reason, generate_approval_message
from app.utils.security import get_current_user, CurrentUser

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)


@router.post("/apply", response_model=LoanResponse)
async def apply_for_loan(
    application: LoanCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Submit a loan application and get instant risk assessment.
    
    Requires authentication. Calculates risk, generates AI explanation,
    saves to database, and logs the action.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Calculate risk score using the new engine
        risk_result = calculate_risk_score(
            amount=application.amount,
            tenure_months=application.tenure_months,
            income=application.monthly_income,
            expenses=application.monthly_expenses
        )

        # Generate AI explanation based on status
        if risk_result["status"] == "REJECTED":
            ai_explanation = await generate_rejection_reason(risk_result["reasons"])
        else:
            ai_explanation = await generate_approval_message(
                amount=application.amount,
                emi=risk_result["emi"],
                tenure_months=application.tenure_months
            )

        # Prepare loan data for database
        loan_data = {
            "user_id": current_user.id,
            "amount": application.amount,
            "tenure_months": application.tenure_months,
            "interest_rate": 12.0,
            "emi": risk_result["emi"],
            "status": risk_result["status"],
            "risk_score": risk_result["score"],
            "risk_reason": ", ".join(risk_result["reasons"]),
            "ai_explanation": ai_explanation
        }

        # Store loan application in Supabase
        response = supabase_client.table("loans").insert(loan_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save loan application"
            )

        loan_record = response.data[0]

        # Log the action (non-blocking, won't crash on failure)
        await audit.log_action(
            user_id=current_user.id,
            action="LOAN_APPLICATION",
            details={
                "loan_id": loan_record.get("id"),
                "amount": application.amount,
                "status": risk_result["status"],
                "risk_score": risk_result["score"],
                "purpose": application.purpose
            }
        )

        # Calculate max approved amount (only if approved)
        max_approved = application.amount if risk_result["status"] == "APPROVED" else None

        return LoanResponse(
            id=loan_record.get("id"),
            status=risk_result["status"],
            risk_score=risk_result["score"],
            max_approved_amount=max_approved,
            emi=risk_result["emi"],
            ai_explanation=ai_explanation
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my-loans")
async def get_my_loans(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get all loan applications for the authenticated user.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        response = supabase_client.table("loans").select("*").eq(
            "user_id", current_user.id
        ).order("created_at", desc=True).execute()

        return {"loans": response.data, "total": len(response.data)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/")
async def get_all_loans():
    """
    Get all loan applications (admin view).
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        response = supabase_client.table("loans").select("*").execute()
        return {"loans": response.data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{loan_id}")
async def get_loan_by_id(loan_id: str):
    """
    Get a specific loan by ID.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        response = supabase_client.table("loans").select("*").eq("id", loan_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
