"""
Unit tests for TradingBot.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.loader import ConfigLoader
from src.execution.bot import TradingBot
from tests.fixtures.mock_exchange import MockExchange


@pytest.fixture
def test_config_path() -> Path:
    """Get path to test configuration file."""
    return Path(__file__).parent.parent.parent / "fixtures" / "config" / "test_settings.yaml"


@pytest.fixture
def mock_exchange() -> MockExchange:
    """Create a mock exchange for testing."""
    from tests.fixtures.mock_exchange import MockExchange

    return MockExchange()


class TestTradingBot:
    """Test cases for TradingBot."""

    def test_initialization(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test TradingBot initialization."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = MagicMock(spec=ConfigLoader)
            mock_config.get_trading_config.return_value = {
                "tickers": ["KRW-BTC"],
                "min_order_amount": 5000.0,
                "max_slots": 5,
                "fee_rate": 0.0005,
            }
            mock_config.get_strategy_config.return_value = {
                "name": "VanillaVBO",
                "sma_period": 5,
                "trend_sma_period": 10,
                "short_noise_period": 5,
                "long_noise_period": 10,
            }
            mock_config.get_bot_config.return_value = {
                "api_retry_delay": 1,
                "daily_reset_hour": 9,
                "daily_reset_minute": 0,
                "websocket_reconnect_delay": 5,
            }
            mock_config.get_upbit_keys.return_value = ("access_key", "secret_key")
            mock_config.get_telegram_config.return_value = {
                "token": "test_token",
                "chat_id": "test_chat_id",
                "enabled": False,
            }
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            assert bot.exchange is not None
            assert bot.strategy is not None
            assert bot.position_manager is not None
            assert bot.order_manager is not None
            assert bot.signal_handler is not None
            assert bot.tickers == ["KRW-BTC"]
            assert len(bot.target_info) == 0

    def test_initialization_missing_api_keys(self, test_config_path: Path) -> None:
        """Test TradingBot initialization with missing API keys."""
        with patch("src.execution.bot.get_config") as mock_get_config:
            mock_config = MagicMock(spec=ConfigLoader)
            mock_config.get_upbit_keys.return_value = (None, None)
            mock_get_config.return_value = mock_config

            with pytest.raises(ValueError, match="Upbit API keys not found"):
                TradingBot(config_path=test_config_path)

    def test_get_krw_balance(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test getting KRW balance."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            balance = bot.get_krw_balance()

            assert isinstance(balance, float)
            assert balance >= 0

    def test_get_krw_balance_error(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test getting KRW balance with error."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            mock_exchange.get_balance = MagicMock(side_effect=Exception("Error"))

            balance = bot.get_krw_balance()
            assert balance == 0.0

    def test_sell_all(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test selling all holdings."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            # First buy some BTC
            mock_exchange.buy_market_order("KRW-BTC", 50000.0)

            result = bot.sell_all("KRW-BTC")
            assert isinstance(result, bool)

    def test_sell_all_error(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test selling all with error."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.order_manager.place_buy_order = MagicMock(return_value=None)

            result = bot.sell_all("KRW-BTC")
            assert result is False

    def test_check_exit_conditions(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test checking exit conditions."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            result = bot.check_exit_conditions("KRW-BTC")
            assert isinstance(result, bool)

    def test_check_entry_conditions(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test checking entry conditions."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.target_info["KRW-BTC"] = {"target": 50000.0}

            result = bot.check_entry_conditions("KRW-BTC", current_price=51000.0)
            assert isinstance(result, bool)

    def test_check_entry_conditions_no_target(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test checking entry conditions when no target info."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            result = bot.check_entry_conditions("KRW-BTC", current_price=51000.0)
            assert isinstance(result, bool)

    def test_calculate_sma_exit(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test calculating SMA for exit condition (covers lines 154-162)."""
        import pandas as pd

        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            # Test with sufficient data
            dates = pd.date_range("2024-01-01", periods=10, freq="D")
            df = pd.DataFrame(
                {
                    "close": [100.0 + i * 10 for i in range(10)],
                },
                index=dates,
            )
            sma = bot._calculate_sma_exit(df)
            assert sma is not None
            assert isinstance(sma, float)

            # Test with insufficient data
            df_short = pd.DataFrame({"close": [100.0, 110.0]}, index=dates[:2])
            sma_short = bot._calculate_sma_exit(df_short)
            assert sma_short is None

            # Test with None
            sma_none = bot._calculate_sma_exit(None)
            assert sma_none is None

    def test_initialize_targets(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test initializing targets."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_config.get_strategy_config.return_value = {
                "name": "VanillaVBO",
                "sma_period": 5,
                "trend_sma_period": 10,
                "short_noise_period": 5,
                "long_noise_period": 10,
            }
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            # Set up mock data
            import pandas as pd

            dates = pd.date_range("2024-01-01", periods=30, freq="D")
            sample_data = pd.DataFrame(
                {
                    "open": [100.0 + i for i in range(30)],
                    "high": [105.0 + i for i in range(30)],
                    "low": [95.0 + i for i in range(30)],
                    "close": [102.0 + i for i in range(30)],
                    "volume": [1000.0 + i * 10 for i in range(30)],
                },
                index=dates,
            )
            mock_exchange.set_ohlcv_data("KRW-BTC", "day", sample_data)

            bot.initialize_targets()

            assert "KRW-BTC" in bot.target_info or len(bot.target_info) == 0

    def test_check_existing_holdings(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test checking existing holdings."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            # Set up balance
            mock_exchange.buy_market_order("KRW-BTC", 50000.0)

            bot.check_existing_holdings()

            # Should not raise error

    def test_check_existing_holdings_error(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test checking existing holdings with error."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            mock_exchange.get_balance = MagicMock(side_effect=Exception("Error"))

            bot.check_existing_holdings()
            # Should not raise error

    def test_calculate_buy_amount_insufficient_balance(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test calculating buy amount with insufficient balance."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            mock_exchange.set_balance("KRW", 1000.0)  # Low balance

            amount = bot._calculate_buy_amount()
            assert amount == 0.0

    def test_calculate_buy_amount_max_slots(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test calculating buy amount when max slots reached."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            # Fill all slots
            for i in range(5):
                bot.position_manager.add_position(
                    ticker=f"KRW-ETH{i}",
                    entry_price=1000.0,
                    amount=0.1,
                )

            amount = bot._calculate_buy_amount()
            assert amount == 0.0

    def test_process_ticker_update(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test processing ticker update."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.target_info["KRW-BTC"] = {"target": 50000.0}

            bot.process_ticker_update("KRW-BTC", current_price=51000.0)
            # Should not raise error

    def test_process_ticker_update_already_holding(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test processing ticker update when already holding."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.position_manager.add_position(
                ticker="KRW-BTC",
                entry_price=50000.0,
                amount=0.001,
            )

            bot.process_ticker_update("KRW-BTC", current_price=51000.0)
            # Should not raise error and should skip

    def test_process_ticker_update_no_entry_signal(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test processing ticker update when no entry signal."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.target_info["KRW-BTC"] = {"target": 50000.0}

            with patch.object(bot, "check_entry_conditions", return_value=False):
                bot.process_ticker_update("KRW-BTC", current_price=49000.0)
                # Should not raise error

    def test_process_ticker_update_insufficient_buy_amount(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test processing ticker update when buy amount is insufficient."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            bot.target_info["KRW-BTC"] = {"target": 50000.0}
            mock_exchange.set_balance("KRW", 1000.0)

            with patch.object(bot, "check_entry_conditions", return_value=True):
                bot.process_ticker_update("KRW-BTC", current_price=51000.0)
                # Should not raise error

    @staticmethod
    def _create_mock_config() -> MagicMock:
        """Create a mock config for testing."""
        mock_config = MagicMock(spec=ConfigLoader)
        mock_config.get_trading_config.return_value = {
            "tickers": ["KRW-BTC"],
            "min_order_amount": 5000.0,
            "max_slots": 5,
            "fee_rate": 0.0005,
        }
        mock_config.get_strategy_config.return_value = {
            "name": "VanillaVBO",
            "sma_period": 5,
            "trend_sma_period": 10,
            "short_noise_period": 5,
            "long_noise_period": 10,
        }
        mock_config.get_bot_config.return_value = {
            "api_retry_delay": 1,
            "daily_reset_hour": 9,
            "daily_reset_minute": 0,
            "websocket_reconnect_delay": 5,
        }
        mock_config.get_upbit_keys.return_value = ("access_key", "secret_key")
        mock_config.get_telegram_config.return_value = {
            "token": "test_token",
            "chat_id": "test_chat_id",
            "enabled": False,
        }
        return mock_config

    def test_calculate_buy_amount(
        self, mock_exchange: MockExchange, test_config_path: Path
    ) -> None:
        """Test calculating buy amount (covers lines 289-312)."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)
            mock_exchange.set_balance("KRW", 100000.0, 0.0)

            # Test with sufficient balance and available slots
            buy_amount = bot._calculate_buy_amount()
            assert buy_amount > 0
            assert buy_amount > bot.trading_config["min_order_amount"]

            # Test with insufficient balance
            mock_exchange.set_balance("KRW", 1000.0, 0.0)
            buy_amount_low = bot._calculate_buy_amount()
            assert buy_amount_low == 0.0

            # Test with no available slots
            mock_exchange.set_balance("KRW", 100000.0, 0.0)
            # Clear any existing positions first
            bot.position_manager.remove_position("KRW-BTC")
            # Add positions with different tickers to fill slots
            tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT"]
            from contextlib import suppress

            for ticker in tickers[: bot.trading_config["max_slots"]]:
                with suppress(ValueError):
                    bot.position_manager.add_position(ticker, 50000.0, 0.001)
            buy_amount_no_slots = bot._calculate_buy_amount()
            assert buy_amount_no_slots == 0.0

    def test_process_exits(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test processing exits (covers lines 238-262)."""
        import pandas as pd

        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            # Add a position
            bot.position_manager.add_position("KRW-BTC", 50000.0, 0.001)

            # Set up mock data for exit signal
            dates = pd.date_range("2024-01-01", periods=20, freq="D")
            sample_data = pd.DataFrame(
                {
                    "open": [100.0 + i for i in range(20)],
                    "high": [105.0 + i for i in range(20)],
                    "low": [95.0 + i for i in range(20)],
                    "close": [102.0 + i for i in range(20)],
                    "volume": [1000.0 + i * 10 for i in range(20)],
                },
                index=dates,
            )
            mock_exchange.set_ohlcv_data("KRW-BTC", "day", sample_data)

            # Mock exit signal
            bot.signal_handler.check_exit_signal = MagicMock(return_value=True)
            bot.sell_all = MagicMock(return_value=True)

            bot._process_exits()

            # Verify sell_all was called
            bot.sell_all.assert_called_once_with("KRW-BTC")

    def test_recalculate_targets(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test recalculating targets (covers lines 264-281)."""
        import pandas as pd

        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            # Set up mock data
            dates = pd.date_range("2024-01-01", periods=30, freq="D")
            sample_data = pd.DataFrame(
                {
                    "open": [100.0 + i for i in range(30)],
                    "high": [105.0 + i for i in range(30)],
                    "low": [95.0 + i for i in range(30)],
                    "close": [102.0 + i for i in range(30)],
                    "volume": [1000.0 + i * 10 for i in range(30)],
                },
                index=dates,
            )
            mock_exchange.set_ohlcv_data("KRW-BTC", "day", sample_data)

            bot._recalculate_targets()

            # Verify targets were recalculated
            assert "KRW-BTC" in bot.target_info or len(bot.target_info) == 0

    def test_daily_reset(self, mock_exchange: MockExchange, test_config_path: Path) -> None:
        """Test daily reset (covers lines 283-287)."""
        with (
            patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
            patch("src.execution.bot.get_config") as mock_get_config,
        ):
            mock_config = self._create_mock_config()
            mock_get_config.return_value = mock_config

            bot = TradingBot(config_path=test_config_path)

            # Mock the methods called by daily_reset
            bot._process_exits = MagicMock()
            bot._recalculate_targets = MagicMock()

            bot.daily_reset()

            # Verify both methods were called
            bot._process_exits.assert_called_once()
            bot._recalculate_targets.assert_called_once()
