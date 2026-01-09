"""Strategy factory functions for backtest CLI.

Encapsulates strategy creation logic with parameter handling.
"""

from __future__ import annotations

from src.strategies.base import Strategy
from src.strategies.mean_reversion import (
    MeanReversionStrategy,
    SimpleMeanReversionStrategy,
)
from src.strategies.momentum import (
    MomentumStrategy,
    SimpleMomentumStrategy,
)
from src.strategies.pair_trading import PairTradingStrategy
from src.strategies.volatility_breakout import create_vbo_strategy


def create_strategy(  # noqa: PLR0913
    strategy: str,
    ticker_list: list[str],
    *,
    sma_period: int | None = None,
    trend_sma_period: int | None = None,
    short_noise_period: int | None = None,
    long_noise_period: int | None = None,
    exclude_current: bool | None = None,
) -> Strategy:
    """Create strategy object based on strategy name.

    Args:
        strategy: Strategy name (vanilla, strict, minimal, legacy, etc.)
        ticker_list: List of tickers for validation
        sma_period: SMA period for legacy strategy
        trend_sma_period: Trend SMA period for legacy strategy
        short_noise_period: Short noise period for legacy strategy
        long_noise_period: Long noise period for legacy strategy
        exclude_current: Exclude current for legacy strategy

    Returns:
        Configured strategy object

    Raises:
        ValueError: If strategy is unknown or pair-trading with wrong ticker count
    """
    if strategy == "vanilla":
        return create_vbo_strategy(
            name="VanillaVBO",
            use_trend_filter=False,
            use_noise_filter=False,
        )
    elif strategy == "strict":
        return create_vbo_strategy(
            name="StrictVBO",
            use_trend_filter=True,
            use_noise_filter=True,
        )
    elif strategy == "minimal":
        return create_vbo_strategy(
            name="MinimalVBO",
            use_trend_filter=False,
            use_noise_filter=False,
        )
    elif strategy == "legacy":
        return _create_legacy_strategy(
            sma_period=sma_period,
            trend_sma_period=trend_sma_period,
            short_noise_period=short_noise_period,
            long_noise_period=long_noise_period,
            exclude_current=exclude_current,
        )
    elif strategy == "momentum":
        return MomentumStrategy(name="MomentumStrategy")
    elif strategy == "simple-momentum":
        return SimpleMomentumStrategy(name="SimpleMomentum")
    elif strategy == "mean-reversion":
        return MeanReversionStrategy(name="MeanReversionStrategy")
    elif strategy == "simple-mean-reversion":
        return SimpleMeanReversionStrategy(name="SimpleMeanReversion")
    elif strategy == "pair-trading":
        return _create_pair_trading_strategy(ticker_list)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def _create_legacy_strategy(
    *,
    sma_period: int | None,
    trend_sma_period: int | None,
    short_noise_period: int | None,
    long_noise_period: int | None,
    exclude_current: bool | None,
) -> Strategy:
    """Create legacy VBO strategy with default parameters."""
    legacy_kwargs: dict[str, int | bool] = {
        "sma_period": sma_period if sma_period is not None else 5,
        "trend_sma_period": trend_sma_period if trend_sma_period is not None else 10,
        "short_noise_period": short_noise_period if short_noise_period is not None else 5,
        "long_noise_period": long_noise_period if long_noise_period is not None else 10,
        "exclude_current": exclude_current if exclude_current is not None else True,
    }
    return create_vbo_strategy(
        name="LegacyBT",
        use_trend_filter=True,
        use_noise_filter=True,
        **legacy_kwargs,  # type: ignore[arg-type]
    )


def _create_pair_trading_strategy(ticker_list: list[str]) -> PairTradingStrategy:
    """Create pair trading strategy with ticker validation.

    Raises:
        ValueError: If ticker count is not exactly 2
    """
    if len(ticker_list) != 2:
        raise ValueError(
            f"Pair trading requires exactly 2 tickers, got {len(ticker_list)}: {ticker_list}"
        )
    return PairTradingStrategy(name="PairTradingStrategy")


__all__ = ["create_strategy"]
