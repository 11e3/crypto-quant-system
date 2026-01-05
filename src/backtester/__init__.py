"""Backtester package."""

from src.backtester.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestResult,
    Trade,
    VectorizedBacktestEngine,
    run_backtest,
)
from src.backtester.report import (
    BacktestReport,
    PerformanceMetrics,
    generate_report,
)

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "BacktestReport",
    "PerformanceMetrics",
    "Trade",
    "VectorizedBacktestEngine",
    "generate_report",
    "run_backtest",
]
