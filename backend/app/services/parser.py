"""
Parser service for RISKOFF API.
Handles receipt image parsing and bank statement CSV parsing with auto-categorization.
Includes identity verification for security.
"""

import io
import json
import difflib
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from app.config import gemini_model


# ============ Category Keywords ============
CATEGORY_KEYWORDS = {
    "Transport": ["uber", "ola", "fuel", "petrol", "diesel", "cab", "taxi", "metro", "bus", "train", "parking"],
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "hotel", "food", "pizza", "burger", "dominos", "starbucks", "mcdonald"],
    "Shopping": ["amazon", "flipkart", "myntra", "shopping", "mall", "store", "retail"],
    "Income": ["salary", "transfer", "credit", "refund", "cashback", "interest"],
    "Utilities": ["electricity", "water", "gas", "bill", "recharge", "mobile", "internet", "broadband"],
    "Healthcare": ["hospital", "pharmacy", "medical", "doctor", "clinic", "medicine", "health"],
    "Entertainment": ["netflix", "spotify", "movie", "cinema", "game", "subscription"],
}


def categorize_transaction(description: str) -> str:
    """
    Auto-categorize a transaction based on keywords in the description.
    
    Args:
        description: Transaction description text
        
    Returns:
        Category string (Transport, Food, Income, etc.)
    """
    if not description:
        return "Misc"
    
    description_lower = description.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    
    return "Misc"


# ============ Identity Verification ============
def is_name_match(extracted_name: str, user_name: str, threshold: float = 0.6) -> bool:
    """
    Check if two names are similar using fuzzy matching.
    Handles format differences like "Doe, John" vs "John Doe".
    
    Args:
        extracted_name: Name found in the document
        user_name: User's registered name
        threshold: Similarity threshold (0.0 to 1.0, default 0.6)
        
    Returns:
        True if names are similar enough
    """
    if not extracted_name or not user_name:
        return False
    
    # Normalize both names
    extracted_lower = extracted_name.lower().strip()
    user_lower = user_name.lower().strip()
    
    # Direct match
    if extracted_lower == user_lower:
        return True
    
    # Check if user name is contained in extracted name
    if user_lower in extracted_lower or extracted_lower in user_lower:
        return True
    
    # Handle "Last, First" format - split and compare parts
    user_parts = set(user_lower.replace(",", " ").split())
    extracted_parts = set(extracted_lower.replace(",", " ").split())
    
    # Check if all user name parts appear in extracted name
    if user_parts.issubset(extracted_parts) or extracted_parts.issubset(user_parts):
        return True
    
    # Fuzzy match using difflib
    similarity = difflib.SequenceMatcher(None, extracted_lower, user_lower).ratio()
    if similarity >= threshold:
        return True
    
    # Also check reversed name order
    user_parts_list = user_lower.replace(",", "").split()
    if len(user_parts_list) >= 2:
        reversed_name = " ".join(reversed(user_parts_list))
        reversed_similarity = difflib.SequenceMatcher(None, extracted_lower, reversed_name).ratio()
        if reversed_similarity >= threshold:
            return True
    
    return False


def verify_identity_in_file(file_content: bytes, user_full_name: str) -> bool:
    """
    Verify that the user's name appears in the bank statement file header.
    
    Args:
        file_content: Raw file bytes
        user_full_name: User's registered full name
        
    Returns:
        True if identity verified, raises ValueError if not
    """
    if not user_full_name:
        # If no name to verify, skip verification
        return True
    
    try:
        # Read first 1024 bytes or first 10 lines (whichever covers more)
        header_bytes = file_content[:2048]  # Read a bit more for safety
        
        # Try to decode as UTF-8, fallback to latin-1
        try:
            header_text = header_bytes.decode('utf-8')
        except UnicodeDecodeError:
            header_text = header_bytes.decode('latin-1', errors='ignore')
        
        # Take first 10 lines
        header_lines = header_text.split('\n')[:10]
        header_text = '\n'.join(header_lines)
        
        # Check if user name appears in header
        if is_name_match(header_text, user_full_name):
            return True
        
        # Check each line individually
        for line in header_lines:
            if is_name_match(line, user_full_name):
                return True
        
        # Name not found - raise error
        raise ValueError(f"Identity Mismatch: File does not belong to {user_full_name}")
        
    except ValueError:
        raise
    except Exception as e:
        # If there's an error reading the file, don't fail on verification
        # Let the parsing step handle it
        return True


