"""
Unit tests for MockExchange.
"""

import pytest

from src.exceptions.exchange import ExchangeError, InsufficientBalanceError
from src.exchange.types import OrderSide, OrderStatus
from tests.fixtures.mock_exchange import MockExchange


class TestMockExchange:
    """Test cases for MockExchange."""

    def test_get_balance(self, mock_exchange: MockExchange) -> None:
        """Test getting balance."""
        balance = mock_exchange.get_balance("KRW")
        assert balance.currency == "KRW"
        assert balance.available == 1_000_000.0
        assert balance.locked == 0.0

    def test_get_current_price(self, mock_exchange: MockExchange) -> None:
        """Test getting current price."""
        price = mock_exchange.get_current_price("KRW-BTC")
        assert price == 50_000_000.0

    def test_get_current_price_not_found(self, mock_exchange: MockExchange) -> None:
        """Test getting price for non-existent ticker."""
        with pytest.raises(ExchangeError):
            mock_exchange.get_current_price("KRW-UNKNOWN")

    def test_buy_market_order(self, mock_exchange: MockExchange) -> None:
        """Test placing a buy order."""
        initial_balance = mock_exchange.get_balance("KRW")
        order = mock_exchange.buy_market_order("KRW-BTC", 50_000.0)  # 50,000 KRW

        assert order.side == OrderSide.BUY
        assert order.symbol == "KRW-BTC"
        assert order.status == OrderStatus.FILLED

        # Check balance was deducted
        new_balance = mock_exchange.get_balance("KRW")
        assert new_balance.available == initial_balance.available - 50_000.0

        # Check BTC balance was added
        btc_balance = mock_exchange.get_balance("BTC")
        assert btc_balance.available > 0

    def test_buy_order_insufficient_balance(self, mock_exchange: MockExchange) -> None:
        """Test buy order with insufficient balance."""
        mock_exchange.set_balance("KRW", 1000.0)  # Very low balance

        with pytest.raises(InsufficientBalanceError):
            mock_exchange.buy_market_order("KRW-BTC", 50_000.0)  # 50,000 KRW

    def test_sell_market_order(self, mock_exchange: MockExchange) -> None:
        """Test placing a sell order."""
        # First buy some BTC
        mock_exchange.buy_market_order("KRW-BTC", 50_000.0)
        initial_krw = mock_exchange.get_balance("KRW")
        initial_btc = mock_exchange.get_balance("BTC")

        # Sell 0.001 BTC
        order = mock_exchange.sell_market_order("KRW-BTC", 0.001)

        assert order.side == OrderSide.SELL
        assert order.symbol == "KRW-BTC"
        assert order.amount == 0.001
        assert order.status == OrderStatus.FILLED

        # Check balance was increased
        new_balance = mock_exchange.get_balance("KRW")
        expected_revenue = 50_000_000.0 * 0.001
        assert new_balance.available == initial_krw.available + expected_revenue

        # Check BTC balance was decreased
        new_btc = mock_exchange.get_balance("BTC")
        assert new_btc.available == initial_btc.available - 0.001

    def test_get_order_status(self, mock_exchange: MockExchange) -> None:
        """Test getting order status."""
        order = mock_exchange.buy_market_order("KRW-BTC", 0.001)
        retrieved_order = mock_exchange.get_order_status(order.order_id)

        assert retrieved_order.order_id == order.order_id
        assert retrieved_order.status == OrderStatus.FILLED

    def test_cancel_order(self, mock_exchange: MockExchange) -> None:
        """Test canceling an order."""
        order = mock_exchange.buy_market_order("KRW-BTC", 0.001)
        mock_exchange.cancel_order(order.order_id)

        cancelled_order = mock_exchange.get_order_status(order.order_id)
        assert cancelled_order.status == OrderStatus.CANCELLED

    def test_configure_failures(self, mock_exchange: MockExchange) -> None:
        """Test configuring failure modes."""
        mock_exchange.configure_failures(fail_buy=True)

        with pytest.raises(ExchangeError):
            mock_exchange.buy_market_order("KRW-BTC", 0.001)
