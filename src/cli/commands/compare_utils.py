"""
Strategy creation utilities for Compare CLI command.
"""

from src.strategies.base import Strategy
from src.strategies.mean_reversion import (
    MeanReversionStrategy,
    SimpleMeanReversionStrategy,
)
from src.strategies.momentum import MomentumStrategy, SimpleMomentumStrategy
from src.strategies.volatility_breakout import create_vbo_strategy

__all__ = ["create_strategy_for_compare"]


def create_strategy_for_compare(strategy_name: str) -> Strategy | None:
    """
    Create strategy instance for comparison.

    Args:
        strategy_name: Strategy variant name

    Returns:
        Strategy instance, or None if unknown
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
    elif strategy_name == "momentum":
        return MomentumStrategy(name="MomentumStrategy")
    elif strategy_name == "simple-momentum":
        return SimpleMomentumStrategy(name="SimpleMomentum")
    elif strategy_name == "mean-reversion":
        return MeanReversionStrategy(name="MeanReversionStrategy")
    elif strategy_name == "simple-mean-reversion":
        return SimpleMeanReversionStrategy(name="SimpleMeanReversion")
    return None
