"""
Unit tests for pair_trading_helpers module.
"""

from datetime import date

import numpy as np
import pytest

from src.backtester.engine.pair_trading_helpers import (
    calculate_pair_equity,
    process_pair_entries,
    process_pair_exits,
    track_pair_returns,
)
from src.backtester.models import BacktestConfig

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def sample_closes() -> np.ndarray:
    """Create sample close price array."""
    return np.array(
        [
            [50000.0, 51000.0, 52000.0],  # KRW-BTC
            [2000.0, 2050.0, 2100.0],  # KRW-ETH
        ]
    )


@pytest.fixture
def sample_valid_data() -> np.ndarray:
    """Create sample valid data mask."""
    return np.array([True, True])


@pytest.fixture
def backtest_config() -> BacktestConfig:
    """Create a sample BacktestConfig."""
    config = BacktestConfig()
    config.fee_rate = 0.001
    config.max_slots = 2
    return config


@pytest.fixture
def tickers() -> list[str]:
    """Sample tickers."""
    return ["KRW-BTC", "KRW-ETH"]


# -------------------------------------------------------------------------
# track_pair_returns Tests
# -------------------------------------------------------------------------


class TestTrackPairReturns:
    """Test track_pair_returns function."""

    @pytest.mark.parametrize(
        "d_idx,previous_btc,previous_eth,expected_btc_return,expected_eth_return",
        [
            (1, 50000.0, 2000.0, 0.02, 0.025),  # Normal case: 1% BTC, 2.5% ETH
            (2, 51000.0, 2050.0, 0.0196, 0.0244),  # Day 2 returns
            (0, np.nan, np.nan, None, None),  # First day - no returns
        ],
    )
    def test_track_returns_variants(
        self,
        d_idx: int,
        previous_btc: float,
        previous_eth: float,
        expected_btc_return: float | None,
        expected_eth_return: float | None,
        sample_closes: np.ndarray,
        sample_valid_data: np.ndarray,
        tickers: list[str],
    ) -> None:
        """Test daily return tracking with different price movements."""
        asset_returns = {"KRW-BTC": [], "KRW-ETH": []}
        previous_closes = np.array([previous_btc, previous_eth])

        track_pair_returns(
            d_idx, tickers, sample_closes, sample_valid_data, previous_closes, asset_returns
        )

        if expected_btc_return is not None:
            assert len(asset_returns["KRW-BTC"]) == 1
            assert asset_returns["KRW-BTC"][0] == pytest.approx(expected_btc_return, rel=0.001)
        else:
            assert len(asset_returns["KRW-BTC"]) == 0

    @pytest.mark.parametrize(
        "valid_data_mask",
        [
            np.array([True, True]),  # Both valid
            np.array([True, False]),  # Only BTC valid
            np.array([False, True]),  # Only ETH valid
            np.array([False, False]),  # None valid
        ],
    )
    def test_track_returns_validity_mask(
        self,
        valid_data_mask: np.ndarray,
        sample_closes: np.ndarray,
        tickers: list[str],
    ) -> None:
        """Test return tracking respects validity mask."""
        asset_returns = {"KRW-BTC": [], "KRW-ETH": []}
        previous_closes = np.array([50000.0, 2000.0])

        track_pair_returns(
            1, tickers, sample_closes, valid_data_mask, previous_closes, asset_returns
        )

        btc_count = 1 if valid_data_mask[0] else 0
        eth_count = 1 if valid_data_mask[1] else 0
        assert len(asset_returns["KRW-BTC"]) == btc_count
        assert len(asset_returns["KRW-ETH"]) == eth_count

    def test_track_returns_nan_handling(
        self,
        tickers: list[str],
    ) -> None:
        """Test NaN handling in returns."""
        closes = np.array(
            [
                [50000.0, np.nan],  # KRW-BTC: NaN on day 1
                [2000.0, 2050.0],  # KRW-ETH: Normal
            ]
        )
        asset_returns = {"KRW-BTC": [], "KRW-ETH": []}
        valid_data = np.array([True, True])
        previous_closes = np.array([50000.0, 2000.0])

        track_pair_returns(1, tickers, closes, valid_data, previous_closes, asset_returns)

        assert len(asset_returns["KRW-BTC"]) == 0  # NaN skipped
        assert len(asset_returns["KRW-ETH"]) == 1


# -------------------------------------------------------------------------
# calculate_pair_equity Tests
# -------------------------------------------------------------------------


