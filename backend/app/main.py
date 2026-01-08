"""
RISKOFF API - FastAPI Entry Point
A Fintech application for risk assessment and loan management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import supabase_client
from app.routers import auth, loans, upload, admin, zudu

# Initialize FastAPI application
app = FastAPI(
    title="RISKOFF API",
    description="A Fintech API for risk assessment and loan management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(loans.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(zudu.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint to check if the API is active."""
    return {
        "status": "active",
        "service": "RISKOFF API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API and Supabase connection status.
    """
    health_status = {
        "api_status": "healthy",
        "supabase_status": "unknown"
    }

    if supabase_client is None:
        health_status["supabase_status"] = "not_configured"
        health_status["message"] = "Supabase client not initialized. Check environment variables."
        return health_status

    try:
        # Verify Supabase connection
        response = supabase_client.auth.get_session()
        health_status["supabase_status"] = "connected"
        health_status["message"] = "All systems operational"
    except Exception as e:
        health_status["supabase_status"] = "error"
        health_status["message"] = f"Supabase connection error: {str(e)}"

    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)