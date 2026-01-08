"""
AI Agent router for RISKOFF API.
Provides intelligent chat interface for users to interact with their loan information.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.config import supabase_client
from app.schemas import ChatRequest, ChatResponse
from app.services.llm import generate_bank_chat_response
from app.utils.security import get_current_user, CurrentUser

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"]
)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Chat with the AI Financial Agent.
    
    The agent has access to the user's loan information and can answer
    questions about loan status, EMI, and provide financial guidance.
    
    Requires authentication.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )

    try:
        # Get user's full name from profiles table (or use metadata from auth)
        user_name = current_user.full_name or "Valued Customer"
        
        # Try to get additional profile info if available
        try:
            profile_response = supabase_client.table("profiles").select("full_name").eq("id", current_user.id).limit(1).execute()
            if profile_response.data and profile_response.data[0].get("full_name"):
                user_name = profile_response.data[0]["full_name"]
        except:
            pass  # Use the name from auth metadata if profiles table doesn't exist

        # Get the user's latest loan application
        loan_details = {"status": "No active application"}
        
        try:
            loan_response = supabase_client.table("loans").select("*").eq(
                "user_id", current_user.id
            ).order("created_at", desc=True).limit(1).execute()

            if loan_response.data:
                loan = loan_response.data[0]
                loan_details = {
                    "status": loan.get("status", "PENDING"),
                    "amount": loan.get("amount", 0),
                    "emi": loan.get("emi", 0),
                    "risk_score": loan.get("risk_score", 0),
                    "tenure_months": loan.get("tenure_months", 0),
                    "ai_explanation": loan.get("ai_explanation", "")
                }
        except Exception as e:
            # If loans table query fails, continue with default context
            pass

        # Generate AI response
        result = await generate_bank_chat_response(
            user_name=user_name,
            loan_details=loan_details,
            user_query=request.query
        )

        return ChatResponse(
            response=result["response"],
            suggested_action=result.get("suggested_action")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )
