"""
Utility functions for optimization CLI command.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from src.backtester import BacktestConfig, OptimizationResult
from src.backtester.report_pkg.report import generate_report
from src.strategies.volatility_breakout import create_vbo_strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = [
    "parse_range",
    "create_strategy_factory",
    "print_optimization_results",
    "print_top_results",
    "save_optimization_report",
]


def parse_range(range_str: str) -> list[int]:
    """Parse comma-separated range string to list of integers."""
    return [int(x.strip()) for x in range_str.split(",")]


def create_strategy_factory(strategy: str) -> Any:
    """Create strategy factory function for given strategy type."""

    def create_strategy(params: dict[str, int]) -> Any:
        sma_period = params["sma_period"]
        trend_sma_period = params["trend_sma_period"]
        short_noise = params.get("short_noise_period", sma_period)
        long_noise = params.get("long_noise_period", trend_sma_period)

        if strategy == "vanilla":
            return create_vbo_strategy(
                name=f"VBO_{sma_period}_{trend_sma_period}",
                sma_period=sma_period,
                trend_sma_period=trend_sma_period,
                short_noise_period=short_noise,
                long_noise_period=long_noise,
                exclude_current=False,
                use_trend_filter=True,
                use_noise_filter=True,
            )
        else:  # legacy
            return create_vbo_strategy(
                name=f"Legacy_{sma_period}_{trend_sma_period}",
                sma_period=sma_period,
                trend_sma_period=trend_sma_period,
                short_noise_period=short_noise,
                long_noise_period=long_noise,
                exclude_current=True,
                use_trend_filter=True,
                use_noise_filter=True,
            )

    return create_strategy


def print_optimization_results(result: OptimizationResult, metric: str) -> None:
    """Print optimization results summary."""
    logger.info("\n=== Optimization Results ===\n")
    logger.info(f"Best Parameters: {result.best_params}")
    logger.info(f"Best {metric}: {result.best_score:.4f}")
    logger.info("\nBest Result Metrics:")
    logger.info(f"  CAGR: {result.best_result.cagr:.2f}%")
    logger.info(f"  Total Return: {result.best_result.total_return:.2f}%")
    logger.info(f"  Sharpe Ratio: {result.best_result.sharpe_ratio:.2f}")
    logger.info(f"  Max Drawdown: {result.best_result.mdd:.2f}%")
    logger.info(f"  Win Rate: {result.best_result.win_rate:.2f}%")
    logger.info(f"  Total Trades: {result.best_result.total_trades}")


def print_top_results(result: OptimizationResult, metric: str, top_n: int = 5) -> None:
    """Print top N optimization results."""
    logger.info(f"\n=== Top {top_n} Results ===")
    logger.info(f"{'Rank':<6} {'Params':<30} {metric.capitalize():>15}")
    logger.info("-" * 60)
    for i, (params, _, score) in enumerate(result.all_results[:top_n], 1):
        params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        logger.info(f"{i:<6} {params_str:<30} {score:>15.4f}")


def save_optimization_report(
    result: OptimizationResult,
    output: str,
    config: BacktestConfig,
    tickers: list[str],
) -> None:
    """Save optimization report to file."""
    output_path = Path(output)
    if output_path.is_dir() or not output_path.suffix:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path / f"optimization_{timestamp}.html"
    else:
        output_path = Path(output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_report(
        result.best_result,
        save_path=output_path,
        show=False,
        format="html",
        strategy_obj=None,
        config=config,
        tickers=tickers,
    )
    logger.info(f"\nReport saved: {output_path}")
