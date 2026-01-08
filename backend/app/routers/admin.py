"""
Admin router for RISKOFF API.
Handles administrative operations on loans.
"""

from fastapi import APIRouter, HTTPException, status
from app.config import supabase_client
from app.schemas import LoanStatusUpdate

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/loans")
async def get_all_loans():
    """
    Get all loan applications for admin review.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        response = supabase_client.table("loans").select("*").order("created_at", desc=True).execute()
        return {"loans": response.data, "total": len(response.data)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/loans/status")
async def update_loan_status(update: LoanStatusUpdate):
    """
    Update the status of a loan application.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    valid_statuses = ["PENDING", "APPROVED", "REJECTED"]
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    try:
        update_data = {"status": update.status}
        if update.remarks:
            update_data["admin_remarks"] = update.remarks

        response = supabase_client.table("loans").update(update_data).eq("id", update.loan_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )

        return {
            "message": "Loan status updated successfully",
            "loan": response.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats")
async def get_dashboard_stats():
    """
    Get dashboard statistics for admin.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Fetch all loans
        response = supabase_client.table("loans").select("*").execute()
        loans = response.data

        # Calculate stats
        total_loans = len(loans)
        pending = sum(1 for l in loans if l.get("status") == "PENDING")
        approved = sum(1 for l in loans if l.get("status") == "APPROVED")
        rejected = sum(1 for l in loans if l.get("status") == "REJECTED")
        total_amount = sum(l.get("amount", 0) for l in loans)

        return {
            "total_loans": total_loans,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "total_amount_requested": total_amount
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
