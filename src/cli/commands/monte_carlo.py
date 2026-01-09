"""
CLI command for Monte Carlo simulation of backtest results.
"""

import click

from src.backtester import BacktestConfig, run_backtest
from src.backtester.analysis.monte_carlo import run_monte_carlo
from src.cli.commands.monte_carlo_output import (
    print_monte_carlo_results,
    save_monte_carlo_report,
)
from src.cli.commands.monte_carlo_utils import create_strategy_for_monte_carlo
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@click.command(name="monte-carlo")
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
    type=click.Choice(
        ["vanilla", "minimal", "legacy", "momentum", "mean-reversion"],
        case_sensitive=False,
    ),
    default="vanilla",
    help="Strategy variant to use",
)
@click.option(
    "--n-simulations",
    "-n",
    type=int,
    default=1000,
    help="Number of Monte Carlo simulations (default: 1000)",
)
@click.option(
    "--method",
    type=click.Choice(["bootstrap", "parametric"], case_sensitive=False),
    default="bootstrap",
    help="Simulation method: bootstrap (resample) or parametric (normal dist)",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=str),
    default=None,
    help="Output path for Monte Carlo report",
)
def monte_carlo(
    tickers: tuple[str, ...],
    interval: str,
    initial_capital: float,
    fee_rate: float,
    max_slots: int,
    strategy: str,
    n_simulations: int,
    method: str,
    seed: int | None,
    output: str | None,
) -> None:
    """
    Run Monte Carlo simulation on backtest results.

    Example:
        crypto-quant monte-carlo --strategy vanilla --n-simulations 2000
    """
    ticker_list = list(tickers)

    logger.info("Starting Monte Carlo simulation...")
    logger.info(f"Tickers: {ticker_list}")
    logger.info(f"Interval: {interval}")
    logger.info(f"Strategy: {strategy}")
    logger.info(f"Simulations: {n_simulations}")
    logger.info(f"Method: {method}")

    # Create strategy
    strategy_obj = create_strategy_for_monte_carlo(strategy)
    if strategy_obj is None:
        return

    # Create config
    config = BacktestConfig(
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        slippage_rate=fee_rate,
        max_slots=max_slots,
        use_cache=True,
    )

    # Run backtest first
    logger.info("Running initial backtest...")
    result = run_backtest(
        strategy=strategy_obj,
        tickers=ticker_list,
        interval=interval,
        config=config,
    )

    # Run Monte Carlo simulation
    logger.info(f"Running {n_simulations} Monte Carlo simulations...")
    mc_result = run_monte_carlo(
        result=result,
        n_simulations=n_simulations,
        method=method,
        random_seed=seed,
    )

    # Print results
    print_monte_carlo_results(result, mc_result, n_simulations)

    # Generate report if output specified
    if output:
        save_monte_carlo_report(result, output, strategy_obj, config, ticker_list)
