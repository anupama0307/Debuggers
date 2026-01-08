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
    expenses: float,
    existing_emi: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate risk score based on loan application parameters.
    
    Scoring Rules:
    - Start at 0 points
    - If (new EMI + existing EMI + expenses) > income: INSTANT REJECT (can't afford)
    - If total EMI > 50% of (income - expenses): Add 40 points (high burden on disposable income)
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
        existing_emi: Sum of EMIs from existing approved loans
    
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
    
    # Calculate EMI for new loan using proper formula (12% annual interest)
    new_emi = calculate_emi(principal=amount, tenure_months=tenure_months, annual_rate=12.0)
    
    # Total EMI burden = new loan EMI + existing approved loan EMIs
    total_emi = new_emi + existing_emi
    
    # Calculate Debt-to-Income ratio (DTI) using TOTAL EMI
    dti_ratio = total_emi / income
    
    # Calculate expense ratio
    expense_ratio = expenses / income
    
    # Calculate disposable income (income after expenses)
    disposable_income = income - expenses
    
    # ========== CRITICAL CHECK: CAN THEY AFFORD IT? ==========
    
    # If total EMI (new + existing) + expenses exceed income, they literally cannot pay
    if (total_emi + expenses) > income:
        if existing_emi > 0:
            return {
                "score": 100.0,
                "status": "REJECTED",
                "emi": new_emi,
                "reasons": [
                    f"Unaffordable: New EMI (₹{new_emi:,.0f}) + Existing EMIs (₹{existing_emi:,.0f}) + Expenses (₹{expenses:,.0f}) = ₹{(total_emi + expenses):,.0f} exceeds monthly income (₹{income:,.0f})",
                    "Applicant cannot afford this loan along with existing loan obligations"
                ]
            }
        else:
            return {
                "score": 100.0,
                "status": "REJECTED",
                "emi": new_emi,
                "reasons": [
                    f"Unaffordable: EMI (₹{new_emi:,.0f}) + Expenses (₹{expenses:,.0f}) = ₹{(new_emi + expenses):,.0f} exceeds monthly income (₹{income:,.0f})",
                    "Applicant cannot afford this loan with current income and expenses"
                ]
            }
    
    # Add info about existing loans if any
    if existing_emi > 0:
        reasons.append(f"Existing loan EMIs: ₹{existing_emi:,.0f}/month")
    
    # If total EMI takes more than 70% of disposable income, very risky
    if disposable_income > 0:
        emi_to_disposable = total_emi / disposable_income
        if emi_to_disposable > 0.70:
            score += 40
            reasons.append(f"Total EMI is {emi_to_disposable:.0%} of disposable income (very high)")
        elif emi_to_disposable > 0.50:
            score += 25
            reasons.append(f"Total EMI is {emi_to_disposable:.0%} of disposable income (moderate)")
    
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
        "emi": new_emi,
        "reasons": reasons
    }
