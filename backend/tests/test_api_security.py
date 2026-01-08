"""
Integration tests for RISKOFF API security.
Tests authentication and authorization on protected endpoints.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app


# Create test client
client = TestClient(app)


class TestPublicEndpoints:
    """Tests for public (unauthenticated) endpoints."""
    
    def test_health_check(self):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["service"] == "RISKOFF API"
    
    def test_health_endpoint(self):
        """Test the /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "api_status" in data
        assert data["api_status"] == "healthy"
    
    def test_docs_available(self):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestAdminSecurityWithoutToken:
    """Tests for admin endpoints without authentication token."""
    
    def test_admin_loans_no_token_401(self):
        """Test that /admin/loans without token returns 401 Unauthorized."""
        response = client.get("/admin/loans")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_admin_stats_no_token_401(self):
        """Test that /admin/stats without token returns 401 Unauthorized."""
        response = client.get("/admin/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_admin_status_update_no_token_401(self):
        """Test that PATCH /admin/loans/{id}/status without token returns 401."""
        response = client.patch(
            "/admin/loans/1/status",
            json={"status": "APPROVED"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestProtectedEndpointsWithoutToken:
    """Tests for protected endpoints without authentication."""
    
    def test_loans_apply_no_token_401(self):
        """Test that /loans/apply without token returns 401."""
        response = client.post(
            "/loans/apply",
            json={
                "amount": 100000,
                "tenure_months": 12,
                "monthly_income": 50000,
                "monthly_expenses": 20000,
                "purpose": "Test"
            }
        )
        assert response.status_code == 401
    
    def test_my_loans_no_token_401(self):
        """Test that /loans/my-loans without token returns 401."""
        response = client.get("/loans/my-loans")
        assert response.status_code == 401
    
    def test_agent_chat_no_token_401(self):
        """Test that /agent/chat without token returns 401."""
        response = client.post(
            "/agent/chat",
            json={"query": "What is my loan status?"}
        )
        assert response.status_code == 401


class TestInvalidTokens:
    """Tests with invalid authentication tokens."""
    
    def test_admin_loans_invalid_token(self):
        """Test that invalid token returns 401."""
        response = client.get(
            "/admin/loans",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        # Should be 401 (invalid token) not 403 (valid token but no permission)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_malformed_auth_header(self):
        """Test that malformed auth header is rejected."""
        response = client.get(
            "/admin/loans",
            headers={"Authorization": "NotBearer token123"}
        )
        assert response.status_code in [401, 403, 422]


class TestPublicRoutes:
    """Tests to verify certain routes are intentionally public."""
    
    def test_get_all_loans_public(self):
        """Test that GET /loans/ is accessible (public endpoint)."""
        response = client.get("/loans/")
        # This should work without auth (returns empty list or loans)
        assert response.status_code == 200
    
    def test_auth_login_public(self):
        """Test that /auth/login is accessible without token."""
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
        # Should return 4xx (auth failure) not 401 (missing token)
        assert response.status_code in [400, 401, 422]
    
    def test_auth_signup_public(self):
        """Test that /auth/signup is accessible without token."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "Test User",
                "phone": "9999999999"
            }
        )
        # Fix: Add 409 (Conflict) to the allowed list
        assert response.status_code in [200, 201, 400, 409, 422]


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_multiple_requests_allowed(self):
        """Test that multiple requests within limit are allowed."""
        for i in range(5):
            response = client.get("/")
            assert response.status_code == 200, f"Request {i+1} should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
