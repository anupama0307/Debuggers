"""
Risk Engine service for RISKOFF API.
Calculates risk scores for loan applications.
"""

from typing import List
from app.schemas import RiskResult


def calculate_risk_score(
    amount: float,
    tenure_months: int,
    income: float,
    expenses: float
) -> RiskResult:
    """
    Calculate risk score based on loan application parameters.

    Scoring factors:
    - Debt-to-Income Ratio (DTI)
    - Loan-to-Income Ratio
    - Monthly disposable income
    - Tenure appropriateness

    Returns:
        RiskResult with score (0-100), status, and reasons
    """
    reasons: List[str] = []
    score = 100.0  # Start with perfect score

    # Calculate key metrics
    monthly_disposable = income - expenses
    emi_estimate = amount / tenure_months
    dti_ratio = (expenses + emi_estimate) / income if income > 0 else 1.0
    loan_to_income_ratio = amount / (income * 12) if income > 0 else float('inf')

    # 1. Check if EMI is affordable (should be < 50% of disposable income)
    if monthly_disposable <= 0:
        score -= 40
        reasons.append("Monthly expenses exceed or equal income")
    elif emi_estimate > monthly_disposable * 0.5:
        score -= 25
        reasons.append("Estimated EMI exceeds 50% of disposable income")
    elif emi_estimate > monthly_disposable * 0.3:
        score -= 10
        reasons.append("EMI is high relative to disposable income")

    # 2. Debt-to-Income Ratio assessment
    if dti_ratio > 0.7:
        score -= 30
        reasons.append("High debt-to-income ratio (above 70%)")
    elif dti_ratio > 0.5:
        score -= 15
        reasons.append("Moderate debt-to-income ratio (50-70%)")
    elif dti_ratio > 0.4:
        score -= 5
        reasons.append("Acceptable debt-to-income ratio")

    # 3. Loan-to-Income Ratio
    if loan_to_income_ratio > 5:
        score -= 20
        reasons.append("Loan amount exceeds 5x annual income")
    elif loan_to_income_ratio > 3:
        score -= 10
        reasons.append("Loan amount is 3-5x annual income")

    # 4. Tenure assessment
    if tenure_months > 120:
        score -= 10
        reasons.append("Extended loan tenure (over 10 years)")
    elif tenure_months < 6:
        score -= 5
        reasons.append("Short tenure may result in high EMI")

    # 5. Minimum income check
    if income < 15000:
        score -= 15
        reasons.append("Income below minimum threshold")

    # Ensure score stays within bounds
    score = max(0, min(100, score))

    # Determine risk status
    if score >= 70:
        status = "LOW"
        if not reasons:
            reasons.append("Strong financial profile")
    elif score >= 40:
        status = "MEDIUM"
        if not reasons:
            reasons.append("Moderate risk factors present")
    else:
        status = "HIGH"
        if not reasons:
            reasons.append("Multiple risk factors identified")

    return RiskResult(
        score=round(score, 2),
        status=status,
        reasons=reasons
    )