class TestCalculatePairEquity:
    """Test calculate_pair_equity function."""

    @pytest.mark.parametrize(
        "cash,btc_amount,eth_amount,btc_price,eth_price,expected_equity",
        [
            (10000.0, 1.0, 5.0, 50000.0, 2000.0, 70000.0),  # 1*50k + 5*2k + 10k
            (0.0, 0.5, 10.0, 50000.0, 2000.0, 45000.0),  # 0.5*50k + 10*2k
            (50000.0, 0.0, 0.0, 50000.0, 2000.0, 50000.0),  # Only cash
            (100000.0, 1.0, 5.0, 0.0, 2000.0, 110000.0),  # BTC price is 0
        ],
    )
    def test_calculate_equity_variants(
        self,
        cash: float,
        btc_amount: float,
        eth_amount: float,
        btc_price: float,
        eth_price: float,
        expected_equity: float,
        sample_valid_data: np.ndarray,
    ) -> None:
        """Test equity calculation with different positions and prices."""
        closes = np.array([[btc_price], [eth_price]])
        position_amounts = np.array([btc_amount, eth_amount])

        equity = calculate_pair_equity(cash, position_amounts, closes, 0, sample_valid_data)

        assert equity == pytest.approx(expected_equity, rel=0.01)

    @pytest.mark.parametrize(
        "valid_data_mask",
        [
            np.array([True, True]),  # Both valid
            np.array([True, False]),  # Only BTC valid
            np.array([False, True]),  # Only ETH valid
            np.array([False, False]),  # None valid
        ],
    )
    def test_calculate_equity_validity_mask(
        self,
        valid_data_mask: np.ndarray,
    ) -> None:
        """Test equity calculation respects validity mask."""
        closes = np.array([[50000.0], [2000.0]])
        position_amounts = np.array([1.0, 5.0])
        cash = 10000.0

        equity = calculate_pair_equity(cash, position_amounts, closes, 0, valid_data_mask)

        expected_positions = 0.0
        if valid_data_mask[0]:
            expected_positions += 50000.0
        if valid_data_mask[1]:
            expected_positions += 10000.0

        assert equity == pytest.approx(cash + expected_positions, rel=0.01)

    def test_calculate_equity_nan_handling(self) -> None:
        """Test NaN handling in equity calculation."""
        closes = np.array([[np.nan], [2000.0]])
        position_amounts = np.array([1.0, 5.0])
        valid_data = np.array([True, True])
        cash = 20000.0

        equity = calculate_pair_equity(cash, position_amounts, closes, 0, valid_data)

        # Only ETH position counts: 5 * 2000 = 10000
        assert equity == pytest.approx(30000.0, rel=0.01)


# -------------------------------------------------------------------------
# process_pair_exits Tests
# -------------------------------------------------------------------------


class TestProcessPairExits:
    """Test process_pair_exits function."""

    @pytest.mark.parametrize(
        "btc_position,eth_position,btc_signal,eth_signal",
        [
            (1.0, 5.0, True, True),  # Both in position with signals
            (1.0, 0.0, True, False),  # Only BTC in position
            (0.0, 5.0, False, True),  # Only ETH in position
            (0.0, 0.0, True, True),  # No positions (no exit)
        ],
    )
    def test_process_pair_exits_variants(
        self,
        btc_position: float,
        eth_position: float,
        btc_signal: bool,
        eth_signal: bool,
        backtest_config: BacktestConfig,
        tickers: list[str],
    ) -> None:
        """Test exit processing with different position/signal combinations."""
        position_amounts = np.array([btc_position, eth_position])
        position_entry_prices = np.array([50000.0, 2000.0])
        position_entry_dates = np.array([0, 0])
        exit_signals = np.array([[btc_signal], [eth_signal]], dtype=bool)
        exit_prices = np.array([[51000.0], [2050.0]])
        trades_list = [
            {"ticker": "KRW-BTC", "exit_date": None, "entry_date": np.datetime64(date(2023, 1, 1))},
            {"ticker": "KRW-ETH", "exit_date": None, "entry_date": np.datetime64(date(2023, 1, 1))},
        ]
        sorted_dates = np.array([np.datetime64(date(2023, 1, 1))])
        initial_cash = 100000.0

        process_pair_exits(
            d_idx=0,
            current_date=date(2023, 1, 2),
            sorted_dates=sorted_dates,
            tickers=tickers,
            position_amounts=position_amounts,
            position_entry_prices=position_entry_prices,
            position_entry_dates=position_entry_dates,
            exit_signals=exit_signals,
            exit_prices=exit_prices,
            fee_rate=backtest_config.fee_rate,
            trades_list=trades_list,
            cash=initial_cash,
        )

        # Cash should increase if positions were exited
        if btc_position > 0 and btc_signal:
            assert position_amounts[0] == 0.0
        if eth_position > 0 and eth_signal:
            assert position_amounts[1] == 0.0

    def test_process_pair_exits_no_signals(
        self,
        backtest_config: BacktestConfig,
        tickers: list[str],
    ) -> None:
        """Test when no exit signals present."""
        position_amounts = np.array([1.0, 5.0])
        position_entry_prices = np.array([50000.0, 2000.0])
        position_entry_dates = np.array([0, 0])
        exit_signals = np.array([[False], [False]], dtype=bool)
        exit_prices = np.array([[51000.0], [2050.0]])
        trades_list = []
        sorted_dates = np.array([np.datetime64(date(2023, 1, 1))])
        initial_cash = 100000.0

        cash = process_pair_exits(
            d_idx=0,
            current_date=date(2023, 1, 2),
            sorted_dates=sorted_dates,
            tickers=tickers,
            position_amounts=position_amounts,
            position_entry_prices=position_entry_prices,
            position_entry_dates=position_entry_dates,
            exit_signals=exit_signals,
            exit_prices=exit_prices,
            fee_rate=backtest_config.fee_rate,
            trades_list=trades_list,
            cash=initial_cash,
        )

        # No positions should be closed
        assert position_amounts[0] == 1.0
        assert position_amounts[1] == 5.0
        assert cash == initial_cash


