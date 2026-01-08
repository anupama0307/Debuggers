"""
Upload router for RISKOFF API.
Handles receipt image and bank statement uploads with database persistence.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends
from typing import Optional
from app.config import supabase_client
from app.schemas import ReceiptData
from app.services.parser import parse_bank_statement_csv, analyze_receipt_image, transcribe_audio
from app.utils.security import get_current_user, CurrentUser, get_current_user_optional

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


@router.post("/receipt")
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    """
    Upload a receipt image and extract transaction details using Gemini Vision AI.
    
    Returns the extracted data for user verification before saving.
    Authentication is optional - logged-in users get user_id attached.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )

    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )

    try:
        # Parse receipt using Gemini Vision AI
        receipt_data = await analyze_receipt_image(file_content, file.content_type)

        # Add user_id if authenticated
        if current_user:
            receipt_data["user_id"] = current_user.id

        return {
            "status": "success",
            "message": "Receipt analyzed successfully. Please verify the extracted data.",
            "data": receipt_data
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}"
        )


@router.post("/bank-statement")
async def upload_bank_statement(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Upload a bank statement CSV, parse transactions, and save to database.
    
    Requires authentication. Transactions are linked to the user's account.
    Includes identity verification - the file must contain the user's name.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed. Please upload a .csv file."
        )

    try:
        # Read file content
        file_content = await file.read()

        # Validate file is not empty
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty"
            )

        # Get user's full name for identity verification
        user_full_name = current_user.full_name
        
        # Try to get name from profiles table if not in token
        if not user_full_name and supabase_client:
            try:
                profile_response = supabase_client.table("profiles").select("full_name").eq(
                    "id", current_user.id
                ).limit(1).execute()
                if profile_response.data and profile_response.data[0].get("full_name"):
                    user_full_name = profile_response.data[0]["full_name"]
            except:
                pass  # Continue without profile lookup

        # Step 1: Save bank statement record
        statement_record = {
            "user_id": current_user.id,
            "file_name": file.filename,
            "file_url": f"uploads/statements/{current_user.id}/{file.filename}",  # Simulated path
            "status": "processing"
        }

        try:
            statement_response = supabase_client.table("bank_statements").insert(statement_record).execute()
            statement_id = statement_response.data[0]["id"] if statement_response.data else None
        except Exception as e:
            # If bank_statements table doesn't exist, continue without it
            statement_id = None

        # Step 2: Parse the bank statement CSV with identity verification
        try:
            transactions = parse_bank_statement_csv(file_content, user_full_name)
        except ValueError as e:
            error_message = str(e)
            if "Identity Mismatch" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Identity Verification Failed: The uploaded file does not match your account."
                )
            raise

        if not transactions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No transactions found in the CSV file"
            )

        # Step 3: Prepare transactions for database insert
        transactions_to_insert = []
        for txn in transactions:
            db_transaction = {
                "user_id": current_user.id,
                "description": txn.get("description"),
                "amount": txn.get("amount"),
                "category": txn.get("category", "Misc"),
                "transaction_date": txn.get("date"),
                "transaction_type": txn.get("type", "Debit")
            }
            # Only include if we have at least description or amount
            if db_transaction["description"] or db_transaction["amount"]:
                transactions_to_insert.append(db_transaction)

        # Step 4: Bulk insert transactions
        inserted_count = 0
        if transactions_to_insert:
            try:
                insert_response = supabase_client.table("transactions").insert(transactions_to_insert).execute()
                inserted_count = len(insert_response.data) if insert_response.data else 0
            except Exception as e:
                # Log error but don't fail - return parsed data
                print(f"⚠️ Database insert error: {e}")

        # Step 5: Update statement status to completed
        if statement_id:
            try:
                supabase_client.table("bank_statements").update({
                    "status": "completed",
                    "transactions_count": inserted_count
                }).eq("id", statement_id).execute()
            except:
                pass

        return {
            "status": "success",
            "message": "Bank statement processed successfully",
            "transactions_parsed": len(transactions),
            "transactions_saved": inserted_count,
            "statement_id": statement_id,
            "transactions": transactions[:10]  # Return first 10 for preview
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bank statement: {str(e)}"
        )


@router.post("/receipt/save")
async def save_receipt_transaction(
    merchant_name: str,
    total_amount: float,
    transaction_date: Optional[str] = None,
    category: str = "Other",
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Save a verified receipt transaction to the database.
    
    This is called after the user verifies the extracted receipt data.
    """
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

    try:
        transaction_data = {
            "user_id": current_user.id,
            "description": merchant_name,
            "amount": -abs(total_amount),  # Negative for expense
            "category": category,
            "transaction_date": transaction_date,
            "transaction_type": "Debit"
        }

        response = supabase_client.table("transactions").insert(transaction_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save transaction"
            )

        return {
            "status": "success",
            "message": "Receipt transaction saved successfully",
            "transaction": response.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving transaction: {str(e)}"
        )


@router.post("/audio/transcribe")
async def transcribe_audio_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Transcribe an audio file to text using Gemini AI.
    
    Supports voice notes that can be fed into the AI Agent.
    Useful for queries like "I need a loan for 5 lakhs".
    
    Requires authentication.
    """
    # Allowed audio MIME types
    allowed_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/x-m4a",
        "audio/m4a",
        "audio/mp4",
        "audio/ogg",
        "audio/webm"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: MP3, WAV, M4A, OGG, WebM"
        )
    
    # Validate file size (max 25MB for audio)
    file_content = await file.read()
    max_size = 25 * 1024 * 1024  # 25MB
    
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 25MB limit"
        )
    
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty"
        )
    
    try:
        # Transcribe audio using Gemini
        transcription = await transcribe_audio(file_content, file.content_type)
        
        return {
            "status": "success",
            "transcription": transcription,
            "file_name": file.filename,
            "file_size_bytes": len(file_content),
            "user_id": current_user.id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {str(e)}"
        )
