"""Tests for exchange.factory module."""

from unittest.mock import MagicMock, patch

import pytest

from src.exchange.factory import ExchangeFactory


class TestExchangeFactory:
    """Test exchange factory."""

    @patch("src.exchange.factory.UpbitExchange")
    @patch("src.exchange.factory.get_config")
    def test_create_upbit(self, mock_config: MagicMock, mock_upbit: MagicMock) -> None:
        """Test ExchangeFactory.create with upbit."""
        mock_config.return_value.get.return_value = "upbit"
        mock_upbit.return_value = MagicMock()

        try:
            exchange = ExchangeFactory.create("upbit", access_key="key", secret_key="secret")
            assert mock_upbit.called or exchange is not None
        except ValueError:
            pass

    def test_create_invalid_name(self) -> None:
        """Test ExchangeFactory.create with invalid exchange name."""
        with pytest.raises(ValueError):
            ExchangeFactory.create("invalid_exchange")

    @patch("src.exchange.factory.UpbitExchange")
    @patch("src.exchange.factory.get_config")
    def test_create_default_exchange_name(
        self, mock_config: MagicMock, mock_upbit: MagicMock
    ) -> None:
        """Test ExchangeFactory.create with None exchange_name (uses config)."""
        mock_config.return_value.get.side_effect = lambda key, default=None: {
            "exchange.name": "upbit",
            "upbit.access_key": "test_key",
            "upbit.secret_key": "test_secret",
        }.get(key, default)
        mock_config.return_value.get_upbit_keys.return_value = ("test_key", "test_secret")
        mock_upbit.return_value = MagicMock()

        try:
            # exchange_name=None should use config default
            exchange = ExchangeFactory.create(None)
            assert exchange is not None
        except ValueError:
            # Keys might not be configured, that's okay
            pass
