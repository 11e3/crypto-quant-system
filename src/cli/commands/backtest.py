"""Backtest CLI command.

Provides command-line interface for running backtests with various strategies.
"""

from __future__ import annotations

import logging

import click

from src.backtester.engine import run_backtest
from src.backtester.models import BacktestConfig
from src.cli.commands.backtest_factory import create_strategy
from src.cli.commands.backtest_output import (
    generate_backtest_report,
    log_backtest_results,
    log_risk_metrics,
    log_strategy_parameters,
)

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(
        [
            "vanilla",
            "strict",
            "minimal",
            "legacy",
            "momentum",
            "simple-momentum",
            "mean-reversion",
            "simple-mean-reversion",
            "pair-trading",
        ]
    ),
    default="vanilla",
    help="Strategy type to use",
)
@click.option(
    "--ticker",
    "-t",
    multiple=True,
    default=["KRW-BTC"],
    help="Ticker(s) to backtest (can specify multiple)",
)
@click.option(
    "--interval",
    "-i",
    type=click.Choice(["day", "minute240", "week"]),
    default="day",
    help="Data interval",
)
@click.option("--k", type=float, default=0.5, help="K value for VBO strategies")
@click.option(
    "--initial-capital",
    type=float,
    default=10_000_000.0,
    help="Initial capital",
)
@click.option("--fee-rate", type=float, default=0.0005, help="Fee rate (0.05%)")
@click.option("--max-slots", type=int, default=5, help="Maximum concurrent positions")
@click.option(
    "--position-sizing",
    type=click.Choice(["equal", "volatility", "kelly"]),
    default="equal",
    help="Position sizing method",
)
@click.option(
    "--position-sizing-risk",
    type=float,
    default=0.02,
    help="Risk percentage for position sizing",
)
@click.option(
    "--position-sizing-lookback",
    type=int,
    default=20,
    help="Lookback period for position sizing",
)
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.option("--output", "-o", default=None, help="Output report path (HTML/PNG)")
@click.option("--sma-period", type=int, default=None, help="SMA period for legacy")
@click.option(
    "--trend-sma-period",
    type=int,
    default=None,
    help="Trend SMA period for legacy",
)
@click.option(
    "--short-noise-period",
    type=int,
    default=None,
    help="Short noise period for legacy",
)
@click.option(
    "--long-noise-period",
    type=int,
    default=None,
    help="Long noise period for legacy",
)
@click.option(
    "--exclude-current",
    type=bool,
    default=None,
    help="Exclude current for legacy",
)
def backtest(  # noqa: PLR0913
    strategy: str,
    ticker: tuple[str, ...],
    interval: str,
    k: float,
    initial_capital: float,
    fee_rate: float,
    max_slots: int,
    position_sizing: str,
    position_sizing_risk: float,
    position_sizing_lookback: int,
    no_cache: bool,
    output: str | None,
    sma_period: int | None,
    trend_sma_period: int | None,
    short_noise_period: int | None,
    long_noise_period: int | None,
    exclude_current: bool | None,
) -> None:
    """Run backtest with specified strategy and parameters."""
    ticker_list = list(ticker)
    logger.info(f"Running backtest: strategy={strategy}, tickers={ticker_list}")

    # Create strategy (k parameter handled internally by strategy)
    _ = k  # k is available via CLI but strategy uses internal calculation
    strategy_obj = create_strategy(
        strategy=strategy,
        ticker_list=ticker_list,
        sma_period=sma_period,
        trend_sma_period=trend_sma_period,
        short_noise_period=short_noise_period,
        long_noise_period=long_noise_period,
        exclude_current=exclude_current,
    )

    log_strategy_parameters(strategy_obj)

    # Create config
    config = BacktestConfig(
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        slippage_rate=fee_rate,
        max_slots=max_slots,
        position_sizing=position_sizing,
        position_sizing_risk_pct=position_sizing_risk,
        position_sizing_lookback=position_sizing_lookback,
        use_cache=not no_cache,
    )

    # Run backtest
    result = run_backtest(
        strategy=strategy_obj,
        tickers=ticker_list,
        interval=interval,
        config=config,
    )

    # Output results
    log_backtest_results(result)
    log_risk_metrics(result)

    # Generate report if output specified
    if output:
        generate_backtest_report(
            result=result,
            output=output,
            strategy_obj=strategy_obj,
            config=config,
            ticker_list=ticker_list,
        )


__all__ = ["backtest"]
