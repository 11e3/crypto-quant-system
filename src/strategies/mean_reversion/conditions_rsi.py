"""
RSI-based conditions for Mean Reversion strategy.

These conditions use RSI indicator to identify oversold and overbought conditions.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition

__all__ = [
    "RSIOversoldCondition",
    "RSIOverboughtCondition",
    "MeanReversionStrengthCondition",
]


class RSIOversoldCondition(Condition):
    """
    Entry condition: RSI is oversold (below threshold).

    Confirms oversold condition for mean reversion entry.
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

    Indicates price has reverted and may reverse.
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


class MeanReversionStrengthCondition(Condition):
    """
    Condition: Mean reversion strength based on deviation from mean.

    Filters for strong mean reversion opportunities.
    """

    def __init__(
        self,
        sma_key: str = "sma",
        min_deviation_pct: float = 0.02,
        name: str = "MeanReversionStrength",
    ) -> None:
        """
        Initialize mean reversion strength condition.

        Args:
            sma_key: Key for SMA value in indicators dict
            min_deviation_pct: Minimum deviation percentage from SMA (default 2%)
            name: Condition name
        """
        super().__init__(name)
        self.sma_key = sma_key
        self.min_deviation_pct = min_deviation_pct

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if price has deviated enough from mean."""
        sma = indicators.get(self.sma_key)

        if sma is None or sma <= 0:
            return False

        # Calculate deviation percentage
        deviation_pct = abs(current.close - sma) / sma
        return deviation_pct >= self.min_deviation_pct
