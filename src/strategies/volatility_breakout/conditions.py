"""
Entry and exit conditions for Volatility Breakout strategy.

These conditions can be mixed and matched to create custom VBO variants.

This module re-exports all conditions from submodules for backward compatibility.
"""

# Entry conditions
# Market filter conditions (including deprecated aliases)
from src.strategies.volatility_breakout.conditions_deprecated import (
    DayOfWeekFilter,
    MarketRegimeFilter,
    NoiseFilter,
    NoiseThresholdFilter,
    TrendFilter,
    VolatilityFilter,
    VolumeFilter,
)
from src.strategies.volatility_breakout.conditions_entry import (
    BreakoutCondition,
    ConsecutiveUpCondition,
    PriceAboveSMACondition,
    SMABreakoutCondition,
    TrendAlignmentCondition,
    VolatilityThresholdCondition,
)

# Exit conditions
from src.strategies.volatility_breakout.conditions_exit import (
    PriceBelowSMACondition,
    WhipsawExitCondition,
)
from src.strategies.volatility_breakout.conditions_filters import (
    DayOfWeekCondition,
    MarketRegimeCondition,
    NoiseCondition,
    NoiseThresholdCondition,
    TrendCondition,
    VolatilityRangeCondition,
    VolumeCondition,
)

__all__ = [
    # Entry conditions
    "BreakoutCondition",
    "SMABreakoutCondition",
    "PriceAboveSMACondition",
    "TrendAlignmentCondition",
    "VolatilityThresholdCondition",
    "ConsecutiveUpCondition",
    # Exit conditions
    "PriceBelowSMACondition",
    "WhipsawExitCondition",
    # Market filter conditions
    "TrendCondition",
    "NoiseCondition",
    "NoiseThresholdCondition",
    "VolatilityRangeCondition",
    "VolumeCondition",
    "DayOfWeekCondition",
    "MarketRegimeCondition",
    # Deprecated aliases (backward compatibility)
    "TrendFilter",
    "NoiseFilter",
    "NoiseThresholdFilter",
    "VolatilityFilter",
    "VolumeFilter",
    "DayOfWeekFilter",
    "MarketRegimeFilter",
]
