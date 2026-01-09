"""
Market filter conditions for Volatility Breakout strategy.

These conditions filter trading opportunities based on market state.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition


class TrendCondition(Condition):
    """
    Trend condition using moving average.

    Only allows trading when target price is above the trend SMA,
    indicating an uptrend environment.
    """

    def __init__(
        self,
        sma_key: str = "sma_trend",
        name: str = "TrendCondition",
    ) -> None:
        """
        Initialize trend condition.

        Args:
            sma_key: Key for trend SMA in indicators
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
        """Check if target is above trend SMA."""
        target = indicators.get("target")
        trend_sma = indicators.get(self.sma_key)

        if target is None or trend_sma is None:
            return False

        return target > trend_sma


class NoiseCondition(Condition):
    """
    Dynamic noise condition.

    Only allows trading when short-term noise is below long-term
    baseline, indicating a relatively calm market suitable for
    breakout strategies.
    """

    def __init__(
        self,
        short_noise_key: str = "short_noise",
        long_noise_key: str = "long_noise",
        name: str = "NoiseCondition",
    ) -> None:
        """
        Initialize noise condition.

        Args:
            short_noise_key: Key for short-term noise ratio
            long_noise_key: Key for long-term noise baseline
            name: Condition name
        """
        super().__init__(name)
        self.short_noise_key = short_noise_key
        self.long_noise_key = long_noise_key

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if current noise is below baseline."""
        short_noise = indicators.get(self.short_noise_key)
        long_noise = indicators.get(self.long_noise_key)

        if short_noise is None or long_noise is None:
            return False

        # Market is "calm" when short-term noise < long-term average
        return short_noise < long_noise


class NoiseThresholdCondition(Condition):
    """
    Absolute noise threshold condition.

    Filters out periods where noise ratio exceeds a fixed threshold.
    """

    def __init__(
        self,
        noise_key: str = "short_noise",
        max_noise: float = 0.7,
        name: str = "NoiseThresholdCondition",
    ) -> None:
        """
        Initialize noise threshold condition.

        Args:
            noise_key: Key for noise ratio
            max_noise: Maximum allowed noise ratio (0-1)
            name: Condition name
        """
        super().__init__(name)
        self.noise_key = noise_key
        self.max_noise = max_noise

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if noise is below threshold."""
        noise = indicators.get(self.noise_key)

        if noise is None:
            return False

        return noise <= self.max_noise


class VolatilityRangeCondition(Condition):
    """
    Volatility range condition.

    Only allows trading when volatility is within acceptable range.
    """

    def __init__(
        self,
        min_volatility_pct: float = 0.005,
        max_volatility_pct: float = 0.15,
        name: str = "VolatilityRangeCondition",
    ) -> None:
        """
        Initialize volatility range condition.

        Args:
            min_volatility_pct: Minimum range as % of price
            max_volatility_pct: Maximum range as % of price
            name: Condition name
        """
        super().__init__(name)
        self.min_volatility_pct = min_volatility_pct
        self.max_volatility_pct = max_volatility_pct

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if volatility is within range."""
        prev_range = indicators.get("prev_range")

        if prev_range is None or current.open <= 0:
            return False

        volatility_pct = prev_range / current.open

        return self.min_volatility_pct <= volatility_pct <= self.max_volatility_pct


# Re-export from conditions_market for backward compatibility
from src.strategies.volatility_breakout.conditions_market import (  # noqa: E402
    DayOfWeekCondition,
    MarketRegimeCondition,
    VolumeCondition,
)

__all__ = [
    # New Condition classes
    "TrendCondition",
    "NoiseCondition",
    "NoiseThresholdCondition",
    "VolatilityRangeCondition",
    "VolumeCondition",
    "DayOfWeekCondition",
    "MarketRegimeCondition",
]
