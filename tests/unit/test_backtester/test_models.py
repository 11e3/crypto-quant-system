"""Tests for backtester.models module."""

import numpy as np

from src.backtester.models import BacktestResult
from src.risk.metrics import PortfolioRiskMetrics


class TestBacktestResult:
    """Test cases for BacktestResult."""

    def test_summary_without_risk_metrics(self) -> None:
        """Test summary without risk_metrics."""
        result = BacktestResult(
            equity_curve=np.array([1.0, 1.1, 1.15]),
            dates=np.array(["2024-01-01", "2024-01-02", "2024-01-03"]),
            trades=[],
            cagr=15.0,
            mdd=-10.0,
            sharpe_ratio=1.5,
            calmar_ratio=1.5,
            total_return=15.0,
            win_rate=55.0,
            total_trades=10,
        )

        summary_text = result.summary()

        assert "CAGR" in summary_text
        assert "MDD" in summary_text
        assert "Risk Metrics" not in summary_text

    def test_summary_with_risk_metrics(self) -> None:
        """Test summary with risk_metrics - line 173->179."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            var_99=0.08,
            cvar_95=0.08,
            cvar_99=0.12,
            portfolio_volatility=0.15,
            avg_correlation=0.3,
            max_correlation=0.8,
            min_correlation=-0.2,
            max_position_pct=0.25,
            position_concentration=0.15,
        )

        result = BacktestResult(
            equity_curve=np.array([1.0, 1.1, 1.15]),
            dates=np.array(["2024-01-01", "2024-01-02", "2024-01-03"]),
            trades=[],
            cagr=15.0,
            mdd=-10.0,
            sharpe_ratio=1.5,
            calmar_ratio=1.5,
            total_return=15.0,
            win_rate=55.0,
            total_trades=10,
            risk_metrics=risk_metrics,
        )

        summary_text = result.summary()

        assert "CAGR" in summary_text
        assert "Risk Metrics" in summary_text or "VaR" in summary_text
