"""
Admin router for RISKOFF API.
Handles administrative operations with role-based access control.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from app.config import supabase_client
from app.schemas import LoanStatusUpdate, RiskAnalysisRequest
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
    
    Returns loans ordered by newest first with user info.
    Requires admin role.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not initialized"
        )

    try:
        # Fetch all loans
        response = supabase_client.table("loans").select("*").order(
            "created_at", desc=True
        ).execute()
        
        loans = response.data or []
        
        # Enrich loans with user info and derived fields
        enriched_loans = []
        for loan in loans:
            # Get user info from profiles table
            user_id = loan.get("user_id")
            if user_id:
                try:
                    profile_response = supabase_client.table("profiles").select(
                        "full_name, email"
                    ).eq("id", user_id).limit(1).execute()
                    
                    if profile_response.data:
                        profile = profile_response.data[0]
                        loan["user_name"] = profile.get("full_name", "N/A")
                        loan["user_email"] = profile.get("email", "N/A")
                    else:
                        loan["user_name"] = "Unknown"
                        loan["user_email"] = "N/A"
                except:
                    loan["user_name"] = "Unknown"
                    loan["user_email"] = "N/A"
            else:
                loan["user_name"] = "Unknown"
                loan["user_email"] = "N/A"
            
            # Derive risk_category from risk_score if not present
            if not loan.get("risk_category") and loan.get("risk_score") is not None:
                score = loan.get("risk_score", 0)
                if score <= 30:
                    loan["risk_category"] = "LOW"
                elif score <= 60:
                    loan["risk_category"] = "MEDIUM"
                else:
                    loan["risk_category"] = "HIGH"
            
            enriched_loans.append(loan)
        
        return {"loans": enriched_loans, "total": len(enriched_loans)}
        
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


@router.post("/risk-analysis")
async def analyze_risk(request: RiskAnalysisRequest, admin: CurrentUser = Depends(verify_admin)):
    """
    Perform risk analysis on customer data.
    
    Calculates risk score based on multiple factors including:
    - Age, income, employment stability
    - Debt-to-income ratio
    - Customer credit score
    - Loan amount vs income ratio
    
    Returns detailed risk assessment with recommendation.
    Requires admin role.
    """
    try:
        # Calculate monthly income
        monthly_income = request.annual_income / 12
        
        # Calculate EMI (12% annual interest rate)
        rate = 0.12 / 12
        months = request.loan_tenure_months
        principal = request.loan_amount_requested
        emi = (principal * rate * pow(1 + rate, months)) / (pow(1 + rate, months) - 1)
        
        # EMI to Income Ratio
        emi_to_income = (emi / monthly_income) * 100
        
        # Debt to Income Ratio (including existing loans)
        total_monthly_debt = emi + (request.existing_loan_amount / 12)
        debt_to_income = (total_monthly_debt / monthly_income) * 100
        
        # Initialize risk score (0-100, lower is better)
        risk_score = 0
        risk_factors = []
        
        # Age factor (18-25 higher risk, 26-55 optimal, 56+ slightly higher)
        if request.age < 25:
            risk_score += 10
            risk_factors.append("Young age (higher risk profile)")
        elif request.age > 55:
            risk_score += 8
            risk_factors.append("Age above 55 years")
        
        # Employment stability
        if request.employment_years < 1:
            risk_score += 20
            risk_factors.append("Less than 1 year employment")
        elif request.employment_years < 3:
            risk_score += 10
            risk_factors.append("Less than 3 years employment")
        
        # Customer score factor
        if request.customer_score < 300:
            risk_score += 35
            risk_factors.append("Very low customer score (< 300)")
        elif request.customer_score < 500:
            risk_score += 25
            risk_factors.append("Low customer score (< 500)")
        elif request.customer_score < 650:
            risk_score += 15
            risk_factors.append("Below average customer score (< 650)")
        elif request.customer_score < 750:
            risk_score += 5
            risk_factors.append("Average customer score")
        
        # EMI to Income ratio
        if emi_to_income > 60:
            risk_score += 30
            risk_factors.append(f"EMI to income ratio too high ({emi_to_income:.1f}%)")
        elif emi_to_income > 50:
            risk_score += 20
            risk_factors.append(f"High EMI to income ratio ({emi_to_income:.1f}%)")
        elif emi_to_income > 40:
            risk_score += 10
            risk_factors.append(f"Moderate EMI to income ratio ({emi_to_income:.1f}%)")
        
        # Loan amount vs annual income
        loan_to_income = request.loan_amount_requested / request.annual_income
        if loan_to_income > 5:
            risk_score += 25
            risk_factors.append("Loan amount > 5x annual income")
        elif loan_to_income > 3:
            risk_score += 15
            risk_factors.append("Loan amount > 3x annual income")
        elif loan_to_income > 2:
            risk_score += 5
            risk_factors.append("Loan amount > 2x annual income")
        
        # Expense mismatch (fraud indicator)
        if request.has_expense_mismatch:
            risk_score += 20
            risk_factors.append("⚠️ Expense mismatch detected (potential fraud)")
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Determine risk category and decision
        if risk_score <= 25:
            risk_category = "LOW"
            decision = "AUTO_APPROVE"
            recommendation = "Low risk customer. Recommend immediate approval."
        elif risk_score <= 50:
            risk_category = "MEDIUM"
            decision = "MANUAL_REVIEW"
            recommendation = "Moderate risk. Manual verification recommended before approval."
        else:
            risk_category = "HIGH"
            decision = "AUTO_REJECT"
            recommendation = "High risk profile. Consider rejection or request additional documentation."
        
        # Calculate max recommended loan based on income
        disposable_income = monthly_income - request.monthly_expenses
        max_emi_affordable = disposable_income * 0.4  # 40% of disposable income
        max_loan = (max_emi_affordable * (pow(1 + rate, months) - 1)) / (rate * pow(1 + rate, months))
        
        return {
            "risk_score": risk_score,
            "risk_percentage": risk_score,
            "risk_category": risk_category,
            "decision": decision,
            "recommendation": recommendation,
            "monthly_emi": round(emi, 2),
            "emi_to_income_ratio": round(emi_to_income, 2),
            "debt_to_income_ratio": round(debt_to_income, 2),
            "max_recommended_loan": round(max(max_loan, 0), 2),
            "risk_factors": risk_factors if risk_factors else ["No significant risk factors identified"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Risk analysis failed: {str(e)}"
        )