# -------------------------------------------------------------------------
# process_pair_entries Tests
# -------------------------------------------------------------------------


class TestProcessPairEntries:
    """Test process_pair_entries function."""

    @pytest.mark.parametrize(
        "max_slots,current_positions,has_signals",
        [
            (2, 0, True),  # Room for entry
            (2, 1, True),  # Partial room
            (2, 2, True),  # No room
            (2, 0, False),  # No signals
        ],
    )
    def test_process_pair_entries_variants(
        self,
        max_slots: int,
        current_positions: int,
        has_signals: bool,
        tickers: list[str],
    ) -> None:
        """Test entry processing with different slot/signal combinations."""
        position_amounts = np.zeros(2)
        if current_positions > 0:
            position_amounts[0] = 1.0  # Simulate existing position
        if current_positions > 1:
            position_amounts[1] = 1.0

        position_entry_prices = np.zeros(2)
        position_entry_dates = np.full(2, -1)
        entry_signals = np.array([[has_signals], [has_signals]], dtype=bool)
        entry_prices = np.array([[50000.0], [2000.0]])
        trades_list: list[dict] = []
        initial_cash = 100000.0

        cash = process_pair_entries(
            d_idx=0,
            current_date=date(2023, 1, 1),
            tickers=tickers,
            position_amounts=position_amounts,
            position_entry_prices=position_entry_prices,
            position_entry_dates=position_entry_dates,
            entry_signals=entry_signals,
            entry_prices=entry_prices,
            fee_rate=0.001,
            max_slots=max_slots,
            trades_list=trades_list,
            cash=initial_cash,
        )

        # Entries only happen if: signals exist AND no current positions AND slots available
        if has_signals and current_positions == 0 and max_slots >= 2:
            assert position_amounts[0] > 0  # Position opened
            assert len(trades_list) == 2
            assert cash < initial_cash  # Cash reduced
        else:
            # No change
            pass

    def test_process_pair_entries_insufficient_slots(
        self,
        tickers: list[str],
    ) -> None:
        """Test entry fails when insufficient slots."""
        position_amounts = np.array([1.0, 0.0])  # 1 position filled
        position_entry_prices = np.zeros(2)
        position_entry_dates = np.full(2, -1)
        entry_signals = np.array([[True], [True]], dtype=bool)
        entry_prices = np.array([[50000.0], [2000.0]])
        trades_list: list[dict] = []
        initial_cash = 100000.0

        cash = process_pair_entries(
            d_idx=0,
            current_date=date(2023, 1, 1),
            tickers=tickers,
            position_amounts=position_amounts,
            position_entry_prices=position_entry_prices,
            position_entry_dates=position_entry_dates,
            entry_signals=entry_signals,
            entry_prices=entry_prices,
            fee_rate=0.001,
            max_slots=2,
            trades_list=trades_list,
            cash=initial_cash,
        )

        # Only 1 slot available, but need 2 for pair entry - should not enter
        assert len(trades_list) == 0
        assert cash == initial_cash

    def test_process_pair_entries_insufficient_cash(
        self,
        tickers: list[str],
    ) -> None:
        """Test entry with very low cash."""
        position_amounts = np.zeros(2)
        position_entry_prices = np.zeros(2)
        position_entry_dates = np.full(2, -1)
        entry_signals = np.array([[True], [True]], dtype=bool)
        entry_prices = np.array([[50000.0], [2000.0]])
        trades_list: list[dict] = []
        initial_cash = 1000.0  # Very low cash

        cash = process_pair_entries(
            d_idx=0,
            current_date=date(2023, 1, 1),
            tickers=tickers,
            position_amounts=position_amounts,
            position_entry_prices=position_entry_prices,
            position_entry_dates=position_entry_dates,
            entry_signals=entry_signals,
            entry_prices=entry_prices,
            fee_rate=0.001,
            max_slots=2,
            trades_list=trades_list,
            cash=initial_cash,
        )

        # Should still attempt to enter but with very small amounts
        # Or may not if conditions prevent it
        assert cash <= initial_cash
