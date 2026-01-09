"""
Volume and time-based conditions for Volatility Breakout strategy.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition


class VolumeCondition(Condition):
    """
    Volume condition.

    Only allows trading when volume is above minimum threshold
    relative to recent average.
    """

    def __init__(
        self,
        min_volume_ratio: float = 0.5,
        lookback: int = 20,
        name: str = "VolumeCondition",
    ) -> None:
        """
        Initialize volume condition.

        Args:
            min_volume_ratio: Minimum volume as ratio of average
            lookback: Lookback period for average calculation
            name: Condition name
        """
        super().__init__(name)
        self.min_volume_ratio = min_volume_ratio
        self.lookback = lookback

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if volume is above threshold."""
        if len(history) < self.lookback:
            return True  # Not enough data, allow trading

        if "volume" not in history.columns:
            return True  # No volume data available

        avg_volume = history["volume"].tail(self.lookback).mean()

        if avg_volume <= 0:
            return True

        result: bool = bool(current.volume >= avg_volume * self.min_volume_ratio)
        return result


class DayOfWeekCondition(Condition):
    """
    Day of week condition.

    Allows trading only on specified days of the week.
    """

    def __init__(
        self,
        allowed_days: list[int] | None = None,
        name: str = "DayOfWeekCondition",
    ) -> None:
        """
        Initialize day of week condition.

        Args:
            allowed_days: List of allowed weekdays (0=Monday, 6=Sunday)
                         Default is Monday-Friday (0-4)
            name: Condition name
        """
        super().__init__(name)
        self.allowed_days = allowed_days or [0, 1, 2, 3, 4]

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if current day is allowed."""
        return current.date.weekday() in self.allowed_days


class MarketRegimeCondition(Condition):
    """
    Market regime condition based on price position relative to long-term MA.

    Only trades in bullish regimes (price above long-term MA).
    """

    def __init__(
        self,
        sma_key: str = "sma_trend",
        name: str = "MarketRegimeCondition",
    ) -> None:
        """
        Initialize market regime condition.

        Args:
            sma_key: Key for long-term SMA
            name: Condition name
        """
        super().__init__(name)
        self.sma_key = sma_key

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if price is above long-term SMA."""
        sma = indicators.get(self.sma_key)

        if sma is None:
            return False

        return current.close > sma


__all__ = [
    "VolumeCondition",
    "DayOfWeekCondition",
    "MarketRegimeCondition",
]
