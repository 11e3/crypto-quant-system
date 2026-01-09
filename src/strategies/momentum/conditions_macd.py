"""
MACD-based conditions for Momentum strategy.
"""

import pandas as pd

from src.strategies.base import OHLCV, Condition


class MACDBullishCondition(Condition):
    """
    Entry condition: MACD line crosses above signal line (bullish crossover).

    Indicates strengthening upward momentum.
    """

    def __init__(
        self,
        macd_key: str = "macd",
        signal_key: str = "macd_signal",
        name: str = "MACDBullish",
    ) -> None:
        """
        Initialize MACD bullish condition.

        Args:
            macd_key: Key for MACD line value in indicators dict
            signal_key: Key for MACD signal line value in indicators dict
            name: Condition name
        """
        super().__init__(name)
        self.macd_key = macd_key
        self.signal_key = signal_key

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if MACD is above signal line."""
        macd = indicators.get(self.macd_key)
        signal = indicators.get(self.signal_key)

        if macd is None or signal is None:
            return False

        if len(history) < 2:
            return macd > signal

        prev_macd = history.iloc[-2].get("macd")
        prev_signal = history.iloc[-2].get("macd_signal")

        if prev_macd is None or prev_signal is None:
            return macd > signal

        crossover = (prev_macd <= prev_signal) and (macd > signal)
        above_signal = macd > signal

        return crossover or above_signal


class MACDBearishCondition(Condition):
    """
    Exit condition: MACD line crosses below signal line (bearish crossover).

    Indicates weakening upward momentum.
    """

    def __init__(
        self,
        macd_key: str = "macd",
        signal_key: str = "macd_signal",
        name: str = "MACDBearish",
    ) -> None:
        """
        Initialize MACD bearish condition.

        Args:
            macd_key: Key for MACD line value in indicators dict
            signal_key: Key for MACD signal line value in indicators dict
            name: Condition name
        """
        super().__init__(name)
        self.macd_key = macd_key
        self.signal_key = signal_key

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Check if MACD is below signal line."""
        macd = indicators.get(self.macd_key)
        signal = indicators.get(self.signal_key)

        if macd is None or signal is None:
            return False

        if len(history) < 2:
            return macd < signal

        prev_macd = history.iloc[-2].get("macd")
        prev_signal = history.iloc[-2].get("macd_signal")

        if prev_macd is None or prev_signal is None:
            return macd < signal

        crossover = (prev_macd >= prev_signal) and (macd < signal)
        below_signal = macd < signal

        return crossover or below_signal


__all__ = [
    "MACDBullishCondition",
    "MACDBearishCondition",
]
