from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.backtester.engine import (
    BacktestConfig,
    BacktestResult,
    VectorizedBacktestEngine,
)
from src.strategies.base import Strategy

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def mock_config():
    return BacktestConfig(
        initial_capital=10000.0,
        fee_rate=0.001,
        slippage_rate=0.001,
        max_slots=2,
        position_sizing="equal",
        use_cache=False,
    )


@pytest.fixture
def engine(mock_config):
    return VectorizedBacktestEngine(config=mock_config)


@pytest.fixture
def mock_strategy():
    strategy = MagicMock(spec=Strategy)
    strategy.name = "TestStrategy"
    # Basic attributes needed for cache params
    strategy.entry_conditions = MagicMock()
    strategy.entry_conditions.conditions = []
    strategy.exit_conditions = MagicMock()
    strategy.exit_conditions.conditions = []
    strategy.required_indicators.return_value = []
    return strategy


@pytest.fixture
def sample_data():
    """Create a sample OHLCV DataFrame with sufficient history."""
    periods = 50
    dates = pd.date_range(start="2023-01-01", periods=periods, freq="D")

    # Initialize with clean data types
    df = pd.DataFrame(
        {
            "open": np.full(periods, 100.0, dtype="float64"),
            "high": np.full(periods, 105.0, dtype="float64"),
            "low": np.full(periods, 95.0, dtype="float64"),
            "close": np.full(periods, 100.0, dtype="float64"),
            "volume": np.full(periods, 1000.0, dtype="float64"),
            "sma": np.full(periods, 90.0, dtype="float64"),
            "target": np.full(periods, 100.5, dtype="float64"),
            "entry_signal": np.zeros(periods, dtype=bool),
            "exit_signal": np.zeros(periods, dtype=bool),
        },
        index=dates,
    )

    return df


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------


