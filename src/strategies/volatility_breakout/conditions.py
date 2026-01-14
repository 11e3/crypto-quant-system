"""
Entry and exit conditions for Volatility Breakout strategy.

These conditions can be mixed and matched to create custom VBO variants.
This module re-exports all conditions from submodules.
"""

import warnings
from typing import Any, TypeVar, cast

# Entry conditions
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

# Filter conditions (all consolidated in conditions_filters)
from src.strategies.volatility_breakout.conditions_filters import (
    DayOfWeekCondition,
    MarketRegimeCondition,
    NoiseCondition,
    NoiseThresholdCondition,
    TrendCondition,
    VolatilityRangeCondition,
    VolumeCondition,
)

T = TypeVar("T")


def _create_deprecated_alias(condition_class: type[T], filter_name: str) -> type[T]:
    """Create a deprecated alias with warning."""

    class DeprecatedFilter(condition_class):  # type: ignore[valid-type, misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            warnings.warn(
                f"{filter_name} is deprecated. Use {condition_class.__name__} instead.",
                DeprecationWarning,
                stacklevel=3,
            )
            super().__init__(*args, **kwargs)

    DeprecatedFilter.__name__ = filter_name
    DeprecatedFilter.__qualname__ = filter_name
    return cast(type[T], DeprecatedFilter)


# Deprecated aliases for backward compatibility
TrendFilter = _create_deprecated_alias(TrendCondition, "TrendFilter")
NoiseFilter = _create_deprecated_alias(NoiseCondition, "NoiseFilter")
NoiseThresholdFilter = _create_deprecated_alias(NoiseThresholdCondition, "NoiseThresholdFilter")
VolatilityFilter = _create_deprecated_alias(VolatilityRangeCondition, "VolatilityFilter")
VolumeFilter = _create_deprecated_alias(VolumeCondition, "VolumeFilter")
DayOfWeekFilter = _create_deprecated_alias(DayOfWeekCondition, "DayOfWeekFilter")
MarketRegimeFilter = _create_deprecated_alias(MarketRegimeCondition, "MarketRegimeFilter")


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
