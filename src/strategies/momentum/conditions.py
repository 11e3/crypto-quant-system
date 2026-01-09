"""
Entry and exit conditions for Momentum strategy.

These conditions use momentum indicators like RSI, MACD, and moving averages
to identify trend-following opportunities.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition

# Re-export RSI and MACD conditions for backward compatibility
from src.strategies.momentum.conditions_macd import (  # noqa: E402
    MACDBearishCondition,
    MACDBullishCondition,
)
from src.strategies.momentum.conditions_rsi import (  # noqa: E402
    RSIOverboughtCondition,
    RSIOversoldCondition,
)


class PriceAboveSMACondition(Condition):
    """
    Condition: Current price must be above SMA.

    Used to confirm uptrend before entry.
    """

    def __init__(self, sma_key: str = "sma", name: str = "PriceAboveSMA") -> None:
        """
        Initialize price above SMA condition.

        Args:
            sma_key: Key for SMA value in indicators dict
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
        """Check if close is above SMA."""
        sma = indicators.get(self.sma_key)

        if sma is None:
            return False

        return current.close > sma


class PriceBelowSMACondition(Condition):
    """
    Exit condition: Close price falls below SMA.

    Standard exit signal for momentum strategy.
    """

    def __init__(self, sma_key: str = "sma", name: str = "PriceBelowSMA") -> None:
        """
        Initialize price below SMA condition.

        Args:
            sma_key: Key for SMA value in indicators dict
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
        """Check if close is below SMA."""
        sma = indicators.get(self.sma_key)

        if sma is None:
            return False

        return current.close < sma


class MomentumStrengthCondition(Condition):
    """
    Condition: Momentum strength based on price change over period.

    Filters for strong momentum moves.
    """

    def __init__(
        self,
        lookback: int = 10,
        min_change_pct: float = 0.02,
        name: str = "MomentumStrength",
    ) -> None:
        """
        Initialize momentum strength condition.

        Args:
            lookback: Lookback period for momentum calculation
            min_change_pct: Minimum price change percentage (default 2%)
            name: Condition name
        """
        super().__init__(name)
        self.lookback = lookback
        self.min_change_pct = min_change_pct

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if momentum is strong enough."""
        if len(history) < self.lookback:
            return False

        # Calculate price change over lookback period
        past_close: float = float(history.iloc[-self.lookback]["close"])
        if past_close <= 0:
            return False

        change_pct: float = float((current.close - past_close) / past_close)
        return change_pct >= self.min_change_pct


__all__ = [
    "PriceAboveSMACondition",
    "PriceBelowSMACondition",
    "MomentumStrengthCondition",
    # Re-exported from conditions_rsi
    "RSIOversoldCondition",
    "RSIOverboughtCondition",
    # Re-exported from conditions_macd
    "MACDBullishCondition",
    "MACDBearishCondition",
]
