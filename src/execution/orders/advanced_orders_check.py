"""
Advanced order checking logic.

Contains order trigger checking functions.
"""

from datetime import date

from src.execution.orders.advanced_orders_models import AdvancedOrder, OrderType
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_stop_loss(
    order: AdvancedOrder,
    check_low: float,
    current_date: date,
) -> bool:
    """
    Check if stop loss is triggered.

    Args:
        order: Order to check
        check_low: Low price to check against
        current_date: Current date

    Returns:
        True if triggered
    """
    if order.stop_loss_price is None:
        return False

    if check_low <= order.stop_loss_price:
        order.is_triggered = True
        order.is_active = False
        order.triggered_price = order.stop_loss_price
        order.triggered_date = current_date
        logger.info(
            f"Stop loss triggered: {order.ticker} @ {order.stop_loss_price:.0f} "
            f"(entry: {order.entry_price:.0f})"
        )
        return True

    return False


def check_take_profit(
    order: AdvancedOrder,
    check_high: float,
    current_date: date,
) -> bool:
    """
    Check if take profit is triggered.

    Args:
        order: Order to check
        check_high: High price to check against
        current_date: Current date

    Returns:
        True if triggered
    """
    if order.take_profit_price is None:
        return False

    if check_high >= order.take_profit_price:
        order.is_triggered = True
        order.is_active = False
        order.triggered_price = order.take_profit_price
        order.triggered_date = current_date
        logger.info(
            f"Take profit triggered: {order.ticker} @ {order.take_profit_price:.0f} "
            f"(entry: {order.entry_price:.0f})"
        )
        return True

    return False


def update_trailing_stop(
    order: AdvancedOrder,
    check_high: float,
) -> None:
    """
    Update trailing stop highest price and stop loss.

    Args:
        order: Order to update
        check_high: Current high price
    """
    if order.order_type != OrderType.TRAILING_STOP:
        return

    if order.highest_price is None or check_high > order.highest_price:
        order.highest_price = check_high
        if order.trailing_stop_pct is not None:
            order.stop_loss_price = order.highest_price * (1 - order.trailing_stop_pct)
            logger.debug(
                f"Updated trailing stop for {order.ticker}: "
                f"high={order.highest_price:.0f}, "
                f"stop={order.stop_loss_price:.0f}"
            )


__all__ = [
    "check_stop_loss",
    "check_take_profit",
    "update_trailing_stop",
]
