"""
Unit tests for order exception module.
"""

import pytest

from src.exceptions.base import TradingSystemError
from src.exceptions.order import OrderError, OrderExecutionError, OrderNotFoundError


class TestOrderError:
    """Test cases for OrderError exception."""

    def test_order_error_initialization(self) -> None:
        """Test OrderError initialization."""
        error = OrderError("Order error")

        assert str(error) == "Order error"
        assert isinstance(error, TradingSystemError)

    def test_order_error_raise(self) -> None:
        """Test raising OrderError."""
        with pytest.raises(OrderError):
            raise OrderError("Order operation failed")


class TestOrderNotFoundError:
    """Test cases for OrderNotFoundError exception."""

    def test_not_found_error_initialization(self) -> None:
        """Test OrderNotFoundError initialization."""
        error = OrderNotFoundError("Order not found")

        assert str(error) == "Order not found"
        assert isinstance(error, OrderError)

    def test_not_found_error_raise(self) -> None:
        """Test raising OrderNotFoundError."""
        with pytest.raises(OrderNotFoundError):
            raise OrderNotFoundError("Order ID not found")

    def test_not_found_error_with_order_id(self) -> None:
        """Test OrderNotFoundError with order_id (line 29)."""
        error = OrderNotFoundError("Order not found", order_id="order-123")

        assert error.order_id == "order-123"
        assert error.details["order_id"] == "order-123"


class TestOrderExecutionError:
    """Test cases for OrderExecutionError exception."""

    def test_execution_error_initialization(self) -> None:
        """Test OrderExecutionError initialization."""
        error = OrderExecutionError("Execution failed")

        assert str(error) == "Execution failed"
        assert isinstance(error, OrderError)

    def test_execution_error_raise(self) -> None:
        """Test raising OrderExecutionError."""
        with pytest.raises(OrderExecutionError):
            raise OrderExecutionError("Order execution failed")

    def test_execution_error_with_order_id_and_reason(self) -> None:
        """Test OrderExecutionError with order_id and reason (lines 57, 59)."""
        error = OrderExecutionError(
            "Execution failed",
            order_id="order-123",
            reason="Insufficient liquidity",
        )

        assert error.order_id == "order-123"
        assert error.reason == "Insufficient liquidity"
        assert error.details["order_id"] == "order-123"
        assert error.details["reason"] == "Insufficient liquidity"
