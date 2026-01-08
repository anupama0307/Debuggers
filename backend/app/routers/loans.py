"""
Loans router for RISKOFF API.
Handles loan applications and risk assessment.
"""

from fastapi import APIRouter, HTTPException, status
from app.config import supabase_client
from app.schemas import LoanApplication, RiskResult
from app.services.risk_engine import calculate_risk_score

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)


@router.post("/apply", response_model=RiskResult)
async def apply_for_loan(application: LoanApplication):
    """
    Submit a loan application and get instant risk assessment.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Calculate risk score
        risk_result = calculate_risk_score(
            amount=application.amount,
            tenure_months=application.tenure_months,
            income=application.income,
            expenses=application.expenses
        )

        # Store loan application in Supabase
        loan_data = {
            "amount": application.amount,
            "tenure_months": application.tenure_months,
            "income": application.income,
            "expenses": application.expenses,
            "risk_score": risk_result.score,
            "risk_status": risk_result.status,
            "status": "PENDING"
        }

        response = supabase_client.table("loans").insert(loan_data).execute()

        return risk_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/")
async def get_all_loans():
    """
    Get all loan applications.
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
