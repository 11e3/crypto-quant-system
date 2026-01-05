"""
Unit tests for exchange exception module.
"""

import pytest

from src.exceptions.base import TradingSystemError
from src.exceptions.exchange import (
    ExchangeAuthenticationError,
    ExchangeConnectionError,
    ExchangeError,
    ExchangeOrderError,
    InsufficientBalanceError,
)


class TestExchangeError:
    """Test cases for ExchangeError exception."""

    def test_exchange_error_initialization(self) -> None:
        """Test ExchangeError initialization."""
        error = ExchangeError("Exchange error")

        assert str(error) == "Exchange error"
        assert isinstance(error, TradingSystemError)

    def test_exchange_error_raise(self) -> None:
        """Test raising ExchangeError."""
        with pytest.raises(ExchangeError):
            raise ExchangeError("Exchange operation failed")


class TestExchangeConnectionError:
    """Test cases for ExchangeConnectionError exception."""

    def test_connection_error_initialization(self) -> None:
        """Test ExchangeConnectionError initialization."""
        error = ExchangeConnectionError("Connection failed")

        assert str(error) == "Connection failed"
        assert isinstance(error, ExchangeError)

    def test_connection_error_raise(self) -> None:
        """Test raising ExchangeConnectionError."""
        with pytest.raises(ExchangeConnectionError):
            raise ExchangeConnectionError("Cannot connect to exchange")


class TestExchangeAuthenticationError:
    """Test cases for ExchangeAuthenticationError exception."""

    def test_authentication_error_initialization(self) -> None:
        """Test ExchangeAuthenticationError initialization (line 25)."""
        error = ExchangeAuthenticationError("Authentication failed")

        assert str(error) == "Authentication failed"
        assert isinstance(error, ExchangeError)

    def test_authentication_error_raise(self) -> None:
        """Test raising ExchangeAuthenticationError."""
        with pytest.raises(ExchangeAuthenticationError):
            raise ExchangeAuthenticationError("Invalid credentials")


class TestExchangeOrderError:
    """Test cases for ExchangeOrderError exception."""

    def test_order_error_initialization(self) -> None:
        """Test ExchangeOrderError initialization."""
        error = ExchangeOrderError("Order failed")

        assert str(error) == "Order failed"
        assert isinstance(error, ExchangeError)

    def test_order_error_raise(self) -> None:
        """Test raising ExchangeOrderError."""
        with pytest.raises(ExchangeOrderError):
            raise ExchangeOrderError("Order execution failed")


class TestInsufficientBalanceError:
    """Test cases for InsufficientBalanceError exception."""

    def test_insufficient_balance_error_initialization(self) -> None:
        """Test InsufficientBalanceError initialization."""
        error = InsufficientBalanceError("Insufficient balance")

        assert str(error) == "Insufficient balance"
        assert isinstance(error, ExchangeOrderError)

    def test_insufficient_balance_error_raise(self) -> None:
        """Test raising InsufficientBalanceError."""
        with pytest.raises(InsufficientBalanceError):
            raise InsufficientBalanceError("Not enough balance for order")

    def test_insufficient_balance_error_with_details(self) -> None:
        """Test InsufficientBalanceError with currency, required, available (lines 59, 61, 63)."""
        error = InsufficientBalanceError(
            "Insufficient balance",
            currency="KRW",
            required=100000.0,
            available=50000.0,
        )

        assert error.currency == "KRW"
        assert error.required == 100000.0
        assert error.available == 50000.0
        assert error.details["currency"] == "KRW"
        assert error.details["required"] == 100000.0
        assert error.details["available"] == 50000.0
