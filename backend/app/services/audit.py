"""
Audit Logging service for RISKOFF API.
Provides centralized audit trail for all important actions.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.config import supabase_client


async def log_action(
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log an action to the audit_logs table in Supabase.
    
    This function is designed to be non-blocking and fail-safe.
    Logging errors will not crash the main application.
    
    Args:
        user_id: The ID of the user performing the action
        action: The action type (e.g., "LOAN_APPLICATION", "LOGIN", "STATUS_UPDATE")
        details: Optional dictionary with additional context
    
    Returns:
        bool: True if logging succeeded, False otherwise
    """
    if not supabase_client:
        print("⚠️ Audit: Supabase client not initialized, skipping log")
        return False
    
    try:
        log_entry = {
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase_client.table("audit_logs").insert(log_entry).execute()
        return True
        
    except Exception as e:
        # Silently fail - audit logging should never crash the main app
        print(f"⚠️ Audit log error (non-critical): {str(e)}")
        return False


async def log_loan_application(
    user_id: str,
    loan_id: int,
    amount: float,
    status: str,
    risk_score: float
) -> bool:
    """
    Convenience function to log loan application events.
    """
    return await log_action(
        user_id=user_id,
        action="LOAN_APPLICATION",
        details={
            "loan_id": loan_id,
            "amount": amount,
            "status": status,
            "risk_score": risk_score
        }
    )


async def log_status_change(
    user_id: str,
    loan_id: int,
    old_status: str,
    new_status: str,
    admin_id: Optional[str] = None
) -> bool:
    """
    Convenience function to log loan status changes.
    """
    return await log_action(
        user_id=user_id,
        action="LOAN_STATUS_CHANGE",
        details={
            "loan_id": loan_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": admin_id or "system"
        }
    )
