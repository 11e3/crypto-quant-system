"""Tests for signal_processor module."""

import pandas as pd
import pytest

from src.backtester.engine.signal_processor import add_price_columns, get_valid_dates_mask
from src.backtester.models import BacktestConfig


@pytest.fixture
def sample_config() -> BacktestConfig:
    """Create sample backtest config."""
    return BacktestConfig(
        initial_capital=1000000,
        slippage_rate=0.001,
        fee_rate=0.0005,
    )


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create sample DataFrame."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [95.0, 96.0, 97.0],
            "close": [102.0, 103.0, 104.0],
            "entry_signal": [True, False, True],
            "exit_signal": [False, True, True],
        }
    )


class TestSignalProcessor:
    """Test cases for signal_processor functions."""

    def test_add_price_columns_with_target(
        self, sample_config: BacktestConfig, sample_df: pd.DataFrame
    ) -> None:
        """Test add_price_columns with target column."""
        sample_df["target"] = [101.0, 102.0, 103.0]
        sample_df["entry_price"] = [0.0, 0.0, 0.0]
        sample_df["exit_price"] = [0.0, 0.0, 0.0]

        result = add_price_columns(sample_df, sample_config)

        assert "entry_price" in result.columns
        assert "exit_price" in result.columns
        assert "is_whipsaw" in result.columns

    def test_add_price_columns_no_target(
        self, sample_config: BacktestConfig, sample_df: pd.DataFrame
    ) -> None:
        """Test add_price_columns without target column (uses close)."""
        result = add_price_columns(sample_df, sample_config)

        assert "entry_price" in result.columns
        # Entry price should be based on close + slippage
        expected_entry = sample_df["close"] * (1 + sample_config.slippage_rate)
        pd.testing.assert_series_equal(result["entry_price"], expected_entry, check_names=False)

    def test_get_valid_dates_mask_all_columns(self) -> None:
        """Test get_valid_dates_mask with sma and target columns (lines 67-74)."""
        df = pd.DataFrame(
            {
                "close": [100.0, None, 102.0],
                "sma": [99.0, 100.0, None],
                "target": [101.0, None, 103.0],
            }
        )

        mask = get_valid_dates_mask(df)

        # Only first row should be valid (all values present)
        assert mask.iloc[0] is True or mask.iloc[0]
        assert not mask.iloc[1]  # close is None
        assert not mask.iloc[2]  # sma is None

    def test_get_valid_dates_mask_no_optional_columns(self) -> None:
        """Test get_valid_dates_mask without sma/target columns."""
        df = pd.DataFrame(
            {
                "close": [100.0, 101.0, None],
            }
        )

        mask = get_valid_dates_mask(df)

        assert mask.iloc[0]
        assert mask.iloc[1]
        assert not mask.iloc[2]
