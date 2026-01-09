"""Backtester package."""

from src.backtester.analysis.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulator,
    run_monte_carlo,
)
from src.backtester.engine import (
    BacktestEngine,
    EventDrivenBacktestEngine,
    SimpleBacktestEngine,  # Deprecated alias
    VectorizedBacktestEngine,
    run_backtest,
)
from src.backtester.models import (
    BacktestConfig,
    BacktestResult,
    Trade,
)
from src.backtester.optimization import (
    OptimizationResult,
    ParameterOptimizer,
    optimize_strategy_parameters,
)
from src.backtester.parallel import (
    ParallelBacktestRunner,
    ParallelBacktestTask,
    compare_strategies,
    optimize_parameters,
)
from src.backtester.report_pkg.report import (
    BacktestReport,
    PerformanceMetrics,
    generate_report,
)
from src.backtester.wfa.walk_forward import (
    WalkForwardAnalyzer,
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward_analysis,
)

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "BacktestReport",
    "PerformanceMetrics",
    "Trade",
    "VectorizedBacktestEngine",
    "SimpleBacktestEngine",
    "generate_report",
    "run_backtest",
    "ParallelBacktestRunner",
    "ParallelBacktestTask",
    "compare_strategies",
    "optimize_parameters",
    "OptimizationResult",
    "ParameterOptimizer",
    "optimize_strategy_parameters",
    "MonteCarloResult",
    "MonteCarloSimulator",
    "run_monte_carlo",
    "WalkForwardAnalyzer",
    "WalkForwardPeriod",
    "WalkForwardResult",
    "run_walk_forward_analysis",
]
