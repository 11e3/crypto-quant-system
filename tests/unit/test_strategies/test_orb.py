"""
Tests for Opening Range Breakout Strategy.
"""

import numpy as np
import pandas as pd
import pytest

from src.strategies.opening_range_breakout.conditions import (
    ATRORBCondition,
    NoiseFilterCondition,
    STDORBCondition,
    TrendFilterCondition,
)
from src.strategies.opening_range_breakout.orb import ORBStrategy


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    close = 100 + np.cumsum(np.random.randn(100))
    high = close + np.abs(np.random.randn(100))
    low = close - np.abs(np.random.randn(100))
    open_price = close + np.random.randn(100) * 0.5

    return pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )


class TestATRORBCondition:
    """Tests for ATRORBCondition."""

    def test_initialization(self) -> None:
        """Test ATRORBCondition initialization."""
        condition = ATRORBCondition(k_multiplier=0.5, atr_window=14)
        assert condition.k_multiplier == 0.5
        assert condition.atr_window == 14
        assert condition.name == "atr_orb"

    def test_initialization_custom_name(self) -> None:
        """Test ATRORBCondition with custom name."""
        condition = ATRORBCondition(name="custom_atr_orb")
        assert condition.name == "custom_atr_orb"

    def test_evaluate(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test ATRORBCondition evaluation."""
        condition = ATRORBCondition(k_multiplier=0.3, atr_window=5)
        result = condition.evaluate(sample_ohlcv_data)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert result.dtype == bool

    def test_evaluate_breakout_detection(self) -> None:
        """Test that breakout is correctly detected."""
        # Create data where breakout definitely occurs
        data = pd.DataFrame(
            {
                "open": [100.0] * 20,
                "high": [105.0] * 20,  # High above open + small ATR
                "low": [95.0] * 20,
                "close": [102.0] * 20,
            }
        )

        condition = ATRORBCondition(k_multiplier=0.1, atr_window=5)
        result = condition.evaluate(data)

        # Should have some True values where high >= open + k * ATR
        assert result.sum() > 0


class TestSTDORBCondition:
    """Tests for STDORBCondition."""

    def test_initialization(self) -> None:
        """Test STDORBCondition initialization."""
        condition = STDORBCondition()
        assert condition.name == "std_orb"

    def test_initialization_custom_name(self) -> None:
        """Test STDORBCondition with custom name."""
        condition = STDORBCondition(name="custom_std_orb")
        assert condition.name == "custom_std_orb"

    def test_evaluate(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test STDORBCondition evaluation."""
        condition = STDORBCondition()
        result = condition.evaluate(sample_ohlcv_data)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert result.dtype == bool

    def test_evaluate_breakout_detection(self) -> None:
        """Test that breakout is detected when close equals high."""
        data = pd.DataFrame(
            {
                "open": [100.0, 100.0, 100.0],
                "high": [105.0, 102.0, 108.0],
                "low": [95.0, 98.0, 99.0],
                "close": [105.0, 100.0, 108.0],  # Close equals high for index 0 and 2
            }
        )

        condition = STDORBCondition()
        result = condition.evaluate(data)

        assert result.iloc[0] is True or result.iloc[0] == True  # noqa: E712
        assert result.iloc[2] is True or result.iloc[2] == True  # noqa: E712


class TestNoiseFilterCondition:
    """Tests for NoiseFilterCondition."""

    def test_initialization(self) -> None:
        """Test NoiseFilterCondition initialization."""
        condition = NoiseFilterCondition(noise_window=5, noise_threshold=0.5)
        assert condition.noise_window == 5
        assert condition.noise_threshold == 0.5
        assert condition.name == "noise_filter"

    def test_initialization_custom_name(self) -> None:
        """Test NoiseFilterCondition with custom name."""
        condition = NoiseFilterCondition(name="custom_noise")
        assert condition.name == "custom_noise"

    def test_evaluate(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test NoiseFilterCondition evaluation."""
        condition = NoiseFilterCondition(noise_window=5, noise_threshold=0.8)
        result = condition.evaluate(sample_ohlcv_data)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert result.dtype == bool


class TestTrendFilterCondition:
    """Tests for TrendFilterCondition."""

    def test_initialization(self) -> None:
        """Test TrendFilterCondition initialization."""
        condition = TrendFilterCondition(sma_window=20, price_column="open")
        assert condition.sma_window == 20
        assert condition.price_column == "open"
        assert condition.name == "trend_filter"

    def test_initialization_close_price(self) -> None:
        """Test TrendFilterCondition with close price."""
        condition = TrendFilterCondition(price_column="close")
        assert condition.price_column == "close"

    def test_evaluate(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test TrendFilterCondition evaluation."""
        condition = TrendFilterCondition(sma_window=10)
        result = condition.evaluate(sample_ohlcv_data)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert result.dtype == bool


class TestORBStrategy:
    """Tests for ORBStrategy."""

    def test_initialization_atr_mode(self) -> None:
        """Test ORBStrategy initialization with ATR mode."""
        strategy = ORBStrategy(breakout_mode="atr")
        assert strategy.breakout_mode == "atr"
        assert strategy.name == "orb"
        assert isinstance(strategy.breakout_condition, ATRORBCondition)

    def test_initialization_std_mode(self) -> None:
        """Test ORBStrategy initialization with STD mode."""
        strategy = ORBStrategy(breakout_mode="std")
        assert strategy.breakout_mode == "std"
        assert isinstance(strategy.breakout_condition, STDORBCondition)

    def test_initialization_custom_params(self) -> None:
        """Test ORBStrategy with custom parameters."""
        strategy = ORBStrategy(
            breakout_mode="atr",
            k_multiplier=0.7,
            atr_window=20,
            atr_multiplier=3.0,
            vol_target=0.03,
            noise_window=10,
            noise_threshold=0.4,
            sma_window=30,
            trend_price="close",
            atr_slippage=0.2,
            name="custom_orb",
        )

        assert strategy.k_multiplier == 0.7
        assert strategy.atr_window == 20
        assert strategy.atr_multiplier == 3.0
        assert strategy.vol_target == 0.03
        assert strategy.noise_window == 10
        assert strategy.noise_threshold == 0.4
        assert strategy.sma_window == 30
        assert strategy.trend_price == "close"
        assert strategy.atr_slippage == 0.2
        assert strategy.name == "custom_orb"

    def test_required_indicators(self) -> None:
        """Test required_indicators returns expected list."""
        strategy = ORBStrategy()
        indicators = strategy.required_indicators()

        assert "atr" in indicators
        assert "noise" in indicators
        assert "sma" in indicators

    def test_calculate_indicators(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test calculate_indicators adds required columns."""
        strategy = ORBStrategy(atr_window=5, sma_window=10)
        result = strategy.calculate_indicators(sample_ohlcv_data)

        assert "atr" in result.columns
        assert "noise" in result.columns
        assert "sma" in result.columns

    def test_generate_signals_atr_mode(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test generate_signals in ATR mode."""
        strategy = ORBStrategy(breakout_mode="atr", atr_window=5, sma_window=10)
        result = strategy.generate_signals(sample_ohlcv_data)

        assert "entry_signal" in result.columns
        assert "exit_signal" in result.columns
        assert "target" in result.columns
        assert "trailing_stop_distance" in result.columns
        assert "position_size_multiplier" in result.columns
        assert "slippage_amount" in result.columns

    def test_generate_signals_std_mode(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test generate_signals in STD mode."""
        strategy = ORBStrategy(breakout_mode="std", atr_window=5, sma_window=10)
        result = strategy.generate_signals(sample_ohlcv_data)

        assert "entry_signal" in result.columns
        # In std mode, target should equal high
        # Skip first few rows due to NaN
        valid_rows = ~result["target"].isna()
        if valid_rows.sum() > 0:
            assert (result.loc[valid_rows, "target"] == result.loc[valid_rows, "high"]).all()

    def test_get_parameters(self) -> None:
        """Test get_parameters returns all parameters."""
        strategy = ORBStrategy(
            breakout_mode="atr",
            k_multiplier=0.6,
            atr_window=15,
        )
        params = strategy.get_parameters()

        assert params["breakout_mode"] == "atr"
        assert params["k_multiplier"] == 0.6
        assert params["atr_window"] == 15
        assert "atr_multiplier" in params
        assert "vol_target" in params

    def test_repr(self) -> None:
        """Test string representation."""
        strategy = ORBStrategy(name="test_orb")
        repr_str = repr(strategy)

        assert "ORBStrategy" in repr_str
        assert "breakout_mode" in repr_str
