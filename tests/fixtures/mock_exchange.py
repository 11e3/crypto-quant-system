"""
Mock Exchange implementation for testing.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from src.exceptions.exchange import ExchangeError, InsufficientBalanceError
from src.exchange import Exchange
from src.exchange.types import Balance, Order, OrderSide, OrderStatus, OrderType, Ticker

if TYPE_CHECKING:
    import pandas as pd


class MockExchange(Exchange):
    """
    Mock implementation of Exchange for testing.

    Provides in-memory state management and configurable behavior.
    """

    def __init__(self) -> None:
        """Initialize mock exchange with default state."""
        self._balances: dict[str, Balance] = {
            "KRW": Balance(currency="KRW", balance=1_000_000.0, locked=0.0),
        }
        self._orders: dict[str, Order] = {}
        self._tickers: dict[str, Ticker] = {
            "KRW-BTC": Ticker(
                symbol="KRW-BTC",
                price=50_000_000.0,
                volume=1000.0,
            ),
            "KRW-ETH": Ticker(
                symbol="KRW-ETH",
                price=3_000_000.0,
                volume=500.0,
            ),
        }
        self._ohlcv_data: dict[tuple[str, str], pd.DataFrame] = {}
        self._order_counter = 0
        self._should_fail_buy = False
        self._should_fail_sell = False
        self._should_insufficient_balance = False

    def get_balance(self, currency: str) -> Balance:
        """Get balance for a currency."""
        if currency not in self._balances:
            return Balance(currency=currency, balance=0.0, locked=0.0)
        return self._balances[currency]

    def get_current_price(self, ticker: str) -> float:
        """Get current price for a ticker."""
        if ticker not in self._tickers:
            raise ExchangeError(f"Ticker {ticker} not found")
        return self._tickers[ticker].price

    def get_ticker(self, ticker: str) -> Ticker:
        """Get ticker information."""
        if ticker not in self._tickers:
            raise ExchangeError(f"Ticker {ticker} not found")
        return self._tickers[ticker]

    def get_ohlcv(
        self,
        ticker: str,
        interval: str = "day",
        count: int = 200,
    ) -> "pd.DataFrame":
        """Get OHLCV data for a ticker."""
        key = (ticker, interval)
        if key in self._ohlcv_data:
            return self._ohlcv_data[key].tail(count)

        # Return empty DataFrame if no data set
        import pandas as pd

        return pd.DataFrame()

    def buy_market_order(self, ticker: str, amount: float) -> Order:
        """Place a market buy order."""
        if self._should_fail_buy:
            raise ExchangeError("Mock buy order failure")

        if self._should_insufficient_balance:
            raise InsufficientBalanceError("Insufficient balance")

        price = self.get_current_price(ticker)
        # amount is in quote currency (KRW), calculate base currency amount
        base_amount = amount / price
        total_cost = amount

        krw_balance = self.get_balance("KRW")
        if krw_balance.available < total_cost:
            raise InsufficientBalanceError(
                f"Insufficient balance: {krw_balance.available} < {total_cost}"
            )

        # Update balance
        self._balances["KRW"] = Balance(
            currency="KRW",
            balance=krw_balance.balance - total_cost,
            locked=krw_balance.locked,
        )

        # Add base currency to balance
        base_currency = ticker.split("-")[1]  # e.g., "BTC" from "KRW-BTC"
        if base_currency not in self._balances:
            self._balances[base_currency] = Balance(currency=base_currency, balance=0.0, locked=0.0)
        base_balance = self._balances[base_currency]
        self._balances[base_currency] = Balance(
            currency=base_currency,
            balance=base_balance.balance + base_amount,
            locked=base_balance.locked,
        )

        # Create order
        self._order_counter += 1
        order = Order(
            order_id=f"mock-buy-{self._order_counter}",
            symbol=ticker,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=OrderStatus.FILLED,
            amount=base_amount,
            price=price,
            filled_amount=base_amount,
            created_at=datetime.now(),
        )
        self._orders[order.order_id] = order

        return order

    def sell_market_order(self, ticker: str, amount: float) -> Order:
        """Place a market sell order.

        Args:
            ticker: Trading pair (e.g., "KRW-BTC")
            amount: Amount in base currency (e.g., BTC)
        """
        if self._should_fail_sell:
            raise ExchangeError("Mock sell order failure")

        price = self.get_current_price(ticker)
        base_currency = ticker.split("-")[1]  # e.g., "BTC" from "KRW-BTC"

        # Check base currency balance
        if base_currency not in self._balances:
            raise InsufficientBalanceError(f"Insufficient {base_currency} balance")
        base_balance = self._balances[base_currency]
        if base_balance.available < amount:
            raise InsufficientBalanceError(
                f"Insufficient {base_currency} balance: {base_balance.available} < {amount}"
            )

        # Update base currency balance
        self._balances[base_currency] = Balance(
            currency=base_currency,
            balance=base_balance.balance - amount,
            locked=base_balance.locked,
        )

        # Update KRW balance
        krw_balance = self.get_balance("KRW")
        total_revenue = price * amount
        self._balances["KRW"] = Balance(
            currency="KRW",
            balance=krw_balance.balance + total_revenue,
            locked=krw_balance.locked,
        )

        # Create order
        self._order_counter += 1
        order = Order(
            order_id=f"mock-sell-{self._order_counter}",
            symbol=ticker,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            status=OrderStatus.FILLED,
            amount=amount,
            price=price,
            filled_amount=amount,
            created_at=datetime.now(),
        )
        self._orders[order.order_id] = order

        return order

    def get_order_status(self, order_id: str) -> Order:
        """Get status of an order."""
        if order_id not in self._orders:
            raise ExchangeError(f"Order {order_id} not found")
        return self._orders[order_id]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id not in self._orders:
            raise ExchangeError(f"Order {order_id} not found")
        order = self._orders[order_id]
        self._orders[order_id] = Order(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            status=OrderStatus.CANCELLED,
            amount=order.amount,
            price=order.price,
            filled_amount=order.filled_amount,
            created_at=order.created_at,
        )
        return True

    # Helper methods for test configuration
    def set_balance(self, currency: str, balance: float, locked: float = 0.0) -> None:
        """Set balance for testing."""
        self._balances[currency] = Balance(currency=currency, balance=balance, locked=locked)

    def set_price(self, ticker: str, price: float) -> None:
        """Set price for a ticker."""
        if ticker not in self._tickers:
            self._tickers[ticker] = Ticker(
                symbol=ticker,
                price=price,
                volume=0.0,
            )
        else:
            ticker_obj = self._tickers[ticker]
            self._tickers[ticker] = Ticker(
                symbol=ticker,
                price=price,
                volume=ticker_obj.volume,
            )

    def set_ohlcv_data(self, ticker: str, interval: str, data: "pd.DataFrame") -> None:
        """Set OHLCV data for testing."""
        self._ohlcv_data[(ticker, interval)] = data

    def configure_failures(
        self,
        fail_buy: bool = False,
        fail_sell: bool = False,
        insufficient_balance: bool = False,
    ) -> None:
        """Configure failure modes for testing."""
        self._should_fail_buy = fail_buy
        self._should_fail_sell = fail_sell
        self._should_insufficient_balance = insufficient_balance
