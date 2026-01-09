"""
RSI-based conditions for Momentum strategy.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition


class RSIOversoldCondition(Condition):
    """
    Entry condition: RSI is oversold (below threshold).

    Indicates potential buying opportunity when momentum is recovering.
    """

    def __init__(
        self,
        rsi_key: str = "rsi",
        oversold_threshold: float = 30.0,
        name: str = "RSIOversold",
    ) -> None:
        """
        Initialize RSI oversold condition.

        Args:
            rsi_key: Key for RSI value in indicators dict
            oversold_threshold: RSI threshold for oversold (default 30)
            name: Condition name
        """
        super().__init__(name)
        self.rsi_key = rsi_key
        self.oversold_threshold = oversold_threshold

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if RSI is oversold."""
        rsi = indicators.get(self.rsi_key)

        if rsi is None:
            return False

        return rsi < self.oversold_threshold


class RSIOverboughtCondition(Condition):
    """
    Exit condition: RSI is overbought (above threshold).

    Indicates potential selling opportunity when momentum is weakening.
    """

    def __init__(
        self,
        rsi_key: str = "rsi",
        overbought_threshold: float = 70.0,
        name: str = "RSIOverbought",
    ) -> None:
        """
        Initialize RSI overbought condition.

        Args:
            rsi_key: Key for RSI value in indicators dict
            overbought_threshold: RSI threshold for overbought (default 70)
            name: Condition name
        """
        super().__init__(name)
        self.rsi_key = rsi_key
        self.overbought_threshold = overbought_threshold

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if RSI is overbought."""
        rsi = indicators.get(self.rsi_key)

        if rsi is None:
            return False

        return rsi > self.overbought_threshold


__all__ = [
    "RSIOversoldCondition",
    "RSIOverboughtCondition",
]
