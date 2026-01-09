"""
Pair trading data preparation utilities.

Handles data filtering, signal preparation, and array building for pair trading.
"""

from datetime import date

import numpy as np
import pandas as pd

from src.backtester.models import BacktestConfig
from src.utils.memory import get_float_dtype


def filter_by_date_range(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    start_date: date | None,
    end_date: date | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter dataframes by date range."""
    if start_date is None and end_date is None:
        return df1, df2

    df1_index = pd.to_datetime(df1.index)
    df2_index = pd.to_datetime(df2.index)

    if start_date is not None:
        df1 = df1[df1_index >= pd.Timestamp(start_date)]
        df2 = df2[df2_index >= pd.Timestamp(start_date)]
    if end_date is not None:
        df1 = df1[df1_index <= pd.Timestamp(end_date)]
        df2 = df2[df2_index <= pd.Timestamp(end_date)]

    return df1, df2


def prepare_ticker_signals(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    merged_df: pd.DataFrame,
    ticker1: str,
    ticker2: str,
    config: BacktestConfig,
) -> dict[str, pd.DataFrame]:
    """Prepare signal DataFrames for each ticker."""
    df1_signals = df1.copy()
    df2_signals = df2.copy()

    common_dates = merged_df.index.intersection(df1_signals.index).intersection(df2_signals.index)
    common_dates = pd.DatetimeIndex(common_dates)

    df1_signals = df1_signals.loc[common_dates]
    df2_signals = df2_signals.loc[common_dates]
    merged_signals = merged_df.loc[common_dates]

    df1_signals["entry_signal"] = merged_signals["entry_signal"].astype(bool).values
    df1_signals["exit_signal"] = merged_signals["exit_signal"].astype(bool).values
    df2_signals["entry_signal"] = merged_signals["entry_signal"].astype(bool).values
    df2_signals["exit_signal"] = merged_signals["exit_signal"].astype(bool).values

    df1_signals["entry_price"] = df1_signals["close"] * (1 + config.slippage_rate)
    df1_signals["exit_price"] = df1_signals["close"] * (1 - config.slippage_rate)
    df2_signals["entry_price"] = df2_signals["close"] * (1 + config.slippage_rate)
    df2_signals["exit_price"] = df2_signals["close"] * (1 - config.slippage_rate)

    return {ticker1: df1_signals, ticker2: df2_signals}


def get_common_dates(
    merged_df: pd.DataFrame,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
) -> np.ndarray:
    """Get sorted array of common dates."""
    common_dates = merged_df.index.intersection(df1.index).intersection(df2.index)
    common_dates = pd.DatetimeIndex(common_dates)
    all_dates = {d.date() for d in common_dates.to_pydatetime()}
    return np.array(sorted(all_dates))


def build_pair_arrays(
    ticker_data: dict[str, pd.DataFrame],
    sorted_dates: np.ndarray,
    tickers: list[str],
) -> dict[str, np.ndarray]:
    """Build numpy arrays for pair trading."""
    n_tickers = 2
    n_dates = len(sorted_dates)
    float_dtype = get_float_dtype()

    arrays: dict[str, np.ndarray] = {
        "closes": np.full((n_tickers, n_dates), np.nan, dtype=float_dtype),
        "entry_signals": np.zeros((n_tickers, n_dates), dtype=bool),
        "exit_signals": np.zeros((n_tickers, n_dates), dtype=bool),
        "entry_prices": np.full((n_tickers, n_dates), np.nan, dtype=float_dtype),
        "exit_prices": np.full((n_tickers, n_dates), np.nan, dtype=float_dtype),
    }

    date_to_idx = {d: i for i, d in enumerate(sorted_dates)}

    for t_idx, ticker in enumerate(tickers):
        df = ticker_data[ticker]
        df_index = pd.DatetimeIndex(df.index)
        df_dates = pd.Series(df_index.to_pydatetime()).dt.date
        df_idx = df_dates.map(date_to_idx)
        valid_mask = df_idx.notna()

        if not valid_mask.any():
            continue

        idx = df_idx[valid_mask].astype(int).to_numpy()
        valid_idx = idx[idx < n_dates]
        if len(valid_idx) != len(idx):
            valid_mask = valid_mask & (df_idx < n_dates)
            idx = df_idx[valid_mask].astype(int).to_numpy()

        mask = valid_mask.to_numpy()
        arrays["closes"][t_idx, idx] = df.loc[mask, "close"].to_numpy(dtype=float_dtype)
        arrays["entry_signals"][t_idx, idx] = df.loc[mask, "entry_signal"].astype(bool).to_numpy()
        arrays["exit_signals"][t_idx, idx] = df.loc[mask, "exit_signal"].astype(bool).to_numpy()
        arrays["entry_prices"][t_idx, idx] = df.loc[mask, "entry_price"].to_numpy(dtype=float_dtype)
        arrays["exit_prices"][t_idx, idx] = df.loc[mask, "exit_price"].to_numpy(dtype=float_dtype)

    return arrays


def filter_pair_valid_dates(
    arrays: dict[str, np.ndarray],
    sorted_dates: np.ndarray,
    min_required_days: int,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Filter to valid dates for pair trading."""
    n_dates = len(sorted_dates)
    valid_date_mask = np.zeros(n_dates, dtype=bool)

    for d_idx in range(n_dates):
        has_valid_data = ~np.isnan(arrays["closes"][:, d_idx])
        if np.all(has_valid_data) and d_idx >= min_required_days:
            valid_date_mask[d_idx] = True

    valid_indices = np.where(valid_date_mask)[0]
    if len(valid_indices) == 0:
        return np.array([]), arrays

    first_valid_idx = valid_indices[0]
    last_valid_idx = valid_indices[-1] + 1

    sorted_dates = sorted_dates[first_valid_idx:last_valid_idx]
    for key in arrays:
        arrays[key] = arrays[key][:, first_valid_idx:last_valid_idx]

    return sorted_dates, arrays
