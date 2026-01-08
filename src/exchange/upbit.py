"""
Upbit exchange implementation.
"""

import logging
from datetime import datetime
from typing import cast

import pandas as pd
import pyupbit

from src.exceptions.exchange import (
    ExchangeConnectionError,
    ExchangeError,
    ExchangeOrderError,
    InsufficientBalanceError,
)
from src.exchange.base import Exchange
from src.exchange.types import Balance, Order, OrderSide, OrderStatus, OrderType, Ticker


def _get_logger() -> logging.Logger:
    """Lazy import logger to avoid circular imports."""
    from src.utils.logger import get_logger

    return get_logger(__name__)


class UpbitExchange(Exchange):
    """
    Upbit exchange implementation.

    Wraps pyupbit library to provide Exchange interface.
    """

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        Initialize Upbit exchange client.

        Args:
            access_key: Upbit API access key
            secret_key: Upbit API secret key

        Raises:
            ExchangeAuthenticationError: If credentials are invalid
        """
        try:
            self.client = pyupbit.Upbit(access_key, secret_key)
            # Test connection
            self.client.get_balances()
        except Exception as e:
            _get_logger().error(f"Failed to initialize Upbit client: {e}", exc_info=True)
            raise ExchangeConnectionError(f"Failed to connect to Upbit: {e}") from e

    def get_balance(self, currency: str) -> Balance:
        """
        Get balance for a currency.

        ⚠️ Performance Note:
        This method retrieves locked amounts by querying pending orders.
        For high-frequency calls or many assets, consider:
        1. Caching balance data with TTL
        2. Using batch balance queries
        3. Maintaining local position state

        Args:
            currency: Currency code (e.g., 'KRW', 'BTC')

        Returns:
            Balance object

        Raises:
            ExchangeError: If API call fails
        """
        try:
            balance = self.client.get_balance(currency)
            if balance is None:
                return Balance(currency=currency, balance=0.0, locked=0.0)

            # Get locked amount from pending orders
            # NOTE: This adds API call overhead. For production with many assets,
            # implement caching or use WebSocket updates
            locked = 0.0
            try:
                # Query waiting orders for this currency
                # This is a performance bottleneck for multi-asset portfolios
                orders = self.client.get_order(currency, state="wait")
                if orders and isinstance(orders, list):
                    for order in orders:
                        if isinstance(order, dict):
                            locked += float(order.get("locked", 0.0))
            except Exception as e:
                # If locked amount query fails, log but don't fail the whole call
                _get_logger().debug(f"Could not retrieve locked amount for {currency}: {e}")
                # Locked remains 0.0

            return Balance(currency=currency, balance=float(balance), locked=locked)
        except Exception as e:
            _get_logger().error(f"Error getting balance for {currency}: {e}", exc_info=True)
            raise ExchangeError(f"Failed to get balance for {currency}: {e}") from e

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
        try:
            price = pyupbit.get_current_price(symbol)
            if price is None:
                raise ExchangeError(f"No price data available for {symbol}")
            return float(price)
        except Exception as e:
            _get_logger().error(f"Error getting price for {symbol}: {e}", exc_info=True)
            raise ExchangeError(f"Failed to get price for {symbol}: {e}") from e

    def get_ticker(self, symbol: str) -> Ticker:
        """
        Get ticker information for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')

        Returns:
            Ticker object

        Raises:
            ExchangeError: If API call fails
        """
        try:
            ticker_data = pyupbit.get_ticker(symbol)
            if ticker_data is None:
                raise ExchangeError(f"No ticker data available for {symbol}")

            price = float(ticker_data.get("trade_price", 0.0))
            volume = float(ticker_data.get("acc_trade_volume_24h", 0.0))

            return Ticker(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=datetime.now(),
            )
        except Exception as e:
            _get_logger().error(f"Error getting ticker for {symbol}: {e}", exc_info=True)
            raise ExchangeError(f"Failed to get ticker for {symbol}: {e}") from e

    def buy_market_order(self, symbol: str, amount: float) -> Order:
        """
        Place a market buy order.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')
            amount: Amount to buy (in KRW)

        Returns:
            Order object

        Raises:
            InsufficientBalanceError: If insufficient balance
            ExchangeOrderError: If order placement fails
        """
        try:
            result = self.client.buy_market_order(symbol, amount)
            if not result or "uuid" not in result:
                raise ExchangeOrderError(f"Buy order failed: {result}")

            order_id = result["uuid"]
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                amount=amount,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                metadata=result,
            )
        except Exception as e:
            _get_logger().error(f"Error placing buy order for {symbol}: {e}", exc_info=True)
            if "insufficient" in str(e).lower():
                raise InsufficientBalanceError(f"Insufficient balance: {e}") from e
            raise ExchangeOrderError(f"Failed to place buy order: {e}") from e

    def sell_market_order(self, symbol: str, amount: float) -> Order:
        """
        Place a market sell order.

        Args:
            symbol: Trading pair symbol (e.g., 'KRW-BTC')
            amount: Amount to sell (in base currency, e.g., BTC)

        Returns:
            Order object

        Raises:
            InsufficientBalanceError: If insufficient balance
            ExchangeOrderError: If order placement fails
        """
        try:
            result = self.client.sell_market_order(symbol, amount)
            if not result or "uuid" not in result:
                raise ExchangeOrderError(f"Sell order failed: {result}")

            order_id = result["uuid"]
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=amount,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                metadata=result,
            )
        except Exception as e:
            _get_logger().error(f"Error placing sell order for {symbol}: {e}", exc_info=True)
            if "insufficient" in str(e).lower():
                raise InsufficientBalanceError(f"Insufficient balance: {e}") from e
            raise ExchangeOrderError(f"Failed to place sell order: {e}") from e

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
        """
        try:
            df = pyupbit.get_ohlcv(symbol, interval=interval, count=count)
            if df is None or len(df) == 0:
                _get_logger().warning(f"No OHLCV data for {symbol}")
                return None
            return cast(pd.DataFrame, df)
        except Exception as e:
            _get_logger().error(f"Error getting OHLCV for {symbol}: {e}", exc_info=True)
            return None

    def get_order_status(self, order_id: str) -> Order:
        """
        Get status of an existing order.

        Args:
            order_id: Order identifier (UUID)

        Returns:
            Order object with current status

        Raises:
            ExchangeError: If API call fails

        Implementation Notes:
            pyupbit.get_order() can return:
            - Single dict for UUID-based queries
            - List of dicts for market-based queries
            - None if order not found

            This implementation normalizes the response to always work with a single order.
        """
        try:
            # pyupbit.get_order() returns different types based on query:
            # - UUID query: returns single order dict or None
            # - Market query: returns list of orders or None
            result = self.client.get_order(order_id)

            if not result:
                raise ExchangeError(f"Order {order_id} not found")

            # Normalize response: convert list to single item if needed
            if isinstance(result, list):
                if len(result) == 0:
                    raise ExchangeError(f"Order {order_id} not found")
                # Take first matching order
                result = result[0]

            # Parse order status from Upbit format
            state = result.get("state", "wait")
            status_map = {
                "wait": OrderStatus.PENDING,
                "done": OrderStatus.FILLED,
                "cancel": OrderStatus.CANCELLED,
            }
            status = status_map.get(state, OrderStatus.PENDING)

            # Parse order side
            side_str = result.get("side", "")
            side = OrderSide.BUY if side_str == "bid" else OrderSide.SELL

            # Parse order type
            ord_type = result.get("ord_type", "")
            order_type = OrderType.MARKET if ord_type == "price" else OrderType.LIMIT

            return Order(
                order_id=order_id,
                symbol=result.get("market", ""),
                side=side,
                order_type=order_type,
                amount=float(result.get("volume", 0.0)),
                price=float(result.get("price", 0.0)) if result.get("price") else None,
                status=status,
                filled_amount=float(result.get("executed_volume", 0.0)),
                filled_price=float(result.get("avg_price", 0.0))
                if result.get("avg_price")
                else None,
                created_at=pd.to_datetime(result.get("created_at"))
                if result.get("created_at")
                else None,
                metadata=result,
            )
        except Exception as e:
            _get_logger().error(f"Error getting order status for {order_id}: {e}", exc_info=True)
            raise ExchangeError(f"Failed to get order status: {e}") from e

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order identifier (UUID)

        Returns:
            True if cancellation successful

        Raises:
            ExchangeError: If cancellation fails
        """
        try:
            result = self.client.cancel_order(order_id)
            return result is not None
        except Exception as e:
            _get_logger().error(f"Error cancelling order {order_id}: {e}", exc_info=True)
            raise ExchangeError(f"Failed to cancel order: {e}") from e
