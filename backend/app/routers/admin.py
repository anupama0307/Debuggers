"""
Admin router for RISKOFF API.
Handles administrative operations on loans.
"""

from fastapi import APIRouter, HTTPException, status
from app.config import supabase_client
from app.schemas import LoanStatusUpdate, RiskAnalysisRequest
from app.services.risk_engine import calculate_emi

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


@router.post("/risk-analysis")
async def analyze_risk(data: RiskAnalysisRequest):
    """
    Analyze risk for a customer based on financial details.
    Returns risk score, decision, EMI, and recommendations.
    """
    try:
        # Calculate monthly income from annual
        monthly_income = data.annual_income / 12
        
        # Calculate EMI for requested loan
        monthly_emi = calculate_emi(
            principal=data.loan_amount_requested,
            tenure_months=data.loan_tenure_months,
            annual_rate=12.0
        )
        
        # Calculate key ratios
        emi_to_income_ratio = (monthly_emi / monthly_income) * 100 if monthly_income > 0 else 100
        expense_ratio = (data.monthly_expenses / monthly_income) * 100 if monthly_income > 0 else 100
        dti_ratio = ((monthly_emi + (data.existing_loan_amount / 12)) / monthly_income) * 100 if monthly_income > 0 else 100
        
        # Calculate disposable income
        disposable_income = monthly_income - data.monthly_expenses - (data.existing_loan_amount / 12)
        
        # Risk factors list
        risk_factors = []
        risk_score = 0
        
        # Age factor
        if data.age < 25:
            risk_factors.append("Young age - less financial stability")
            risk_score += 10
        elif data.age > 55:
            risk_factors.append("Higher age - closer to retirement")
            risk_score += 15
        
        # Employment factor
        if data.employment_years < 2:
            risk_factors.append("Limited employment history (< 2 years)")
            risk_score += 20
        elif data.employment_years < 5:
            risk_factors.append("Moderate employment history (2-5 years)")
            risk_score += 5
        
        # Customer score factor
        if data.customer_score < 500:
            risk_factors.append(f"Poor credit score ({data.customer_score})")
            risk_score += 35
        elif data.customer_score < 650:
            risk_factors.append(f"Below average credit score ({data.customer_score})")
            risk_score += 20
        elif data.customer_score < 750:
            risk_factors.append(f"Average credit score ({data.customer_score})")
            risk_score += 10
        
        # EMI to income ratio
        if emi_to_income_ratio > 50:
            risk_factors.append(f"Very high EMI burden ({emi_to_income_ratio:.1f}% of income)")
            risk_score += 30
        elif emi_to_income_ratio > 40:
            risk_factors.append(f"High EMI burden ({emi_to_income_ratio:.1f}% of income)")
            risk_score += 20
        elif emi_to_income_ratio > 30:
            risk_factors.append(f"Moderate EMI burden ({emi_to_income_ratio:.1f}% of income)")
            risk_score += 10
        
        # Expense ratio
        if expense_ratio > 70:
            risk_factors.append(f"High expense ratio ({expense_ratio:.1f}% of income)")
            risk_score += 15
        
        # Existing loans
        if data.existing_loan_amount > monthly_income * 6:
            risk_factors.append("High existing loan burden")
            risk_score += 20
        
        # Fraud flag
        if data.has_expense_mismatch:
            risk_factors.append("⚠️ Expense mismatch detected (potential fraud)")
            risk_score += 40
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        risk_percentage = risk_score
        
        # Determine risk category
        if risk_score < 30:
            risk_category = "LOW"
        elif risk_score < 50:
            risk_category = "MEDIUM"
        elif risk_score < 70:
            risk_category = "HIGH"
        else:
            risk_category = "CRITICAL"
        
        # Determine decision
        if data.has_expense_mismatch:
            decision = "AUTO_REJECT"
            recommendation = "❌ Application flagged for potential fraud. Manual verification required before any approval."
        elif risk_score < 30 and data.customer_score >= 650:
            decision = "AUTO_APPROVE"
            recommendation = "✅ Strong financial profile. Recommend auto-approval with standard terms."
        elif risk_score < 50:
            decision = "MANUAL_REVIEW"
            recommendation = "⚠️ Moderate risk. Recommend manual review with possible reduced amount or shorter tenure."
        else:
            decision = "AUTO_REJECT"
            recommendation = "❌ High risk profile. Recommend rejection or significant loan restructuring."
        
        # Calculate max recommended loan (based on 40% EMI to income ratio)
        max_emi_affordable = monthly_income * 0.40 - (data.existing_loan_amount / 12)
        if max_emi_affordable > 0:
            # Reverse calculate principal from EMI
            monthly_rate = 12.0 / 12 / 100
            factor = (1 + monthly_rate) ** data.loan_tenure_months
            max_recommended_loan = max_emi_affordable * (factor - 1) / (monthly_rate * factor)
            max_recommended_loan = max(0, round(max_recommended_loan, -3))  # Round to nearest 1000
        else:
            max_recommended_loan = 0
        
        return {
            "decision": decision,
            "risk_score": risk_score,
            "risk_percentage": risk_percentage,
            "risk_category": risk_category,
            "monthly_emi": round(monthly_emi, 2),
            "emi_to_income_ratio": round(emi_to_income_ratio, 1),
            "max_recommended_loan": max_recommended_loan,
            "risk_factors": risk_factors if risk_factors else ["No significant risk factors identified"],
            "recommendation": recommendation
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
