"""
Tests for VBO indicators functionality.
"""

import pandas as pd
import pytest

from src.strategies.volatility_breakout.vbo_indicators import calculate_vbo_indicators


class TestCalculateVboIndicators:
    """Tests for calculate_vbo_indicators function."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create sample OHLC data."""
        return pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [102.0, 103.0, 104.0, 105.0, 106.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [101.0, 102.0, 103.0, 104.0, 105.0],
            }
        )

    def test_calculate_vbo_indicators_default(self, sample_df: pd.DataFrame) -> None:
        """Test calculate_vbo_indicators with default parameters."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
        )

        # Check that output is DataFrame
        assert isinstance(result, pd.DataFrame)

        # Check that original columns are preserved
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns

    def test_calculate_vbo_indicators_includes_noise(self, sample_df: pd.DataFrame) -> None:
        """Test that noise indicators are added."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
        )

        # Check for noise columns
        assert "short_noise" in result.columns
        assert "long_noise" in result.columns

    def test_calculate_vbo_indicators_with_custom_periods(self, sample_df: pd.DataFrame) -> None:
        """Test with custom period parameters."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=3,
            trend_sma_period=10,
            short_noise_period=3,
            long_noise_period=6,
            exclude_current=True,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_df)

    def test_calculate_vbo_indicators_atr_period(self, sample_df: pd.DataFrame) -> None:
        """Test with custom ATR period."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            atr_period=10,
        )

        assert isinstance(result, pd.DataFrame)
        assert "short_noise" in result.columns

    def test_calculate_vbo_indicators_base_k(self, sample_df: pd.DataFrame) -> None:
        """Test with custom base K parameter."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            base_k=0.5,
        )

        assert isinstance(result, pd.DataFrame)
        assert "short_noise" in result.columns

    def test_calculate_vbo_indicators_improved_and_adaptive(self, sample_df: pd.DataFrame) -> None:
        """Test with both improved and adaptive indicators."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            use_improved_noise=True,
            use_adaptive_k=True,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_df)

    def test_calculate_vbo_indicators_improved_only(self, sample_df: pd.DataFrame) -> None:
        """Test with only improved noise indicators."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            use_improved_noise=True,
        )

        assert isinstance(result, pd.DataFrame)
        # Improved noise replaces short_noise and long_noise
        assert "short_noise" in result.columns
        assert "long_noise" in result.columns

    def test_calculate_vbo_indicators_adaptive_k_only(self, sample_df: pd.DataFrame) -> None:
        """Test with only adaptive K values."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            use_adaptive_k=True,
        )

        assert isinstance(result, pd.DataFrame)
        assert "target" in result.columns

    def test_calculate_vbo_indicators_dataframe_length(self, sample_df: pd.DataFrame) -> None:
        """Test that output has same length as input."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
        )
        assert len(result) == len(sample_df)

    def test_calculate_vbo_indicators_with_exclude_current(self, sample_df: pd.DataFrame) -> None:
        """Test with exclude_current parameter."""
        result = calculate_vbo_indicators(
            sample_df,
            sma_period=5,
            trend_sma_period=20,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=True,
        )
        assert len(result) == len(sample_df)