def parse_bank_statement_csv(
    file_content: bytes,
    user_full_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parse bank statement CSV file and extract transactions with auto-categorization.
    Includes identity verification if user_full_name is provided.

    Args:
        file_content: Raw CSV file bytes
        user_full_name: Optional user's full name for identity verification

    Returns:
        List of transaction dictionaries with cleaned data and categories
        
    Raises:
        ValueError: If identity verification fails or parsing errors occur
    """
    # Step 1: Identity Verification (if user name provided)
    if user_full_name:
        verify_identity_in_file(file_content, user_full_name)
    
    # Step 2: Parse CSV
    try:
        # Read CSV from bytes
        df = pd.read_csv(io.BytesIO(file_content))

        # Standardize column names (lowercase and strip whitespace)
        df.columns = df.columns.str.lower().str.strip()

        # Common column mappings
        column_mappings = {
            "date": ["date", "transaction_date", "txn_date", "value_date", "posting_date"],
            "description": ["description", "narration", "particulars", "remarks", "details", "transaction_details"],
            "amount": ["amount", "transaction_amount", "txn_amount", "value"],
            "type": ["type", "transaction_type", "txn_type", "dr/cr", "debit/credit"],
            "debit": ["debit", "withdrawal", "dr", "debit_amount"],
            "credit": ["credit", "deposit", "cr", "credit_amount"],
            "balance": ["balance", "closing_balance", "available_balance", "running_balance"]
        }

        # Rename columns to standard names
        for standard_name, possible_names in column_mappings.items():
            for col_name in possible_names:
                if col_name in df.columns:
                    df = df.rename(columns={col_name: standard_name})
                    break

        # Handle amount calculation from debit/credit columns
        if "amount" not in df.columns:
            if "debit" in df.columns or "credit" in df.columns:
                df["debit"] = pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0)
                df["credit"] = pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
                df["amount"] = df["credit"] - df["debit"]  # positive = income, negative = expense

        # Clean and convert amount to float
        if "amount" in df.columns:
            # Remove currency symbols and commas
            df["amount"] = df["amount"].astype(str).str.replace(r"[₹$,\s]", "", regex=True)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        # Add category based on description
        if "description" in df.columns:
            df["category"] = df["description"].apply(categorize_transaction)
        else:
            df["category"] = "Misc"

        # Determine transaction type (Debit/Credit) if not present
        if "type" not in df.columns and "amount" in df.columns:
            df["type"] = df["amount"].apply(lambda x: "Credit" if x > 0 else "Debit")

        # Convert to list of dictionaries
        transactions = df.to_dict(orient="records")

        # Clean up NaN values and format data
        cleaned_transactions = []
        for txn in transactions:
            cleaned_txn = {}
            for key, value in txn.items():
                if pd.isna(value):
                    cleaned_txn[key] = None
                elif isinstance(value, float):
                    cleaned_txn[key] = round(value, 2)
                else:
                    cleaned_txn[key] = value
            cleaned_transactions.append(cleaned_txn)

        return cleaned_transactions

    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV parsing error: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing bank statement: {e}")


async def analyze_receipt_image(image_bytes: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Analyze receipt image using Gemini Vision to extract transaction details.

    Args:
        image_bytes: Raw image bytes
        content_type: MIME type of the image (default: image/jpeg)

    Returns:
        Dictionary with merchant_name, total_amount, transaction_date, category
    """
    if not gemini_model:
        raise ValueError("Gemini AI model not initialized. Check GEMINI_API_KEY.")

    try:
        # Prepare the image for Gemini
        image_part = {
            "mime_type": content_type,
            "data": image_bytes
        }

        # Structured prompt for receipt extraction
        prompt = """Analyze this receipt image. Extract the following fields in strict JSON format:
{
    "merchant_name": "Name of the store or business",
    "total_amount": 0.00,
    "transaction_date": "YYYY-MM-DD",
    "category": "Food/Shopping/Travel/Medical/Entertainment/Utilities/Other"
}

Rules:
- If you cannot read a field clearly, use null for that field.
- For total_amount, extract the final total or grand total as a number.
- For transaction_date, convert to YYYY-MM-DD format.
- Choose the most appropriate category.
- Return ONLY the JSON object, no additional text or explanation."""

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

        # Validate and clean the parsed data
        result = {
            "merchant_name": parsed_data.get("merchant_name"),
            "total_amount": None,
            "transaction_date": parsed_data.get("transaction_date"),
            "category": parsed_data.get("category", "Other")
        }

        # Ensure total_amount is a valid number
        amount = parsed_data.get("total_amount")
        if amount is not None:
            try:
                result["total_amount"] = round(float(amount), 2)
            except (ValueError, TypeError):
                result["total_amount"] = None

        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    except Exception as e:
        raise ValueError(f"Error analyzing receipt image: {e}")


# Keep legacy function name for backward compatibility
async def parse_receipt_image(file_content: bytes, content_type: str) -> Dict[str, Any]:
    """Legacy wrapper for analyze_receipt_image."""
    return await analyze_receipt_image(file_content, content_type)


def parse_bank_statement(file_content: bytes) -> List[Dict[str, Any]]:
    """Legacy wrapper for parse_bank_statement_csv."""
    return parse_bank_statement_csv(file_content)


# ============ Audio Transcription ============
async def transcribe_audio(file_content: bytes, mime_type: str) -> str:
    """
    Transcribe audio file to text using Gemini 1.5 Flash.
    
    Args:
        file_content: Raw audio file bytes
        mime_type: MIME type of the audio (e.g., 'audio/mpeg', 'audio/wav')
        
    Returns:
        Transcribed text from the audio
        
    Raises:
        ValueError: If transcription fails
    """
    if not gemini_model:
        raise ValueError("Gemini AI model not initialized. Check GEMINI_API_KEY.")
    
    try:
        # Prepare the audio for Gemini
        audio_part = {
            "mime_type": mime_type,
            "data": file_content
        }
        
        # Prompt for transcription
        prompt = "Transcribe this audio file exactly as spoken. Return only the transcribed text, no additional commentary or formatting."
        
        # Generate transcription using Gemini
        response = gemini_model.generate_content([prompt, audio_part])
        
        if not response or not response.text:
            raise ValueError("Empty response from Gemini")
        
        transcribed_text = response.text.strip()
        
        return transcribed_text
        
    except Exception as e:
        raise ValueError(f"Error transcribing audio: {e}")
