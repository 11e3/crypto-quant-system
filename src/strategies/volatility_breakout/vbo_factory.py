"""
VBO strategy factory functions.

Provides functions to create customized VBO strategies.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.strategies.volatility_breakout.vbo import VanillaVBO

from src.strategies.base import Condition
from src.strategies.volatility_breakout.conditions import (
    BreakoutCondition,
    NoiseCondition,
    PriceBelowSMACondition,
    SMABreakoutCondition,
    TrendCondition,
)


def create_vbo_strategy(
    name: str = "CustomVBO",
    sma_period: int = 4,
    trend_sma_period: int = 8,
    short_noise_period: int = 4,
    long_noise_period: int = 8,
    use_breakout: bool = True,
    use_sma_breakout: bool = True,
    use_sma_exit: bool = True,
    use_trend_filter: bool = True,
    use_noise_filter: bool = True,
    extra_entry_conditions: Sequence[Condition] | None = None,
    extra_exit_conditions: Sequence[Condition] | None = None,
    exclude_current: bool = False,
) -> VanillaVBO:
    """
    Factory function to create customized VBO strategy.

    Provides fine-grained control over which conditions
    are included in the strategy.

    Args:
        name: Strategy name
        sma_period: Period for exit SMA
        trend_sma_period: Period for trend SMA
        short_noise_period: Period for K value
        long_noise_period: Period for noise baseline
        use_breakout: Include breakout condition
        use_sma_breakout: Include SMA breakout condition
        use_sma_exit: Include SMA exit condition
        use_trend_filter: Include trend condition (formerly filter)
        use_noise_filter: Include noise condition (formerly filter)
        extra_entry_conditions: Additional entry conditions
        extra_exit_conditions: Additional exit conditions
        exclude_current: If True, exclude current bar from calculations

    Returns:
        Configured VanillaVBO instance

    Example:
        Create VBO without noise condition::

            strategy = create_vbo_strategy(
                name="VBO_NoNoise",
                use_noise_filter=False,
            )

        Add custom momentum condition::

            from src.strategies.volatility_breakout.conditions import ConsecutiveUpCondition
            strategy = create_vbo_strategy(
                name="VBO_Momentum",
                extra_entry_conditions=[ConsecutiveUpCondition(days=2)],
            )
    """
    from src.strategies.volatility_breakout.vbo import VanillaVBO

    # Build entry conditions
    entry_conditions: list[Condition] = []
    if use_breakout:
        entry_conditions.append(BreakoutCondition())
    if use_sma_breakout:
        entry_conditions.append(SMABreakoutCondition())
    if use_trend_filter:
        entry_conditions.append(TrendCondition())
    if use_noise_filter:
        entry_conditions.append(NoiseCondition())
    if extra_entry_conditions:
        entry_conditions.extend(list(extra_entry_conditions))

    # Build exit conditions
    exit_conditions: list[Condition] = []
    if use_sma_exit:
        exit_conditions.append(PriceBelowSMACondition())
    if extra_exit_conditions:
        exit_conditions.extend(list(extra_exit_conditions))

    return VanillaVBO(
        name=name,
        sma_period=sma_period,
        trend_sma_period=trend_sma_period,
        short_noise_period=short_noise_period,
        long_noise_period=long_noise_period,
        entry_conditions=entry_conditions,
        exit_conditions=exit_conditions,
        use_default_conditions=False,
        exclude_current=exclude_current,
    )


def quick_vbo(
    sma: int = 4,
    n: int = 2,
) -> VanillaVBO:
    """
    Create VBO with simplified parameters matching original bt.py.

    Args:
        sma: Base SMA period
        n: Multiplier for trend/long-term periods

    Returns:
        VanillaVBO instance
    """
    from src.strategies.volatility_breakout.vbo import VanillaVBO

    return VanillaVBO(
        name=f"VBO_SMA{sma}_N{n}",
        sma_period=sma,
        trend_sma_period=sma * n,
        short_noise_period=sma,
        long_noise_period=sma * n,
    )
