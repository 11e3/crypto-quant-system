"""Tests for src/backtester/wfa/wfa_models.py - WFA data models."""

from datetime import datetime

import pandas as pd
import pytest

from src.backtester.models import BacktestResult
from src.backtester.wfa.wfa_models import (
    WFAReport,
    WFASegment,
    generate_wfa_html,
)


@pytest.fixture
def sample_backtest_result() -> BacktestResult:
    """Create a sample backtest result."""
    return BacktestResult(
        total_return=0.25,
        sharpe_ratio=1.5,
        mdd=-0.10,
        total_trades=50,
        winning_trades=30,
        win_rate=0.6,
    )


class TestWFASegment:
    """Tests for WFASegment class."""

    def test_oos_is_ratio_no_results(self) -> None:
        """Test OOS/IS ratio when results are missing."""
        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
        )

        assert segment.oos_is_ratio == 0.0

    def test_oos_is_ratio_zero_is_return(self) -> None:
        """Test OOS/IS ratio when IS return is zero or negative."""
        is_result = BacktestResult(
            total_return=0.0,
            sharpe_ratio=0.0,
            mdd=0.0,
            total_trades=0,
            winning_trades=0,
            win_rate=0.0,
        )
        oos_result = BacktestResult(
            total_return=0.10,
            sharpe_ratio=1.0,
            mdd=-0.05,
            total_trades=10,
            winning_trades=6,
            win_rate=0.6,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        assert segment.oos_is_ratio == 0.0

    def test_oos_is_ratio_positive(self) -> None:
        """Test OOS/IS ratio with valid results."""
        is_result = BacktestResult(
            total_return=0.20,
            sharpe_ratio=1.5,
            mdd=-0.10,
            total_trades=50,
            winning_trades=30,
            win_rate=0.6,
        )
        oos_result = BacktestResult(
            total_return=0.10,
            sharpe_ratio=1.0,
            mdd=-0.05,
            total_trades=25,
            winning_trades=15,
            win_rate=0.6,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        assert segment.oos_is_ratio == pytest.approx(0.5)  # 0.10 / 0.20

    def test_overfitting_severity_normal(self) -> None:
        """Test overfitting severity when ratio is high (normal)."""
        is_result = BacktestResult(
            total_return=0.10,
            sharpe_ratio=1.0,
            mdd=-0.05,
            total_trades=25,
            winning_trades=15,
            win_rate=0.6,
        )
        oos_result = BacktestResult(
            total_return=0.05,
            sharpe_ratio=0.8,
            mdd=-0.03,
            total_trades=12,
            winning_trades=7,
            win_rate=0.58,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        # 0.05 / 0.10 = 0.5 > 0.3, so "정상"
        assert segment.overfitting_severity == "정상"

    def test_overfitting_severity_warning(self) -> None:
        """Test overfitting severity when ratio is medium (warning)."""
        is_result = BacktestResult(
            total_return=0.50,
            sharpe_ratio=2.0,
            mdd=-0.10,
            total_trades=50,
            winning_trades=35,
            win_rate=0.7,
        )
        oos_result = BacktestResult(
            total_return=0.10,
            sharpe_ratio=0.5,
            mdd=-0.08,
            total_trades=20,
            winning_trades=10,
            win_rate=0.5,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        # 0.10 / 0.50 = 0.2, which is > 0.1 but <= 0.3, so "경고"
        assert segment.overfitting_severity == "경고"

    def test_overfitting_severity_danger(self) -> None:
        """Test overfitting severity when ratio is low (danger)."""
        is_result = BacktestResult(
            total_return=1.0,
            sharpe_ratio=3.0,
            mdd=-0.05,
            total_trades=100,
            winning_trades=80,
            win_rate=0.8,
        )
        oos_result = BacktestResult(
            total_return=0.05,
            sharpe_ratio=0.2,
            mdd=-0.15,
            total_trades=30,
            winning_trades=12,
            win_rate=0.4,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        # 0.05 / 1.0 = 0.05, which is <= 0.1, so "위험"
        assert segment.overfitting_severity == "위험"


class TestGenerateWFAHtml:
    """Tests for generate_wfa_html function."""

    def test_generate_empty_report(self) -> None:
        """Test generating HTML for empty report."""
        report = WFAReport()

        html = generate_wfa_html(report)

        assert "Walk-Forward Analysis Report" in html
        assert "Summary" in html
        assert "</html>" in html

    def test_generate_report_with_segments(self) -> None:
        """Test generating HTML for report with segments."""
        is_result = BacktestResult(
            total_return=0.20,
            sharpe_ratio=1.5,
            mdd=-0.10,
            total_trades=50,
            winning_trades=30,
            win_rate=0.6,
        )
        oos_result = BacktestResult(
            total_return=0.10,
            sharpe_ratio=1.0,
            mdd=-0.05,
            total_trades=25,
            winning_trades=15,
            win_rate=0.6,
        )

        segment = WFASegment(
            period_start=pd.Timestamp("2024-01-01"),
            period_end=pd.Timestamp("2024-06-30"),
            train_start=pd.Timestamp("2024-01-01"),
            train_end=pd.Timestamp("2024-03-31"),
            test_start=pd.Timestamp("2024-04-01"),
            test_end=pd.Timestamp("2024-06-30"),
            in_sample_result=is_result,
            out_of_sample_result=oos_result,
        )

        report = WFAReport(
            segments=[segment],
            in_sample_avg_return=0.20,
            out_of_sample_avg_return=0.10,
            overfitting_ratio=0.5,
            in_sample_sharpe=1.5,
            out_of_sample_sharpe=1.0,
            in_sample_mdd=-0.10,
            out_of_sample_mdd=-0.05,
        )

        html = generate_wfa_html(report)

        assert "Walk-Forward Analysis Report" in html
        assert "20.00%" in html  # in_sample_avg_return
        assert "Detailed Results by Segment" in html

    def test_generate_report_overfitting_classes(self) -> None:
        """Test overfitting CSS classes in generated HTML."""
        # High overfitting ratio (success)
        report_success = WFAReport(overfitting_ratio=0.5)
        html_success = generate_wfa_html(report_success)
        assert 'class="success"' in html_success

        # Medium overfitting ratio (warning)
        report_warning = WFAReport(overfitting_ratio=0.2)
        html_warning = generate_wfa_html(report_warning)
        assert 'class="warning"' in html_warning

        # Low overfitting ratio (danger)
        report_danger = WFAReport(overfitting_ratio=0.05)
        html_danger = generate_wfa_html(report_danger)
        assert 'class="danger"' in html_danger
