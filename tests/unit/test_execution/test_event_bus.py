"""
Unit tests for EventBus.
"""

from unittest.mock import MagicMock, patch

from src.execution.event_bus import EventBus, get_event_bus, set_event_bus
from src.execution.events import (
    Event,
    EventType,
    OrderEvent,
    PositionEvent,
    SignalEvent,
)


class TestEventBus:
    """Test cases for EventBus."""

    def test_initialization(self) -> None:
        """Test EventBus initialization."""
        bus = EventBus()
        assert len(bus._subscribers) == 0
        assert len(bus._global_subscribers) == 0

    def test_subscribe_direct_call(self) -> None:
        """Test subscribe as direct call."""
        bus = EventBus()
        handler = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler)

        assert handler in bus._subscribers[EventType.ORDER_PLACED]
        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 1

    def test_subscribe_decorator(self) -> None:
        """Test subscribe as decorator."""
        bus = EventBus()

        @bus.subscribe(EventType.ORDER_PLACED)
        def handler(event: Event) -> None:
            pass

        assert handler in bus._subscribers[EventType.ORDER_PLACED]
        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 1

    def test_subscribe_global(self) -> None:
        """Test subscribe to all events (global)."""
        bus = EventBus()
        handler = MagicMock()

        bus.subscribe(None, handler)

        assert handler in bus._global_subscribers
        assert bus.get_subscriber_count(None) == 1

    def test_subscribe_global_decorator(self) -> None:
        """Test subscribe to all events as decorator."""
        bus = EventBus()

        @bus.subscribe()
        def handler(event: Event) -> None:
            pass

        assert handler in bus._global_subscribers
        assert bus.get_subscriber_count(None) == 1

    def test_subscribe_multiple_handlers(self) -> None:
        """Test subscribing multiple handlers to same event."""
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler1)
        bus.subscribe(EventType.ORDER_PLACED, handler2)

        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 2
        assert handler1 in bus._subscribers[EventType.ORDER_PLACED]
        assert handler2 in bus._subscribers[EventType.ORDER_PLACED]

    def test_unsubscribe(self) -> None:
        """Test unsubscribe from events."""
        bus = EventBus()
        handler = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler)
        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 1

        result = bus.unsubscribe(EventType.ORDER_PLACED, handler)
        assert result is True
        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 0

    def test_unsubscribe_not_found(self) -> None:
        """Test unsubscribe when handler is not subscribed."""
        bus = EventBus()
        handler = MagicMock()

        result = bus.unsubscribe(EventType.ORDER_PLACED, handler)
        assert result is False

    def test_publish_specific_subscriber(self) -> None:
        """Test publish to specific subscribers."""
        bus = EventBus()
        handler = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        bus.publish(event)

        handler.assert_called_once_with(event)

    def test_publish_multiple_handlers(self) -> None:
        """Test publish to multiple handlers."""
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler1)
        bus.subscribe(EventType.ORDER_PLACED, handler2)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        bus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_publish_global_subscribers(self) -> None:
        """Test publish to global subscribers."""
        bus = EventBus()
        global_handler = MagicMock()
        specific_handler = MagicMock()

        bus.subscribe(None, global_handler)  # Global subscriber
        bus.subscribe(EventType.ORDER_PLACED, specific_handler)  # Specific subscriber
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        bus.publish(event)

        # Global handler should receive all events
        global_handler.assert_called_once_with(event)
        # Specific handler should also receive the event
        specific_handler.assert_called_once_with(event)

    def test_publish_no_subscribers(self) -> None:
        """Test publish when no subscribers exist."""
        bus = EventBus()
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        # Should not raise any errors
        bus.publish(event)

    def test_publish_handler_error(self) -> None:
        """Test publish when handler raises error."""
        bus = EventBus()

        def failing_handler(event: Event) -> None:
            raise ValueError("Handler error")

        bus.subscribe(EventType.ORDER_PLACED, failing_handler)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        # Should not raise error, just log it
        with patch("src.execution.event_bus.logger") as mock_logger:
            bus.publish(event)
            mock_logger.error.assert_called()

    def test_publish_multiple_handlers_one_fails(self) -> None:
        """Test publish when one handler fails but others succeed."""
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock(side_effect=ValueError("Error"))

        bus.subscribe(EventType.ORDER_PLACED, handler1)
        bus.subscribe(EventType.ORDER_PLACED, handler2)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        # Should not raise error
        with patch("src.execution.event_bus.logger"):
            bus.publish(event)

        # handler1 should still be called
        handler1.assert_called_once_with(event)

    def test_clear(self) -> None:
        """Test clear all subscribers."""
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler1)
        bus.subscribe(None, handler2)

        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 1
        assert bus.get_subscriber_count(None) == 1

        bus.clear()

        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 0
        assert bus.get_subscriber_count(None) == 0

    def test_get_subscriber_count_specific(self) -> None:
        """Test get_subscriber_count for specific event type."""
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, handler1)
        bus.subscribe(EventType.ORDER_PLACED, handler2)
        bus.subscribe(EventType.ORDER_FILLED, handler1)

        assert bus.get_subscriber_count(EventType.ORDER_PLACED) == 2
        assert bus.get_subscriber_count(EventType.ORDER_FILLED) == 1
        assert bus.get_subscriber_count(EventType.ORDER_CANCELLED) == 0

    def test_get_subscriber_count_global(self) -> None:
        """Test get_subscriber_count for global subscribers."""
        bus = EventBus()
        handler = MagicMock()

        bus.subscribe(None, handler)
        assert bus.get_subscriber_count(None) == 1

    def test_publish_different_event_types(self) -> None:
        """Test publish different event types."""
        bus = EventBus()
        order_handler = MagicMock()
        signal_handler = MagicMock()
        position_handler = MagicMock()

        bus.subscribe(EventType.ORDER_PLACED, order_handler)
        bus.subscribe(EventType.ENTRY_SIGNAL, signal_handler)
        bus.subscribe(EventType.POSITION_OPENED, position_handler)

        order_event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )
        signal_event = SignalEvent(
            event_type=EventType.ENTRY_SIGNAL,
            ticker="KRW-BTC",
            signal_type="entry",
            price=50000.0,
        )
        position_event = PositionEvent(
            event_type=EventType.POSITION_OPENED,
            ticker="KRW-BTC",
            amount=1.0,
            entry_price=50000.0,
        )

        bus.publish(order_event)
        bus.publish(signal_event)
        bus.publish(position_event)

        order_handler.assert_called_once_with(order_event)
        signal_handler.assert_called_once_with(signal_event)
        position_handler.assert_called_once_with(position_event)

    def test_publish_global_subscriber_receives_all(self) -> None:
        """Test that global subscriber receives all event types."""
        bus = EventBus()
        global_handler = MagicMock()

        bus.subscribe(None, global_handler)

        order_event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )
        signal_event = SignalEvent(
            event_type=EventType.ENTRY_SIGNAL,
            ticker="KRW-BTC",
            signal_type="entry",
            price=50000.0,
        )

        bus.publish(order_event)
        bus.publish(signal_event)

        assert global_handler.call_count == 2
        global_handler.assert_any_call(order_event)
        global_handler.assert_any_call(signal_event)

    def test_publish_global_subscriber_error(self) -> None:
        """Test publish when global subscriber raises error."""
        bus = EventBus()

        def failing_global_handler(event: Event) -> None:
            raise ValueError("Global handler error")

        bus.subscribe(None, failing_global_handler)
        event = OrderEvent(
            event_type=EventType.ORDER_PLACED,
            order_id="test-123",
            ticker="KRW-BTC",
            side="buy",
            amount=1.0,
            price=50000.0,
            status="pending",
        )

        # Should not raise error, just log it
        with patch("src.execution.event_bus.logger") as mock_logger:
            bus.publish(event)
            mock_logger.error.assert_called()
            # Verify error message contains "global event handler"
            call_args = mock_logger.error.call_args[0][0]
            assert "global event handler" in call_args


class TestGetEventBus:
    """Test cases for get_event_bus and set_event_bus."""

    def test_get_event_bus_creates_singleton(self) -> None:
        """Test get_event_bus creates singleton instance."""
        # Reset the global event bus
        set_event_bus(None)
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2
        assert isinstance(bus1, EventBus)

    def test_set_event_bus(self) -> None:
        """Test set_event_bus sets custom event bus."""
        custom_bus = EventBus()
        set_event_bus(custom_bus)

        bus = get_event_bus()
        assert bus is custom_bus

    def test_set_event_bus_none(self) -> None:
        """Test set_event_bus with None resets to new instance."""
        custom_bus = EventBus()
        set_event_bus(custom_bus)

        set_event_bus(None)
        bus = get_event_bus()

        assert bus is not custom_bus
        assert isinstance(bus, EventBus)
