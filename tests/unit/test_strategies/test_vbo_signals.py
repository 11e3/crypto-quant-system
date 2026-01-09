"""Tests for volatility breakout signals module."""

import pandas as pd
import pytest

from src.strategies.volatility_breakout.conditions_entry import VolatilityThresholdCondition
from src.strategies.volatility_breakout.conditions_exit import PriceBelowSMACondition
from src.strategies.volatility_breakout.vbo_signals import (
    build_entry_signal,
    build_exit_signal,
)


@pytest.fixture
def sample_vbo_data() -> pd.DataFrame:
    """Create sample VBO data with required columns."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [105.0, 106.0, 107.0, 108.0, 109.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [102.0, 103.0, 104.0, 105.0, 106.0],
            "prev_range": [5.0, 5.0, 5.0, 5.0, 5.0],
            "target": [105.0, 106.0, 107.0, 108.0, 109.0],
            "sma": [100.0, 101.0, 102.0, 103.0, 104.0],
            "sma_trend": [True, True, True, True, True],
        }
    )


class TestBuildEntrySignal:
    """Test build_entry_signal function."""

    def test_volatility_threshold_condition(self, sample_vbo_data: pd.DataFrame) -> None:
        """Test VolatilityThreshold condition - covers line 78."""
        condition = VolatilityThresholdCondition(min_range_pct=0.01)
        conditions = [condition]

        signal = build_entry_signal(sample_vbo_data, conditions)

        assert isinstance(signal, pd.Series)
        assert len(signal) == len(sample_vbo_data)

    def test_entry_signal_empty_conditions(self, sample_vbo_data: pd.DataFrame) -> None:
        """Test entry signal with empty conditions list."""
        conditions: list = []

        signal = build_entry_signal(sample_vbo_data, conditions)

        assert isinstance(signal, pd.Series)
        # Without conditions, signal should be based on basic logic (high >= target)

    def test_entry_signal_with_unknown_condition(self, sample_vbo_data: pd.DataFrame) -> None:
        """Test entry signal with unknown condition - covers line 78."""

        class UnknownEntryCondition:
            name = "UnknownEntryCondition"

        condition = UnknownEntryCondition()
        conditions = [condition]

        signal = build_entry_signal(sample_vbo_data, conditions)

        # Unknown condition should be ignored and signal should pass through
        assert isinstance(signal, pd.Series)
        assert len(signal) == len(sample_vbo_data)


class TestBuildExitSignal:
    """Test build_exit_signal function."""

    def test_price_below_sma_condition(self, sample_vbo_data: pd.DataFrame) -> None:
        """Test PriceBelowSMA exit condition."""
        condition = PriceBelowSMACondition()
        conditions = [condition]

        signal = build_exit_signal(sample_vbo_data, conditions)

        assert isinstance(signal, pd.Series)
        assert len(signal) == len(sample_vbo_data)

    def test_exit_signal_with_unknown_condition(self, sample_vbo_data: pd.DataFrame) -> None:
        """Test exit signal with unknown condition - covers line 101->100."""

        # Create a mock condition with a different name
        class UnknownCondition:
            name = "UnknownCondition"

        condition = UnknownCondition()
        conditions = [condition]

        signal = build_exit_signal(sample_vbo_data, conditions)

        # Unknown conditions should be ignored
        assert isinstance(signal, pd.Series)
        assert len(signal) == len(sample_vbo_data)
        # All False since no known condition applied
        assert not signal.any()
