"""
Upload router for RISKOFF API.
Handles receipt image and bank statement uploads.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from app.schemas import ReceiptData
from app.services.parser import parse_receipt_image, parse_bank_statement

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


@router.post("/receipt", response_model=ReceiptData)
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload a receipt image and extract merchant/amount using Gemini AI.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Parse receipt using Gemini AI
        receipt_data = await parse_receipt_image(file_content, file.content_type)

        return receipt_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}"
        )


@router.post("/bank-statement")
async def upload_bank_statement(file: UploadFile = File(...)):
    """
    Upload a bank statement CSV and parse transactions.
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Parse bank statement
        transactions = parse_bank_statement(file_content)

        return {
            "message": "Bank statement parsed successfully",
            "transactions": transactions
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bank statement: {str(e)}"
        )
