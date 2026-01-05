"""
Unit tests for PositionManager.
"""

from unittest.mock import MagicMock

import pytest

from src.execution.event_bus import EventBus, set_event_bus
from src.execution.events import EventType, PositionEvent
from src.execution.position_manager import Position, PositionManager
from tests.fixtures.mock_exchange import MockExchange


class TestPosition:
    """Test cases for Position class."""

    def test_position_initialization(self) -> None:
        """Test Position initialization."""
        position = Position(
            ticker="KRW-BTC",
            entry_price=50_000_000.0,
            amount=0.001,
            entry_date="2024-01-01",
        )
        assert position.ticker == "KRW-BTC"
        assert position.entry_price == 50_000_000.0
        assert position.amount == 0.001
        assert position.entry_date == "2024-01-01"

    def test_position_value(self) -> None:
        """Test Position value calculation."""
        position = Position(
            ticker="KRW-BTC",
            entry_price=50_000_000.0,
            amount=0.001,
        )
        assert position.value == 50_000.0  # 50_000_000 * 0.001

    def test_position_repr(self) -> None:
        """Test Position string representation."""
        position = Position(
            ticker="KRW-BTC",
            entry_price=50_000_000.0,
            amount=0.001,
        )
        repr_str = repr(position)
        assert "KRW-BTC" in repr_str
        assert "50000000" in repr_str or "50000" in repr_str


