"""
Abstract base class for exchange implementations.
"""

from abc import ABC, abstractmethod

import pandas as pd

from src.exchange.types import Balance, Order, Ticker


class Exchange(ABC):
    """
    Abstract interface for cryptocurrency exchanges.

    This interface allows the trading system to work with any exchange
    by implementing exchange-specific logic in subclasses.
    """

    @abstractmethod
    def get_balance(self, currency: str) -> Balance:
        """
        Get balance for a currency.

        Args:
            currency: Currency code (e.g., 'KRW', 'BTC')

        Returns:
            Balance object with available and locked amounts

        Raises:
            ExchangeError: If API call fails
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')

        Returns:
            Current market price

        Raises:
            ExchangeError: If API call fails
        """
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """
        Get ticker information for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')

        Returns:
            Ticker object with price and volume information

        Raises:
            ExchangeError: If API call fails
        """
        pass

    @abstractmethod
    def buy_market_order(self, symbol: str, amount: float) -> Order:
        """
        Place a market buy order.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')
            amount: Amount to buy (in quote currency, e.g., KRW)

        Returns:
            Order object with order details

        Raises:
            ExchangeError: If order placement fails
        """
        pass

    @abstractmethod
    def sell_market_order(self, symbol: str, amount: float) -> Order:
        """
        Place a market sell order.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')
            amount: Amount to sell (in base currency, e.g., BTC)

        Returns:
            Order object with order details

        Raises:
            ExchangeError: If order placement fails
        """
        pass

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        interval: str = "day",
        count: int = 200,
    ) -> pd.DataFrame | None:
        """
        Get OHLCV (candlestick) data.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')
            interval: Data interval (e.g., 'day', 'minute240')
            count: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data, or None on error

        Raises:
            ExchangeError: If API call fails
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Order:
        """
        Get status of an existing order.

        Args:
            order_id: Order identifier

        Returns:
            Order object with current status

        Raises:
            ExchangeError: If API call fails
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order identifier

        Returns:
            True if cancellation successful

        Raises:
            ExchangeError: If cancellation fails
        """
        pass


# Exceptions are now defined in src.exceptions.exchange
# Imported above for backward compatibility
