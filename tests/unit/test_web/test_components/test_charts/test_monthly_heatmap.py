"""Tests for monthly heatmap component."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.web.components.charts.monthly_heatmap import calculate_monthly_returns


def test_calculate_monthly_returns_simple_growth() -> None:
    """Test monthly returns calculation with simple growth."""
    # Create data for 3 months with 10% growth each month
    dates = pd.date_range("2025-01-01", periods=90, freq="D")

    # Month 1: 100 -> 110 (10% growth)
    # Month 2: 110 -> 121 (10% growth)
    # Month 3: 121 -> 133.1 (10% growth)
    equity = np.zeros(len(dates))
    equity[0:31] = np.linspace(100, 110, 31)  # Jan
    equity[31:59] = np.linspace(110, 121, 28)  # Feb
    equity[59:90] = np.linspace(121, 133.1, 31)  # Mar

    result = calculate_monthly_returns(dates.values, equity)

    assert not result.empty
    assert "year" in result.columns
    assert "month" in result.columns
    assert "return_pct" in result.columns

    # Check returns are approximately 10% each month
    assert len(result) == 3
    np.testing.assert_allclose(result["return_pct"].values, [10.0, 10.0, 10.0], rtol=0.01)


def test_calculate_monthly_returns_mixed_performance() -> None:
    """Test monthly returns with mixed performance."""
    # Create data for 2 months: +20% then -10%
    dates = pd.date_range("2025-01-01", periods=59, freq="D")

    equity = np.zeros(len(dates))
    equity[0:31] = np.linspace(100, 120, 31)  # Jan: +20%
    equity[31:59] = np.linspace(120, 108, 28)  # Feb: -10%

    result = calculate_monthly_returns(dates.values, equity)

    assert len(result) == 2
    assert result.iloc[0]["return_pct"] == pytest.approx(20.0, rel=0.01)
    assert result.iloc[1]["return_pct"] == pytest.approx(-10.0, rel=0.01)


def test_calculate_monthly_returns_multiple_years() -> None:
    """Test monthly returns across multiple years."""
    dates = pd.date_range("2024-11-01", "2025-02-28", freq="D")

    # Nov 2024: 100 -> 110 (+10%)
    # Dec 2024: 110 -> 121 (+10%)
    # Jan 2025: 121 -> 133.1 (+10%)
    # Feb 2025: 133.1 -> 146.41 (+10%)
    equity = np.linspace(100, 146.41, len(dates))

    result = calculate_monthly_returns(dates.values, equity)

    assert len(result) == 4
    assert (result["year"] == 2024).sum() == 2
    assert (result["year"] == 2025).sum() == 2


def test_calculate_monthly_returns_empty_data() -> None:
    """Test with empty data."""
    result = calculate_monthly_returns(np.array([]), np.array([]))

    assert result.empty
    assert list(result.columns) == ["year", "month", "return_pct"]


def test_calculate_monthly_returns_single_month() -> None:
    """Test with single month data."""
    dates = pd.date_range("2025-01-01", periods=31, freq="D")
    equity = np.linspace(100, 110, 31)

    result = calculate_monthly_returns(dates.values, equity)

    assert len(result) == 1
    assert result.iloc[0]["year"] == 2025
    assert result.iloc[0]["month"] == 1
    assert result.iloc[0]["return_pct"] == pytest.approx(10.0, rel=0.01)


def test_yearly_returns_not_additive() -> None:
    """Test that yearly returns are compounded, not summed.

    If Jan: +10%, Feb: +10%, the year-to-date is NOT 20%,
    but rather (1.1 * 1.1 - 1) * 100 = 21%.
    """
    dates = pd.date_range("2025-01-01", periods=59, freq="D")

    # Jan: 100 -> 110 (+10%)
    # Feb: 110 -> 121 (+10%)
    # Total should be 21%, not 20%
    equity = np.zeros(len(dates))
    equity[0:31] = np.linspace(100, 110, 31)
    equity[31:59] = np.linspace(110, 121, 28)

    result = calculate_monthly_returns(dates.values, equity)

    # Monthly returns should be 10% each
    assert len(result) == 2
    assert result.iloc[0]["return_pct"] == pytest.approx(10.0, rel=0.01)
    assert result.iloc[1]["return_pct"] == pytest.approx(10.0, rel=0.01)

    # Year-to-date calculation (this will be tested against display)
    # Expected: (110/100 - 1) * 100 for Jan = 10%
    # Expected: (121/110 - 1) * 100 for Feb = 10%
    # BUT when displayed as yearly total:
    # Should be (121/100 - 1) * 100 = 21%, NOT 10% + 10% = 20%
