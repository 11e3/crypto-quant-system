"""
VBO strategy variants.

Contains specialized VBO strategy implementations.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from src.strategies.base import Condition
from src.strategies.volatility_breakout.conditions import (
    BreakoutCondition,
    NoiseThresholdCondition,
    VolatilityRangeCondition,
)

if TYPE_CHECKING:
    from src.strategies.volatility_breakout.vbo import VanillaVBO


def create_minimal_vbo(
    name: str = "MinimalVBO",
    sma_period: int = 4,
    trend_sma_period: int = 8,
    short_noise_period: int = 4,
    long_noise_period: int = 8,
    exclude_current: bool = False,
) -> VanillaVBO:
    """
    Create minimal VBO with only breakout condition (no market conditions).

    Useful as a baseline for comparing condition effectiveness.

    Args:
        name: Strategy name
        sma_period: SMA period
        trend_sma_period: Trend SMA period
        short_noise_period: Short noise period
        long_noise_period: Long noise period
        exclude_current: Exclude current bar

    Returns:
        VanillaVBO instance
    """
    from src.strategies.volatility_breakout.vbo import VanillaVBO

    return VanillaVBO(
        name=name,
        sma_period=sma_period,
        trend_sma_period=trend_sma_period,
        short_noise_period=short_noise_period,
        long_noise_period=long_noise_period,
        entry_conditions=[BreakoutCondition()],
        use_default_conditions=False,
        exclude_current=exclude_current,
    )


def create_strict_vbo(
    name: str = "StrictVBO",
    max_noise: float = 0.6,
    min_volatility_pct: float = 0.01,
    sma_period: int = 4,
    trend_sma_period: int = 8,
    short_noise_period: int = 4,
    long_noise_period: int = 8,
    extra_entry_conditions: Sequence[Condition] | None = None,
    exclude_current: bool = False,
) -> VanillaVBO:
    """
    Create strict VBO with additional conditions for higher quality signals.

    Includes noise threshold and volatility range conditions.

    Args:
        name: Strategy name
        max_noise: Maximum noise threshold
        min_volatility_pct: Minimum volatility percentage
        sma_period: SMA period
        trend_sma_period: Trend SMA period
        short_noise_period: Short noise period
        long_noise_period: Long noise period
        extra_entry_conditions: Additional entry conditions
        exclude_current: Exclude current bar

    Returns:
        VanillaVBO instance
    """
    from src.strategies.volatility_breakout.vbo import VanillaVBO

    extra_conditions: list[Condition] = [
        NoiseThresholdCondition(max_noise=max_noise),
        VolatilityRangeCondition(min_volatility_pct=min_volatility_pct),
    ]

    entry_conditions = list(extra_entry_conditions or []) + extra_conditions

    return VanillaVBO(
        name=name,
        sma_period=sma_period,
        trend_sma_period=trend_sma_period,
        short_noise_period=short_noise_period,
        long_noise_period=long_noise_period,
        entry_conditions=entry_conditions,
        use_default_conditions=True,
        exclude_current=exclude_current,
    )


__all__ = [
    "create_minimal_vbo",
    "create_strict_vbo",
]
