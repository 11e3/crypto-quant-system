"""Tests for collector_fetch module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from src.data.collector_fetch import fetch_all_candles, fetch_candles


class TestFetchCandles:
    """Test cases for fetch_candles function."""

    @patch("src.data.collector_fetch.pyupbit.get_ohlcv")
    def test_fetch_candles_none_result(self, mock_get_ohlcv: MagicMock) -> None:
        """Test when pyupbit returns None (covers line 77)."""
        mock_get_ohlcv.return_value = None

        result = fetch_candles("KRW-BTC", "day", count=10)

        assert result is None
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.collector_fetch.pyupbit.get_ohlcv")
    @patch("src.data.collector_fetch.time.sleep")
    def test_fetch_candles_all_retries_fail(
        self, mock_sleep: MagicMock, mock_get_ohlcv: MagicMock
    ) -> None:
        """Test when all retries fail (covers line 77 else branch)."""
        # All 3 attempts fail
        mock_get_ohlcv.side_effect = Exception("Network error")

        result = fetch_candles("KRW-BTC", "day")

        assert result is None
        assert mock_get_ohlcv.call_count == 3
        # Sleep is only called after failures before last retry
        assert mock_sleep.call_count == 2

    @patch("src.data.collector_fetch.pyupbit.get_ohlcv")
    @patch("src.data.collector_fetch.time.sleep")
    def test_fetch_candles_retry_logic(
        self, mock_sleep: MagicMock, mock_get_ohlcv: MagicMock
    ) -> None:
        """Test retry logic when fetch fails."""
        mock_get_ohlcv.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            pd.DataFrame({"open": [100, 101], "high": [105, 106]}),
        ]

        result = fetch_candles("KRW-BTC", "day")

        assert result is not None
        assert len(result) == 2
        assert mock_get_ohlcv.call_count == 3
        assert mock_sleep.call_count == 2


class TestFetchAllCandles:
    """Test cases for fetch_all_candles function."""

    @patch("src.data.collector_fetch.fetch_candles")
    def test_fetch_all_candles_with_since_filtering(self, mock_fetch: MagicMock) -> None:
        """Test fetch_all_candles with since parameter filtering (covers line 102->123)."""
        # Create data with timestamps
        old_data = pd.DataFrame(
            {"open": [100], "high": [105], "low": [95], "close": [102]},
            index=pd.DatetimeIndex([datetime(2023, 1, 1)]),
        )
        new_data = pd.DataFrame(
            {"open": [110], "high": [115], "low": [105], "close": [112]},
            index=pd.DatetimeIndex([datetime(2023, 1, 10)]),
        )

        # First call returns old data, second returns new data
        mock_fetch.side_effect = [
            pd.concat([old_data, new_data]),
            pd.DataFrame(),  # Empty to stop pagination
        ]

        since = datetime(2023, 1, 5)
        result = fetch_all_candles("KRW-BTC", "day", since=since)

        # Should only contain data after 'since'
        assert result is not None
        assert len(result) == 1
        assert result.index.min() == datetime(2023, 1, 10)

    @patch("src.data.collector_fetch.fetch_candles")
    def test_fetch_all_candles_since_causes_empty_break(self, mock_fetch: MagicMock) -> None:
        """Test when since filter causes empty df and breaks loop (line 102->103)."""
        old_data = pd.DataFrame(
            {"open": [100], "high": [105]},
            index=pd.DatetimeIndex([datetime(2023, 1, 1)]),
        )

        mock_fetch.return_value = old_data

        # Set since to a date after all data
        since = datetime(2023, 1, 10)
        result = fetch_all_candles("KRW-BTC", "day", since=since, max_candles=200)

        # Should return None because filtered df is empty
        assert result is None
