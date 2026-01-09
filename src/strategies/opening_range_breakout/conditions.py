"""
ORB Strategy Entry/Exit Conditions.

Implements ATR-based and standard breakout conditions with filters.
"""

from typing import Literal

import pandas as pd

from src.strategies.base import OHLCV, Condition
from src.utils.indicators import calculate_atr, calculate_noise, calculate_sma


class ATRORBCondition(Condition):
    """
    ATR-based Opening Range Breakout condition.

    Entry signal when price breaks opening price + k * ATR within the period.

    Args:
        k_multiplier: ATR multiplier for breakout threshold
        atr_window: ATR calculation window
        name: Condition name
    """

    def __init__(
        self,
        k_multiplier: float = 0.5,
        atr_window: int = 14,
        name: str = "atr_orb",
    ) -> None:
        super().__init__(name=name)
        self.k_multiplier = k_multiplier
        self.atr_window = atr_window

    def evaluate(
        self,
        current: pd.DataFrame | OHLCV,
        history: pd.DataFrame | None = None,
        indicators: dict[str, float] | None = None,
    ) -> pd.Series:
        """
        Evaluate ATR-based breakout condition.

        Args:
            data: OHLCV DataFrame with 'open', 'high', 'low', 'close'

        Returns:
            Boolean Series indicating breakout signals
        """
        # Calculate ATR
        data = current if isinstance(current, pd.DataFrame) else pd.DataFrame()

        atr = calculate_atr(data, window=self.atr_window)

        # Breakout threshold: open + k * ATR
        breakout_threshold = data["open"] + self.k_multiplier * atr

        # Signal: high >= threshold (breakout occurred in the period)
        signal = data["high"] >= breakout_threshold

        return signal


class STDORBCondition(Condition):
    """
    Standard Opening Range Breakout condition.

    Entry signal when price breaks the period's high.
    Typically used with 30-minute candles for opening range.

    Args:
        name: Condition name
    """

    def __init__(self, name: str = "std_orb") -> None:
        super().__init__(name=name)

    def evaluate(
        self,
        current: pd.DataFrame | OHLCV,
        history: pd.DataFrame | None = None,
        indicators: dict[str, float] | None = None,
    ) -> pd.Series:
        """
        Evaluate standard breakout condition.

        Args:
            data: OHLCV DataFrame with 'high', 'close'

        Returns:
            Boolean Series indicating breakout signals
        """
        # Signal: close >= high (breakout at period's high)
        # Note: This is simplified; in practice might use previous period's high
        data = current if isinstance(current, pd.DataFrame) else pd.DataFrame()

        signal = data["close"] >= data["high"]

        return signal


class NoiseFilterCondition(Condition):
    """
    Noise filter to avoid choppy markets.

    Entry only when recent noise is below threshold, indicating clearer trends.

    Args:
        noise_window: SMA window for noise averaging
        noise_threshold: Maximum allowed noise ratio (0-1)
        name: Condition name
    """

    def __init__(
        self,
        noise_window: int = 5,
        noise_threshold: float = 0.5,
        name: str = "noise_filter",
    ) -> None:
        super().__init__(name=name)
        self.noise_window = noise_window
        self.noise_threshold = noise_threshold

    def evaluate(
        self,
        current: pd.DataFrame | OHLCV,
        history: pd.DataFrame | None = None,
        indicators: dict[str, float] | None = None,
    ) -> pd.Series:
        """
        Evaluate noise filter condition.

        Args:
            data: OHLCV DataFrame with OHLC data

        Returns:
            Boolean Series indicating low-noise periods
        """
        # Calculate noise ratio
        data = current if isinstance(current, pd.DataFrame) else pd.DataFrame()

        noise = calculate_noise(data)

        # Calculate noise SMA
        noise_sma = calculate_sma(noise, window=self.noise_window)

        # Signal: noise below threshold
        signal = noise_sma < self.noise_threshold

        return signal


class TrendFilterCondition(Condition):
    """
    Trend filter using SMA.

    Entry only in uptrend (price above SMA).

    Args:
        sma_window: SMA window for trend determination
        price_column: Column to compare with SMA ('open' or 'close')
        name: Condition name
    """

    def __init__(
        self,
        sma_window: int = 20,
        price_column: Literal["open", "close"] = "open",
        name: str = "trend_filter",
    ) -> None:
        super().__init__(name=name)
        self.sma_window = sma_window
        self.price_column = price_column

    def evaluate(
        self,
        current: pd.DataFrame | OHLCV,
        history: pd.DataFrame | None = None,
        indicators: dict[str, float] | None = None,
    ) -> pd.Series:
        """
        Evaluate trend filter condition.

        Args:
            data: OHLCV DataFrame with price data

        Returns:
            Boolean Series indicating uptrend periods
        """
        # Calculate SMA
        data = current if isinstance(current, pd.DataFrame) else pd.DataFrame()

        sma = calculate_sma(data["close"], window=self.sma_window)

        # Signal: price above SMA (uptrend)
        signal = data[self.price_column] > sma

        return signal
