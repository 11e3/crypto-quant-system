"""
Unit tests for robustness_stats module.
"""

import pytest

from src.backtester.analysis.robustness_models import RobustnessResult
from src.backtester.analysis.robustness_stats import (
    calculate_neighbor_success_rate,
    calculate_sensitivity,
    find_neighbors,
)

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def sample_results() -> list[RobustnessResult]:
    """Create sample robustness results for testing."""
    return [
        RobustnessResult(
            params={"sma_period": 10, "rsi_period": 14},
            total_return=0.15,
            sharpe=1.2,
            max_drawdown=-0.10,
            win_rate=0.55,
            trade_count=50,
        ),
        RobustnessResult(
            params={"sma_period": 12, "rsi_period": 14},
            total_return=0.12,
            sharpe=1.0,
            max_drawdown=-0.12,
            win_rate=0.52,
            trade_count=45,
        ),
        RobustnessResult(
            params={"sma_period": 8, "rsi_period": 14},
            total_return=0.10,
            sharpe=0.9,
            max_drawdown=-0.15,
            win_rate=0.50,
            trade_count=55,
        ),
        RobustnessResult(
            params={"sma_period": 20, "rsi_period": 14},
            total_return=0.05,
            sharpe=0.5,
            max_drawdown=-0.20,
            win_rate=0.45,
            trade_count=30,
        ),
    ]


# -------------------------------------------------------------------------
# find_neighbors Tests
# -------------------------------------------------------------------------


class TestFindNeighbors:
    """Test find_neighbors function."""

    def test_find_neighbors_basic(self, sample_results: list[RobustnessResult]) -> None:
        """Test finding neighbors within tolerance."""
        optimal_params = {"sma_period": 10, "rsi_period": 14}
        neighbors = find_neighbors(optimal_params, sample_results, tolerance=0.20)

        # sma_period 10 ±20% = 8-12, so should include 10, 12, 8 but not 20
        assert len(neighbors) == 3

    def test_find_neighbors_empty_results(self) -> None:
        """Test with empty results list."""
        neighbors = find_neighbors({"sma_period": 10}, [], tolerance=0.20)
        assert neighbors == []

    def test_find_neighbors_no_matching_params(
        self, sample_results: list[RobustnessResult]
    ) -> None:
        """Test with params not in results."""
        optimal_params = {"nonexistent_param": 10}
        neighbors = find_neighbors(optimal_params, sample_results, tolerance=0.20)

        # All results are neighbors since param doesn't exist
        assert len(neighbors) == len(sample_results)

    def test_find_neighbors_non_numeric_params(self) -> None:
        """Test with non-numeric parameter values."""
        results = [
            RobustnessResult(
                params={"strategy": "momentum", "sma_period": 10},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"strategy": "reversion", "sma_period": 12},
                total_return=0.10,
                sharpe=1.0,
                max_drawdown=-0.12,
                win_rate=0.50,
                trade_count=45,
            ),
        ]
        optimal_params = {"strategy": "momentum", "sma_period": 10}
        neighbors = find_neighbors(optimal_params, results, tolerance=0.20)

        # sma_period 10 ±20% = 8-12, so 12 is within range
        assert len(neighbors) == 2

    def test_find_neighbors_zero_optimal_value(self) -> None:
        """Test with zero optimal value (line 49-50 branch)."""
        results = [
            RobustnessResult(
                params={"offset": 0},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"offset": 1},
                total_return=0.10,
                sharpe=1.0,
                max_drawdown=-0.12,
                win_rate=0.50,
                trade_count=45,
            ),
        ]
        optimal_params = {"offset": 0}
        neighbors = find_neighbors(optimal_params, results, tolerance=0.20)

        # Only offset=0 is a neighbor when optimal is 0
        assert len(neighbors) == 1
        assert neighbors[0].params["offset"] == 0

    def test_find_neighbors_outside_tolerance(self, sample_results: list[RobustnessResult]) -> None:
        """Test with tight tolerance that excludes neighbors."""
        optimal_params = {"sma_period": 10, "rsi_period": 14}
        neighbors = find_neighbors(optimal_params, sample_results, tolerance=0.05)

        # Only exact match (10) within 5% tolerance
        assert len(neighbors) == 1


# -------------------------------------------------------------------------
# calculate_sensitivity Tests
# -------------------------------------------------------------------------


