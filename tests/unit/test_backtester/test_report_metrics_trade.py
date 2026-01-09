"""Tests for report_metrics_trade module."""

from __future__ import annotations

import pandas as pd

from src.backtester.report_pkg.report_metrics_trade import (
    _empty_trade_stats,
    calculate_trade_statistics,
)


class TestCalculateTradeStatistics:
    """Tests for calculate_trade_statistics function."""

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame returns empty stats."""
        df = pd.DataFrame()
        result = calculate_trade_statistics(df)
        assert result == _empty_trade_stats()

    def test_no_exit_date_column(self) -> None:
        """DataFrame without exit_date column returns empty stats (line 25)."""
        # DataFrame with trades but no exit_date column
        df = pd.DataFrame(
            {
                "entry_date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "pnl": [100.0, -50.0],
                "pnl_pct": [0.05, -0.025],
            }
        )
        result = calculate_trade_statistics(df)
        # Without exit_date column, closed_trades = pd.DataFrame() -> total_trades = 0
        assert result == _empty_trade_stats()

    def test_all_trades_not_closed(self) -> None:
        """All trades with NaT exit_date returns empty stats."""
        df = pd.DataFrame(
            {
                "exit_date": [pd.NaT, pd.NaT],
                "pnl": [100.0, -50.0],
                "pnl_pct": [0.05, -0.025],
            }
        )
        result = calculate_trade_statistics(df)
        assert result == _empty_trade_stats()

    def test_normal_trades(self) -> None:
        """Normal trades with closed positions."""
        df = pd.DataFrame(
            {
                "exit_date": pd.to_datetime(["2024-01-05", "2024-01-10"]),
                "pnl": [100.0, -50.0],
                "pnl_pct": [0.10, -0.05],
            }
        )
        result = calculate_trade_statistics(df)
        assert result["total_trades"] == 2
        assert result["winning_trades"] == 1
        assert result["losing_trades"] == 1
        assert result["win_rate_pct"] == 50.0
        assert result["profit_factor"] == 2.0  # 100 / 50

    def test_all_winning_trades(self) -> None:
        """All winning trades have infinite profit factor."""
        df = pd.DataFrame(
            {
                "exit_date": pd.to_datetime(["2024-01-05", "2024-01-10"]),
                "pnl": [100.0, 50.0],
                "pnl_pct": [0.10, 0.05],
            }
        )
        result = calculate_trade_statistics(df)
        assert result["profit_factor"] == float("inf")
        assert result["win_rate_pct"] == 100.0
        assert result["losing_trades"] == 0

    def test_all_losing_trades(self) -> None:
        """All losing trades."""
        df = pd.DataFrame(
            {
                "exit_date": pd.to_datetime(["2024-01-05", "2024-01-10"]),
                "pnl": [-100.0, -50.0],
                "pnl_pct": [-0.10, -0.05],
            }
        )
        result = calculate_trade_statistics(df)
        assert result["profit_factor"] == 0.0  # 0 / 150
        assert result["win_rate_pct"] == 0.0
        assert result["winning_trades"] == 0


class TestEmptyTradeStats:
    """Tests for _empty_trade_stats helper."""

    def test_returns_correct_structure(self) -> None:
        """Empty stats have correct keys and values."""
        result = _empty_trade_stats()
        assert result["total_trades"] == 0
        assert result["winning_trades"] == 0
        assert result["losing_trades"] == 0
        assert result["win_rate_pct"] == 0.0
        assert result["profit_factor"] == 0.0
