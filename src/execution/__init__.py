"""
Execution package for live trading.

Contains trading bot, order management, and position tracking.
Also includes execution algorithms (TWAP, VWAP, market impact models).
"""

# Lazy imports to avoid cascade failures from optional dependencies (pyupbit)
# Bot-related imports require pyupbit; algorithms do not

__all__ = [
    "TradingBotFacade",
    "create_bot",
    "OrderManager",
    "PositionManager",
    "SignalHandler",
    # Execution algorithms
    "ExecutionAlgorithm",
    "OrderSlice",
    "ExecutionResult",
    "TWAPAlgorithm",
    "VWAPAlgorithm",
    "MarketImpactModel",
]


def __getattr__(name):
    """Lazy import to avoid loading pyupbit unless needed."""
    # Bot-related imports (require pyupbit)
    if name == "TradingBotFacade":
        from src.execution.bot.bot_facade import TradingBotFacade
        return TradingBotFacade
    elif name == "create_bot":
        from src.execution.bot.bot_facade import create_bot
        return create_bot
    elif name == "OrderManager":
        from src.execution.order_manager import OrderManager
        return OrderManager
    elif name == "PositionManager":
        from src.execution.position_manager import PositionManager
        return PositionManager
    elif name == "SignalHandler":
        from src.execution.signal_handler import SignalHandler
        return SignalHandler
    # Algorithm imports (no pyupbit dependency)
    elif name == "ExecutionAlgorithm":
        from src.execution.algorithms.base import ExecutionAlgorithm
        return ExecutionAlgorithm
    elif name == "OrderSlice":
        from src.execution.algorithms.base import OrderSlice
        return OrderSlice
    elif name == "ExecutionResult":
        from src.execution.algorithms.base import ExecutionResult
        return ExecutionResult
    elif name == "TWAPAlgorithm":
        from src.execution.algorithms.twap import TWAPAlgorithm
        return TWAPAlgorithm
    elif name == "VWAPAlgorithm":
        from src.execution.algorithms.vwap import VWAPAlgorithm
        return VWAPAlgorithm
    elif name == "MarketImpactModel":
        from src.execution.algorithms.market_impact import MarketImpactModel
        return MarketImpactModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
