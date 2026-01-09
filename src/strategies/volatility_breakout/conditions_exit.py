"""
Exit conditions for Volatility Breakout strategy.

These conditions determine when to exit a position.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition


class PriceBelowSMACondition(Condition):
    """
    Exit condition: Close price falls below SMA.

    Standard exit signal for VBO strategy.
    """

    def __init__(self, sma_key: str = "sma", name: str = "PriceBelowSMA") -> None:
        """Initialize condition."""
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


class WhipsawExitCondition(Condition):
    """
    Exit condition for same-day whipsaw detection.

    Triggers when price breaks out but then falls below SMA
    on the same candle, indicating a false breakout.
    """

    def __init__(
        self,
        sma_key: str = "sma",
        name: str = "WhipsawExit",
    ) -> None:
        """Initialize condition."""
        super().__init__(name)
        self.sma_key = sma_key

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check for whipsaw condition."""
        target = indicators.get("target")
        sma = indicators.get(self.sma_key)

        if target is None or sma is None:
            return False

        # Whipsaw: broke out (high >= target) but closed below SMA
        breakout_occurred = current.high >= target
        closed_below_sma = current.close < sma

        return breakout_occurred and closed_below_sma
