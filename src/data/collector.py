"""
Upbit candle data collector with incremental update support.

Fetches OHLCV data from Upbit API and stores in parquet format.
Supports incremental updates by fetching only new data since last update.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd
import pyupbit

from src.config import (
    RAW_DATA_DIR,
    UPBIT_API_RATE_LIMIT_DELAY,
    UPBIT_MAX_CANDLES_PER_REQUEST,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Type aliases
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


class UpbitDataCollector:
    """Collects and manages Upbit OHLCV candle data."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """
        Initialize the data collector.

        Args:
            data_dir: Directory to store parquet files. Defaults to data/raw/
        """
        self.data_dir = data_dir or RAW_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_parquet_path(self, ticker: str, interval: Interval) -> Path:
        """
        Generate parquet file path for given ticker and interval.

        Args:
            ticker: Upbit ticker (e.g., 'KRW-BTC')
            interval: Candle interval (e.g., 'day', 'minute240')

        Returns:
            Path to parquet file
        """
        return self.data_dir / f"{ticker}_{interval}.parquet"

    def _load_existing_data(self, filepath: Path) -> pd.DataFrame | None:
        """
        Load existing parquet data if available.

        Args:
            filepath: Path to parquet file

        Returns:
            DataFrame with existing data or None if file doesn't exist
        """
        if filepath.exists():
            df = pd.read_parquet(filepath)
            df.index = pd.to_datetime(df.index)
            return df
        return None

    def _fetch_candles(
        self,
        ticker: str,
        interval: Interval,
        count: int = UPBIT_MAX_CANDLES_PER_REQUEST,
        to: datetime | None = None,
    ) -> pd.DataFrame | None:
        """
        Fetch candle data from Upbit API.

        Args:
            ticker: Upbit ticker (e.g., 'KRW-BTC')
            interval: Candle interval
            count: Number of candles to fetch (max 200)
            to: End datetime for fetching (exclusive)

        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            df = pyupbit.get_ohlcv(
                ticker=ticker,
                interval=interval,
                count=min(count, UPBIT_MAX_CANDLES_PER_REQUEST),
                to=to,
            )
            return df
        except Exception as e:
            logger.error(f"Error fetching candles for {ticker}: {e}", exc_info=True)
            return None

    def _fetch_all_candles(
        self,
        ticker: str,
        interval: Interval,
        since: datetime | None = None,
        max_candles: int = 10000,
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
            df = self._fetch_candles(ticker, interval, to=to_datetime)

            if df is None or df.empty:
                break

            # Filter data if we have a since datetime
            if since is not None:
                # Keep only rows after 'since' datetime
                df = df[df.index > since]

                if df.empty:
                    break

            all_data.append(df)
            total_fetched += len(df)

            # Get earliest datetime for next pagination
            to_datetime = df.index.min()

            # If we got less than max, we've reached the end
            if len(df) < UPBIT_MAX_CANDLES_PER_REQUEST:
                break

            # Rate limiting
            time.sleep(UPBIT_API_RATE_LIMIT_DELAY)
            logger.debug(f"Fetched {total_fetched} candles for {ticker}...")

        if not all_data:
            return None

        # Combine all dataframes and sort by datetime
        combined = pd.concat(all_data)
        combined = combined[~combined.index.duplicated(keep="first")]
        combined = combined.sort_index()

        return combined

    def collect(
        self,
        ticker: str,
        interval: Interval,
        full_refresh: bool = False,
    ) -> int:
        """
        Collect candle data for a ticker and interval.

        Performs incremental update if data already exists, unless full_refresh is True.

        Args:
            ticker: Upbit ticker (e.g., 'KRW-BTC')
            interval: Candle interval (e.g., 'day', 'minute240')
            full_refresh: If True, fetches all data ignoring existing

        Returns:
            Number of new candles added
        """
        filepath = self._get_parquet_path(ticker, interval)

        # Load existing data
        existing_df = None if full_refresh else self._load_existing_data(filepath)

        # Determine since datetime for incremental update
        since: datetime | None = None
        if existing_df is not None and not existing_df.empty:
            since = existing_df.index.max()
            logger.info(f"Incremental update for {ticker} ({interval}) since {since}")
        else:
            logger.info(f"Full collection for {ticker} ({interval})")

        # Fetch new candles
        new_df = self._fetch_all_candles(ticker, interval, since=since)

        if new_df is None or new_df.empty:
            logger.info(f"No new data for {ticker} ({interval})")
            return 0

        # Merge with existing data
        if existing_df is not None and not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df])
            combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
            combined_df = combined_df.sort_index()
        else:
            combined_df = new_df

        # Ensure index name
        combined_df.index.name = "datetime"

        # Save to parquet
        combined_df.to_parquet(filepath, engine="pyarrow")

        new_count = len(new_df)
        total_count = len(combined_df)
        logger.info(f"Saved {ticker} ({interval}): +{new_count} new, {total_count} total")

        return new_count

    def collect_multiple(
        self,
        tickers: list[str],
        intervals: list[Interval],
        full_refresh: bool = False,
    ) -> dict[str, int]:
        """
        Collect data for multiple tickers and intervals.

        Args:
            tickers: List of Upbit tickers
            intervals: List of intervals
            full_refresh: If True, fetches all data ignoring existing

        Returns:
            Dictionary with counts of new candles per ticker-interval
        """
        results: dict[str, int] = {}

        for ticker in tickers:
            for interval in intervals:
                key = f"{ticker}_{interval}"
                try:
                    count = self.collect(ticker, interval, full_refresh)
                    results[key] = count
                    time.sleep(UPBIT_API_RATE_LIMIT_DELAY)  # Rate limiting between pairs
                except Exception as e:
                    logger.error(f"Error collecting {key}: {e}", exc_info=True)
                    results[key] = -1

        return results
