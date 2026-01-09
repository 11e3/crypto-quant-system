"""
Backtester engine package.

Contains different backtesting engine implementations:
- EventDrivenBacktestEngine: Clear, debuggable event-driven approach
- VectorizedBacktestEngine: High-performance vectorized approach
"""

from src.backtester.engine.backtest_runner import run_backtest
from src.backtester.engine.event_driven import EventDrivenBacktestEngine
from src.backtester.engine.vectorized import VectorizedBacktestEngine
from src.backtester.models import BacktestConfig, BacktestResult, Trade

# Backward compatibility aliases
SimpleBacktestEngine = EventDrivenBacktestEngine
BacktestEngine = VectorizedBacktestEngine

__all__ = [
    "EventDrivenBacktestEngine",
    "VectorizedBacktestEngine",
    "SimpleBacktestEngine",  # Deprecated alias
    "BacktestEngine",  # Backward compatibility
    "run_backtest",
    "BacktestConfig",
    "BacktestResult",
    "Trade",
]
