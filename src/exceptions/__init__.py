"""
Custom exceptions for the trading system.

Provides a hierarchical exception structure for better error handling.
"""

from src.exceptions.base import TradingSystemError
from src.exceptions.data import (
    DataSourceConnectionError,
    DataSourceError,
    DataSourceNotFoundError,
)
from src.exceptions.exchange import (
    ExchangeAuthenticationError,
    ExchangeConnectionError,
    ExchangeError,
    ExchangeOrderError,
    InsufficientBalanceError,
)
from src.exceptions.order import (
    OrderError,
    OrderExecutionError,
    OrderNotFoundError,
)
from src.exceptions.strategy import (
    StrategyConfigurationError,
    StrategyError,
    StrategyExecutionError,
)

__all__ = [
    # Base
    "TradingSystemError",
    # Exchange
    "ExchangeError",
    "ExchangeConnectionError",
    "ExchangeAuthenticationError",
    "ExchangeOrderError",
    "InsufficientBalanceError",
    # Data
    "DataSourceError",
    "DataSourceConnectionError",
    "DataSourceNotFoundError",
    # Order
    "OrderError",
    "OrderNotFoundError",
    "OrderExecutionError",
    # Strategy
    "StrategyError",
    "StrategyConfigurationError",
    "StrategyExecutionError",
]
