"""
BotComponents container and related utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.exchange import Exchange
    from src.execution.handlers.notification_handler import NotificationHandler
    from src.execution.handlers.trade_handler import TradeHandler
    from src.execution.order_manager import OrderManager
    from src.execution.orders.advanced_orders import AdvancedOrderManager
    from src.execution.position_manager import PositionManager
    from src.execution.signal_handler import SignalHandler
    from src.strategies.volatility_breakout import VanillaVBO
    from src.utils.telegram import TelegramNotifier

__all__ = ["BotComponents"]


class BotComponents:
    """Container for bot components."""

    def __init__(
        self,
        exchange: Exchange,
        position_manager: PositionManager,
        order_manager: OrderManager,
        signal_handler: SignalHandler,
        strategy: VanillaVBO,
        advanced_order_manager: AdvancedOrderManager,
        telegram: TelegramNotifier,
        trade_handler: TradeHandler,
        notification_handler: NotificationHandler,
        event_bus: Any,
    ) -> None:
        """Initialize bot components."""
        self.exchange = exchange
        self.position_manager = position_manager
        self.order_manager = order_manager
        self.signal_handler = signal_handler
        self.strategy = strategy
        self.advanced_order_manager = advanced_order_manager
        self.telegram = telegram
        self.trade_handler = trade_handler
        self.notification_handler = notification_handler
        self.event_bus = event_bus
