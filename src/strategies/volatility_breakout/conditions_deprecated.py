"""
Deprecated filter aliases for backward compatibility.

Use the new Condition classes directly:
- TrendCondition instead of TrendFilter
- NoiseCondition instead of NoiseFilter
- NoiseThresholdCondition instead of NoiseThresholdFilter
- VolatilityRangeCondition instead of VolatilityFilter
- VolumeCondition instead of VolumeFilter
- DayOfWeekCondition instead of DayOfWeekFilter
- MarketRegimeCondition instead of MarketRegimeFilter
"""

import warnings
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from src.strategies.base import Condition

# Import from specific modules to avoid circular import
from src.strategies.volatility_breakout.conditions_market import (
    DayOfWeekCondition,
    MarketRegimeCondition,
    VolumeCondition,
)

T = TypeVar("T")


def _get_filter_classes() -> tuple[
    type["Condition"], type["Condition"], type["Condition"], type["Condition"]
]:
    """Lazy import to avoid circular dependency."""
    from src.strategies.volatility_breakout.conditions_filters import (
        NoiseCondition,
        NoiseThresholdCondition,
        TrendCondition,
        VolatilityRangeCondition,
    )

    return TrendCondition, NoiseCondition, NoiseThresholdCondition, VolatilityRangeCondition


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


# Get classes via lazy import to avoid circular dependency
_TrendCondition, _NoiseCondition, _NoiseThresholdCondition, _VolatilityRangeCondition = (
    _get_filter_classes()
)

# Create deprecated aliases with warnings
TrendFilter = _create_deprecated_alias(_TrendCondition, "TrendFilter")
NoiseFilter = _create_deprecated_alias(_NoiseCondition, "NoiseFilter")
NoiseThresholdFilter = _create_deprecated_alias(_NoiseThresholdCondition, "NoiseThresholdFilter")
VolatilityFilter = _create_deprecated_alias(_VolatilityRangeCondition, "VolatilityFilter")
VolumeFilter = _create_deprecated_alias(VolumeCondition, "VolumeFilter")
DayOfWeekFilter = _create_deprecated_alias(DayOfWeekCondition, "DayOfWeekFilter")
MarketRegimeFilter = _create_deprecated_alias(MarketRegimeCondition, "MarketRegimeFilter")

__all__ = [
    "TrendFilter",
    "NoiseFilter",
    "NoiseThresholdFilter",
    "VolatilityFilter",
    "VolumeFilter",
    "DayOfWeekFilter",
    "MarketRegimeFilter",
]
