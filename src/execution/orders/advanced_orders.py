"""
Advanced order types for risk management.

Supports:
- Stop Loss: Automatically sell when price drops below threshold
- Take Profit: Automatically sell when price reaches target
- Trailing Stop: Automatically adjust stop loss as price moves favorably

This module re-exports models for backward compatibility:
- OrderType from advanced_orders_models
- AdvancedOrder from advanced_orders_models
"""

from datetime import date

from src.execution.orders.advanced_orders_check import (
    check_stop_loss,
    check_take_profit,
    update_trailing_stop,
)
from src.execution.orders.advanced_orders_factory import (
    create_stop_loss_order,
    create_take_profit_order,
    create_trailing_stop_order,
)
from src.execution.orders.advanced_orders_models import AdvancedOrder, OrderType
from src.utils.logger import get_logger

__all__ = [
    "OrderType",
    "AdvancedOrder",
    "AdvancedOrderManager",
]

logger = get_logger(__name__)


class AdvancedOrderManager:
    """
    Manages advanced orders (stop loss, take profit, trailing stop).

    Tracks conditional orders and checks if they should be triggered.
    """

    def __init__(self) -> None:
        """Initialize advanced order manager."""
        self.orders: dict[str, AdvancedOrder] = {}  # order_id -> AdvancedOrder

    def create_stop_loss(
        self,
        ticker: str,
        entry_price: float,
        entry_date: date,
        amount: float,
        stop_loss_price: float | None = None,
        stop_loss_pct: float | None = None,
    ) -> AdvancedOrder:
        """Create a stop loss order. See advanced_orders_factory for details."""
        order = create_stop_loss_order(
            ticker=ticker,
            entry_price=entry_price,
            entry_date=entry_date,
            amount=amount,
            order_count=len(self.orders),
            stop_loss_price=stop_loss_price,
            stop_loss_pct=stop_loss_pct,
        )
        self.orders[order.order_id] = order
        return order

    def create_take_profit(
        self,
        ticker: str,
        entry_price: float,
        entry_date: date,
        amount: float,
        take_profit_price: float | None = None,
        take_profit_pct: float | None = None,
    ) -> AdvancedOrder:
        """Create a take profit order. See advanced_orders_factory for details."""
        order = create_take_profit_order(
            ticker=ticker,
            entry_price=entry_price,
            entry_date=entry_date,
            amount=amount,
            order_count=len(self.orders),
            take_profit_price=take_profit_price,
            take_profit_pct=take_profit_pct,
        )
        self.orders[order.order_id] = order
        return order

    def create_trailing_stop(
        self,
        ticker: str,
        entry_price: float,
        entry_date: date,
        amount: float,
        trailing_stop_pct: float,
        initial_stop_loss_pct: float | None = None,
    ) -> AdvancedOrder:
        """Create a trailing stop order. See advanced_orders_factory for details."""
        order = create_trailing_stop_order(
            ticker=ticker,
            entry_price=entry_price,
            entry_date=entry_date,
            amount=amount,
            order_count=len(self.orders),
            trailing_stop_pct=trailing_stop_pct,
            initial_stop_loss_pct=initial_stop_loss_pct,
        )
        self.orders[order.order_id] = order
        return order

    def check_orders(
        self,
        ticker: str,
        current_price: float,
        current_date: date,
        low_price: float | None = None,
        high_price: float | None = None,
    ) -> list[AdvancedOrder]:
        """
        Check if any orders should be triggered.

        Args:
            ticker: Trading pair symbol
            current_price: Current market price
            current_date: Current date
            low_price: Low price of the period (for stop loss checking)
            high_price: High price of the period (for take profit checking)

        Returns:
            List of triggered orders
        """
        triggered_orders: list[AdvancedOrder] = []

        check_low = low_price if low_price is not None else current_price
        check_high = high_price if high_price is not None else current_price

        for order in self.orders.values():
            if not order.is_active or order.is_triggered or order.ticker != ticker:
                continue

            update_trailing_stop(order, check_high)

            if check_stop_loss(order, check_low, current_date):
                triggered_orders.append(order)
                continue

            if check_take_profit(order, check_high, current_date):
                triggered_orders.append(order)
                continue

        return triggered_orders

    def get_active_orders(self, ticker: str | None = None) -> list[AdvancedOrder]:
        """
        Get active orders, optionally filtered by ticker.

        Args:
            ticker: Optional ticker to filter by

        Returns:
            List of active orders
        """
        orders = [o for o in self.orders.values() if o.is_active and not o.is_triggered]
        if ticker:
            orders = [o for o in orders if o.ticker == ticker]
        return orders

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an advanced order.

        Args:
            order_id: Order identifier

        Returns:
            True if cancelled successfully
        """
        if order_id in self.orders:
            self.orders[order_id].is_active = False
            logger.info(f"Cancelled advanced order: {order_id}")
            return True
        return False

    def cancel_all_orders(self, ticker: str | None = None) -> int:
        """
        Cancel all orders, optionally filtered by ticker.

        Args:
            ticker: Optional ticker to filter by

        Returns:
            Number of orders cancelled
        """
        count = 0
        for order in self.orders.values():
            if ticker and order.ticker != ticker:
                continue
            if order.is_active:
                order.is_active = False
                count += 1

        if count > 0:
            logger.info(
                f"Cancelled {count} advanced order(s)" + (f" for {ticker}" if ticker else "")
            )
        return count
