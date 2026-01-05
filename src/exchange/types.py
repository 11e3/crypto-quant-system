"""
Common types for exchange operations.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    """Order side (buy or sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Balance:
    """Account balance for a currency."""

    currency: str
    balance: float
    locked: float = 0.0  # Amount locked in orders

    @property
    def available(self) -> float:
        """Available balance (total - locked)."""
        return self.balance - self.locked


@dataclass
class Ticker:
    """Market ticker information."""

    symbol: str
    price: float
    volume: float = 0.0
    timestamp: datetime | None = None


@dataclass
class Order:
    """Order information."""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: float | None = None  # None for market orders
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    filled_price: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED)
