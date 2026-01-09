"""
Factory functions for creating advanced orders.
"""

from datetime import date

from src.execution.orders.advanced_orders_models import AdvancedOrder, OrderType
from src.utils.logger import get_logger

__all__ = [
    "create_stop_loss_order",
    "create_take_profit_order",
    "create_trailing_stop_order",
]

logger = get_logger(__name__)


def create_stop_loss_order(
    ticker: str,
    entry_price: float,
    entry_date: date,
    amount: float,
    order_count: int,
    stop_loss_price: float | None = None,
    stop_loss_pct: float | None = None,
) -> AdvancedOrder:
    """
    Create a stop loss order.

    Args:
        ticker: Trading pair symbol
        entry_price: Entry price of the position
        entry_date: Entry date
        amount: Position amount
        order_count: Current order count for ID generation
        stop_loss_price: Absolute stop loss price
        stop_loss_pct: Stop loss as percentage below entry (e.g., 0.05 = 5%)

    Returns:
        AdvancedOrder instance

    Raises:
        ValueError: If neither stop_loss_price nor stop_loss_pct is provided
    """
    if stop_loss_price is None and stop_loss_pct is None:
        raise ValueError("Either stop_loss_price or stop_loss_pct must be provided")

    if stop_loss_price is None and stop_loss_pct is not None:
        stop_loss_price = entry_price * (1 - stop_loss_pct)

    order_id = f"stop_loss_{ticker}_{entry_date}_{order_count}"
    order = AdvancedOrder(
        order_id=order_id,
        ticker=ticker,
        order_type=OrderType.STOP_LOSS,
        entry_price=entry_price,
        entry_date=entry_date,
        amount=amount,
        stop_loss_price=stop_loss_price,
        stop_loss_pct=stop_loss_pct,
    )

    logger.info(
        f"Created stop loss order: {ticker} @ {entry_price:.0f}, stop loss @ {stop_loss_price:.0f}"
    )
    return order


def create_take_profit_order(
    ticker: str,
    entry_price: float,
    entry_date: date,
    amount: float,
    order_count: int,
    take_profit_price: float | None = None,
    take_profit_pct: float | None = None,
) -> AdvancedOrder:
    """
    Create a take profit order.

    Args:
        ticker: Trading pair symbol
        entry_price: Entry price of the position
        entry_date: Entry date
        amount: Position amount
        order_count: Current order count for ID generation
        take_profit_price: Absolute take profit price
        take_profit_pct: Take profit as percentage above entry (e.g., 0.10 = 10%)

    Returns:
        AdvancedOrder instance

    Raises:
        ValueError: If neither take_profit_price nor take_profit_pct is provided
    """
    if take_profit_price is None and take_profit_pct is None:
        raise ValueError("Either take_profit_price or take_profit_pct must be provided")

    if take_profit_price is None and take_profit_pct is not None:
        take_profit_price = entry_price * (1 + take_profit_pct)

    order_id = f"take_profit_{ticker}_{entry_date}_{order_count}"
    order = AdvancedOrder(
        order_id=order_id,
        ticker=ticker,
        order_type=OrderType.TAKE_PROFIT,
        entry_price=entry_price,
        entry_date=entry_date,
        amount=amount,
        take_profit_price=take_profit_price,
        take_profit_pct=take_profit_pct,
    )

    logger.info(
        f"Created take profit order: {ticker} @ {entry_price:.0f}, "
        f"take profit @ {take_profit_price:.0f}"
    )
    return order


def create_trailing_stop_order(
    ticker: str,
    entry_price: float,
    entry_date: date,
    amount: float,
    order_count: int,
    trailing_stop_pct: float,
    initial_stop_loss_pct: float | None = None,
) -> AdvancedOrder:
    """
    Create a trailing stop order.

    Args:
        ticker: Trading pair symbol
        entry_price: Entry price of the position
        entry_date: Entry date
        amount: Position amount
        order_count: Current order count for ID generation
        trailing_stop_pct: Percentage to trail from peak (e.g., 0.05 = 5%)
        initial_stop_loss_pct: Initial stop loss percentage (defaults to trailing_stop_pct)

    Returns:
        AdvancedOrder instance
    """
    if initial_stop_loss_pct is None:
        initial_stop_loss_pct = trailing_stop_pct

    initial_stop_loss_price = entry_price * (1 - initial_stop_loss_pct)

    order_id = f"trailing_stop_{ticker}_{entry_date}_{order_count}"
    order = AdvancedOrder(
        order_id=order_id,
        ticker=ticker,
        order_type=OrderType.TRAILING_STOP,
        entry_price=entry_price,
        entry_date=entry_date,
        amount=amount,
        stop_loss_price=initial_stop_loss_price,
        stop_loss_pct=initial_stop_loss_pct,
        trailing_stop_pct=trailing_stop_pct,
        highest_price=entry_price,
    )

    logger.info(
        f"Created trailing stop order: {ticker} @ {entry_price:.0f}, "
        f"trailing {trailing_stop_pct * 100:.1f}% from peak"
    )
    return order
