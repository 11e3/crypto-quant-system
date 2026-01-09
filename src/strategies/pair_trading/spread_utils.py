"""
Spread calculation utilities for pair trading.
"""

import pandas as pd

__all__ = ["calculate_spread_for_pair"]


def calculate_spread_for_pair(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    spread_type: str,
    lookback_period: int,
) -> pd.DataFrame:
    """
    Calculate spread indicators for a pair of assets.

    This function merges data from two tickers and calculates spread indicators.

    Args:
        df1: DataFrame for first asset (ticker1)
        df2: DataFrame for second asset (ticker2)
        spread_type: Type of spread calculation ("ratio" or "difference")
        lookback_period: Period for spread mean/std calculation

    Returns:
        DataFrame with merged data and spread indicators
    """
    from src.utils.indicators import sma

    # Align indices (use intersection of dates)
    common_dates = df1.index.intersection(df2.index)
    df1_aligned = df1.loc[common_dates].copy()
    df2_aligned = df2.loc[common_dates].copy()

    # Create merged dataframe
    merged_df = pd.DataFrame(index=common_dates)
    merged_df["close_asset1"] = df1_aligned["close"]
    merged_df["close_asset2"] = df2_aligned["close"]

    # Add other columns for reference (if available)
    _add_optional_columns(merged_df, df1_aligned, "_asset1")
    _add_optional_columns(merged_df, df2_aligned, "_asset2")

    # Calculate spread
    close1 = merged_df["close_asset1"]
    close2 = merged_df["close_asset2"]

    if spread_type == "ratio":
        merged_df["spread"] = close1 / close2
    else:
        merged_df["spread"] = close1 - close2

    # Calculate spread statistics
    merged_df["spread_mean"] = sma(merged_df["spread"], lookback_period)
    merged_df["spread_std"] = (
        merged_df["spread"].rolling(window=lookback_period, min_periods=lookback_period).std()
    )

    # Calculate Z-score
    merged_df["z_score"] = (merged_df["spread"] - merged_df["spread_mean"]) / merged_df[
        "spread_std"
    ].replace(0, 1)

    return merged_df


def _add_optional_columns(
    merged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    suffix: str,
) -> None:
    """Add optional OHLCV columns from source to merged dataframe."""
    for col in ["open", "high", "low"]:
        if col in source_df.columns:
            merged_df[f"{col}{suffix}"] = source_df[col]

    if "volume" in source_df.columns:
        merged_df[f"volume{suffix}"] = source_df["volume"]
    else:
        merged_df[f"volume{suffix}"] = 0
