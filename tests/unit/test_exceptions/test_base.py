"""
Unit tests for base exception module.
"""

import pytest

from src.exceptions.base import TradingSystemError


class TestTradingSystemError:
    """Test cases for TradingSystemError exception."""

    def test_trading_system_error_initialization(self) -> None:
        """Test TradingSystemError initialization."""
        error = TradingSystemError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_trading_system_error_with_details(self) -> None:
        """Test TradingSystemError with additional details."""
        error = TradingSystemError("Test error", details={"key": "value"})

        assert "Test error" in str(error)
        assert hasattr(error, "details")
        assert error.details == {"key": "value"}

    def test_trading_system_error_raise(self) -> None:
        """Test raising TradingSystemError."""
        with pytest.raises(TradingSystemError) as exc_info:
            raise TradingSystemError("Error occurred")

        assert "Error occurred" in str(exc_info.value)
