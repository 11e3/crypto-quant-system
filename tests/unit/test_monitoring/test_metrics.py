"""Unit tests for monitoring metrics module."""

import pandas as pd
import pytest

from src.monitoring.metrics import (
    PerformanceMetrics,
    compute_performance_from_trades,
    to_dict,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics computation."""

    def test_basic_metrics_computation(self):
        """Test basic performance metrics from closed trades."""
        trades = pd.DataFrame(
            {
                "ticker": ["BTC", "BTC", "ETH"],
                "entry_date": ["2023-01-01", "2023-02-01", "2023-03-01"],
                "exit_date": ["2023-01-10", "2023-02-15", "2023-03-20"],
                "entry_price": [10000.0, 11000.0, 2000.0],
                "exit_price": [11000.0, 10500.0, 2200.0],
                "pnl_pct": [10.0, -4.5, 10.0],
                "is_whipsaw": [False, True, False],
                "commission_cost": [2.0, 1.5, 0.5],
                "slippage_cost": [2.5, 1.8, 0.6],
            }
        )

        metrics = compute_performance_from_trades(trades)

        assert metrics.n_trades == 3
        assert metrics.win_rate == pytest.approx(2 / 3, abs=0.01)
        assert metrics.whipsaw_rate == pytest.approx(1 / 3, abs=0.01)
        assert metrics.total_commission == pytest.approx(4.0, abs=0.1)
        assert metrics.total_slippage == pytest.approx(4.9, abs=0.1)
        assert metrics.avg_commission_per_trade == pytest.approx(4.0 / 3, abs=0.1)
        assert metrics.avg_slippage_per_trade == pytest.approx(4.9 / 3, abs=0.1)

    def test_no_closed_trades_raises_error(self):
        """Test that no closed trades raises ValueError."""
        trades = pd.DataFrame(
            {
                "ticker": ["BTC"],
                "entry_date": ["2023-01-01"],
                "exit_date": [None],
                "pnl_pct": [0.0],
            }
        )

        with pytest.raises(ValueError, match="No closed trades"):
            compute_performance_from_trades(trades)

    def test_missing_cost_columns_defaults_to_zero(self):
        """Test that missing commission/slippage columns default to zero."""
        trades = pd.DataFrame(
            {
                "ticker": ["BTC", "ETH"],
                "entry_date": ["2023-01-01", "2023-02-01"],
                "exit_date": ["2023-01-10", "2023-02-15"],
                "pnl_pct": [10.0, 5.0],
                "is_whipsaw": [False, False],
            }
        )

        metrics = compute_performance_from_trades(trades)

        assert metrics.total_commission == 0.0
        assert metrics.total_slippage == 0.0
        assert metrics.avg_commission_per_trade == 0.0
        assert metrics.avg_slippage_per_trade == 0.0

    def test_to_dict_conversion(self):
        """Test metrics to_dict conversion."""
        metrics = PerformanceMetrics(
            start_date=pd.Timestamp("2023-01-01"),
            end_date=pd.Timestamp("2023-12-31"),
            years=1.0,
            n_trades=100,
            win_rate=0.55,
            total_return=0.25,
            cagr=0.25,
            sharpe=1.5,
            max_drawdown=-0.15,
            whipsaw_rate=0.20,
            total_commission=50.0,
            total_slippage=60.0,
            avg_commission_per_trade=0.5,
            avg_slippage_per_trade=0.6,
        )

        result = to_dict(metrics)

        assert result["start_date"] == "2023-01-01"
        assert result["end_date"] == "2023-12-31"
        assert result["n_trades"] == 100
        assert result["win_rate"] == 0.55
        assert result["total_commission"] == 50.0
        assert result["avg_slippage_per_trade"] == 0.6
