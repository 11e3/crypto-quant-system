"""Tests for metrics_var module."""

import numpy as np

from src.risk.metrics_var import calculate_cvar, calculate_var


class TestMetricsVar:
    """Test cases for VaR and CVaR functions."""

    def test_calculate_var_empty_returns(self) -> None:
        """Test calculate_var with empty returns array (covers line 28)."""
        result = calculate_var(np.array([]), confidence_level=0.95)
        assert result == 0.0

    def test_calculate_var_normal(self) -> None:
        """Test calculate_var with normal returns."""
        returns = np.array([0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01])
        result = calculate_var(returns, confidence_level=0.95)
        assert result > 0  # VaR should be positive (loss magnitude)

    def test_calculate_cvar_empty_returns(self) -> None:
        """Test calculate_cvar with empty returns array (covers line 54)."""
        result = calculate_cvar(np.array([]), confidence_level=0.95)
        assert result == 0.0

    def test_calculate_cvar_normal(self) -> None:
        """Test calculate_cvar with normal returns."""
        returns = np.array([0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.04])
        result = calculate_cvar(returns, confidence_level=0.95)
        assert result > 0  # CVaR should be positive (expected loss magnitude)
