"""
Parallel backtesting support.

Enables concurrent execution of multiple backtests for:
- Multiple strategies
- Parameter optimization
- Strategy comparison
"""

import multiprocessing as mp
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.backtester.engine import run_backtest
from src.backtester.models import BacktestConfig, BacktestResult
from src.backtester.parallel_utils import compare_strategies as compare_strategies
from src.backtester.parallel_utils import optimize_parameters as optimize_parameters
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParallelBacktestTask:
    """Single backtest task for parallel execution."""

    name: str
    strategy: Strategy
    tickers: list[str]
    interval: str
    config: BacktestConfig
    params: dict[str, Any] | None = None  # Store parameters for optimization
    start_date: date | None = None  # Start date for date filtering
    end_date: date | None = None  # End date for date filtering

    def __repr__(self) -> str:
        return f"ParallelBacktestTask(name={self.name}, tickers={self.tickers})"


def _run_single_backtest(task: ParallelBacktestTask) -> tuple[str, BacktestResult]:
    """
    Run a single backtest (worker function for multiprocessing).

    Args:
        task: Backtest task to execute

    Returns:
        Tuple of (task_name, BacktestResult)
    """
    try:
        logger.info(f"Starting backtest: {task.name}")
        result = run_backtest(
            strategy=task.strategy,
            tickers=task.tickers,
            interval=task.interval,
            config=task.config,
            start_date=task.start_date,
            end_date=task.end_date,
        )
        logger.info(f"Completed backtest: {task.name}")
        return (task.name, result)
    except Exception as e:
        logger.error(f"Error in backtest {task.name}: {e}", exc_info=True)
        # Return empty result on error
        empty_result = BacktestResult()
        empty_result.strategy_name = task.name
        return (task.name, empty_result)


class ParallelBacktestRunner:
    """
    Runs multiple backtests in parallel.

    Supports concurrent execution of multiple strategies or parameter combinations.
    """

    def __init__(self, n_workers: int | None = None) -> None:
        """
        Initialize parallel backtest runner.

        Args:
            n_workers: Number of parallel workers. Defaults to CPU count - 1.
        """
        if n_workers is None:
            n_workers = max(1, mp.cpu_count() - 1)
        self.n_workers = n_workers
        logger.info(f"Initialized ParallelBacktestRunner with {n_workers} workers")

    def run(
        self,
        tasks: list[ParallelBacktestTask],
        progress_callback: Callable[[str, BacktestResult], None] | None = None,
    ) -> dict[str, BacktestResult]:
        """
        Run multiple backtests in parallel.

        Args:
            tasks: List of backtest tasks to execute
            progress_callback: Optional callback function called after each task completes
                              Signature: (task_name: str, result: BacktestResult) -> None

        Returns:
            Dictionary mapping task names to BacktestResult objects
        """
        if not tasks:
            logger.warning("No tasks provided to parallel backtest runner")
            return {}

        logger.info(f"Running {len(tasks)} backtests with {self.n_workers} workers")

        # Use multiprocessing Pool for parallel execution
        with mp.Pool(processes=self.n_workers) as pool:
            results = pool.map(_run_single_backtest, tasks)

        # Convert to dictionary
        results_dict: dict[str, BacktestResult] = {}
        for task_name, result in results:
            results_dict[task_name] = result
            if progress_callback:
                progress_callback(task_name, result)

        logger.info(f"Completed {len(results_dict)} backtests")
        return results_dict

    def run_sequential(
        self,
        tasks: list[ParallelBacktestTask],
        progress_callback: Callable[[str, BacktestResult], None] | None = None,
    ) -> dict[str, BacktestResult]:
        """
        Run backtests sequentially (useful for debugging).

        Args:
            tasks: List of backtest tasks to execute
            progress_callback: Optional callback function called after each task completes

        Returns:
            Dictionary mapping task names to BacktestResult objects
        """
        if not tasks:
            logger.warning("No tasks provided to sequential backtest runner")
            return {}

        logger.info(f"Running {len(tasks)} backtests sequentially")

        results_dict: dict[str, BacktestResult] = {}
        for task in tasks:
            task_name, result = _run_single_backtest(task)
            results_dict[task_name] = result
            if progress_callback:
                progress_callback(task_name, result)

        logger.info(f"Completed {len(results_dict)} backtests")
        return results_dict


__all__ = [
    "ParallelBacktestTask",
    "ParallelBacktestRunner",
    "compare_strategies",
    "optimize_parameters",
]
