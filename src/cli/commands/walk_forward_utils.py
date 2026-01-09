"""
Walk-forward CLI helper functions.
"""

from pathlib import Path
from typing import Any

from src.backtester.wfa.walk_forward import WalkForwardResult
from src.strategies.volatility_breakout import create_vbo_strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_range(range_str: str) -> list[int]:
    """Parse comma-separated range string to list of ints."""
    return [int(x.strip()) for x in range_str.split(",")]


def create_strategy_factory(
    strategy: str,
) -> "type[Any]":
    """Create strategy factory function based on strategy type."""

    def factory(params: dict[str, int]) -> Any:
        name_prefix = "VBO" if strategy == "vanilla" else "Legacy"
        exclude_current = strategy != "vanilla"

        return create_vbo_strategy(
            name=f"{name_prefix}_{params['sma_period']}_{params['trend_sma_period']}",
            sma_period=params["sma_period"],
            trend_sma_period=params["trend_sma_period"],
            short_noise_period=params.get("short_noise_period", params["sma_period"]),
            long_noise_period=params.get("long_noise_period", params["trend_sma_period"]),
            exclude_current=exclude_current,
            use_trend_filter=True,
            use_noise_filter=True,
        )

    return factory  # type: ignore[return-value]


def print_walk_forward_results(result: WalkForwardResult) -> None:
    """Print walk-forward analysis results to console."""
    logger.info("\n=== Walk-Forward Analysis Results ===\n")
    logger.info(f"Total Periods: {result.total_periods}")
    logger.info(f"Positive Periods: {result.positive_periods}")
    logger.info(f"Consistency Rate: {result.consistency_rate:.1f}%")
    logger.info("\nAverage Test Metrics:")
    logger.info(f"  CAGR: {result.avg_test_cagr:.2f}%")
    logger.info(f"  Sharpe Ratio: {result.avg_test_sharpe:.2f}")
    logger.info(f"  MDD: {result.avg_test_mdd:.2f}%")
    logger.info(f"\nAverage Optimization CAGR: {result.avg_optimization_cagr:.2f}%")


def print_period_details(result: WalkForwardResult) -> None:
    """Print period details to console."""
    logger.info("\n=== Period Details ===")
    for period in result.periods:
        if period.test_result:
            logger.info(
                f"Period {period.period_num}: "
                f"Test CAGR={period.test_result.cagr:.2f}%, "
                f"Sharpe={period.test_result.sharpe_ratio:.2f}, "
                f"MDD={period.test_result.mdd:.2f}%"
            )
            if period.optimization_result:
                logger.info(
                    f"  Best params: {period.optimization_result.best_params}, "
                    f"score: {period.optimization_result.best_score:.4f}"
                )


def save_walk_forward_report(result: WalkForwardResult, output_path: Path) -> None:
    """Save walk-forward analysis report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Walk-Forward Analysis Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Periods: {result.total_periods}\n")
        f.write(f"Positive Periods: {result.positive_periods}\n")
        f.write(f"Consistency Rate: {result.consistency_rate:.1f}%\n\n")
        f.write(f"Average Test CAGR: {result.avg_test_cagr:.2f}%\n")
        f.write(f"Average Test Sharpe: {result.avg_test_sharpe:.2f}\n")
        f.write(f"Average Test MDD: {result.avg_test_mdd:.2f}%\n\n")
        f.write("Period Details:\n")
        f.write("-" * 60 + "\n")
        for period in result.periods:
            if period.test_result:
                f.write(f"Period {period.period_num} ({period.test_start} to {period.test_end}):\n")
                f.write(f"  CAGR: {period.test_result.cagr:.2f}%\n")
                f.write(f"  Sharpe: {period.test_result.sharpe_ratio:.2f}\n")
                f.write(f"  MDD: {period.test_result.mdd:.2f}%\n")
                if period.optimization_result:
                    f.write(f"  Best params: {period.optimization_result.best_params}\n")
                f.write("\n")

    logger.info(f"\nReport saved: {output_path}")


__all__ = [
    "parse_range",
    "create_strategy_factory",
    "print_walk_forward_results",
    "print_period_details",
    "save_walk_forward_report",
]
