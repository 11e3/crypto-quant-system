"""Tests for src/backtester/report_pkg/report_summary.py - report summary printer."""

from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from src.backtester.report_pkg.report_metrics import PerformanceMetrics
from src.backtester.report_pkg.report_summary import (
    _format_risk_metrics,
    print_performance_summary,
)
from src.risk.metrics import PortfolioRiskMetrics


@pytest.fixture
def sample_metrics() -> PerformanceMetrics:
    """Create sample performance metrics."""
    import numpy as np

    return PerformanceMetrics(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        total_days=365,
        total_return_pct=25.0,
        cagr_pct=25.0,
        mdd_pct=-15.0,
        volatility_pct=20.0,
        sharpe_ratio=1.5,
        sortino_ratio=2.0,
        calmar_ratio=1.67,
        total_trades=50,
        winning_trades=30,
        losing_trades=20,
        win_rate_pct=60.0,
        profit_factor=1.8,
        avg_profit_pct=3.0,
        avg_loss_pct=-1.5,
        avg_trade_pct=1.2,
        equity_curve=np.array([10000.0, 11000.0, 12500.0]),
        drawdown_curve=np.array([0.0, 0.0, 0.0]),
        dates=np.array([date(2024, 1, 1), date(2024, 6, 1), date(2024, 12, 31)]),
        daily_returns=np.array([0.0, 0.1, 0.136]),
    )


@pytest.fixture
def sample_risk_metrics() -> PortfolioRiskMetrics:
    """Create sample risk metrics."""
    return PortfolioRiskMetrics(
        var_95=0.05,
        cvar_95=0.07,
        var_99=0.08,
        cvar_99=0.10,
        portfolio_volatility=0.20,
        avg_correlation=0.5,
        max_correlation=0.8,
        min_correlation=0.2,
        max_position_pct=0.25,
        position_concentration=0.15,
        portfolio_beta=1.1,
    )


class TestPrintPerformanceSummary:
    """Tests for print_performance_summary function."""

    def test_print_summary_without_risk_metrics(
        self, sample_metrics: PerformanceMetrics
    ) -> None:
        """Test printing summary without risk metrics."""
        with patch("src.backtester.report_pkg.report_summary.logger") as mock_logger:
            print_performance_summary(
                metrics=sample_metrics,
                risk_metrics=None,
                strategy_name="TestStrategy",
            )

            # Should call logger.info multiple times
            assert mock_logger.info.call_count > 0

    def test_print_summary_with_risk_metrics(
        self,
        sample_metrics: PerformanceMetrics,
        sample_risk_metrics: PortfolioRiskMetrics,
    ) -> None:
        """Test printing summary with risk metrics."""
        with patch("src.backtester.report_pkg.report_summary.logger") as mock_logger:
            print_performance_summary(
                metrics=sample_metrics,
                risk_metrics=sample_risk_metrics,
                strategy_name="TestStrategy",
            )

            # Should have more calls due to risk metrics
            assert mock_logger.info.call_count > 0


class TestFormatRiskMetrics:
    """Tests for _format_risk_metrics function."""

    def test_format_basic_risk_metrics(self) -> None:
        """Test formatting basic risk metrics."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            cvar_95=0.07,
            var_99=0.08,
            cvar_99=0.10,
            portfolio_volatility=0.20,
            avg_correlation=None,
            max_correlation=None,
            min_correlation=None,
            max_position_pct=None,
            position_concentration=None,
            portfolio_beta=None,
        )

        lines = _format_risk_metrics(risk_metrics)

        assert len(lines) >= 5
        assert any("VaR" in line for line in lines)
        assert any("CVaR" in line for line in lines)

    def test_format_with_correlation_metrics(self) -> None:
        """Test formatting with correlation metrics."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            cvar_95=0.07,
            var_99=0.08,
            cvar_99=0.10,
            portfolio_volatility=0.20,
            avg_correlation=0.5,
            max_correlation=0.8,
            min_correlation=0.2,
            max_position_pct=None,
            position_concentration=None,
            portfolio_beta=None,
        )

        lines = _format_risk_metrics(risk_metrics)

        assert any("Avg Correlation" in line for line in lines)
        assert any("Max Correlation" in line for line in lines)
        assert any("Min Correlation" in line for line in lines)

    def test_format_with_position_metrics(self) -> None:
        """Test formatting with position metrics."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            cvar_95=0.07,
            var_99=0.08,
            cvar_99=0.10,
            portfolio_volatility=0.20,
            avg_correlation=None,
            max_correlation=None,
            min_correlation=None,
            max_position_pct=0.25,
            position_concentration=0.15,
            portfolio_beta=None,
        )

        lines = _format_risk_metrics(risk_metrics)

        assert any("Max Position %" in line for line in lines)
        assert any("Position HHI" in line for line in lines)

    def test_format_with_zero_max_position_pct(self) -> None:
        """Test that zero max_position_pct is not displayed."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            cvar_95=0.07,
            var_99=0.08,
            cvar_99=0.10,
            portfolio_volatility=0.20,
            avg_correlation=None,
            max_correlation=None,
            min_correlation=None,
            max_position_pct=0.0,  # Zero should not be displayed
            position_concentration=0.15,
            portfolio_beta=None,
        )

        lines = _format_risk_metrics(risk_metrics)

        # Should NOT have position metrics when max_position_pct is 0
        assert not any("Max Position %" in line for line in lines)

    def test_format_with_portfolio_beta(self) -> None:
        """Test formatting with portfolio beta."""
        risk_metrics = PortfolioRiskMetrics(
            var_95=0.05,
            cvar_95=0.07,
            var_99=0.08,
            cvar_99=0.10,
            portfolio_volatility=0.20,
            avg_correlation=None,
            max_correlation=None,
            min_correlation=None,
            max_position_pct=None,
            position_concentration=None,
            portfolio_beta=1.1,
        )

        lines = _format_risk_metrics(risk_metrics)

        assert any("Portfolio Beta" in line for line in lines)

    def test_format_all_metrics(
        self, sample_risk_metrics: PortfolioRiskMetrics
    ) -> None:
        """Test formatting with all metrics present."""
        lines = _format_risk_metrics(sample_risk_metrics)

        # Should have all metric types
        assert any("VaR" in line for line in lines)
        assert any("Avg Correlation" in line for line in lines)
        assert any("Max Position %" in line for line in lines)
        assert any("Portfolio Beta" in line for line in lines)
