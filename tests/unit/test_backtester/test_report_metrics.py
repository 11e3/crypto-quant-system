"""Tests for report_metrics module."""

import pytest

from src.backtester.report_pkg.report_metrics import _calculate_cagr


class TestReportMetrics:
    """Test cases for report_metrics functions."""

    def test_calculate_cagr_negative_final(self) -> None:
        """Test _calculate_cagr with negative final value (covers line 129)."""
        result = _calculate_cagr(total_days=365, initial=1000.0, final=-100.0)
        assert result == -100.0

    def test_calculate_cagr_zero_ratio(self) -> None:
        """Test _calculate_cagr edge case (covers line 132)."""
        # This shouldn't normally happen, but test the guard
        result = _calculate_cagr(total_days=365, initial=1000.0, final=0.0)
        # final=0 should also trigger the check
        assert result == -100.0

    def test_calculate_cagr_normal(self) -> None:
        """Test _calculate_cagr with normal values."""
        result = _calculate_cagr(total_days=365, initial=1000.0, final=1100.0)
        # 10% return over 1 year = ~10% CAGR
        assert result == pytest.approx(10.0, abs=0.5)

    def test_calculate_cagr_zero_days(self) -> None:
        """Test _calculate_cagr with zero days."""
        result = _calculate_cagr(total_days=0, initial=1000.0, final=1100.0)
        assert result == 0.0
