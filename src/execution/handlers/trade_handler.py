"""
Trade event handler.

Handles order and position events for trade execution tracking.
"""

from src.execution.event_bus import get_event_bus
from src.execution.events import Event, EventType, OrderEvent, PositionEvent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradeHandler:
    """
    Handler for trade-related events.

    Tracks orders and positions based on events.
    """

    def __init__(self) -> None:
        """Initialize trade handler."""
        self.event_bus = get_event_bus()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers."""
        self.event_bus.subscribe(EventType.ORDER_PLACED, self._handle_order_placed)
        self.event_bus.subscribe(EventType.ORDER_FILLED, self._handle_order_filled)
        self.event_bus.subscribe(EventType.ORDER_FAILED, self._handle_order_failed)
        self.event_bus.subscribe(EventType.POSITION_OPENED, self._handle_position_opened)
        self.event_bus.subscribe(EventType.POSITION_CLOSED, self._handle_position_closed)

    def _handle_order_placed(self, event: Event) -> None:
        """Handle order placed event."""
        if isinstance(event, OrderEvent):
            logger.info(
                f"Order placed: {event.side.upper()} {event.ticker} "
                f"@ {event.price:.0f} (amount: {event.amount:.6f})"
            )

    def _handle_order_filled(self, event: Event) -> None:
        """Handle order filled event."""
        if isinstance(event, OrderEvent):
            logger.info(
                f"Order filled: {event.order_id} - {event.side.upper()} {event.ticker} "
                f"@ {event.price:.0f}"
            )

    def _handle_order_failed(self, event: Event) -> None:
        """Handle order failed event."""
        if isinstance(event, OrderEvent):
            logger.error(
                f"Order failed: {event.order_id} - {event.side.upper()} {event.ticker} - {event.status}"
            )

    def _handle_position_opened(self, event: Event) -> None:
        """Handle position opened event."""
        if isinstance(event, PositionEvent):
            logger.info(
                f"Position opened: {event.ticker} @ {event.entry_price:.0f} "
                f"(amount: {event.amount:.6f})"
            )

    def _handle_position_closed(self, event: Event) -> None:
        """Handle position closed event."""
        if isinstance(event, PositionEvent):
            logger.info(
                f"Position closed: {event.ticker} - PnL: {event.pnl:.0f} KRW ({event.pnl_pct:.2f}%)"
            )
