"""
Unit tests for strategy exception module.
"""

import pytest

from src.exceptions.base import TradingSystemError
from src.exceptions.strategy import (
    StrategyConfigurationError,
    StrategyError,
    StrategyExecutionError,
)


class TestStrategyError:
    """Test cases for StrategyError exception."""

    def test_strategy_error_initialization(self) -> None:
        """Test StrategyError initialization."""
        error = StrategyError("Strategy error")

        assert str(error) == "Strategy error"
        assert isinstance(error, TradingSystemError)

    def test_strategy_error_raise(self) -> None:
        """Test raising StrategyError."""
        with pytest.raises(StrategyError):
            raise StrategyError("Strategy operation failed")


class TestStrategyConfigurationError:
    """Test cases for StrategyConfigurationError exception."""

    def test_configuration_error_initialization(self) -> None:
        """Test StrategyConfigurationError initialization."""
        error = StrategyConfigurationError("Configuration error")

        assert str(error) == "Configuration error"
        assert isinstance(error, StrategyError)

    def test_configuration_error_raise(self) -> None:
        """Test raising StrategyConfigurationError."""
        with pytest.raises(StrategyConfigurationError):
            raise StrategyConfigurationError("Invalid strategy configuration")

    def test_configuration_error_with_strategy_name_and_parameter(self) -> None:
        """Test StrategyConfigurationError with strategy_name and parameter (lines 36, 38)."""
        error = StrategyConfigurationError(
            "Configuration error",
            strategy_name="TestStrategy",
            parameter="sma_period",
        )

        assert error.strategy_name == "TestStrategy"
        assert error.parameter == "sma_period"
        assert error.details["strategy_name"] == "TestStrategy"
        assert error.details["parameter"] == "sma_period"


class TestStrategyExecutionError:
    """Test cases for StrategyExecutionError exception."""

    def test_execution_error_initialization(self) -> None:
        """Test StrategyExecutionError initialization."""
        error = StrategyExecutionError("Execution failed")

        assert str(error) == "Execution failed"
        assert isinstance(error, StrategyError)

    def test_execution_error_raise(self) -> None:
        """Test raising StrategyExecutionError."""
        with pytest.raises(StrategyExecutionError):
            raise StrategyExecutionError("Strategy execution failed")

    def test_execution_error_with_strategy_name_and_ticker(self) -> None:
        """Test StrategyExecutionError with strategy_name and ticker (lines 67, 69)."""
        error = StrategyExecutionError(
            "Execution failed",
            strategy_name="TestStrategy",
            ticker="KRW-BTC",
        )

        assert error.strategy_name == "TestStrategy"
        assert error.ticker == "KRW-BTC"
        assert error.details["strategy_name"] == "TestStrategy"
        assert error.details["ticker"] == "KRW-BTC"
