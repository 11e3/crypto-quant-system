"""
OHLCV data update utilities for UpbitDataSource.
"""

from datetime import datetime

import pandas as pd

from src.utils.logger import get_logger

__all__ = ["calculate_update_count", "merge_ohlcv_data"]

logger = get_logger(__name__)


def calculate_update_count(
    latest_timestamp: datetime,
    interval: str,
) -> int:
    """
    Calculate number of candles to fetch for incremental update.

    Args:
        latest_timestamp: Latest timestamp in existing data
        interval: Data interval (e.g., 'day', 'minute240')

    Returns:
        Number of candles to fetch
    """
    if interval == "day":
        days_since = (datetime.now() - latest_timestamp).days
        return min(days_since + 10, 200)
    elif interval.startswith("minute"):
        try:
            minutes = int(interval.replace("minute", ""))
            minutes_since = (datetime.now() - latest_timestamp).total_seconds() / 60
            return min(int(minutes_since / minutes) + 10, 200)
        except ValueError:
            return 200
    else:
        return 200


def merge_ohlcv_data(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    latest_timestamp: datetime,
) -> tuple[pd.DataFrame, int]:
    """
    Merge existing and new OHLCV data.

    Args:
        existing_df: Existing DataFrame
        new_df: New DataFrame to merge
        latest_timestamp: Latest timestamp to filter new data

    Returns:
        Tuple of (merged DataFrame, number of new rows added)
    """
    # Filter to only new data
    new_df = new_df[new_df.index > latest_timestamp]

    if len(new_df) == 0:
        return existing_df, 0

    # Merge with existing data
    updated_df = pd.concat([existing_df, new_df])
    updated_df = updated_df[~updated_df.index.duplicated(keep="last")]
    updated_df = updated_df.sort_index()

    return updated_df, len(new_df)