class TestCalculateSensitivity:
    """Test calculate_sensitivity function."""

    def test_calculate_sensitivity_basic(self, sample_results: list[RobustnessResult]) -> None:
        """Test basic sensitivity calculation."""
        sensitivity = calculate_sensitivity(sample_results)

        assert "sma_period" in sensitivity
        assert "rsi_period" in sensitivity
        assert 0.0 <= sensitivity["sma_period"] <= 1.0

    def test_calculate_sensitivity_empty_results(self) -> None:
        """Test with empty results (line 77 branch)."""
        sensitivity = calculate_sensitivity([])
        assert sensitivity == {}

    def test_calculate_sensitivity_single_value(self) -> None:
        """Test when parameter has only one unique value (line 100-101 branch)."""
        results = [
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.12,
                sharpe=1.0,
                max_drawdown=-0.12,
                win_rate=0.52,
                trade_count=45,
            ),
        ]
        sensitivity = calculate_sensitivity(results)

        # Same sma_period value in all results -> sensitivity = 0.0
        assert sensitivity["sma_period"] == 0.0

    def test_calculate_sensitivity_nan_correlation(self) -> None:
        """Test when correlation returns NaN (line 108-109 branch)."""
        # Same return for all results -> NaN correlation
        results = [
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.10,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"sma_period": 20},
                total_return=0.10,
                sharpe=1.0,
                max_drawdown=-0.12,
                win_rate=0.52,
                trade_count=45,
            ),
        ]
        sensitivity = calculate_sensitivity(results)

        # Same return for different params -> NaN correlation -> 0.0
        assert sensitivity["sma_period"] == 0.0

    def test_calculate_sensitivity_non_numeric_params(self) -> None:
        """Test with non-numeric parameters (line 95-96 skip)."""
        results = [
            RobustnessResult(
                params={"strategy": "momentum", "sma_period": 10},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"strategy": "reversion", "sma_period": 20},
                total_return=0.05,
                sharpe=0.5,
                max_drawdown=-0.20,
                win_rate=0.45,
                trade_count=30,
            ),
        ]
        sensitivity = calculate_sensitivity(results)

        # strategy is non-numeric, should not be in sensitivity or have 0 values
        assert "sma_period" in sensitivity


# -------------------------------------------------------------------------
# calculate_neighbor_success_rate Tests
# -------------------------------------------------------------------------


class TestCalculateNeighborSuccessRate:
    """Test calculate_neighbor_success_rate function."""

    def test_success_rate_basic(self, sample_results: list[RobustnessResult]) -> None:
        """Test basic success rate calculation."""
        optimal_params = {"sma_period": 10, "rsi_period": 14}
        rate = calculate_neighbor_success_rate(optimal_params, sample_results, tolerance=0.20)

        # Rate should be between 0 and 1
        assert 0.0 <= rate <= 1.0

    def test_success_rate_empty_neighbors(self) -> None:
        """Test when no neighbors found (line 136 branch)."""
        results = [
            RobustnessResult(
                params={"sma_period": 100},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
        ]
        optimal_params = {"sma_period": 10}
        rate = calculate_neighbor_success_rate(optimal_params, results, tolerance=0.10)

        # No neighbors within 10% of 10 (9-11), 100 is too far
        assert rate == 0.0

    def test_success_rate_no_optimal_match(self) -> None:
        """Test when optimal params not in results (line 142 branch)."""
        results = [
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
        ]
        # Optimal params don't exactly match any result
        optimal_params = {"sma_period": 11}
        rate = calculate_neighbor_success_rate(optimal_params, results, tolerance=0.20)

        # sma_period 10 is within 20% of 11, so neighbors exist
        # But optimal_params {"sma_period": 11} != {"sma_period": 10}, so no optimal_returns
        assert rate == 0.0

    def test_success_rate_all_successful(self) -> None:
        """Test when all neighbors are successful."""
        results = [
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.15,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"sma_period": 11},
                total_return=0.14,  # > 0.15 * 0.80 = 0.12
                sharpe=1.1,
                max_drawdown=-0.11,
                win_rate=0.54,
                trade_count=48,
            ),
        ]
        optimal_params = {"sma_period": 10}
        rate = calculate_neighbor_success_rate(optimal_params, results, tolerance=0.20)

        # Both are neighbors, both achieve >= 80% of optimal
        assert rate == 1.0

    def test_success_rate_partial_success(self) -> None:
        """Test when some neighbors fail threshold."""
        results = [
            RobustnessResult(
                params={"sma_period": 10},
                total_return=0.20,
                sharpe=1.2,
                max_drawdown=-0.10,
                win_rate=0.55,
                trade_count=50,
            ),
            RobustnessResult(
                params={"sma_period": 11},
                total_return=0.18,  # > 0.20 * 0.80 = 0.16
                sharpe=1.1,
                max_drawdown=-0.11,
                win_rate=0.54,
                trade_count=48,
            ),
            RobustnessResult(
                params={"sma_period": 12},
                total_return=0.10,  # < 0.20 * 0.80 = 0.16, fails
                sharpe=0.8,
                max_drawdown=-0.15,
                win_rate=0.48,
                trade_count=40,
            ),
        ]
        optimal_params = {"sma_period": 10}
        rate = calculate_neighbor_success_rate(optimal_params, results, tolerance=0.20)

        # 2 out of 3 succeed (10 and 11)
        assert rate == pytest.approx(2 / 3, rel=0.01)
