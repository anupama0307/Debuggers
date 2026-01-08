"""
Risk Engine service for RISKOFF API.
Calculates risk scores for loan applications using EMI and DTI metrics.
"""

from typing import List, Dict, Any


def calculate_emi(principal: float, tenure_months: int, annual_rate: float = 12.0) -> float:
    """
    Calculate EMI using standard formula.
    
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    
    Args:
        principal: Loan principal amount
        tenure_months: Loan tenure in months
        annual_rate: Annual interest rate (default 12%)
    
    Returns:
        Monthly EMI amount
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    
    # Convert annual rate to monthly rate (as decimal)
    monthly_rate = annual_rate / 12 / 100
    
    if monthly_rate == 0:
        return principal / tenure_months
    
    # EMI formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    
    return round(emi, 2)


def calculate_risk_score(
    amount: float,
    tenure_months: int,
    income: float,
    expenses: float
) -> Dict[str, Any]:
    """
    Calculate risk score based on loan application parameters.
    
    Scoring Rules (Member 3 Spec):
    - Start at 0 points
    - DTI > 0.40: Add 30 points
    - DTI > 0.60: Add 50 points (instead of 30)
    - Expenses > 70% of income: Add 20 points
    - Multiplier: If DTI > 0.5 AND Expenses > 80% of income, multiply by 1.5
    - Score > 50: REJECTED, else APPROVED
    
    Args:
        amount: Loan principal amount
        tenure_months: Loan tenure in months
        income: Monthly income
        expenses: Monthly expenses
    
    Returns:
        Dict with score, status, emi, and reasons
    """
    reasons: List[str] = []
    score = 0.0
    
    # Handle division by zero for income
    if income <= 0:
        return {
            "score": 100.0,
            "status": "REJECTED",
            "emi": 0.0,
            "reasons": ["Invalid income: Income must be greater than zero"]
        }
    
    # Calculate EMI using proper formula (12% annual interest)
    emi = calculate_emi(principal=amount, tenure_months=tenure_months, annual_rate=12.0)
    
    # Calculate Debt-to-Income ratio (DTI)
    dti_ratio = emi / income
    
    # Calculate expense ratio
    expense_ratio = expenses / income
    
    # ========== SCORING RULES ==========
    
    # Rule 1: DTI > 0.40 -> Add 30 points
    # Rule 2: DTI > 0.60 -> Add 50 points (replaces 30)
    if dti_ratio > 0.60:
        score += 50
        reasons.append(f"Critical DTI ratio: {dti_ratio:.2%} (above 60%)")
    elif dti_ratio > 0.40:
        score += 30
        reasons.append(f"High DTI ratio: {dti_ratio:.2%} (above 40%)")
    else:
        reasons.append(f"Healthy DTI ratio: {dti_ratio:.2%}")
    
    # Rule 3: Expenses > 70% of income -> Add 20 points
    if expense_ratio > 0.70:
        score += 20
        reasons.append(f"High expense ratio: {expense_ratio:.2%} of income")
    
    # Rule 4: Multiplier - If DTI > 0.5 AND Expenses > 80% of income
    if dti_ratio > 0.50 and expense_ratio > 0.80:
        score *= 1.5
        reasons.append("Risk multiplier applied: High DTI and expenses")
    
    # Ensure score is capped at 100
    score = min(100.0, score)
    
    # Determine status: Score > 50 = REJECTED
    if score > 50:
        status = "REJECTED"
    else:
        status = "APPROVED"
    
    return {
        "score": round(score, 2),
        "status": status,
        "emi": emi,
        "reasons": reasons
    }
