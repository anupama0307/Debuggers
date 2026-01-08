"""
Parser service for RISKOFF API.
Handles receipt image parsing and bank statement CSV parsing.
"""

import io
import json
from typing import List, Dict, Any
from app.config import gemini_model
from app.schemas import ReceiptData


async def parse_receipt_image(file_content: bytes, content_type: str) -> ReceiptData:
    """
    Parse receipt image using Gemini AI to extract merchant and amount.

    Args:
        file_content: Raw image bytes
        content_type: MIME type of the image

    Returns:
        ReceiptData with extracted merchant, amount, date, and category
    """
    if not gemini_model:
        raise ValueError("Gemini AI model not initialized. Check GEMINI_API_KEY.")

    try:
        # Prepare the image for Gemini
        image_part = {
            "mime_type": content_type,
            "data": file_content
        }

        # Prompt for structured extraction
        prompt = """Analyze this receipt image and extract the following information in JSON format:
        {
            "merchant": "Store or business name",
            "amount": 0.00,
            "date": "YYYY-MM-DD or null if not visible",
            "category": "Food/Groceries/Electronics/Fuel/Healthcare/Other"
        }

        Return ONLY the JSON object, no additional text."""

        # Generate response using Gemini
        response = gemini_model.generate_content([prompt, image_part])

        # Parse the response
        response_text = response.text.strip()

        # Clean up response if wrapped in code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        parsed_data = json.loads(response_text)

        return ReceiptData(
            merchant=parsed_data.get("merchant"),
            amount=parsed_data.get("amount"),
            date=parsed_data.get("date"),
            category=parsed_data.get("category")
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    except Exception as e:
        raise ValueError(f"Error processing receipt image: {e}")


def parse_bank_statement(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse bank statement CSV file and extract transactions.

    Args:
        file_content: Raw CSV file bytes

    Returns:
        List of transaction dictionaries
    """
    try:
        import pandas as pd

        # Read CSV from bytes
        df = pd.read_csv(io.BytesIO(file_content))

        # Standardize column names (lowercase and strip whitespace)
        df.columns = df.columns.str.lower().str.strip()

        # Common column mappings
        column_mappings = {
            "date": ["date", "transaction_date", "txn_date", "value_date"],
            "description": ["description", "narration", "particulars", "remarks", "details"],
            "amount": ["amount", "transaction_amount", "txn_amount"],
            "debit": ["debit", "withdrawal", "dr"],
            "credit": ["credit", "deposit", "cr"],
            "balance": ["balance", "closing_balance", "available_balance"]
        }

        # Rename columns to standard names
        for standard_name, possible_names in column_mappings.items():
            for col_name in possible_names:
                if col_name in df.columns:
                    df = df.rename(columns={col_name: standard_name})
                    break

        # Convert to list of dictionaries
        transactions = df.to_dict(orient="records")

        # Clean up NaN values
        for txn in transactions:
            for key, value in txn.items():
                if pd.isna(value):
                    txn[key] = None

        return transactions

    except Exception as e:
        raise ValueError(f"Error parsing bank statement: {e}")
