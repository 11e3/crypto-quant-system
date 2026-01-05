"""
Unit tests for indicators utility module.
"""

import pandas as pd
import pytest

from src.utils.indicators import (
    add_vbo_indicators,
    atr,
    bollinger_bands,
    ema,
    macd,
    noise_ratio,
    noise_ratio_sma,
    rsi,
    sma,
    stochastic,
    target_price,
    volatility_range,
)


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i * 2 for i in range(20)],
            "high": [105.0 + i * 2 for i in range(20)],
            "low": [95.0 + i * 2 for i in range(20)],
            "close": [102.0 + i * 2 for i in range(20)],
            "volume": [1000.0 + i * 10 for i in range(20)],
        },
        index=dates,
    )


class TestSMA:
    """Test cases for SMA functions."""

    def test_sma_series(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test sma function with Series."""
        period = 5
        result = sma(sample_ohlcv_data["close"], period=period)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        # First (period-1) values should be NaN
        assert pd.isna(result.iloc[: period - 1]).all()
        # Last value should not be NaN
        assert not pd.isna(result.iloc[-1])

    def test_sma_calculation(self) -> None:
        """Test SMA calculation correctness."""
        data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = sma(data, period=5)

        assert result.iloc[-1] == 30.0  # (10+20+30+40+50)/5 = 30

    def test_sma_period_one(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test SMA with period=1."""
        result = sma(sample_ohlcv_data["close"], period=1)

        assert isinstance(result, pd.Series)
        assert result.iloc[-1] == sample_ohlcv_data["close"].iloc[-1]

    def test_sma_exclude_current(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test SMA with exclude_current=True."""
        period = 5
        result = sma(sample_ohlcv_data["close"], period=period, exclude_current=True)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        # First period values should be NaN due to shift
        assert pd.isna(result.iloc[:period]).all()


class TestEMA:
    """Test cases for EMA function."""

    def test_ema_series(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test EMA function with Series."""
        period = 5
        result = ema(sample_ohlcv_data["close"], period=period)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert not pd.isna(result.iloc[-1])


class TestATR:
    """Test cases for ATR function."""

    def test_atr(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test ATR function."""
        period = 5
        result = atr(
            sample_ohlcv_data["high"],
            sample_ohlcv_data["low"],
            sample_ohlcv_data["close"],
            period=period,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)


class TestVolatilityRange:
    """Test cases for volatility_range function."""

    def test_volatility_range(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test volatility_range function."""
        result = volatility_range(sample_ohlcv_data["high"], sample_ohlcv_data["low"])

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)
        assert (result == sample_ohlcv_data["high"] - sample_ohlcv_data["low"]).all()


class TestNoiseRatio:
    """Test cases for noise ratio functions."""

    def test_noise_ratio(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test noise_ratio function."""
        result = noise_ratio(
            sample_ohlcv_data["open"],
            sample_ohlcv_data["high"],
            sample_ohlcv_data["low"],
            sample_ohlcv_data["close"],
        )

        # noise_ratio can return Series (when using pd.where) or array
        # In practice, it returns a Series when working with pandas Series inputs
        assert len(result) == len(sample_ohlcv_data)

    def test_noise_ratio_calculation(self) -> None:
        """Test noise ratio calculation."""
        open_ = pd.Series([100.0, 102.0, 98.0])
        high = pd.Series([110.0, 105.0, 115.0])
        low = pd.Series([90.0, 95.0, 85.0])
        close = pd.Series([105.0, 103.0, 110.0])

        result = noise_ratio(open_, high, low, close)

        # noise_ratio returns Series-like object
        assert len(result) == len(open_)

    def test_noise_ratio_sma(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test noise_ratio_sma function."""
        period = 5
        result = noise_ratio_sma(
            sample_ohlcv_data["open"],
            sample_ohlcv_data["high"],
            sample_ohlcv_data["low"],
            sample_ohlcv_data["close"],
            period=period,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)


class TestTargetPrice:
    """Test cases for target price function."""

    def test_target_price(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test target_price function."""
        prev_high = sample_ohlcv_data["high"].shift(1)
        prev_low = sample_ohlcv_data["low"].shift(1)
        k = pd.Series([0.5] * len(sample_ohlcv_data), index=sample_ohlcv_data.index)

        result = target_price(
            sample_ohlcv_data["open"],
            prev_high,
            prev_low,
            k,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)

    def test_target_price_calculation(self) -> None:
        """Test target price calculation."""
        open_ = pd.Series([100.0])
        prev_high = pd.Series([110.0])
        prev_low = pd.Series([90.0])
        k = pd.Series([0.5])

        result = target_price(open_, prev_high, prev_low, k)

        assert isinstance(result, pd.Series)
        assert len(result) == len(open_)
        # Target = 100 + (110-90) * 0.5 = 110
        assert result.iloc[0] == 110.0


class TestRSI:
    """Test cases for RSI function."""

    def test_rsi(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test RSI function."""
        period = 14
        result = rsi(sample_ohlcv_data["close"], period=period)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)


class TestBollingerBands:
    """Test cases for Bollinger Bands function."""

    def test_bollinger_bands(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test Bollinger Bands function."""
        period = 20
        std_dev = 2.0
        upper, middle, lower = bollinger_bands(
            sample_ohlcv_data["close"], period=period, std_dev=std_dev
        )

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_ohlcv_data)
        # Compare non-NaN values only
        valid_mask = ~(pd.isna(upper) | pd.isna(middle) | pd.isna(lower))
        if valid_mask.any():
            assert (upper[valid_mask] >= middle[valid_mask]).all()
            assert (lower[valid_mask] <= middle[valid_mask]).all()


class TestMACD:
    """Test cases for MACD function."""

    def test_macd(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test MACD function."""
        macd_line, signal_line, histogram = macd(sample_ohlcv_data["close"])

        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)
        assert len(macd_line) == len(sample_ohlcv_data)


class TestStochastic:
    """Test cases for Stochastic function."""

    def test_stochastic(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test Stochastic function."""
        k, d = stochastic(
            sample_ohlcv_data["high"],
            sample_ohlcv_data["low"],
            sample_ohlcv_data["close"],
        )

        assert isinstance(k, pd.Series)
        assert isinstance(d, pd.Series)
        assert len(k) == len(sample_ohlcv_data)


class TestAddVBOIndicators:
    """Test cases for add_vbo_indicators function."""

    def test_add_vbo_indicators(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test add_vbo_indicators function."""
        result = add_vbo_indicators(sample_ohlcv_data.copy())

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv_data)
        assert "noise" in result.columns
        assert "short_noise" in result.columns
        assert "long_noise" in result.columns
        assert "sma" in result.columns
        assert "sma_trend" in result.columns
        assert "target" in result.columns

    def test_add_vbo_indicators_exclude_current(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test add_vbo_indicators with exclude_current=True."""
        result = add_vbo_indicators(sample_ohlcv_data.copy(), exclude_current=True)

        assert isinstance(result, pd.DataFrame)
        assert "target" in result.columns
