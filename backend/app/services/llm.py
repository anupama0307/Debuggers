"""
LLM service for RISKOFF API.
Handles Gemini text generation for various AI features.
"""

from typing import Optional
from app.config import gemini_model


async def generate_loan_summary(
    amount: float,
    tenure_months: int,
    risk_score: float,
    risk_status: str
) -> str:
    """
    Generate a human-readable loan summary using Gemini AI.

    Args:
        amount: Loan amount
        tenure_months: Loan tenure in months
        risk_score: Calculated risk score
        risk_status: Risk status (LOW/MEDIUM/HIGH)

    Returns:
        Generated summary text
    """
    if not gemini_model:
        return f"Loan of ₹{amount:,.2f} for {tenure_months} months. Risk: {risk_status} ({risk_score:.1f}/100)"

    try:
        prompt = f"""Generate a brief, professional loan summary for a customer in 2-3 sentences.

        Loan Details:
        - Amount: ₹{amount:,.2f}
        - Tenure: {tenure_months} months
        - Risk Score: {risk_score}/100
        - Risk Status: {risk_status}

        Keep it friendly and informative. Do not include any disclaimers."""

        response = gemini_model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"Loan of ₹{amount:,.2f} for {tenure_months} months. Risk: {risk_status} ({risk_score:.1f}/100)"


async def generate_risk_explanation(
    score: float,
    status: str,
    reasons: list
) -> str:
    """
    Generate a detailed explanation of the risk assessment.

    Args:
        score: Risk score (0-100)
        status: Risk status (LOW/MEDIUM/HIGH)
        reasons: List of risk factors

    Returns:
        Generated explanation text
    """
    if not gemini_model:
        return f"Risk Status: {status} (Score: {score}). Factors: {', '.join(reasons)}"

    try:
        reasons_text = "\n".join(f"- {r}" for r in reasons)
        prompt = f"""Explain this loan risk assessment to a customer in simple, non-technical terms.

        Risk Score: {score}/100
        Risk Status: {status}
        Factors:
        {reasons_text}

        Provide a helpful 2-3 sentence explanation. Be encouraging if score is good, and provide actionable advice if score needs improvement."""

        response = gemini_model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"Risk Status: {status} (Score: {score}). Factors: {', '.join(reasons)}"


async def generate_voice_response(
    context: str,
    user_name: Optional[str] = None
) -> str:
    """
    Generate a conversational response for the Zudu voice agent.

    Args:
        context: Context about what the user is asking
        user_name: Optional user name for personalization

    Returns:
        Generated voice-friendly response
    """
    if not gemini_model:
        return f"I understand you're asking about {context}. Let me help you with that."

    try:
        name_prefix = f"The user's name is {user_name}. " if user_name else ""
        prompt = f"""{name_prefix}Generate a brief, friendly voice response for a fintech voice assistant.

        User Query Context: {context}

        Requirements:
        - Keep it under 50 words
        - Use natural, conversational language
        - Be helpful and professional
        - Suitable for text-to-speech"""

        response = gemini_model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"I understand you're asking about {context}. Let me help you with that."


async def analyze_spending_patterns(transactions: list) -> dict:
    """
    Analyze spending patterns from transaction data using Gemini.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Analysis results with categories and insights
    """
    if not gemini_model or not transactions:
        return {"analysis": "Unable to analyze spending patterns", "categories": {}}

    try:
        # Prepare transaction summary
        txn_summary = "\n".join([
            f"- {t.get('description', 'Unknown')}: ₹{t.get('amount', 0)}"
            for t in transactions[:50]  # Limit to 50 transactions
        ])

        prompt = f"""Analyze these bank transactions and categorize spending patterns.

        Transactions:
        {txn_summary}

        Return a JSON object with:
        {{
            "total_spending": 0,
            "categories": {{"Food": 0, "Transport": 0, "Shopping": 0, ...}},
            "insights": ["insight 1", "insight 2"],
            "recommendation": "brief recommendation"
        }}

        Return ONLY the JSON object."""

        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean up response if wrapped in code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        import json
        return json.loads(response_text)

    except Exception as e:
        return {"analysis": f"Error analyzing patterns: {str(e)}", "categories": {}}
