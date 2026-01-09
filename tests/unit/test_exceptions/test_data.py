"""
Unit tests for data exception module.
"""

import pytest

from src.exceptions.base import TradingSystemError
from src.exceptions.data import (
    DataSourceConnectionError,
    DataSourceError,
    DataSourceNotFoundError,
)


class TestDataSourceError:
    """Test cases for DataSourceError exception."""

    def test_data_source_error_initialization(self) -> None:
        """Test DataSourceError initialization."""
        error = DataSourceError("Data source error")

        assert str(error) == "Data source error"
        assert isinstance(error, TradingSystemError)

    def test_data_source_error_raise(self) -> None:
        """Test raising DataSourceError."""
        with pytest.raises(DataSourceError):
            raise DataSourceError("Failed to fetch data")


class TestDataSourceConnectionError:
    """Test cases for DataSourceConnectionError exception."""

    def test_connection_error_initialization(self) -> None:
        """Test DataSourceConnectionError initialization."""
        error = DataSourceConnectionError("Connection failed")

        assert str(error) == "Connection failed"
        assert isinstance(error, DataSourceError)

    def test_connection_error_raise(self) -> None:
        """Test raising DataSourceConnectionError."""
        with pytest.raises(DataSourceConnectionError):
            raise DataSourceConnectionError("Cannot connect to data source")


class TestDataSourceNotFoundError:
    """Test cases for DataSourceNotFoundError exception."""

    def test_not_found_error_initialization(self) -> None:
        """Test DataSourceNotFoundError initialization."""
        error = DataSourceNotFoundError("Resource not found")

        assert str(error) == "Resource not found"
        assert isinstance(error, DataSourceError)

    def test_not_found_error_raise(self) -> None:
        """Test raising DataSourceNotFoundError."""
        with pytest.raises(DataSourceNotFoundError):
            raise DataSourceNotFoundError("Data file not found")

    def test_not_found_error_with_source(self) -> None:
        """Test DataSourceNotFoundError with source parameter (line 36)."""
        error = DataSourceNotFoundError("Data source not found", source="test_source")
        assert error.source == "test_source"
        assert error.details["source"] == "test_source"

    def test_not_found_error_with_existing_details(self) -> None:
        """Test DataSourceNotFoundError with pre-existing details dict (line 44->46)."""
        existing_details = {"request_id": "req-123", "timestamp": "2024-01-01"}
        error = DataSourceNotFoundError(
            "Data source not found",
            source="test_source",
            details=existing_details,
        )
        assert error.details["request_id"] == "req-123"
        assert error.details["timestamp"] == "2024-01-01"
        assert error.details["source"] == "test_source"
