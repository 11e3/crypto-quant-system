"""
Unit tests for execution handlers.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.execution.event_bus import EventBus, set_event_bus
from src.execution.events import (
    ErrorEvent,
    EventType,
    OrderEvent,
    PositionEvent,
    SignalEvent,
    SystemEvent,
)
from src.execution.handlers.notification_handler import NotificationHandler
from src.execution.handlers.trade_handler import TradeHandler
from src.utils.telegram import TelegramNotifier


@pytest.fixture
def mock_telegram() -> MagicMock:
    """Create a mock Telegram notifier."""
    mock = MagicMock(spec=TelegramNotifier)
    mock.send = MagicMock()
    mock.send_trade_signal = MagicMock()
    return mock


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh event bus for each test."""
    bus = EventBus()
    set_event_bus(bus)
    return bus


class TestNotificationHandler:
    """Test cases for NotificationHandler."""

    def test_initialization(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test NotificationHandler initialization."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        assert handler.telegram == mock_telegram
        assert handler.event_bus is not None

    def test_initialization_without_telegram(self, event_bus: EventBus) -> None:
        """Test NotificationHandler initialization without Telegram."""
        handler = NotificationHandler(telegram_notifier=None)
        assert handler.telegram is None
        assert handler.event_bus is not None

    def test_handle_entry_signal(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling entry signal event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = SignalEvent(
            event_type=EventType.ENTRY_SIGNAL,
            ticker="KRW-BTC",
            signal_type="entry",
            price=50000.0,
            target_price=51000.0,
        )

        handler._handle_entry_signal(event)

        mock_telegram.send_trade_signal.assert_called_once()
        call_args = mock_telegram.send_trade_signal.call_args
        assert call_args[0][0] == "ENTRY_SIGNAL"
        assert call_args[0][1] == "KRW-BTC"
        assert call_args[0][2] == 50000.0

    def test_handle_entry_signal_no_telegram(self, event_bus: EventBus) -> None:
        """Test handling entry signal event without Telegram."""
        handler = NotificationHandler(telegram_notifier=None)
        event = SignalEvent(
            event_type=EventType.ENTRY_SIGNAL,
            ticker="KRW-BTC",
            signal_type="entry",
            price=50000.0,
        )

        handler._handle_entry_signal(event)
        # Should not raise error

    def test_handle_exit_signal(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling exit signal event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = SignalEvent(
            event_type=EventType.EXIT_SIGNAL,
            ticker="KRW-BTC",
            signal_type="exit",
            price=49000.0,
        )

        handler._handle_exit_signal(event)

        mock_telegram.send_trade_signal.assert_called_once()
        call_args = mock_telegram.send_trade_signal.call_args
        assert call_args[0][0] == "EXIT_SIGNAL"
        assert call_args[0][1] == "KRW-BTC"
        assert call_args[0][2] == 49000.0

    def test_handle_order_placed(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling order placed event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="buy",
            amount=0.001,
            price=50000.0,
            status="pending",
        )

        handler._handle_order_placed(event)

        mock_telegram.send_trade_signal.assert_called_once()
        call_args = mock_telegram.send_trade_signal.call_args
        assert call_args[0][0] == "BUY"
        assert call_args[0][1] == "KRW-BTC"
        assert call_args[0][2] == 50000.0

    def test_handle_order_placed_sell(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling sell order placed event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="sell",
            amount=0.001,
            price=49000.0,
            status="pending",
        )

        handler._handle_order_placed(event)

        mock_telegram.send_trade_signal.assert_called_once()
        call_args = mock_telegram.send_trade_signal.call_args
        assert call_args[0][0] == "SELL"

    def test_handle_position_opened(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling position opened event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = PositionEvent(
            event_type=EventType.POSITION_OPENED,
            ticker="KRW-BTC",
            action="opened",
            entry_price=50000.0,
            amount=0.001,
            current_price=51000.0,
        )

        handler._handle_position_opened(event)

        mock_telegram.send_trade_signal.assert_called_once()
        call_args = mock_telegram.send_trade_signal.call_args
        assert call_args[0][0] == "POSITION_OPENED"
        assert call_args[0][1] == "KRW-BTC"
        assert call_args[0][2] == 50000.0

    def test_handle_position_closed(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling position closed event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = PositionEvent(
            event_type=EventType.POSITION_CLOSED,
            ticker="KRW-BTC",
            action="closed",
            entry_price=50000.0,
            amount=0.001,
            current_price=49000.0,
            pnl=-100.0,
            pnl_pct=-2.0,
        )

        handler._handle_position_closed(event)

        mock_telegram.send.assert_called_once()
        call_args = mock_telegram.send.call_args
        assert "Position closed" in call_args[0][0]
        assert "KRW-BTC" in call_args[0][0]

    def test_handle_error(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling error event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        error = ValueError("Test error")
        event = ErrorEvent(
            event_type=EventType.ERROR,
            error_type="ValueError",
            error_message="Test error",
            exception=error,
        )

        handler._handle_error(event)

        mock_telegram.send.assert_called_once()
        call_args = mock_telegram.send.call_args
        assert "ERROR" in call_args[0][0].upper()
        assert "Test error" in call_args[0][0]

    def test_handle_daily_reset(self, mock_telegram: MagicMock, event_bus: EventBus) -> None:
        """Test handling daily reset event."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        event = SystemEvent(
            event_type=EventType.DAILY_RESET,
            action="daily_reset",
            details={"timestamp": "2024-01-01"},
        )

        handler._handle_daily_reset(event)

        mock_telegram.send.assert_called_once()
        call_args = mock_telegram.send.call_args
        assert "DAILY RESET" in call_args[0][0].upper()

    def test_handle_entry_signal_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling entry signal when Telegram raises error."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send_trade_signal.side_effect = Exception("Telegram error")
        event = SignalEvent(
            event_type=EventType.ENTRY_SIGNAL,
            ticker="KRW-BTC",
            signal_type="entry",
            price=50000.0,
        )

        handler._handle_entry_signal(event)
        # Should not raise error

    def test_handle_exit_signal_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling exit signal when Telegram raises error."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send_trade_signal.side_effect = Exception("Telegram error")
        event = SignalEvent(
            event_type=EventType.EXIT_SIGNAL,
            ticker="KRW-BTC",
            signal_type="exit",
            price=49000.0,
        )

        handler._handle_exit_signal(event)
        # Should not raise error

    def test_handle_order_placed_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling order placed when Telegram raises error (lines 91-92)."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send_trade_signal.side_effect = Exception("Telegram error")
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="buy",
            amount=0.001,
            price=50000.0,
            status="pending",
        )

        with patch("src.execution.handlers.notification_handler.logger") as mock_logger:
            handler._handle_order_placed(event)
            mock_logger.error.assert_called_once()
            assert "Error sending order notification" in mock_logger.error.call_args[0][0]

    def test_handle_position_opened_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling position opened when Telegram raises error (lines 104-105)."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send_trade_signal.side_effect = Exception("Telegram error")
        event = PositionEvent(
            event_type=EventType.POSITION_OPENED,
            ticker="KRW-BTC",
            action="opened",
            entry_price=50000.0,
            amount=0.001,
            current_price=51000.0,
        )

        with patch("src.execution.handlers.notification_handler.logger") as mock_logger:
            handler._handle_position_opened(event)
            mock_logger.error.assert_called_once()
            assert "Error sending position opened notification" in mock_logger.error.call_args[0][0]

    def test_handle_position_closed_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling position closed when Telegram raises error (lines 116-117)."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send.side_effect = Exception("Telegram error")
        event = PositionEvent(
            event_type=EventType.POSITION_CLOSED,
            ticker="KRW-BTC",
            action="closed",
            entry_price=50000.0,
            amount=0.001,
            current_price=49000.0,
            pnl=-100.0,
            pnl_pct=-2.0,
        )

        with patch("src.execution.handlers.notification_handler.logger") as mock_logger:
            handler._handle_position_closed(event)
            mock_logger.error.assert_called_once()
            assert "Error sending position closed notification" in mock_logger.error.call_args[0][0]

    def test_handle_error_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling error event when Telegram raises error (lines 125-126)."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send.side_effect = Exception("Telegram error")
        error = ValueError("Test error")
        event = ErrorEvent(
            event_type=EventType.ERROR,
            error_type="ValueError",
            error_message="Test error",
            exception=error,
        )

        with patch("src.execution.handlers.notification_handler.logger") as mock_logger:
            handler._handle_error(event)
            mock_logger.error.assert_called_once()
            assert "Error sending error notification" in mock_logger.error.call_args[0][0]

    def test_handle_daily_reset_telegram_error(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test handling daily reset when Telegram raises error (lines 133-134)."""
        handler = NotificationHandler(telegram_notifier=mock_telegram)
        mock_telegram.send.side_effect = Exception("Telegram error")
        event = SystemEvent(
            event_type=EventType.DAILY_RESET,
            action="daily_reset",
            details={"timestamp": "2024-01-01"},
        )

        with patch("src.execution.handlers.notification_handler.logger") as mock_logger:
            handler._handle_daily_reset(event)
            mock_logger.error.assert_called_once()
            assert "Error sending daily reset notification" in mock_logger.error.call_args[0][0]


class TestTradeHandler:
    """Test cases for TradeHandler."""

    def test_initialization(self, event_bus: EventBus) -> None:
        """Test TradeHandler initialization."""
        handler = TradeHandler()
        assert handler.event_bus is not None

    def test_handle_order_placed(self, event_bus: EventBus) -> None:
        """Test handling order placed event."""
        handler = TradeHandler()
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="buy",
            amount=0.001,
            price=50000.0,
            status="pending",
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_order_placed(event)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "ORDER PLACED" in log_message.upper()
            assert "KRW-BTC" in log_message

    def test_handle_order_placed_sell(self, event_bus: EventBus) -> None:
        """Test handling sell order placed event."""
        handler = TradeHandler()
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="sell",
            amount=0.001,
            price=49000.0,
            status="pending",
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_order_placed(event)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "SELL" in log_message.upper()

    def test_handle_order_placed_wrong_event_type(self, event_bus: EventBus) -> None:
        """Test handling order placed with wrong event type."""
        handler = TradeHandler()
        from src.execution.events import Event

        event = Event(event_type=EventType.ORDER_PLACED)  # Base Event, not OrderEvent

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_order_placed(event)
            mock_logger.info.assert_not_called()

    def test_handle_order_filled(self, event_bus: EventBus) -> None:
        """Test handling order filled event."""
        handler = TradeHandler()
        event = OrderEvent(
            event_type=EventType.ORDER_FILLED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="buy",
            amount=0.001,
            price=50000.0,
            status="filled",
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_order_filled(event)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "ORDER FILLED" in log_message.upper()
            assert "order-123" in log_message

    def test_handle_order_failed(self, event_bus: EventBus) -> None:
        """Test handling order failed event."""
        handler = TradeHandler()
        event = OrderEvent(
            event_type=EventType.ORDER_FAILED,
            order_id="order-123",
            ticker="KRW-BTC",
            side="buy",
            amount=0.001,
            price=50000.0,
            status="failed",
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_order_failed(event)
            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "ORDER FAILED" in log_message.upper()

    def test_handle_position_opened(self, event_bus: EventBus) -> None:
        """Test handling position opened event."""
        handler = TradeHandler()
        event = PositionEvent(
            event_type=EventType.POSITION_OPENED,
            ticker="KRW-BTC",
            action="opened",
            entry_price=50000.0,
            amount=0.001,
            current_price=51000.0,
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_position_opened(event)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "POSITION OPENED" in log_message.upper()
            assert "KRW-BTC" in log_message

    def test_handle_position_closed(self, event_bus: EventBus) -> None:
        """Test handling position closed event."""
        handler = TradeHandler()
        event = PositionEvent(
            event_type=EventType.POSITION_CLOSED,
            ticker="KRW-BTC",
            action="closed",
            entry_price=50000.0,
            amount=0.001,
            current_price=49000.0,
            pnl=-100.0,
            pnl_pct=-2.0,
        )

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_position_closed(event)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "POSITION CLOSED" in log_message.upper()
            assert "KRW-BTC" in log_message

    def test_handle_position_opened_wrong_event_type(self, event_bus: EventBus) -> None:
        """Test handling position opened with wrong event type."""
        handler = TradeHandler()
        from src.execution.events import Event

        event = Event(event_type=EventType.POSITION_OPENED)  # Base Event, not PositionEvent

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_position_opened(event)
            mock_logger.info.assert_not_called()

    def test_handle_position_closed_wrong_event_type(self, event_bus: EventBus) -> None:
        """Test handling position closed with wrong event type."""
        handler = TradeHandler()
        from src.execution.events import Event

        event = Event(event_type=EventType.POSITION_CLOSED)  # Base Event, not PositionEvent

        with patch("src.execution.handlers.trade_handler.logger") as mock_logger:
            handler._handle_position_closed(event)
            mock_logger.info.assert_not_called()

    def test_register_handlers_notification(
        self, mock_telegram: MagicMock, event_bus: EventBus
    ) -> None:
        """Test that NotificationHandler registers all handlers."""
        NotificationHandler(telegram_notifier=mock_telegram)

        # Check that handlers are registered
        assert event_bus.get_subscriber_count(EventType.ENTRY_SIGNAL) >= 1
        assert event_bus.get_subscriber_count(EventType.EXIT_SIGNAL) >= 1
        assert event_bus.get_subscriber_count(EventType.ORDER_PLACED) >= 1
        assert event_bus.get_subscriber_count(EventType.POSITION_OPENED) >= 1
        assert event_bus.get_subscriber_count(EventType.POSITION_CLOSED) >= 1
        assert event_bus.get_subscriber_count(EventType.ERROR) >= 1
        assert event_bus.get_subscriber_count(EventType.DAILY_RESET) >= 1

    def test_register_handlers_trade(self, event_bus: EventBus) -> None:
        """Test that TradeHandler registers all handlers."""
        TradeHandler()

        # Check that handlers are registered
        assert event_bus.get_subscriber_count(EventType.ORDER_PLACED) >= 1
        assert event_bus.get_subscriber_count(EventType.ORDER_FILLED) >= 1
        assert event_bus.get_subscriber_count(EventType.ORDER_FAILED) >= 1
        assert event_bus.get_subscriber_count(EventType.POSITION_OPENED) >= 1
        assert event_bus.get_subscriber_count(EventType.POSITION_CLOSED) >= 1
