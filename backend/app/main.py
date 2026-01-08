"""
RISKOFF API - FastAPI Entry Point
A Fintech application for risk assessment and loan management.
With rate limiting and security middleware.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import supabase_client
from app.routers import auth, loans, upload, admin, agent, zudu, user, grievances

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI application
app = FastAPI(
    title="RISKOFF API",
    description="A Fintech API for risk assessment and loan management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach limiter to app state
app.state.limiter = limiter

# Add rate limit exceeded exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL origins (localhost:3000, localhost:5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers (Authorization, etc.)
)


# ============ Global Exception Handlers ============
# Ensures all errors return consistent JSON structure for frontend

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with consistent JSON response."""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again later.",
            "code": 500
        }
    )

# Include all routers
app.include_router(auth.router)
app.include_router(loans.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(agent.router)
app.include_router(zudu.router)
app.include_router(user.router)
app.include_router(grievances.router)


@app.get("/", tags=["Root"])
@limiter.limit("60/minute")
async def root(request: Request):
    """Root endpoint to check if the API is active."""
    return {
        "status": "active",
        "service": "RISKOFF API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
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


# Global rate limit middleware for all endpoints
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Global middleware that applies to all requests.
    Adds security headers to responses.
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)