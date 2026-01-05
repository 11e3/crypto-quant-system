"""
Unit tests for Telegram utility module.
"""

from unittest.mock import MagicMock, patch

from src.utils.telegram import TelegramNotifier, get_notifier, send_message


class TestTelegramNotifier:
    """Test cases for TelegramNotifier class."""

    def test_initialization(self) -> None:
        """Test TelegramNotifier initialization."""
        notifier = TelegramNotifier(token="test_token", chat_id="test_chat_id", enabled=False)

        assert notifier.token == "test_token"
        assert notifier.chat_id == "test_chat_id"
        assert notifier.enabled is False

    def test_initialization_enabled(self) -> None:
        """Test TelegramNotifier initialization with enabled=True."""
        notifier = TelegramNotifier(token="test_token", chat_id="test_chat_id", enabled=True)

        assert notifier.enabled is True

    def test_send_disabled(self) -> None:
        """Test send when notifier is disabled."""
        notifier = TelegramNotifier(token="test_token", chat_id="test_chat_id", enabled=False)

        result = notifier.send("Test message")

        assert result is False

    def test_send_no_token(self) -> None:
        """Test send when token is not configured."""
        notifier = TelegramNotifier(token="YOUR_BOT_TOKEN", chat_id="test_chat_id", enabled=True)

        result = notifier.send("Test message")

        assert result is False

    @patch("src.utils.telegram.requests.post")
    def test_send_success(self, mock_post: MagicMock) -> None:
        """Test send when successful."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        notifier = TelegramNotifier(token="real_token", chat_id="test_chat_id", enabled=True)
        result = notifier.send("Test message")

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "telegram.org" in call_args[0][0]

    @patch("src.utils.telegram.requests.post")
    def test_send_error(self, mock_post: MagicMock) -> None:
        """Test send when API call fails."""
        mock_post.side_effect = Exception("API Error")

        notifier = TelegramNotifier(token="real_token", chat_id="test_chat_id", enabled=True)
        result = notifier.send("Test message")

        assert result is False

    def test_send_trade_signal_disabled(self) -> None:
        """Test send_trade_signal when notifier is disabled."""
        notifier = TelegramNotifier(token="test_token", chat_id="test_chat_id", enabled=False)

        result = notifier.send_trade_signal("BUY", "KRW-BTC", 50000.0)

        assert result is False

    @patch("src.utils.telegram.TelegramNotifier.send")
    def test_send_trade_signal(self, mock_send: MagicMock) -> None:
        """Test send_trade_signal."""
        mock_send.return_value = True

        notifier = TelegramNotifier(token="real_token", chat_id="test_chat_id", enabled=True)
        result = notifier.send_trade_signal("BUY", "KRW-BTC", 50000.0, target=51000.0)

        assert result is True
        mock_send.assert_called_once()
        message = mock_send.call_args[0][0]
        assert "BUY" in message
        assert "KRW-BTC" in message
        # Price is formatted with commas: "50,000"
        assert "50" in message and "000" in message

    @patch("src.utils.telegram.TelegramNotifier.send")
    def test_send_trade_signal_with_kwargs(self, mock_send: MagicMock) -> None:
        """Test send_trade_signal with additional kwargs."""
        mock_send.return_value = True

        notifier = TelegramNotifier(token="real_token", chat_id="test_chat_id", enabled=True)
        result = notifier.send_trade_signal(
            "SELL", "KRW-BTC", 49000.0, target=48000.0, noise="0.5 < 0.6"
        )

        assert result is True
        message = mock_send.call_args[0][0]
        assert "SELL" in message
        assert "noise" in message.lower()


class TestGetNotifier:
    """Test cases for get_notifier function."""

    def test_get_notifier_returns_instance(self) -> None:
        """Test get_notifier returns TelegramNotifier instance."""
        notifier = get_notifier(token="test_token", chat_id="test_chat_id", enabled=False)

        assert isinstance(notifier, TelegramNotifier)

    def test_get_notifier_disabled(self) -> None:
        """Test get_notifier with enabled=False."""
        notifier = get_notifier(token="test_token", chat_id="test_chat_id", enabled=False)

        assert notifier.enabled is False

    def test_get_notifier_enabled(self) -> None:
        """Test get_notifier with enabled=True."""
        # Reset global notifier to allow new instance
        import src.utils.telegram

        src.utils.telegram._notifier = None

        notifier = get_notifier(token="real_token_test", chat_id="test_chat_id_123", enabled=True)

        # enabled is set based on token and chat_id being non-empty and not "YOUR_"
        # TelegramNotifier.__init__ sets enabled = enabled and bool(token) and bool(chat_id)
        assert notifier.enabled is True


class TestSendMessage:
    """Test cases for send_message function."""

    @patch("src.utils.telegram.get_notifier")
    def test_send_message(self, mock_get_notifier: MagicMock) -> None:
        """Test send_message function (line 142)."""
        mock_notifier = MagicMock()
        mock_notifier.send.return_value = True
        mock_get_notifier.return_value = mock_notifier

        result = send_message("Test message")

        assert result is True
        mock_get_notifier.assert_called_once()
        mock_notifier.send.assert_called_once_with("Test message")
