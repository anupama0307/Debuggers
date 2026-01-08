"""
Unit tests for RISKOFF Risk Engine.
Tests the mathematical logic of EMI calculation and risk scoring.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.risk_engine import calculate_emi, calculate_risk_score


class TestEMICalculation:
    """Tests for EMI calculation function."""
    
    def test_emi_standard_calculation(self):
        """Test EMI calculation for 100K loan, 12 months, 12% interest."""
        emi = calculate_emi(principal=100000, tenure_months=12, annual_rate=12.0)
        # Expected EMI for 100K at 12% for 12 months is approximately 8884.88
        assert abs(emi - 8884.88) < 1, f"Expected ~8884.88, got {emi}"
    
    def test_emi_zero_principal(self):
        """Test EMI with zero principal returns zero."""
        emi = calculate_emi(principal=0, tenure_months=12)
        assert emi == 0.0
    
    def test_emi_zero_tenure(self):
        """Test EMI with zero tenure returns zero."""
        emi = calculate_emi(principal=100000, tenure_months=0)
        assert emi == 0.0
    
    def test_emi_larger_loan(self):
        """Test EMI calculation for larger loan amount."""
        emi = calculate_emi(principal=500000, tenure_months=24, annual_rate=12.0)
        # Should be roughly 23536.74
        assert emi > 23000 and emi < 24000, f"Expected ~23536, got {emi}"
    
    def test_emi_long_tenure(self):
        """Test EMI calculation for longer tenure (lower EMI)."""
        emi_short = calculate_emi(principal=100000, tenure_months=12)
        emi_long = calculate_emi(principal=100000, tenure_months=36)
        # Longer tenure should have lower EMI
        assert emi_long < emi_short, "Longer tenure should have lower EMI"


class TestRiskScoreCalculation:
    """Tests for risk score calculation function."""
    
    def test_low_dti_approved(self):
        """Test that low DTI ratio results in APPROVED status."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=50000,
            expenses=20000
        )
        assert result["status"] == "APPROVED", f"Expected APPROVED, got {result['status']}"
        assert result["score"] <= 50, f"Score should be <= 50, got {result['score']}"
    
    def test_high_dti_rejected(self):
        """Test that high DTI ratio (>60%) results in high risk score."""
        result = calculate_risk_score(
            amount=500000,
            tenure_months=12,
            income=30000,
            expenses=25000
        )
        # DTI would be very high, should be rejected
        assert result["score"] > 50, f"High DTI should have score > 50, got {result['score']}"
        assert result["status"] == "REJECTED", f"Expected REJECTED, got {result['status']}"
    
    def test_medium_dti_threshold(self):
        """Test DTI at the 40% threshold boundary."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=20000,  # EMI ~8884, DTI ~44%
            expenses=5000
        )
        # DTI > 40% should add 30 points
        assert result["score"] >= 30, f"DTI > 40% should add 30 points, got {result['score']}"
    
    def test_high_expenses_penalty(self):
        """Test that expenses >70% of income adds penalty."""
        result = calculate_risk_score(
            amount=50000,
            tenure_months=12,
            income=50000,
            expenses=40000  # 80% of income
        )
        # High expenses should add 20 points
        assert "expense" in str(result["reasons"]).lower(), "Should mention expense ratio"
    
    def test_zero_income_rejected(self):
        """Test that zero income is properly rejected."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=0,
            expenses=0
        )
        assert result["status"] == "REJECTED", "Zero income should be rejected"
        assert result["score"] == 100.0, "Zero income should have max score"
    
    def test_multiplier_effect(self):
        """Test the 1.5x multiplier for high DTI + high expenses."""
        # Create scenario with DTI > 50% and expenses > 80%
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=15000,  # Very low income
            expenses=13000  # 86% of income
        )
        # Should trigger multiplier
        assert result["status"] == "REJECTED"
    
    def test_emi_returned_correctly(self):
        """Test that EMI is correctly returned in result."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=100000,
            expenses=30000
        )
        assert "emi" in result, "Result should contain EMI"
        assert result["emi"] > 0, "EMI should be positive"
        assert abs(result["emi"] - 8884.88) < 1, f"EMI should be ~8884.88, got {result['emi']}"
    
    def test_reasons_provided(self):
        """Test that reasons list is provided in result."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=50000,
            expenses=20000
        )
        assert "reasons" in result, "Result should contain reasons"
        assert len(result["reasons"]) > 0, "Should have at least one reason"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_negative_principal(self):
        """Test handling of negative principal."""
        emi = calculate_emi(principal=-100000, tenure_months=12)
        assert emi == 0.0, "Negative principal should return 0"
    
    def test_very_high_income(self):
        """Test with very high income (safe borrower)."""
        result = calculate_risk_score(
            amount=100000,
            tenure_months=12,
            income=500000,  # Very high income
            expenses=50000
        )
        assert result["status"] == "APPROVED"
        assert result["score"] == 0, "High income should have 0 risk score"
    
    def test_minimum_loan(self):
        """Test with minimum loan amount."""
        result = calculate_risk_score(
            amount=1000,  # Small loan
            tenure_months=1,
            income=50000,
            expenses=20000
        )
        assert result["status"] == "APPROVED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