class TestVectorizedBacktestEngine:
    def test_load_data_success(self, engine, tmp_path, sample_data):
        file_path = tmp_path / "test_data.parquet"
        sample_data.to_parquet(file_path)

        df = engine.load_data(file_path)
        assert len(df) == 50
        assert "close" in df.columns

    def test_load_data_file_not_found(self, engine):
        with pytest.raises(FileNotFoundError):
            engine.load_data(Path("non_existent_file.parquet"))

    def test_add_price_columns(self, engine, sample_data):
        sample_data["entry_signal"] = True
        sample_data["exit_signal"] = True

        df = engine._add_price_columns(sample_data)

        assert df["is_whipsaw"].all()
        # VBO logic: target * (1 + slippage)
        expected_entry = 100.5 * (1 + 0.001)
        assert df["entry_price"].iloc[0] == pytest.approx(expected_entry)

    def test_calculate_metrics_vectorized(self, engine):
        dates = np.array([date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)])
        equity_curve = np.array([10000.0, 11000.0, 9900.0])
        trades_df = pd.DataFrame()

        result = engine._calculate_metrics_vectorized(equity_curve, dates, trades_df)

        assert result.total_return == pytest.approx(-1.0)
        assert result.mdd == pytest.approx(10.0)

    def test_run_basic_flow(self, engine, mock_strategy, sample_data, tmp_path):
        """Test standard backtest run with sufficient data."""
        fpath = tmp_path / "KRW-BTC_day.parquet"

        # Set Signals using label-based indexing (safer/clearer than iloc)
        # Index 30 = 2023-01-31, Index 35 = 2023-02-05
        sample_data.loc[sample_data.index[30], "entry_signal"] = True
        sample_data.loc[sample_data.index[35], "exit_signal"] = True

        # [FIX] Explicitly enforce boolean type to ensure engine reads it correctly
        sample_data["entry_signal"] = sample_data["entry_signal"].astype(bool)
        sample_data["exit_signal"] = sample_data["exit_signal"].astype(bool)

        sample_data.to_parquet(fpath)
        data_files = {"KRW-BTC": fpath}

        # Important: Mock must return the dataframe containing signals
        mock_strategy.calculate_indicators.return_value = sample_data
        mock_strategy.generate_signals.return_value = sample_data

        with patch("src.backtester.engine.optimize_dtypes", side_effect=lambda x: x):
            result = engine.run(mock_strategy, data_files)

        assert isinstance(result, BacktestResult)
        assert result.total_trades == 1
        assert result.trades[0].ticker == "KRW-BTC"
        assert result.trades[0].is_closed  # This should now pass
        assert result.trades[0].exit_date == sample_data.index[35].date()

    def test_run_whipsaw_logic(self, engine, mock_strategy, sample_data, tmp_path):
        """Test whipsaw logic (entry and close < sma same day)."""
        fpath = tmp_path / "KRW-ETH_day.parquet"

        idx = 30
        sample_data.loc[sample_data.index[idx], "entry_signal"] = True
        sample_data.loc[sample_data.index[idx], "close"] = 100.0
        sample_data.loc[sample_data.index[idx], "sma"] = 9999.0  # SMA > Close -> Whipsaw

        sample_data.to_parquet(fpath)
        data_files = {"KRW-ETH": fpath}

        mock_strategy.calculate_indicators.return_value = sample_data
        mock_strategy.generate_signals.return_value = sample_data

        with patch("src.backtester.engine.optimize_dtypes", side_effect=lambda x: x):
            result = engine.run(mock_strategy, data_files)

        assert len(result.trades) == 1
        assert result.trades[0].is_whipsaw
        assert result.trades[0].entry_date == result.trades[0].exit_date

    def test_run_pair_trading(self, engine, tmp_path):
        """Test pair trading using a real dummy class to pass isinstance checks."""

        # Define a dummy class for PairTradingStrategy that implements abstract methods
        class MockPairTradingStrategy(Strategy):
            def __init__(self):
                super().__init__("PairStrat")
                self.lookback_period = 10

            def required_indicators(self):
                return []

            def calculate_indicators(self, df):
                # Required abstract method implementation
                return df

            def generate_signals(self, df):
                # Required abstract method implementation
                return df

            def calculate_spread_for_pair(self, df1, df2):
                # Return a DF with entry/exit signals
                merged = pd.DataFrame(index=df1.index)
                merged["entry_signal"] = False
                merged["exit_signal"] = False

                # Set signals
                if len(merged) > 30:
                    merged.iloc[30, merged.columns.get_loc("entry_signal")] = True
                    merged.iloc[35, merged.columns.get_loc("exit_signal")] = True
                return merged

        # Patch the module-level PairTradingStrategy with our Dummy CLASS
        with patch("src.backtester.engine.PairTradingStrategy", MockPairTradingStrategy):
            strategy_instance = MockPairTradingStrategy()

            # Setup Data
            periods = 50
            dates = pd.date_range("2023-01-01", periods=periods)
            df = pd.DataFrame(
                {
                    "open": np.full(periods, 100.0, dtype="float64"),
                    "high": np.full(periods, 105.0, dtype="float64"),
                    "low": np.full(periods, 95.0, dtype="float64"),
                    "close": np.full(periods, 100.0, dtype="float64"),
                    "volume": np.full(periods, 1000.0, dtype="float64"),
                    "entry_signal": np.zeros(periods, dtype=bool),
                    "exit_signal": np.zeros(periods, dtype=bool),
                    # Note: engine._run_pair_trading expects entry/exit_price or calculates them
                    "entry_price": np.full(periods, 100.0, dtype="float64"),
                    "exit_price": np.full(periods, 100.0, dtype="float64"),
                },
                index=dates,
            )

            fpath1 = tmp_path / "A_day.parquet"
            fpath2 = tmp_path / "B_day.parquet"
            df.to_parquet(fpath1)
            df.to_parquet(fpath2)
            data_files = {"A": fpath1, "B": fpath2}

            with patch("src.backtester.engine.optimize_dtypes", side_effect=lambda x: x):
                result = engine.run(strategy_instance, data_files)

            assert len(result.trades) == 2  # 1 trade per ticker

    @patch("src.backtester.engine.calculate_position_size")
    def test_position_sizing_integration(
        self, mock_calc_size, engine, mock_strategy, sample_data, tmp_path
    ):
        """Test position sizing integration for single asset."""
        # Set config to use volatility sizing
        engine.config.position_sizing = "volatility"

        fpath = tmp_path / "KRW-BTC_day.parquet"
        sample_data.iloc[30, sample_data.columns.get_loc("entry_signal")] = True
        sample_data.loc[sample_data.index[30], "entry_signal"] = True
        sample_data.to_parquet(fpath)
        data_files = {"KRW-BTC": fpath}

        mock_strategy.calculate_indicators.return_value = sample_data
        mock_strategy.generate_signals.return_value = sample_data

        # Mock return of position sizing (single asset uses calculate_position_size)
        mock_calc_size.return_value = 5000.0

        with patch("src.backtester.engine.optimize_dtypes", side_effect=lambda x: x):
            engine.run(mock_strategy, data_files)

        # Verify call
        mock_calc_size.assert_called()

    def test_risk_metrics_integration(self, engine):
        dates = np.array([date(2023, 1, 1), date(2023, 1, 2)])
        equity = np.array([100.0, 110.0])
        trades = pd.DataFrame()

        with patch("src.backtester.engine.calculate_portfolio_risk_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock(var_95=0.05)
            result = engine._calculate_metrics_vectorized(equity, dates, trades)
            assert result.risk_metrics is not None
