"""
Event definitions for event-driven architecture.

Events represent significant occurrences in the trading system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events in the trading system."""

    # Signal events
    ENTRY_SIGNAL = "entry_signal"
    EXIT_SIGNAL = "exit_signal"
    SIGNAL_GENERATED = "signal_generated"

    # Order events
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FAILED = "order_failed"

    # Position events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"

    # Market events
    PRICE_UPDATE = "price_update"
    TICKER_UPDATE = "ticker_update"

    # System events
    DAILY_RESET = "daily_reset"
    TARGET_RECALCULATED = "target_recalculated"
    ERROR = "error"


@dataclass
class Event:
    """
    Base event class for all trading system events.

    All events inherit from this base class and add specific data fields.
    """

    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""  # Source component that generated the event
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Event({self.event_type.value}, source={self.source}, time={self.timestamp})"


@dataclass
class SignalEvent(Event):
    """Event for trading signals."""

    ticker: str = ""
    signal_type: str = ""  # "entry" or "exit"
    price: float = 0.0
    target_price: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class OrderEvent(Event):
    """Event for order-related actions."""

    order_id: str = ""
    ticker: str = ""
    side: str = ""  # "buy" or "sell"
    amount: float = 0.0
    price: float = 0.0
    status: str = ""  # "pending", "filled", "cancelled", "failed"


@dataclass
class PositionEvent(Event):
    """Event for position changes."""

    ticker: str = ""
    action: str = ""  # "opened", "closed", "updated"
    entry_price: float = 0.0
    amount: float = 0.0
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class MarketEvent(Event):
    """Event for market data updates."""

    ticker: str = ""
    price: float = 0.0
    volume: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0


@dataclass
class SystemEvent(Event):
    """Event for system-level operations."""

    action: str = ""  # "daily_reset", "target_recalculated", etc.
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorEvent(Event):
    """Event for errors and exceptions."""

    error_type: str = ""
    error_message: str = ""
    exception: Exception | None = None
    context: dict[str, Any] = field(default_factory=dict)
