"""
Backtest command.

Runs backtesting on historical data.
"""

import click

from src.backtester import BacktestConfig, run_backtest
from src.strategies.volatility_breakout import create_vbo_strategy
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@click.command(name="backtest")
@click.option(
    "--tickers",
    "-t",
    multiple=True,
    default=["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"],
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
    type=click.Choice(["vanilla", "minimal", "legacy"], case_sensitive=False),
    default="legacy",
    help="Strategy variant to use (default: legacy - default VBO strategy)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=str),
    default=None,
    help="Output directory for reports (default: reports/)",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable indicator cache",
)
def backtest(
    tickers: tuple[str, ...],
    interval: str,
    initial_capital: float,
    fee_rate: float,
    max_slots: int,
    strategy: str,
    output: str | None,
    no_cache: bool,
) -> None:
    """
    Run backtest on historical data.

    Example:
        upbit-quant backtest --tickers KRW-BTC KRW-ETH --interval day
    """
    ticker_list = list(tickers)

    logger.info("Starting backtest...")
    logger.info(f"Tickers: {ticker_list}")
    logger.info(f"Interval: {interval}")
    logger.info(f"Strategy: {strategy}")
    logger.info(f"Initial capital: {initial_capital}")
    logger.info(f"Fee rate: {fee_rate}")
    logger.info(f"Max slots: {max_slots}")

    # Create strategy based on variant
    if strategy == "vanilla":
        strategy_obj = create_vbo_strategy(
            name="VanillaVBO",
            use_trend_filter=True,
            use_noise_filter=True,
        )
    elif strategy == "minimal":
        strategy_obj = create_vbo_strategy(
            name="MinimalVBO",
            use_trend_filter=False,
            use_noise_filter=False,
        )
    elif strategy == "legacy":
        strategy_obj = create_vbo_strategy(
            name="LegacyBT",
            sma_period=5,
            trend_sma_period=10,
            short_noise_period=5,
            long_noise_period=10,
            use_trend_filter=True,
            use_noise_filter=True,
            exclude_current=True,
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Create config
    config = BacktestConfig(
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        slippage_rate=fee_rate,  # Use same as fee rate
        max_slots=max_slots,
        use_cache=not no_cache,
    )

    # Run backtest
    result = run_backtest(
        strategy=strategy_obj,
        tickers=ticker_list,
        interval=interval,
        config=config,
    )

    # Print summary
    logger.info("\n=== Backtest Results ===")
    period_days = (result.dates[-1] - result.dates[0]).days if len(result.dates) > 0 else 0
    logger.info(f"Period: {period_days} days")
    logger.info(f"Total Return: {result.total_return:.2f}%")
    logger.info(f"CAGR: {result.cagr:.2f}%")
    logger.info(f"MDD: {result.mdd:.2f}%")
    logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    logger.info(f"Calmar Ratio: {result.calmar_ratio:.2f}")
    logger.info(f"Trade Count: {result.total_trades}")
    logger.info(f"Win Rate: {result.win_rate:.2f}%")
    logger.info(f"Profit Factor: {result.profit_factor:.2f}")

    # Generate report if output specified
    if output:
        from pathlib import Path

        from src.backtester.report import generate_report

        save_path = Path(output) if isinstance(output, str) else output
        generate_report(result, save_path=save_path, show=False)
        logger.info(f"\nReport saved to: {save_path}")
