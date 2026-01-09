"""
Parameter optimization for trading strategies.

Provides grid search and random search optimization methods.
"""

from collections.abc import Callable
from typing import Any

from src.backtester.models import BacktestConfig
from src.backtester.optimization_models import OptimizationResult
from src.backtester.optimization_search import grid_search, random_search
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ParameterOptimizer:
    """
    Optimize strategy parameters using various search methods.

    Supports:
    - Grid Search: Test all parameter combinations (thorough but slow)
    - Random Search: Sample random combinations (fast but may miss optimum)

    Example:
        >>> optimizer = ParameterOptimizer(
        ...     strategy_factory=lambda p: VBO(**p),
        ...     tickers=["KRW-BTC"],
        ...     interval="day",
        ...     config=BacktestConfig(),
        ... )
        >>> result = optimizer.optimize({"sma": [10, 20, 30]}, metric="sharpe_ratio")
    """

    def __init__(
        self,
        strategy_factory: Callable[[dict[str, Any]], Strategy],
        tickers: list[str],
        interval: str,
        config: BacktestConfig,
        n_workers: int | None = None,
    ) -> None:
        """
        Initialize parameter optimizer.

        Args:
            strategy_factory: Function that creates a strategy from parameters
            tickers: List of tickers to backtest
            interval: Data interval (e.g., "day", "minute240")
            config: Backtest configuration
            n_workers: Number of parallel workers
        """
        self.strategy_factory = strategy_factory
        self.tickers = tickers
        self.interval = interval
        self.config = config
        self.n_workers = n_workers

    def optimize(
        self,
        param_grid: dict[str, list[Any]],
        metric: str = "sharpe_ratio",
        maximize: bool = True,
        method: str = "grid",
        n_iter: int = 100,
    ) -> OptimizationResult:
        """
        Optimize parameters using specified method.

        Args:
            param_grid: Parameter names to value lists mapping
            metric: Metric to optimize (sharpe_ratio, cagr, calmar_ratio, etc.)
            maximize: If True, maximize metric; if False, minimize
            method: Optimization method ('grid' or 'random')
            n_iter: Number of iterations for random search

        Returns:
            OptimizationResult with best parameters and results
        """
        if method == "grid":
            return grid_search(
                strategy_factory=self.strategy_factory,
                param_grid=param_grid,
                tickers=self.tickers,
                interval=self.interval,
                config=self.config,
                metric=metric,
                maximize=maximize,
                n_workers=self.n_workers,
            )
        elif method == "random":
            return random_search(
                strategy_factory=self.strategy_factory,
                param_grid=param_grid,
                tickers=self.tickers,
                interval=self.interval,
                config=self.config,
                metric=metric,
                maximize=maximize,
                n_iter=n_iter,
                n_workers=self.n_workers,
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")


def optimize_strategy_parameters(
    strategy_factory: Callable[[dict[str, Any]], Strategy],
    param_grid: dict[str, list[Any]],
    tickers: list[str],
    interval: str,
    config: BacktestConfig,
    metric: str = "sharpe_ratio",
    maximize: bool = True,
    method: str = "grid",
    n_iter: int = 100,
    n_workers: int | None = None,
) -> OptimizationResult:
    """
    Optimize strategy parameters (convenience function).

    Args:
        strategy_factory: Function that creates a strategy from parameters
        param_grid: Parameter names to value lists mapping
        tickers: List of tickers to backtest
        interval: Data interval
        config: Backtest configuration
        metric: Metric to optimize
        maximize: If True, maximize metric
        method: Optimization method ('grid' or 'random')
        n_iter: Number of iterations for random search
        n_workers: Number of parallel workers

    Returns:
        OptimizationResult with best parameters
    """
    optimizer = ParameterOptimizer(
        strategy_factory=strategy_factory,
        tickers=tickers,
        interval=interval,
        config=config,
        n_workers=n_workers,
    )

    return optimizer.optimize(
        param_grid=param_grid,
        metric=metric,
        maximize=maximize,
        method=method,
        n_iter=n_iter,
    )


__all__ = [
    "ParameterOptimizer",
    "OptimizationResult",
    "optimize_strategy_parameters",
]
