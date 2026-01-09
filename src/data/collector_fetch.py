"""
Upbit API candle fetching utilities.
"""

import time
from datetime import datetime
from typing import Literal

import pandas as pd
import pyupbit

from src.config import UPBIT_API_RATE_LIMIT_DELAY, UPBIT_MAX_CANDLES_PER_REQUEST
from src.utils.logger import get_logger

__all__ = ["fetch_candles", "fetch_all_candles"]

logger = get_logger(__name__)

Interval = Literal[
    "minute1",
    "minute3",
    "minute5",
    "minute10",
    "minute15",
    "minute30",
    "minute60",
    "minute240",
    "day",
    "week",
    "month",
]


def fetch_candles(
    ticker: str,
    interval: Interval,
    count: int = UPBIT_MAX_CANDLES_PER_REQUEST,
    to: datetime | None = None,
) -> pd.DataFrame | None:
    """
    Fetch candle data from Upbit API with retry logic.

    Args:
        ticker: Upbit ticker (e.g., 'KRW-BTC')
        interval: Candle interval
        count: Number of candles to fetch (max 200)
        to: End datetime for fetching (exclusive)

    Returns:
        DataFrame with OHLCV data or None if error
    """
    max_retries = 3
    retry_delay = 1.0

    for attempt in range(max_retries):
        try:
            result = pyupbit.get_ohlcv(
                ticker=ticker,
                interval=interval,
                count=min(count, UPBIT_MAX_CANDLES_PER_REQUEST),
                to=to,
            )
            if result is None:
                return None
            return pd.DataFrame(result)
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (2**attempt)
                logger.warning(
                    f"Error fetching {ticker} (attempt {attempt + 1}): {e}. "
                    f"Retrying in {sleep_time}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"Error fetching {ticker} after {max_retries} attempts: {e}")
                return None
    return None


def fetch_all_candles(
    ticker: str,
    interval: Interval,
    since: datetime | None = None,
    max_candles: int = 50000,
) -> pd.DataFrame | None:
    """
    Fetch all candles with pagination support.

    Args:
        ticker: Upbit ticker
        interval: Candle interval
        since: Only fetch candles after this datetime
        max_candles: Maximum number of candles to fetch

    Returns:
        DataFrame with all fetched OHLCV data
    """
    all_data: list[pd.DataFrame] = []
    to_datetime: datetime | None = None
    total_fetched = 0

    while total_fetched < max_candles:
        df = fetch_candles(ticker, interval, to=to_datetime)

        if df is None or df.empty:
            break

        if since is not None:
            df = df[df.index > since]
            if df.empty:
                break

        all_data.append(df)
        total_fetched += len(df)
        to_datetime = df.index.min()

        if len(df) < UPBIT_MAX_CANDLES_PER_REQUEST:
            break

        time.sleep(UPBIT_API_RATE_LIMIT_DELAY)
        logger.debug(f"Fetched {total_fetched} candles for {ticker}...")

    if not all_data:
        return None

    combined = pd.concat(all_data)
    combined = combined[~combined.index.duplicated(keep="first")]
    combined = combined.sort_index()

    return combined
