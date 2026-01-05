"""
Base classes for strategy abstraction.

Provides modular interfaces for building trading strategies with
composable conditions and filters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from typing import Any

import pandas as pd


class SignalType(Enum):
    """Trading signal types."""

    BUY = auto()
    SELL = auto()
    HOLD = auto()


@dataclass
class Signal:
    """Trading signal with metadata."""

    signal_type: SignalType
    ticker: str
    price: float
    date: date
    strength: float = 1.0  # Signal strength/confidence (0-1)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Represents a trading position."""

    ticker: str
    amount: float
    entry_price: float
    entry_date: date


@dataclass
class OHLCV:
    """Single OHLCV bar data."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def range(self) -> float:
        """Price range (high - low)."""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Candle body size."""
        return abs(self.close - self.open)


class Condition(ABC):
    """
    Abstract base class for entry/exit conditions.

    Conditions are atomic logic units that evaluate market data
    and return True/False for signal generation.
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize condition.

        Args:
            name: Human-readable condition name
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """
        Evaluate condition against market data.

        Args:
            current: Current bar OHLCV data
            history: Historical DataFrame with OHLCV + indicators
            indicators: Pre-calculated indicator values for current bar

        Returns:
            True if condition is met
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# Alias for backward compatibility
# Filters are now treated as Conditions in the unified architecture
Filter = Condition


class CompositeCondition(Condition):
    """Combines multiple conditions with AND/OR logic."""

    def __init__(
        self,
        conditions: list[Condition],
        operator: str = "AND",
        name: str | None = None,
    ) -> None:
        """
        Initialize composite condition.

        Args:
            conditions: List of conditions to combine
            operator: "AND" or "OR"
            name: Human-readable name
        """
        super().__init__(name)
        self.conditions = conditions
        self.operator = operator.upper()

    def evaluate(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """Evaluate all conditions with specified operator."""
        if not self.conditions:
            return True

        results = [c.evaluate(current, history, indicators) for c in self.conditions]

        if self.operator == "AND":
            return all(results)
        elif self.operator == "OR":
            return any(results)
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    def add(self, condition: Condition) -> "CompositeCondition":
        """Add a condition and return self for chaining."""
        self.conditions.append(condition)
        return self

    def remove(self, condition: Condition) -> "CompositeCondition":
        """Remove a condition and return self for chaining."""
        self.conditions.remove(condition)
        return self


class Strategy(ABC):
    """
    Abstract base class for trading strategies.

    Strategies combine conditions to generate trading signals.
    All conditions (including market filters) are handled as entry/exit conditions.
    """

    def __init__(
        self,
        name: str | None = None,
        entry_conditions: list[Condition] | None = None,
        exit_conditions: list[Condition] | None = None,
    ) -> None:
        """
        Initialize strategy.

        Args:
            name: Strategy name
            entry_conditions: Conditions for entry signals (includes market filters)
            exit_conditions: Conditions for exit signals
        """
        self.name = name or self.__class__.__name__
        self.entry_conditions = CompositeCondition(
            entry_conditions or [], operator="AND", name="EntryConditions"
        )
        self.exit_conditions = CompositeCondition(
            exit_conditions or [], operator="AND", name="ExitConditions"
        )

    @abstractmethod
    def required_indicators(self) -> list[str]:
        """
        Return list of required indicator names.

        Returns:
            List of indicator names this strategy needs
        """
        pass

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all required indicators for the strategy.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        pass

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry/exit signals using vectorized operations.

        Override this method for custom vectorized signal logic.
        Default implementation uses standard VBO signals.

        Args:
            df: DataFrame with OHLCV and indicators

        Returns:
            DataFrame with 'entry_signal' and 'exit_signal' columns
        """
        df = df.copy()

        # Default: use indicator-based signals
        # Entry: high >= target AND target > sma AND filters pass
        entry_breakout = df["high"] >= df["target"]
        entry_sma = df["target"] > df["sma"]

        # Default filters
        has_trend_filter = "sma_trend" in df.columns
        has_noise_filter = "short_noise" in df.columns and "long_noise" in df.columns

        entry_signal = entry_breakout & entry_sma

        if has_trend_filter:
            entry_signal = entry_signal & (df["target"] > df["sma_trend"])

        if has_noise_filter:
            entry_signal = entry_signal & (df["short_noise"] < df["long_noise"])

        # Exit: close < sma
        exit_signal = df["close"] < df["sma"]

        df["entry_signal"] = entry_signal
        df["exit_signal"] = exit_signal

        return df

    def check_entry(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
    ) -> bool:
        """
        Check if entry conditions are met.

        Args:
            current: Current bar data
            history: Historical data
            indicators: Current indicator values

        Returns:
            True if should enter position
        """
        return self.entry_conditions.evaluate(current, history, indicators)

    def check_exit(
        self,
        current: OHLCV,
        history: pd.DataFrame,
        indicators: dict[str, float],
        position: Position,
    ) -> bool:
        """
        Check if exit conditions are met.

        Args:
            current: Current bar data
            history: Historical data
            indicators: Current indicator values
            position: Current position

        Returns:
            True if should exit position
        """
        return self.exit_conditions.evaluate(current, history, indicators)

    def add_entry_condition(self, condition: Condition) -> "Strategy":
        """Add entry condition and return self for chaining."""
        self.entry_conditions.add(condition)
        return self

    def add_exit_condition(self, condition: Condition) -> "Strategy":
        """Add exit condition and return self for chaining."""
        self.exit_conditions.add(condition)
        return self

    def remove_entry_condition(self, condition: Condition) -> "Strategy":
        """Remove entry condition and return self for chaining."""
        self.entry_conditions.remove(condition)
        return self

    def remove_exit_condition(self, condition: Condition) -> "Strategy":
        """Remove exit condition and return self for chaining."""
        self.exit_conditions.remove(condition)
        return self

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"entry_conditions={len(self.entry_conditions.conditions)}, "
            f"exit_conditions={len(self.exit_conditions.conditions)})"
        )
