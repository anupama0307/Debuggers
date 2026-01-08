"""
Admin router for RISKOFF API.
Handles administrative operations with role-based access control.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from app.config import supabase_client
from app.schemas import LoanStatusUpdate
from app.utils.security import get_current_user, CurrentUser
from app.services import notification, audit

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# ============ Admin Verification Dependency ============
async def verify_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Dependency to verify the current user has admin privileges.
    
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
    
    try:
        # Check if user has admin role in profiles table
        response = supabase_client.table("profiles").select("role").eq(
            "id", current_user.id
        ).limit(1).execute()
        
        if not response.data:
            # No profile found - check if it might be stored elsewhere
            # For now, deny access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        user_role = response.data[0].get("role", "").lower()
        
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


# ============ Admin Endpoints ============

@router.get("/stats")
async def get_dashboard_stats(admin: CurrentUser = Depends(verify_admin)):
    """
    Get dashboard statistics for admin.
    
    Returns counts of loans by status and total volume.
    Requires admin role.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Fetch all loans
        response = supabase_client.table("loans").select("status, amount").execute()
        loans = response.data or []

        # Calculate stats
        total_loans = len(loans)
        pending_count = sum(1 for l in loans if l.get("status") == "PENDING")
        approved_count = sum(1 for l in loans if l.get("status") == "APPROVED")
        rejected_count = sum(1 for l in loans if l.get("status") == "REJECTED")
        total_volume = sum(float(l.get("amount", 0)) for l in loans)

        return {
            "total_loans": total_loans,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "total_volume": round(total_volume, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/loans")
async def get_all_loans(admin: CurrentUser = Depends(verify_admin)):
    """
    Get all loan applications for admin review.
    
    Returns loans ordered by newest first.
    Requires admin role.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        response = supabase_client.table("loans").select("*").order(
            "created_at", desc=True
        ).execute()
        
        return {"loans": response.data or [], "total": len(response.data or [])}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/loans/{loan_id}/status")
async def update_loan_status(
    loan_id: int,
    update: LoanStatusUpdate,
    admin: CurrentUser = Depends(verify_admin)
):
    """
    Update the status of a loan application.
    
    Sends email notification to the user about the status change.
    Requires admin role.
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
        # First, get the current loan to retrieve user_id and current explanation
        loan_response = supabase_client.table("loans").select("*").eq(
            "id", loan_id
        ).limit(1).execute()
        
        if not loan_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loan with ID {loan_id} not found"
            )
        
        current_loan = loan_response.data[0]
        user_id = current_loan.get("user_id")
        old_status = current_loan.get("status")
        current_explanation = current_loan.get("ai_explanation", "")
        
        # Prepare update data
        update_data = {"status": update.status}
        
        # Append admin override to explanation
        admin_note = f"\n\n[Admin Override by {admin.email}]"
        if update.remarks:
            admin_note += f": {update.remarks}"
        update_data["ai_explanation"] = current_explanation + admin_note
        
        # Also store remarks separately if provided
        if update.remarks:
            update_data["admin_remarks"] = update.remarks

        # Update the loan
        response = supabase_client.table("loans").update(update_data).eq(
            "id", loan_id
        ).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update loan status"
            )

        updated_loan = response.data[0]
        
        # Fetch user email from profiles
        user_email = None
        user_name = "Valued Customer"
        
        if user_id:
            try:
                profile_response = supabase_client.table("profiles").select(
                    "email, full_name"
                ).eq("id", user_id).limit(1).execute()
                
                if profile_response.data:
                    user_email = profile_response.data[0].get("email")
                    user_name = profile_response.data[0].get("full_name", user_name)
            except:
                pass  # Continue without email notification
        
        # Send email notification
        if user_email:
            notification.send_loan_status_notification(
                to_email=user_email,
                user_name=user_name,
                loan_id=loan_id,
                new_status=update.status,
                remarks=update.remarks
            )
        
        # Log the action
        await audit.log_action(
            user_id=admin.id,
            action="ADMIN_STATUS_CHANGE",
            details={
                "loan_id": loan_id,
                "old_status": old_status,
                "new_status": update.status,
                "remarks": update.remarks,
                "notified_user": user_email is not None
            }
        )

        return {
            "message": "Loan status updated successfully",
            "loan": updated_loan,
            "notification_sent": user_email is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ Legacy Endpoints (Backward Compatibility) ============

@router.patch("/loans/status")
async def update_loan_status_legacy(update: LoanStatusUpdate):
    """
    Legacy endpoint for updating loan status.
    Kept for backward compatibility.
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

        response = supabase_client.table("loans").update(update_data).eq(
            "id", update.loan_id
        ).execute()

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
