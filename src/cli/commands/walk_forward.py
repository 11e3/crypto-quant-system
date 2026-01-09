"""
CLI command for walk-forward analysis.
"""

from datetime import datetime
from pathlib import Path

import click

from src.backtester import BacktestConfig, run_walk_forward_analysis
from src.cli.commands.walk_forward_utils import (
    create_strategy_factory,
    parse_range,
    print_period_details,
    print_walk_forward_results,
    save_walk_forward_report,
)
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@click.command(name="walk-forward")
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
    help="Strategy variant to analyze",
)
@click.option(
    "--optimization-days",
    type=int,
    default=365,
    help="Length of optimization period in days (default: 365)",
)
@click.option(
    "--test-days",
    type=int,
    default=90,
    help="Length of test period in days (default: 90)",
)
@click.option(
    "--step-days",
    type=int,
    default=90,
    help="Step size between periods in days (default: 90)",
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
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count - 1)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=str),
    default=None,
    help="Output path for walk-forward report",
)
def walk_forward(
    tickers: tuple[str, ...],
    interval: str,
    initial_capital: float,
    fee_rate: float,
    max_slots: int,
    strategy: str,
    optimization_days: int,
    test_days: int,
    step_days: int,
    metric: str,
    sma_range: str,
    trend_range: str,
    workers: int | None,
    output: str | None,
) -> None:
    """
    Run walk-forward analysis on trading strategy.

    Walk-forward analysis splits data into multiple periods:
    - Optimization period: Used to find best parameters
    - Test period: Used to test the optimized parameters

    This helps prevent overfitting and validates strategy robustness.

    Example:
        crypto-quant walk-forward --strategy vanilla --optimization-days 365 --test-days 90
    """
    ticker_list = list(tickers)

    logger.info("Starting walk-forward analysis...")
    logger.info(f"Tickers: {ticker_list}, Interval: {interval}, Strategy: {strategy}")
    logger.info(f"Optimization: {optimization_days}d, Test: {test_days}d, Step: {step_days}d")

    # Parse parameter ranges
    param_grid: dict[str, list[int]] = {}
    param_grid["sma_period"] = parse_range(sma_range)
    param_grid["trend_sma_period"] = parse_range(trend_range)
    param_grid["short_noise_period"] = param_grid["sma_period"]
    param_grid["long_noise_period"] = param_grid["trend_sma_period"]

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

    # Run walk-forward analysis
    result = run_walk_forward_analysis(
        strategy_factory=create_strategy,
        param_grid=param_grid,
        tickers=ticker_list,
        interval=interval,
        config=config,
        optimization_days=optimization_days,
        test_days=test_days,
        step_days=step_days,
        metric=metric,
        n_workers=workers,
    )

    # Print results
    print_walk_forward_results(result)
    print_period_details(result)

    # Generate report if output specified
    if output:
        output_path = Path(output)
        if output_path.is_dir() or not output_path.suffix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_path / f"walk_forward_{timestamp}.txt"
        else:
            output_path = Path(output)

        save_walk_forward_report(result, output_path)
