"""
Unit tests for event_loop module.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.backtester.engine.event_data_loader import Position
from src.backtester.engine.event_loop import (
    calculate_portfolio_equity,
    close_remaining_positions,
    process_entries,
    process_exits,
)
from src.backtester.models import BacktestConfig, Trade

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def backtest_config() -> BacktestConfig:
    """Create a sample BacktestConfig."""
    config = BacktestConfig()
    config.initial_capital = 100000.0
    config.max_slots = 3
    config.stop_loss_pct = 0.05
    config.take_profit_pct = 0.10
    return config


@pytest.fixture
def sample_position() -> Position:
    """Create a sample Position."""
    return Position(
        ticker="KRW-BTC",
        entry_price=50000.0,
        entry_date=date(2023, 1, 1),
        amount=1.0,
        highest_price=50000.0,
    )


@pytest.fixture
def current_data() -> dict[str, pd.Series]:
    """Create sample current market data."""
    return {
        "KRW-BTC": pd.Series(
            {
                "open": 50100.0,
                "high": 51000.0,
                "low": 49000.0,
                "close": 50500.0,
                "volume": 100.0,
                "entry_signal": False,
                "exit_signal": False,
            }
        ),
        "KRW-ETH": pd.Series(
            {
                "open": 2000.0,
                "high": 2050.0,
                "low": 1950.0,
                "close": 2025.0,
                "volume": 500.0,
                "entry_signal": True,
                "exit_signal": False,
            }
        ),
    }


# -------------------------------------------------------------------------
# process_exits Tests
# -------------------------------------------------------------------------


class TestProcessExits:
    """Test process_exits function."""

    @patch("src.backtester.engine.event_loop.check_exit_condition")
    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_process_exits_no_positions(
        self, mock_execute_exit: MagicMock, mock_check: MagicMock, backtest_config: BacktestConfig
    ) -> None:
        """Test when no positions exist."""
        trades, revenue, remaining = process_exits({}, {}, date(2023, 1, 1), backtest_config)

        assert trades == []
        assert revenue == 0.0
        assert remaining == {}

    @patch("src.backtester.engine.event_loop.check_exit_condition")
    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_process_exits_position_not_in_data(
        self,
        mock_execute_exit: MagicMock,
        mock_check: MagicMock,
        sample_position: Position,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when position ticker not in current_data."""
        positions = {"KRW-BTC": sample_position}
        trades, revenue, remaining = process_exits(positions, {}, date(2023, 1, 1), backtest_config)

        # Position should remain if ticker not in data
        assert len(remaining) == 1
        assert "KRW-BTC" in remaining

    @patch("src.backtester.engine.event_loop.check_exit_condition")
    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_process_exits_no_signal(
        self,
        mock_execute_exit: MagicMock,
        mock_check: MagicMock,
        sample_position: Position,
        current_data: dict[str, pd.Series],
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when exit condition not triggered."""
        mock_check.return_value = (False, "")
        positions = {"KRW-BTC": sample_position}

        trades, revenue, remaining = process_exits(
            positions, current_data, date(2023, 1, 1), backtest_config
        )

        assert len(trades) == 0
        assert revenue == 0.0
        assert len(remaining) == 1

    @patch("src.backtester.engine.event_loop.check_exit_condition")
    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_process_exits_with_signal(
        self,
        mock_execute_exit: MagicMock,
        mock_check: MagicMock,
        sample_position: Position,
        current_data: dict[str, pd.Series],
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when exit condition is triggered."""
        mock_check.return_value = (True, "take_profit")
        mock_trade = MagicMock(spec=Trade)
        mock_execute_exit.return_value = (mock_trade, 1000.0)

        positions = {"KRW-BTC": sample_position}
        trades, revenue, remaining = process_exits(
            positions, current_data, date(2023, 1, 1), backtest_config
        )

        assert len(trades) == 1
        assert revenue == 1000.0
        assert "KRW-BTC" not in remaining


# -------------------------------------------------------------------------
# process_entries Tests
# -------------------------------------------------------------------------


class TestProcessEntries:
    """Test process_entries function."""

    @pytest.mark.parametrize(
        "max_slots,current_positions,entry_signals",
        [
            (3, 0, 1),  # 3 slots available, 1 signal expected
            (3, 1, 1),  # 2 slots available
            (3, 3, 0),  # 0 slots available
            (2, 2, 0),  # All slots full
        ],
    )
    @patch("src.backtester.engine.event_loop.execute_entry")
    def test_process_entries_available_slots(
        self,
        mock_entry: MagicMock,
        max_slots: int,
        current_positions: int,
        entry_signals: int,
        backtest_config: BacktestConfig,
        current_data: dict[str, pd.Series],
    ) -> None:
        """Test available slots calculation."""
        config = BacktestConfig()
        config.max_slots = max_slots
        config.initial_capital = backtest_config.initial_capital

        positions = {}
        if current_positions > 0:
            for i in range(current_positions):
                positions[f"KRW-ASSET{i}"] = Position(
                    ticker=f"KRW-ASSET{i}",
                    entry_price=10000.0,
                    entry_date=date(2023, 1, 1),
                    amount=1.0,
                    highest_price=10000.0,
                )

        mock_entry.return_value = (None, 0.0)
        updated, cash, signals = process_entries(
            positions, current_data, date(2023, 1, 1), 50000.0, config
        )

        assert signals == entry_signals

    @patch("src.backtester.engine.event_loop.execute_entry")
    def test_process_entries_no_slots(
        self,
        mock_entry: MagicMock,
        backtest_config: BacktestConfig,
        current_data: dict[str, pd.Series],
    ) -> None:
        """Test when max_slots is reached (line 106 branch)."""
        # Fill all slots
        positions = {f"KRW-ASSET{i}": MagicMock() for i in range(backtest_config.max_slots)}

        updated, cash, signals = process_entries(
            positions, current_data, date(2023, 1, 1), 50000.0, backtest_config
        )

        # Should return immediately
        assert updated == positions
        assert cash == 50000.0

    @patch("src.backtester.engine.event_loop.execute_entry")
    def test_process_entries_missing_signal(
        self,
        mock_entry: MagicMock,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when entry_signal not in data (line 119 branch)."""
        current_data = {
            "KRW-BTC": pd.Series({"close": 50000.0}),  # No entry_signal key
        }

        updated, cash, signals = process_entries(
            {}, current_data, date(2023, 1, 1), 50000.0, backtest_config
        )

        assert signals == 0
        mock_entry.assert_not_called()

    @pytest.mark.parametrize("entry_signal", [True, False])
    @patch("src.backtester.engine.event_loop.execute_entry")
    def test_process_entries_signal_variants(
        self,
        mock_entry: MagicMock,
        entry_signal: bool,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test with different entry_signal values."""
        current_data = {
            "KRW-BTC": pd.Series(
                {"close": 50000.0, "entry_signal": entry_signal, "open": 50100.0, "high": 51000.0}
            ),
        }

        mock_entry.return_value = (None, 0.0)
        updated, cash, signals = process_entries(
            {}, current_data, date(2023, 1, 1), 50000.0, backtest_config
        )

        if entry_signal:
            assert signals == 1
        else:
            assert signals == 0

    @patch("src.backtester.engine.event_loop.execute_entry")
    def test_process_entries_position_already_exists(
        self,
        mock_entry: MagicMock,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when ticker already in positions (line 115 skip)."""
        positions = {"KRW-BTC": MagicMock()}
        current_data = {
            "KRW-BTC": pd.Series(
                {
                    "close": 50000.0,
                    "entry_signal": True,
                    "open": 50100.0,
                    "high": 51000.0,
                }
            ),
        }

        updated, cash, signals = process_entries(
            positions, current_data, date(2023, 1, 1), 50000.0, backtest_config
        )

        # KRW-BTC should not be processed again
        assert signals == 0  # Entry signal not counted


# -------------------------------------------------------------------------
# calculate_portfolio_equity Tests
# -------------------------------------------------------------------------


class TestCalculatePortfolioEquity:
    """Test calculate_portfolio_equity function."""

    @pytest.mark.parametrize(
        "position_amount,close_price,cash,expected_equity",
        [
            (1.0, 50000.0, 10000.0, 60000.0),  # 1 * 50000 + 10000
            (2.0, 25000.0, 5000.0, 55000.0),  # 2 * 25000 + 5000
            (0.5, 10000.0, 45000.0, 50000.0),  # 0.5 * 10000 + 45000
            (0.0, 50000.0, 100000.0, 100000.0),  # No position
        ],
    )
    def test_calculate_equity_variants(
        self,
        position_amount: float,
        close_price: float,
        cash: float,
        expected_equity: float,
    ) -> None:
        """Test equity calculation with different positions and prices."""
        position = Position(
            ticker="KRW-BTC",
            entry_price=50000.0,
            entry_date=date(2023, 1, 1),
            amount=position_amount,
            highest_price=50000.0,
        )
        positions = {"KRW-BTC": position} if position_amount > 0 else {}

        current_data = {
            "KRW-BTC": pd.Series({"close": close_price}),
        }

        equity = calculate_portfolio_equity(positions, current_data, cash)
        assert equity == pytest.approx(expected_equity, rel=0.01)

    def test_calculate_equity_position_not_in_data(self) -> None:
        """Test when position ticker not in current_data (line 163 skip)."""
        position = Position(
            ticker="KRW-BTC",
            entry_price=50000.0,
            entry_date=date(2023, 1, 1),
            amount=1.0,
            highest_price=50000.0,
        )
        positions = {"KRW-BTC": position}
        current_data = {"KRW-ETH": pd.Series({"close": 2000.0})}

        equity = calculate_portfolio_equity(positions, current_data, 10000.0)

        # Only cash counted since KRW-BTC not in data
        assert equity == 10000.0

    def test_calculate_equity_multiple_positions(self) -> None:
        """Test with multiple positions."""
        positions = {
            "KRW-BTC": Position(
                ticker="KRW-BTC",
                entry_price=50000.0,
                entry_date=date(2023, 1, 1),
                amount=1.0,
                highest_price=50000.0,
            ),
            "KRW-ETH": Position(
                ticker="KRW-ETH",
                entry_price=2000.0,
                entry_date=date(2023, 1, 1),
                amount=10.0,
                highest_price=2000.0,
            ),
        }

        current_data = {
            "KRW-BTC": pd.Series({"close": 51000.0}),
            "KRW-ETH": pd.Series({"close": 2050.0}),
        }

        equity = calculate_portfolio_equity(positions, current_data, 29000.0)
        # 51000 + (10 * 2050) + 29000 = 100500
        assert equity == pytest.approx(100500.0, rel=0.01)


# -------------------------------------------------------------------------
# close_remaining_positions Tests
# -------------------------------------------------------------------------


class TestCloseRemainingPositions:
    """Test close_remaining_positions function."""

    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_close_no_positions(
        self, mock_exit: MagicMock, backtest_config: BacktestConfig
    ) -> None:
        """Test when no positions to close."""
        ticker_data = {"KRW-BTC": pd.DataFrame()}
        trades = close_remaining_positions({}, ticker_data, date(2023, 12, 31), backtest_config)

        assert trades == []

    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_close_position_ticker_not_in_data(
        self,
        mock_exit: MagicMock,
        sample_position: Position,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when position ticker not in ticker_data (line 193 skip)."""
        positions = {"KRW-BTC": sample_position}
        ticker_data = {}

        trades = close_remaining_positions(
            positions, ticker_data, date(2023, 12, 31), backtest_config
        )

        assert trades == []
        mock_exit.assert_not_called()

    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_close_final_data_not_found(
        self,
        mock_exit: MagicMock,
        sample_position: Position,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test when final_date not in dataframe (line 202 empty result)."""
        positions = {"KRW-BTC": sample_position}
        df = pd.DataFrame(
            {
                "index_date": [date(2023, 1, 1), date(2023, 1, 2)],
                "close": [50000.0, 51000.0],
            }
        )
        ticker_data = {"KRW-BTC": df}

        trades = close_remaining_positions(
            positions, ticker_data, date(2023, 12, 31), backtest_config
        )

        # Final date not in data, so no closing trade
        assert trades == []

    @patch("src.backtester.engine.event_loop.execute_exit")
    def test_close_with_final_data(
        self,
        mock_exit: MagicMock,
        sample_position: Position,
        backtest_config: BacktestConfig,
    ) -> None:
        """Test closing position with final date data."""
        positions = {"KRW-BTC": sample_position}
        df = pd.DataFrame(
            {
                "index_date": [date(2023, 1, 1), date(2023, 12, 31)],
                "close": [50000.0, 52000.0],
                "open": [49900.0, 52100.0],
                "high": [51000.0, 53000.0],
                "low": [49000.0, 51000.0],
            }
        )
        ticker_data = {"KRW-BTC": df}

        trades = close_remaining_positions(
            positions, ticker_data, date(2023, 12, 31), backtest_config
        )

        # close_remaining_positions creates Trade directly, doesn't call execute_exit
        assert len(trades) == 1
        assert trades[0].ticker == "KRW-BTC"
        assert trades[0].exit_date == date(2023, 12, 31)
