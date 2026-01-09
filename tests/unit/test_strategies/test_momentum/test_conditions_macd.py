"""
Unit tests for MACD conditions in Momentum strategy.

Tests cover all branches including edge cases for lines:
49, 57-60, 99, 102, 110-113
"""

import pandas as pd
import pytest

from src.strategies.base import OHLCV
from src.strategies.momentum.conditions_macd import (
    MACDBearishCondition,
    MACDBullishCondition,
)


@pytest.fixture
def sample_ohlcv() -> OHLCV:
    """Create a sample OHLCV datapoint."""
    return OHLCV(
        date=pd.Timestamp("2024-01-01").date(),
        open=100.0,
        high=105.0,
        low=98.0,
        close=103.0,
        volume=1000.0,
    )


@pytest.fixture
def sample_history() -> pd.DataFrame:
    """Create a sample history DataFrame with MACD indicators."""
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
            "close": [100.0, 101.0],
            "macd": [0.5, 0.8],
            "macd_signal": [0.6, 0.7],
        }
    )


class TestMACDBullishCondition:
    """Test MACDBullishCondition for all branches."""

    def test_initialization(self) -> None:
        """Test condition initialization."""
        condition = MACDBullishCondition()
        assert condition.macd_key == "macd"
        assert condition.signal_key == "macd_signal"
        assert condition.name == "MACDBullish"

    def test_custom_keys(self) -> None:
        """Test custom indicator keys."""
        condition = MACDBullishCondition(
            macd_key="my_macd", signal_key="my_signal", name="CustomMACDBullish"
        )
        assert condition.macd_key == "my_macd"
        assert condition.signal_key == "my_signal"
        assert condition.name == "CustomMACDBullish"

    def test_macd_is_none(self, sample_ohlcv: OHLCV, sample_history: pd.DataFrame) -> None:
        """Test when MACD is None (line 49)."""
        condition = MACDBullishCondition()
        indicators = {"macd_signal": 0.7}
        result = condition.evaluate(sample_ohlcv, sample_history, indicators)
        assert result is False

    def test_signal_is_none(self, sample_ohlcv: OHLCV, sample_history: pd.DataFrame) -> None:
        """Test when signal is None (line 49)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.8}
        result = condition.evaluate(sample_ohlcv, sample_history, indicators)
        assert result is False

    def test_both_none(self, sample_ohlcv: OHLCV, sample_history: pd.DataFrame) -> None:
        """Test when both MACD and signal are None (line 49)."""
        condition = MACDBullishCondition()
        indicators: dict[str, float] = {}
        result = condition.evaluate(sample_ohlcv, sample_history, indicators)
        assert result is False

    def test_history_less_than_2_above_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test with history < 2 rows and MACD > signal (line 57-60)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        empty_history = pd.DataFrame()
        result = condition.evaluate(sample_ohlcv, empty_history, indicators)
        assert result is True

    def test_history_less_than_2_below_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test with history < 2 rows and MACD < signal (line 57-60)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        empty_history = pd.DataFrame()
        result = condition.evaluate(sample_ohlcv, empty_history, indicators)
        assert result is False

    def test_prev_macd_is_none(self, sample_ohlcv: OHLCV) -> None:
        """Test when previous MACD is None (line 99)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True  # Falls back to macd > signal

    def test_prev_signal_is_none(self, sample_ohlcv: OHLCV) -> None:
        """Test when previous signal is None (line 99)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.5, 0.8],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_bullish_crossover(self, sample_ohlcv: OHLCV) -> None:
        """Test bullish crossover (prev_macd <= prev_signal, macd > signal)."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.5, 0.6],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_already_above_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test when MACD is already above signal without crossover."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.8, 0.85],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_below_signal_no_crossover(self, sample_ohlcv: OHLCV) -> None:
        """Test when MACD is below signal with no crossover."""
        condition = MACDBullishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.4, 0.5],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is False


class TestMACDBearishCondition:
    """Test MACDBearishCondition for all branches."""

    def test_initialization(self) -> None:
        """Test condition initialization."""
        condition = MACDBearishCondition()
        assert condition.macd_key == "macd"
        assert condition.signal_key == "macd_signal"
        assert condition.name == "MACDBearish"

    def test_macd_is_none(self, sample_ohlcv: OHLCV, sample_history: pd.DataFrame) -> None:
        """Test when MACD is None (line 102)."""
        condition = MACDBearishCondition()
        indicators = {"macd_signal": 0.7}
        result = condition.evaluate(sample_ohlcv, sample_history, indicators)
        assert result is False

    def test_signal_is_none(self, sample_ohlcv: OHLCV, sample_history: pd.DataFrame) -> None:
        """Test when signal is None (line 102)."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5}
        result = condition.evaluate(sample_ohlcv, sample_history, indicators)
        assert result is False

    def test_history_less_than_2_below_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test with history < 2 rows and MACD < signal (line 110-113)."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        empty_history = pd.DataFrame()
        result = condition.evaluate(sample_ohlcv, empty_history, indicators)
        assert result is True

    def test_history_less_than_2_above_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test with history < 2 rows and MACD > signal (line 110-113)."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        empty_history = pd.DataFrame()
        result = condition.evaluate(sample_ohlcv, empty_history, indicators)
        assert result is False

    def test_prev_macd_is_none(self, sample_ohlcv: OHLCV) -> None:
        """Test when previous MACD is None."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_prev_signal_is_none(self, sample_ohlcv: OHLCV) -> None:
        """Test when previous signal is None."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.8, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_bearish_crossover(self, sample_ohlcv: OHLCV) -> None:
        """Test bearish crossover (prev_macd >= prev_signal, macd < signal)."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.8, 0.75],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_already_below_signal(self, sample_ohlcv: OHLCV) -> None:
        """Test when MACD is already below signal without crossover."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.5, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.4, 0.45],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is True

    def test_above_signal_no_crossover(self, sample_ohlcv: OHLCV) -> None:
        """Test when MACD is above signal with no crossover."""
        condition = MACDBearishCondition()
        indicators = {"macd": 0.9, "macd_signal": 0.7}
        history = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2023-12-30", "2023-12-31"]),
                "close": [100.0, 101.0],
                "macd": [0.8, 0.85],
                "macd_signal": [0.6, 0.7],
            }
        )
        result = condition.evaluate(sample_ohlcv, history, indicators)
        assert result is False


__all__ = [
    "TestMACDBullishCondition",
    "TestMACDBearishCondition",
]
