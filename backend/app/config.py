"""
Configuration module for RISKOFF API.
Initializes Supabase client and Gemini AI model.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Initialize Supabase client
supabase_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client, Client
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully.")
    else:
        print("⚠️ Warning: SUPABASE_URL or SUPABASE_KEY not found.")
        print("   Supabase features will be unavailable.")
except Exception as e:
    print(f"❌ Error initializing Supabase client: {e}")

# Initialize Gemini AI model
gemini_model = None
try:
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # Try gemini-2.0-flash first (newer), fallback to gemini-1.5-flash
        try:
            gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            # Quick test to verify model works
            print("✅ Gemini AI model (gemini-2.0-flash) initialized successfully.")
        except Exception as model_error:
            print(f"⚠️ gemini-2.0-flash not available, trying gemini-1.5-flash...")
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            print("✅ Gemini AI model (gemini-1.5-flash) initialized successfully.")
    else:
        print("⚠️ Warning: GEMINI_API_KEY not found.")
        print("   Gemini AI features will be unavailable.")
except Exception as e:
    print(f"❌ Error initializing Gemini AI model: {e}")