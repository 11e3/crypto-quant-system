"""
Execution package for live trading.

Contains trading bot, order management, and position tracking.
"""

from src.execution.bot.bot_facade import TradingBotFacade, create_bot
from src.execution.order_manager import OrderManager
from src.execution.position_manager import PositionManager
from src.execution.signal_handler import SignalHandler

__all__ = [
    "TradingBotFacade",
    "create_bot",
    "OrderManager",
    "PositionManager",
    "SignalHandler",
]
