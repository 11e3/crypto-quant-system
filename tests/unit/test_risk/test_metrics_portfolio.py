"""Tests for metrics_portfolio module."""

import numpy as np

from src.risk.metrics_portfolio import (
    calculate_portfolio_correlation,
    calculate_position_concentration,
)


class TestMetricsPortfolio:
    """Test cases for portfolio metrics functions."""

    def test_calculate_portfolio_correlation_single_asset(self) -> None:
        """Test calculate_portfolio_correlation with single asset (covers line 27)."""
        asset_returns = {"ASSET1": np.array([0.01, 0.02, 0.03])}

        avg, max_val, min_val, matrix = calculate_portfolio_correlation(asset_returns)

        # Should return zeros and empty dataframe for single asset
        assert avg == 0.0
        assert max_val == 0.0
        assert min_val == 0.0
        assert matrix.empty

    def test_calculate_portfolio_correlation_multiple_assets(self) -> None:
        """Test calculate_portfolio_correlation with multiple assets."""
        asset_returns = {
            "ASSET1": np.array([0.01, 0.02, 0.03, 0.01]),
            "ASSET2": np.array([0.02, 0.01, 0.02, 0.03]),
        }

        avg, max_val, min_val, matrix = calculate_portfolio_correlation(asset_returns)

        # Should return valid correlation values
        assert isinstance(avg, float)
        assert isinstance(max_val, float)
        assert isinstance(min_val, float)
        assert not matrix.empty

    def test_calculate_position_concentration_empty(self) -> None:
        """Test calculate_position_concentration with empty positions (covers line 66)."""
        result_max, result_hhi = calculate_position_concentration({}, total_portfolio_value=10000.0)

        # Should return 0.0 for both metrics when empty
        assert result_max == 0.0
        assert result_hhi == 0.0

    def test_calculate_position_concentration_normal(self) -> None:
        """Test calculate_position_concentration with normal positions."""
        position_values = {
            "ASSET1": 5000.0,
            "ASSET2": 3000.0,
            "ASSET3": 2000.0,
        }
        total = sum(position_values.values())

        result_max, result_hhi = calculate_position_concentration(
            position_values, total_portfolio_value=total
        )

        # Should return valid metrics
        assert 0.0 < result_max <= 1.0
        assert 0.0 < result_hhi <= 1.0
