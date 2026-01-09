"""
Strategy creation utilities for Monte Carlo CLI command.
"""

from src.strategies.base import Strategy
from src.strategies.volatility_breakout import create_vbo_strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = ["create_strategy_for_monte_carlo"]


def create_strategy_for_monte_carlo(strategy_name: str) -> Strategy | None:
    """
    Create strategy instance for Monte Carlo simulation.

    Args:
        strategy_name: Strategy variant name
            - "vanilla": Full VBO with all filters
            - "minimal": VBO without filters
            - "legacy": Legacy parameters

    Returns:
        Strategy instance, or None if unsupported
    """
    if strategy_name == "vanilla":
        return create_vbo_strategy(
            name="VanillaVBO",
            sma_period=4,
            trend_sma_period=8,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            use_trend_filter=True,
            use_noise_filter=True,
        )
    elif strategy_name == "minimal":
        return create_vbo_strategy(
            name="MinimalVBO",
            sma_period=4,
            trend_sma_period=8,
            short_noise_period=4,
            long_noise_period=8,
            exclude_current=False,
            use_trend_filter=False,
            use_noise_filter=False,
        )
    elif strategy_name == "legacy":
        return create_vbo_strategy(
            name="LegacyBT",
            sma_period=5,
            trend_sma_period=10,
            short_noise_period=5,
            long_noise_period=10,
            exclude_current=True,
            use_trend_filter=True,
            use_noise_filter=True,
        )
    else:
        logger.error(f"Strategy {strategy_name} not yet supported for Monte Carlo")
        return None