class TestPositionManager:
    """Test cases for PositionManager."""

    def test_initialization(self, mock_exchange: MockExchange) -> None:
        """Test PositionManager initialization."""
        manager = PositionManager(mock_exchange, publish_events=False)
        assert manager.exchange == mock_exchange
        assert len(manager.positions) == 0
        assert manager.publish_events is False

    def test_has_position(self, mock_exchange: MockExchange) -> None:
        """Test checking if position exists."""
        manager = PositionManager(mock_exchange, publish_events=False)
        assert not manager.has_position("KRW-BTC")

        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        assert manager.has_position("KRW-BTC")
        assert not manager.has_position("KRW-ETH")

    def test_get_position(self, mock_exchange: MockExchange) -> None:
        """Test getting a position."""
        manager = PositionManager(mock_exchange, publish_events=False)
        assert manager.get_position("KRW-BTC") is None

        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        retrieved = manager.get_position("KRW-BTC")
        assert retrieved is not None
        assert retrieved.ticker == "KRW-BTC"
        assert retrieved.entry_price == 50_000_000.0
        assert retrieved.amount == 0.001

    def test_add_position(self, mock_exchange: MockExchange) -> None:
        """Test adding a position."""
        manager = PositionManager(mock_exchange, publish_events=False)
        position = manager.add_position(
            ticker="KRW-BTC",
            entry_price=50_000_000.0,
            amount=0.001,
            entry_date="2024-01-01",
        )

        assert position.ticker == "KRW-BTC"
        assert position.entry_price == 50_000_000.0
        assert position.amount == 0.001
        assert position.entry_date == "2024-01-01"
        assert manager.has_position("KRW-BTC")

    def test_add_position_duplicate(self, mock_exchange: MockExchange) -> None:
        """Test adding duplicate position raises error."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)

        with pytest.raises(ValueError, match="Position already exists"):
            manager.add_position("KRW-BTC", 50_000_000.0, 0.002)

    def test_add_position_with_events(self, mock_exchange: MockExchange) -> None:
        """Test adding a position with event publishing."""
        event_bus = EventBus()
        set_event_bus(event_bus)
        handler = MagicMock()
        event_bus.subscribe(EventType.POSITION_OPENED, handler)

        manager = PositionManager(mock_exchange, publish_events=True)
        position = manager.add_position("KRW-BTC", 50_000_000.0, 0.001)

        assert position is not None
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, PositionEvent)
        assert event.event_type == EventType.POSITION_OPENED
        assert event.ticker == "KRW-BTC"
        assert event.action == "opened"
        assert event.entry_price == 50_000_000.0
        assert event.amount == 0.001

    def test_remove_position(self, mock_exchange: MockExchange) -> None:
        """Test removing a position."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)

        position = manager.remove_position("KRW-BTC")
        assert position is not None
        assert position.ticker == "KRW-BTC"
        assert not manager.has_position("KRW-BTC")

    def test_remove_nonexistent_position(self, mock_exchange: MockExchange) -> None:
        """Test removing non-existent position returns None."""
        manager = PositionManager(mock_exchange, publish_events=False)
        position = manager.remove_position("KRW-BTC")
        assert position is None

    def test_remove_position_with_events(self, mock_exchange: MockExchange) -> None:
        """Test removing a position with event publishing."""
        event_bus = EventBus()
        set_event_bus(event_bus)
        handler = MagicMock()
        event_bus.subscribe(EventType.POSITION_CLOSED, handler)

        manager = PositionManager(mock_exchange, publish_events=True)
        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        mock_exchange.set_price("KRW-BTC", 55_000_000.0)

        position = manager.remove_position("KRW-BTC")

        assert position is not None
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, PositionEvent)
        assert event.event_type == EventType.POSITION_CLOSED
        assert event.ticker == "KRW-BTC"
        assert event.action == "closed"
        assert event.entry_price == 50_000_000.0
        assert event.amount == 0.001
        assert event.current_price == 55_000_000.0

    def test_get_current_price(self, mock_exchange: MockExchange) -> None:
        """Test getting current price."""
        manager = PositionManager(mock_exchange, publish_events=False)
        price = manager.get_current_price("KRW-BTC")
        assert price == 50_000_000.0

    def test_get_current_price_error(self, mock_exchange: MockExchange) -> None:
        """Test getting current price for non-existent ticker returns 0."""
        manager = PositionManager(mock_exchange, publish_events=False)
        price = manager.get_current_price("KRW-UNKNOWN")
        assert price == 0.0

    def test_calculate_pnl(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        # Price increased by 10%
        mock_exchange.set_price("KRW-BTC", 55_000_000.0)
        pnl = manager.calculate_pnl("KRW-BTC")
        expected_pnl = (55_000_000.0 - 50_000_000.0) * 0.001
        assert pnl == pytest.approx(expected_pnl)

    def test_calculate_pnl_with_price(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL with provided price."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        pnl = manager.calculate_pnl("KRW-BTC", current_price=55_000_000.0)
        expected_pnl = (55_000_000.0 - 50_000_000.0) * 0.001
        assert pnl == pytest.approx(expected_pnl)

    def test_calculate_pnl_no_position(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL for non-existent position returns 0."""
        manager = PositionManager(mock_exchange, publish_events=False)
        pnl = manager.calculate_pnl("KRW-BTC")
        assert pnl == 0.0

    def test_calculate_pnl_zero_price(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL with zero or negative price returns 0."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        # Test with zero price
        pnl = manager.calculate_pnl("KRW-BTC", current_price=0.0)
        assert pnl == 0.0

        # Test with negative price
        pnl = manager.calculate_pnl("KRW-BTC", current_price=-1.0)
        assert pnl == 0.0

    def test_calculate_pnl_pct(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL percentage."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        # Price increased by 10%
        mock_exchange.set_price("KRW-BTC", 55_000_000.0)
        pnl_pct = manager.calculate_pnl_pct("KRW-BTC")
        expected_pct = ((55_000_000.0 / 50_000_000.0) - 1.0) * 100.0
        assert pnl_pct == pytest.approx(expected_pct)

    def test_calculate_pnl_pct_with_price(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL percentage with provided price."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        pnl_pct = manager.calculate_pnl_pct("KRW-BTC", current_price=55_000_000.0)
        expected_pct = ((55_000_000.0 / 50_000_000.0) - 1.0) * 100.0
        assert pnl_pct == pytest.approx(expected_pct)

    def test_calculate_pnl_pct_no_position(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL percentage for non-existent position returns 0."""
        manager = PositionManager(mock_exchange, publish_events=False)
        pnl_pct = manager.calculate_pnl_pct("KRW-BTC")
        assert pnl_pct == 0.0

    def test_calculate_pnl_pct_zero_price(self, mock_exchange: MockExchange) -> None:
        """Test calculating PnL percentage with zero or negative price returns 0."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", entry_price=50_000_000.0, amount=0.001)

        # Test with zero current price
        pnl_pct = manager.calculate_pnl_pct("KRW-BTC", current_price=0.0)
        assert pnl_pct == 0.0

        # Test with negative current price
        pnl_pct = manager.calculate_pnl_pct("KRW-BTC", current_price=-1.0)
        assert pnl_pct == 0.0

        # Test with zero entry price (edge case - position with zero entry price)
        # Note: This is a theoretical edge case, as positions shouldn't have zero entry price
        # But we test it to cover the condition in the code
        manager.clear_all()
        manager.positions["KRW-ETH"] = Position("KRW-ETH", entry_price=0.0, amount=0.001)
        pnl_pct = manager.calculate_pnl_pct("KRW-ETH", current_price=50_000_000.0)
        assert pnl_pct == 0.0

    def test_get_all_positions(self, mock_exchange: MockExchange) -> None:
        """Test getting all positions."""
        manager = PositionManager(mock_exchange, publish_events=False)
        assert len(manager.get_all_positions()) == 0

        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        manager.add_position("KRW-ETH", 3_000_000.0, 0.01)

        positions = manager.get_all_positions()
        assert len(positions) == 2
        assert "KRW-BTC" in positions
        assert "KRW-ETH" in positions

    def test_get_position_count(self, mock_exchange: MockExchange) -> None:
        """Test getting position count."""
        manager = PositionManager(mock_exchange, publish_events=False)
        assert manager.get_position_count() == 0

        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        assert manager.get_position_count() == 1

        manager.add_position("KRW-ETH", 3_000_000.0, 0.01)
        assert manager.get_position_count() == 2

        manager.remove_position("KRW-BTC")
        assert manager.get_position_count() == 1

    def test_clear_all(self, mock_exchange: MockExchange) -> None:
        """Test clearing all positions."""
        manager = PositionManager(mock_exchange, publish_events=False)
        manager.add_position("KRW-BTC", 50_000_000.0, 0.001)
        manager.add_position("KRW-ETH", 3_000_000.0, 0.01)

        manager.clear_all()
        assert manager.get_position_count() == 0
        assert len(manager.get_all_positions()) == 0
