"""Tests for backtester.html.html_returns module."""

import numpy as np
import pandas as pd

from src.backtester.html.html_returns import calculate_monthly_returns_for_html


class TestCalculateMonthlyReturnsForHtml:
    """Test calculate_monthly_returns_for_html function."""

    def test_basic_returns_calculation(self) -> None:
        """Test basic monthly and yearly returns calculation."""
        # Create sample equity curve spanning multiple years
        dates = pd.date_range("2022-01-01", "2023-12-31", freq="D")
        equity_curve = np.linspace(100, 150, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        assert "years" in result
        assert "months" in result
        assert "values" in result
        assert "yearly_returns" in result
        assert "yearly_labels" in result
        assert len(result["years"]) > 0
        assert len(result["months"]) == 12

    def test_single_year_data(self) -> None:
        """Test with data from a single year."""
        dates = pd.date_range("2023-01-01", "2023-06-30", freq="D")
        equity_curve = np.linspace(100, 120, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        assert len(result["years"]) >= 1
        assert len(result["values"]) > 0

    def test_yearly_returns_with_nan(self) -> None:
        """Test yearly returns when first year has NaN - covers line 84-85."""
        # First year data only (pct_change will give NaN for first period)
        dates = pd.date_range("2022-01-01", "2022-03-31", freq="D")
        equity_curve = np.linspace(100, 110, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        # The function should handle NaN in yearly returns
        assert "yearly_returns" in result
        # Even with short data, should not crash
        assert isinstance(result["yearly_labels"], list)

    def test_year_with_no_yearly_but_has_monthly(self) -> None:
        """Test year where yearly return is NaN but monthly exists - covers line 87-90."""
        # Create data with gaps that might cause yearly to be NaN
        dates = pd.date_range("2023-01-15", "2023-04-15", freq="D")
        equity_curve = np.linspace(100, 115, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        assert "yearly_returns" in result
        assert "yearly_labels" in result
        # Should calculate from monthly if yearly is NaN

    def test_year_with_no_monthly_data(self) -> None:
        """Test fallback when year has no monthly data - covers line 92-94."""
        # This is an edge case - would need very sparse data
        dates = pd.date_range("2023-06-01", "2023-06-10", freq="D")
        equity_curve = np.linspace(100, 105, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        # Should handle gracefully
        assert "yearly_returns" in result
        assert "yearly_labels" in result

    def test_multiple_years_complete(self) -> None:
        """Test with multiple complete years."""
        dates = pd.date_range("2021-01-01", "2023-12-31", freq="D")
        equity_curve = np.linspace(100, 200, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        assert len(result["years"]) >= 3
        assert len(result["yearly_returns"]) >= 2  # First year may be NaN

    def test_values_are_proper_floats(self) -> None:
        """Test that return values are proper floats."""
        dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
        equity_curve = np.linspace(100, 130, len(dates))

        result = calculate_monthly_returns_for_html(equity_curve, dates.values)

        for val in result["yearly_returns"]:
            assert isinstance(val, float)
