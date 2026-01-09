"""
Parallel backtest utility functions.

Provides convenience functions for strategy comparison and parameter optimization.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import product
from typing import TYPE_CHECKING, Any

from src.backtester.models import BacktestConfig, BacktestResult
from src.strategies.base import Strategy
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.backtester.parallel import ParallelBacktestTask

__all__ = ["compare_strategies", "optimize_parameters"]

logger = get_logger(__name__)


def compare_strategies(
    strategies: list[Strategy],
    tickers: list[str],
    interval: str,
    config: BacktestConfig,
    n_workers: int | None = None,
) -> dict[str, BacktestResult]:
    """
    Compare multiple strategies using parallel backtesting.

    Args:
        strategies: List of strategies to compare
        tickers: List of tickers to backtest
        interval: Data interval
        config: Backtest configuration
        n_workers: Number of parallel workers

    Returns:
        Dictionary mapping strategy names to BacktestResult objects
    """
    from src.backtester.parallel import ParallelBacktestRunner, ParallelBacktestTask

    tasks = [
        ParallelBacktestTask(
            name=strategy.name,
            strategy=strategy,
            tickers=tickers,
            interval=interval,
            config=config,
        )
        for strategy in strategies
    ]

    runner = ParallelBacktestRunner(n_workers=n_workers)
    return runner.run(tasks)


def optimize_parameters(
    strategy_factory: Callable[[dict[str, Any]], Strategy],
    param_grid: dict[str, list[Any]],
    tickers: list[str],
    interval: str,
    config: BacktestConfig,
    n_workers: int | None = None,
) -> dict[str, BacktestResult]:
    """
    Optimize strategy parameters using grid search with parallel backtesting.

    Args:
        strategy_factory: Function that creates a strategy from parameters
        param_grid: Dictionary mapping parameter names to lists of values
        tickers: List of tickers to backtest
        interval: Data interval
        config: Backtest configuration
        n_workers: Number of parallel workers

    Returns:
        Dictionary mapping parameter combination names to BacktestResult objects
    """
    from src.backtester.parallel import ParallelBacktestRunner, ParallelBacktestTask

    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(product(*param_values))

    tasks: list[ParallelBacktestTask] = []
    for combo in combinations:
        params = dict(zip(param_names, combo, strict=False))
        strategy = strategy_factory(params)
        task_name = f"{strategy.name}_{'_'.join(str(v) for v in combo)}"
        tasks.append(
            ParallelBacktestTask(
                name=task_name,
                strategy=strategy,
                tickers=tickers,
                interval=interval,
                config=config,
            )
        )

    logger.info(f"Generated {len(tasks)} parameter combinations for optimization")

    runner = ParallelBacktestRunner(n_workers=n_workers)
    return runner.run(tasks)
