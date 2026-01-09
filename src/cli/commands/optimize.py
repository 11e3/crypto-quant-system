"""
CLI command for optimizing strategy parameters.
"""

import click

from src.backtester import BacktestConfig, optimize_strategy_parameters
from src.cli.commands.optimize_utils import (
    create_strategy_factory,
    parse_range,
    print_optimization_results,
    print_top_results,
    save_optimization_report,
)
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@click.command(name="optimize")
@click.option(
    "--tickers",
    "-t",
    multiple=True,
    default=["KRW-BTC", "KRW-ETH"],
    help="Trading pair tickers to backtest",
)
@click.option(
    "--interval",
    "-i",
    default="day",
    type=click.Choice(["minute240", "day", "week"], case_sensitive=False),
    help="Data interval for backtesting",
)
@click.option(
    "--initial-capital",
    "-c",
    type=float,
    default=1.0,
    help="Initial capital (default: 1.0)",
)
@click.option(
    "--fee-rate",
    "-f",
    type=float,
    default=0.0005,
    help="Trading fee rate (default: 0.0005 = 0.05%%)",
)
@click.option(
    "--max-slots",
    "-s",
    type=int,
    default=4,
    help="Maximum number of concurrent positions (default: 4)",
)
@click.option(
    "--strategy",
    type=click.Choice(["vanilla", "legacy"], case_sensitive=False),
    default="vanilla",
    help="Strategy variant to optimize",
)
@click.option(
    "--metric",
    type=click.Choice(
        ["sharpe_ratio", "cagr", "total_return", "calmar_ratio", "win_rate", "profit_factor"],
        case_sensitive=False,
    ),
    default="sharpe_ratio",
    help="Metric to optimize (default: sharpe_ratio)",
)
@click.option(
    "--method",
    type=click.Choice(["grid", "random"], case_sensitive=False),
    default="grid",
    help="Optimization method: grid or random (default: grid)",
)
@click.option(
    "--n-iter",
    type=int,
    default=100,
    help="Number of iterations for random search (default: 100)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count - 1)",
)
@click.option(
    "--sma-range",
    type=str,
    default="4,5,6",
    help="SMA period range (comma-separated, e.g., '4,5,6')",
)
@click.option(
    "--trend-range",
    type=str,
    default="8,10,12",
    help="Trend SMA period range (comma-separated, e.g., '8,10,12')",
)
@click.option(
    "--short-noise-range",
    type=str,
    default=None,
    help="Short noise period range (comma-separated)",
)
@click.option(
    "--long-noise-range",
    type=str,
    default=None,
    help="Long noise period range (comma-separated)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=str),
    default=None,
    help="Output path for optimization report",
)
def optimize(
    tickers: tuple[str, ...],
    interval: str,
    initial_capital: float,
    fee_rate: float,
    max_slots: int,
    strategy: str,
    metric: str,
    method: str,
    n_iter: int,
    workers: int | None,
    sma_range: str,
    trend_range: str,
    short_noise_range: str | None,
    long_noise_range: str | None,
    output: str | None,
) -> None:
    """
    Optimize strategy parameters using grid or random search.

    Example:
        crypto-quant optimize --strategy vanilla --metric sharpe_ratio --sma-range 4,5,6 --trend-range 8,10,12
    """
    ticker_list = list(tickers)

    logger.info("Starting parameter optimization...")
    logger.info(f"Tickers: {ticker_list}, Interval: {interval}, Strategy: {strategy}")
    logger.info(f"Metric: {metric}, Method: {method}")

    # Parse parameter ranges
    param_grid: dict[str, list[int]] = {}
    param_grid["sma_period"] = parse_range(sma_range)
    param_grid["trend_sma_period"] = parse_range(trend_range)
    param_grid["short_noise_period"] = (
        parse_range(short_noise_range) if short_noise_range else param_grid["sma_period"]
    )
    param_grid["long_noise_period"] = (
        parse_range(long_noise_range) if long_noise_range else param_grid["trend_sma_period"]
    )

    # Create strategy factory
    create_strategy = create_strategy_factory(strategy)

    # Create config
    config = BacktestConfig(
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        slippage_rate=fee_rate,
        max_slots=max_slots,
        use_cache=True,
    )

    # Run optimization
    result = optimize_strategy_parameters(
        strategy_factory=create_strategy,
        param_grid=param_grid,
        tickers=ticker_list,
        interval=interval,
        config=config,
        metric=metric,
        maximize=True,
        method=method,
        n_iter=n_iter,
        n_workers=workers,
    )

    # Print results
    print_optimization_results(result, metric)
    print_top_results(result, metric)

    # Generate report if output specified
    if output:
        save_optimization_report(result, output, config, ticker_list)
