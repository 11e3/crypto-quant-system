"""
Unit tests for risk metrics module.

Tests cover all branches including edge cases for lines:
63, 93, 159-162
"""

import numpy as np
import pytest

from src.risk.metrics import (
    PortfolioRiskMetrics,
    calculate_portfolio_risk_metrics,
    calculate_portfolio_volatility,
)


class TestCalculatePortfolioVolatility:
    """Test calculate_portfolio_volatility function."""

    def test_with_valid_returns(self) -> None:
        """Test volatility calculation with valid returns."""
        returns = np.array([0.01, -0.02, 0.03, -0.01, 0.02])
        vol = calculate_portfolio_volatility(returns, annualization_factor=252)
        assert vol > 0.0

    def test_with_empty_returns(self) -> None:
        """Test volatility calculation with empty returns (line 93)."""
        returns = np.array([])
        vol = calculate_portfolio_volatility(returns)
        assert vol == 0.0


class TestCalculatePortfolioRiskMetrics:
    """Test calculate_portfolio_risk_metrics function."""

    @pytest.fixture
    def sample_data(self) -> dict[str, np.ndarray]:
        """Create sample data for testing."""
        return {
            "equity_curve": np.array([10000, 10100, 10050, 10200, 10150]),
            "daily_returns": np.array([0.01, -0.005, 0.015, -0.005]),
        }

    def test_basic_metrics(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test basic metrics calculation."""
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
        )
        assert isinstance(metrics, PortfolioRiskMetrics)
        # VaR can be positive or negative depending on returns
        assert metrics.var_95 is not None
        assert metrics.var_99 is not None
        assert metrics.cvar_95 is not None
        assert metrics.cvar_99 is not None
        assert metrics.portfolio_volatility > 0

    def test_with_asset_returns_single_asset(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with single asset returns - no correlation (line 140)."""
        asset_returns = {
            "ASSET1": np.array([0.01, -0.005, 0.015, -0.005]),
        }
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            asset_returns=asset_returns,
        )
        # With only 1 asset, correlation should be None
        assert metrics.avg_correlation is None
        assert metrics.max_correlation is None
        assert metrics.min_correlation is None

    def test_with_asset_returns_multiple_assets(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with multiple asset returns - correlation calculated (line 138)."""
        asset_returns = {
            "ASSET1": np.array([0.01, -0.005, 0.015, -0.005]),
            "ASSET2": np.array([0.02, -0.01, 0.01, -0.003]),
        }
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            asset_returns=asset_returns,
        )
        # With 2 assets, correlation should be calculated
        assert metrics.avg_correlation is not None
        assert metrics.max_correlation is not None
        assert metrics.min_correlation is not None

    def test_with_empty_asset_returns(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with empty asset returns (line 140)."""
        asset_returns: dict[str, np.ndarray] = {}
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            asset_returns=asset_returns,
        )
        assert metrics.avg_correlation is None
        assert metrics.max_correlation is None
        assert metrics.min_correlation is None

    def test_with_position_values(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with position values - concentration calculated (line 148)."""
        position_values = {"ASSET1": 5000.0, "ASSET2": 3000.0, "ASSET3": 2000.0}
        total_portfolio_value = 10000.0
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            position_values=position_values,
            total_portfolio_value=total_portfolio_value,
        )
        # With position values, concentration should be calculated
        assert metrics.max_position_pct is not None
        assert metrics.position_concentration is not None
        assert metrics.max_position_pct == 0.5  # 5000/10000

    def test_without_position_values(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test without position values (line 151)."""
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
        )
        assert metrics.max_position_pct is None
        assert metrics.position_concentration is None

    def test_with_empty_position_values(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with empty position values (line 151)."""
        position_values: dict[str, float] = {}
        total_portfolio_value = 10000.0
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            position_values=position_values,
            total_portfolio_value=total_portfolio_value,
        )
        assert metrics.max_position_pct is None
        assert metrics.position_concentration is None

    def test_with_benchmark_returns(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with benchmark returns - beta calculated (line 155-162)."""
        benchmark_returns = np.array([0.015, -0.008, 0.012, -0.004])
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            benchmark_returns=benchmark_returns,
        )
        # Beta should be calculated
        assert metrics.portfolio_beta is not None

    def test_with_empty_benchmark_returns(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with empty benchmark returns (line 157)."""
        benchmark_returns = np.array([])
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            benchmark_returns=benchmark_returns,
        )
        # Beta should be None
        assert metrics.portfolio_beta is None

    def test_with_mismatched_benchmark_length(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with mismatched benchmark returns length (line 159)."""
        benchmark_returns = np.array([0.015, -0.008])  # Only 2 values vs 4 returns
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            benchmark_returns=benchmark_returns,
        )
        # Beta should be None due to length mismatch
        assert metrics.portfolio_beta is None

    def test_with_zero_variance_benchmark(self, sample_data: dict[str, np.ndarray]) -> None:
        """Test with zero variance benchmark (line 162)."""
        benchmark_returns = np.array([0.0, 0.0, 0.0, 0.0])  # Zero variance
        metrics = calculate_portfolio_risk_metrics(
            equity_curve=sample_data["equity_curve"],
            daily_returns=sample_data["daily_returns"],
            benchmark_returns=benchmark_returns,
        )
        # Beta should be None because benchmark variance is 0
        assert metrics.portfolio_beta is None


class TestPortfolioRiskMetrics:
    """Test PortfolioRiskMetrics dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        metrics = PortfolioRiskMetrics(
            var_95=-0.05,
            var_99=-0.08,
            cvar_95=-0.06,
            cvar_99=-0.09,
            portfolio_volatility=0.15,
            avg_correlation=0.5,
            max_correlation=0.8,
            min_correlation=0.2,
            max_position_pct=0.4,
            position_concentration=0.25,
            portfolio_beta=1.2,
        )
        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["var_95"] == -0.05
        assert result["portfolio_beta"] == 1.2


__all__ = [
    "TestCalculatePortfolioVolatility",
    "TestCalculatePortfolioRiskMetrics",
    "TestPortfolioRiskMetrics",
]
