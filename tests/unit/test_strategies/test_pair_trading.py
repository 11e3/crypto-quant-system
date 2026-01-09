"""
Unit tests for PairTradingStrategy.
"""

import numpy as np
import pandas as pd

from src.strategies.pair_trading import PairTradingStrategy
from src.strategies.pair_trading.conditions import (
    SpreadMeanReversionCondition,
    SpreadZScoreCondition,
)


class TestPairTradingStrategy:
    """Test cases for PairTradingStrategy."""

    def test_strategy_initialization(self) -> None:
        """Test strategy initialization."""
        strategy = PairTradingStrategy()
        assert strategy.lookback_period == 60
        assert strategy.entry_z_score == 2.0
        assert strategy.exit_z_score == 0.5
        assert strategy.spread_type == "ratio"
        assert strategy.name == "PairTradingStrategy"

    def test_strategy_initialization_custom_params(self) -> None:
        """Test strategy initialization with custom parameters."""
        strategy = PairTradingStrategy(
            name="CustomPairTrading",
            lookback_period=30,
            entry_z_score=1.5,
            exit_z_score=0.3,
            spread_type="difference",
        )
        assert strategy.lookback_period == 30
        assert strategy.entry_z_score == 1.5
        assert strategy.exit_z_score == 0.3
        assert strategy.spread_type == "difference"
        assert strategy.name == "CustomPairTrading"

    def test_strategy_initialization_without_default_conditions(self) -> None:
        """Test strategy initialization without default conditions."""
        strategy = PairTradingStrategy(use_default_conditions=False)
        assert len(strategy.entry_conditions.conditions) == 0
        assert len(strategy.exit_conditions.conditions) == 0

    def test_strategy_initialization_custom_conditions(self) -> None:
        """Test strategy initialization with custom conditions."""
        custom_entry = [SpreadZScoreCondition(entry_threshold=1.5)]
        custom_exit = [SpreadMeanReversionCondition(exit_threshold=0.3)]
        strategy = PairTradingStrategy(
            entry_conditions=custom_entry,
            exit_conditions=custom_exit,
            use_default_conditions=False,
        )
        assert len(strategy.entry_conditions.conditions) == 1
        assert len(strategy.exit_conditions.conditions) == 1
        assert strategy.entry_conditions.conditions[0].name == "SpreadZScore"
        assert strategy.exit_conditions.conditions[0].name == "SpreadMeanReversion"

    def test_strategy_default_conditions(self) -> None:
        """Test that default conditions are added."""
        strategy = PairTradingStrategy()
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        exit_names = [c.name for c in strategy.exit_conditions.conditions]

        assert "SpreadZScore" in entry_names
        assert "SpreadMeanReversion" in exit_names

    def test_required_indicators(self) -> None:
        """Test required_indicators method."""
        strategy = PairTradingStrategy()
        indicators = strategy.required_indicators()
        assert "spread" in indicators
        assert "spread_mean" in indicators
        assert "spread_std" in indicators
        assert "z_score" in indicators

    def test_calculate_spread_for_pair(self) -> None:
        """Test calculate_spread_for_pair method."""
        strategy = PairTradingStrategy(lookback_period=20, spread_type="ratio")

        # Create sample data
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 100.0 + np.arange(100) * 0.1,
                "volume": 1000.0,
            },
            index=dates,
        )
        df2 = pd.DataFrame(
            {
                "open": 50.0,
                "high": 52.0,
                "low": 48.0,
                "close": 50.0 + np.arange(100) * 0.05,
                "volume": 2000.0,
            },
            index=dates,
        )

        merged_df = strategy.calculate_spread_for_pair(df1, df2)

        # Check that indicators are added
        assert "spread" in merged_df.columns
        assert "spread_mean" in merged_df.columns
        assert "spread_std" in merged_df.columns
        assert "z_score" in merged_df.columns

        # Check spread calculation (ratio) - only check non-NaN values
        valid_spread = merged_df["spread"].dropna()
        if len(valid_spread) > 0:
            assert (valid_spread > 0).all()

        # Check that indicators are calculated (not all NaN after lookback period)
        # Note: spread_mean and z_score may be NaN if spread_std is 0 or insufficient data
        valid_data = merged_df.iloc[strategy.lookback_period :]
        # At least spread should be calculated
        assert valid_data["spread"].notna().sum() > 0

    def test_calculate_spread_difference_type(self) -> None:
        """Test spread calculation with difference type."""
        strategy = PairTradingStrategy(lookback_period=20, spread_type="difference")

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 0.1}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.05}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)

        # Spread should be difference (can be positive or negative)
        assert "spread" in merged_df.columns
        # Difference spread can be any value
        assert merged_df["spread"].notna().sum() > 0

    def test_generate_signals(self) -> None:
        """Test signal generation."""
        strategy = PairTradingStrategy(lookback_period=20, entry_z_score=1.5)

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 0.1}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.05}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)
        signals_df = strategy.generate_signals(merged_df)

        # Check that signals are added
        assert "entry_signal" in signals_df.columns
        assert "exit_signal" in signals_df.columns

        # Check signal types
        assert signals_df["entry_signal"].dtype == bool
        assert signals_df["exit_signal"].dtype == bool

    def test_generate_signals_empty_conditions(
        self,
    ) -> None:
        """Test signal generation with no conditions."""
        strategy = PairTradingStrategy(use_default_conditions=False)

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 0.1}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.05}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)
        signals_df = strategy.generate_signals(merged_df)

        # All entry signals should be True (no conditions = all pass)
        assert signals_df["entry_signal"].all()
        # All exit signals should be False (no conditions = no exit)
        assert not signals_df["exit_signal"].any()

    def test_generate_signals_z_score_threshold(self) -> None:
        """Test signal generation with Z-score threshold."""
        strategy = PairTradingStrategy(
            entry_conditions=[SpreadZScoreCondition(entry_threshold=1.5)],
            use_default_conditions=False,
        )

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        # Create data with large spread deviation
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 2.0}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.5}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)
        signals_df = strategy.generate_signals(merged_df)

        # Entry signal should be True when |z_score| >= 1.5
        entry_rows = signals_df[signals_df["entry_signal"]]
        if len(entry_rows) > 0:
            assert (entry_rows["z_score"].abs() >= 1.5).all()

    def test_z_score_calculation(self) -> None:
        """Test Z-score calculation."""
        strategy = PairTradingStrategy(lookback_period=20)

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 0.1}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.05}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)

        # Z-score should be calculated
        assert "z_score" in merged_df.columns

        # Z-score formula: (spread - mean) / std
        valid_data = merged_df.iloc[strategy.lookback_period :]
        if len(valid_data) > 0:
            calculated_z = (valid_data["spread"] - valid_data["spread_mean"]) / valid_data[
                "spread_std"
            ].replace(0, 1)
            pd.testing.assert_series_equal(
                valid_data["z_score"],
                calculated_z,
                check_names=False,
                rtol=1e-5,
            )

    def test_spread_mean_std_calculation(self) -> None:
        """Test spread mean and std calculation."""
        strategy = PairTradingStrategy(lookback_period=20)

        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df1 = pd.DataFrame({"close": 100.0 + np.arange(100) * 0.1}, index=dates)
        df2 = pd.DataFrame({"close": 50.0 + np.arange(100) * 0.05}, index=dates)

        merged_df = strategy.calculate_spread_for_pair(df1, df2)

        # Check spread mean and std
        valid_data = merged_df.iloc[strategy.lookback_period :]
        if len(valid_data) > 0:
            # Spread mean should be close to rolling mean
            expected_mean = (
                merged_df["spread"]
                .rolling(window=strategy.lookback_period, min_periods=strategy.lookback_period)
                .mean()
            )
            pd.testing.assert_series_equal(
                valid_data["spread_mean"],
                expected_mean.iloc[strategy.lookback_period :],
                check_names=False,
                rtol=1e-5,
            )

    def test_calculate_indicators_with_two_close_columns(self) -> None:
        """Test calculate_indicators with two close columns (lines 130-136)."""
        strategy = PairTradingStrategy(lookback_period=20, spread_type="ratio")
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "close_A": 100.0 + np.arange(100) * 0.1,
                "close_B": 50.0 + np.arange(100) * 0.05,
            },
            index=dates,
        )
        result = strategy.calculate_indicators(df)
        assert "spread" in result.columns
        assert "z_score" in result.columns

    def test_calculate_indicators_single_asset_fallback(self) -> None:
        """Test calculate_indicators with single asset fallback (lines 141-148)."""
        strategy = PairTradingStrategy(lookback_period=20)
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "close": 100.0 + np.arange(100) * 0.1,
                "volume": 1000.0,
            },
            index=dates,
        )
        result = strategy.calculate_indicators(df)
        assert "spread" in result.columns
        assert result["spread"].iloc[0] == 0.0
        assert result["z_score"].iloc[0] == 0.0

    def test_calculate_indicators_no_close_columns(self) -> None:
        """Test calculate_indicators with no close columns (lines 150-154)."""
        strategy = PairTradingStrategy(lookback_period=20)
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "volume": 1000.0,
            },
            index=dates,
        )
        try:
            strategy.calculate_indicators(df)
            raise AssertionError("Expected ValueError")
        except ValueError as e:
            assert "Pair trading requires data from two assets" in str(e)

    def test_calculate_indicators_difference_spread(self) -> None:
        """Test calculate_indicators with difference spread (lines 162-164)."""
        strategy = PairTradingStrategy(lookback_period=20, spread_type="difference")
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "close_asset1": 100.0 + np.arange(100) * 0.1,
                "close_asset2": 50.0 + np.arange(100) * 0.05,
            },
            index=dates,
        )
        result = strategy.calculate_indicators(df)
        assert "spread" in result.columns
        # Difference spread: close_asset1 - close_asset2
        expected_spread = 100.0 + np.arange(100) * 0.1 - (50.0 + np.arange(100) * 0.05)
        assert result["spread"].iloc[0] == expected_spread[0]

    def test_generate_signals_with_conditions(self) -> None:
        """Test generate_signals with entry and exit conditions (lines 186-201)."""
        strategy = PairTradingStrategy(lookback_period=20, entry_z_score=1.5, exit_z_score=0.3)
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "close": 100.0,
                "z_score": [2.0, 1.0, 0.2, -2.5, 0.1] * 20,
            },
            index=dates,
        )
        result = strategy.generate_signals(df)
        assert "entry_signal" in result.columns
        assert "exit_signal" in result.columns
        # Entry signal should be True when |z_score| >= 1.5
        assert result["entry_signal"].iloc[0]  # z_score=2.0
        assert not result["entry_signal"].iloc[1]  # z_score=1.0
        # Exit signal should be True when |z_score| <= 0.3
        assert result["exit_signal"].iloc[2]  # z_score=0.2
        assert not result["exit_signal"].iloc[0]  # z_score=2.0

    def test_is_pair_trading_property(self) -> None:
        """Test is_pair_trading property."""
        strategy = PairTradingStrategy()
        assert strategy.is_pair_trading is True


__all__ = ["TestPairTradingStrategy"]
