"""
Unit tests for UpbitDataSource module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data.upbit_source import UpbitDataSource


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def data_source(temp_data_dir: Path) -> UpbitDataSource:
    """Create UpbitDataSource instance for testing."""
    return UpbitDataSource(data_dir=temp_data_dir)


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(5)],
            "high": [105.0 + i for i in range(5)],
            "low": [95.0 + i for i in range(5)],
            "close": [102.0 + i for i in range(5)],
            "volume": [1000.0 + i * 10 for i in range(5)],
        },
        index=dates,
    )


class TestUpbitDataSource:
    """Test cases for UpbitDataSource class."""

    def test_initialization(self, temp_data_dir: Path) -> None:
        """Test UpbitDataSource initialization."""
        data_source = UpbitDataSource(data_dir=temp_data_dir)

        assert data_source.data_dir == temp_data_dir
        assert temp_data_dir.exists()

    def test_initialization_creates_directory(self, tmp_path: Path) -> None:
        """Test that initialization creates directory if it doesn't exist."""
        data_dir = tmp_path / "new_data"
        UpbitDataSource(data_dir=data_dir)

        assert data_dir.exists()
        assert data_dir.is_dir()

    def test_get_filepath(self, data_source: UpbitDataSource) -> None:
        """Test filepath generation."""
        path = data_source._get_filepath("KRW-BTC", "day")

        assert path == data_source.data_dir / "KRW-BTC_day.parquet"

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_get_ohlcv(
        self,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test getting OHLCV data from API."""
        mock_get_ohlcv.return_value = sample_ohlcv_data

        result = data_source.get_ohlcv("KRW-BTC", "day", count=5)

        assert result is not None
        assert len(result) == len(sample_ohlcv_data)
        assert "open" in result.columns
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_get_ohlcv_with_date_range(
        self,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test getting OHLCV data with date range."""
        mock_get_ohlcv.return_value = sample_ohlcv_data

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        result = data_source.get_ohlcv("KRW-BTC", "day", start_date=start_date, end_date=end_date)

        assert result is not None
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_get_ohlcv_none(self, mock_get_ohlcv: MagicMock, data_source: UpbitDataSource) -> None:
        """Test getting OHLCV when API returns None."""
        mock_get_ohlcv.return_value = None

        result = data_source.get_ohlcv("KRW-BTC", "day")

        assert result is None

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_get_ohlcv_empty(self, mock_get_ohlcv: MagicMock, data_source: UpbitDataSource) -> None:
        """Test getting OHLCV when API returns empty DataFrame."""
        mock_get_ohlcv.return_value = pd.DataFrame()

        result = data_source.get_ohlcv("KRW-BTC", "day")

        assert result is None

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_get_ohlcv_error(self, mock_get_ohlcv: MagicMock, data_source: UpbitDataSource) -> None:
        """Test getting OHLCV when API raises error."""
        from src.exceptions.data import DataSourceConnectionError

        mock_get_ohlcv.side_effect = Exception("API Error")

        with pytest.raises(DataSourceConnectionError):
            data_source.get_ohlcv("KRW-BTC", "day")

    @patch("src.data.upbit_source.pyupbit.get_current_price")
    def test_get_current_price(
        self, mock_get_price: MagicMock, data_source: UpbitDataSource
    ) -> None:
        """Test getting current price."""
        mock_get_price.return_value = 50000.0

        result = data_source.get_current_price("KRW-BTC")

        assert result == 50000.0
        mock_get_price.assert_called_once_with("KRW-BTC")

    @patch("src.data.upbit_source.pyupbit.get_current_price")
    def test_get_current_price_none(
        self, mock_get_price: MagicMock, data_source: UpbitDataSource
    ) -> None:
        """Test getting current price when API returns None (line 121)."""
        from src.exceptions.data import DataSourceError

        mock_get_price.return_value = None

        # DataSourceNotFoundError is caught and re-raised as DataSourceError
        with pytest.raises(DataSourceError, match="Failed to get price"):
            data_source.get_current_price("KRW-BTC")

    @patch("src.data.upbit_source.pyupbit.get_current_price")
    def test_get_current_price_error(
        self, mock_get_price: MagicMock, data_source: UpbitDataSource
    ) -> None:
        """Test getting current price when API raises error."""
        from src.exceptions.data import DataSourceError

        mock_get_price.side_effect = Exception("API Error")

        with pytest.raises(DataSourceError):
            data_source.get_current_price("KRW-BTC")

    def test_save_ohlcv(
        self, data_source: UpbitDataSource, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test saving OHLCV data."""
        result = data_source.save_ohlcv("KRW-BTC", "day", sample_ohlcv_data)

        assert result is True
        filepath = data_source._get_filepath("KRW-BTC", "day")
        assert filepath.exists()

        # Verify saved data
        loaded_df = pd.read_parquet(filepath)
        assert len(loaded_df) == len(sample_ohlcv_data)

    def test_save_ohlcv_custom_filepath(
        self, data_source: UpbitDataSource, sample_ohlcv_data: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Test saving OHLCV data with custom filepath."""
        custom_path = tmp_path / "custom.parquet"
        result = data_source.save_ohlcv(
            "KRW-BTC", "day", sample_ohlcv_data, filepath=str(custom_path)
        )

        assert result is True
        assert custom_path.exists()

    @patch("src.data.upbit_source.pd.DataFrame.to_parquet")
    def test_save_ohlcv_error(
        self,
        mock_to_parquet: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test saving OHLCV data when save fails (lines 156-158)."""
        mock_to_parquet.side_effect = Exception("Save error")

        result = data_source.save_ohlcv("KRW-BTC", "day", sample_ohlcv_data)

        assert result is False

    def test_load_ohlcv(
        self, data_source: UpbitDataSource, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test loading OHLCV data from file."""
        filepath = data_source._get_filepath("KRW-BTC", "day")
        sample_ohlcv_data.to_parquet(filepath)

        result = data_source.load_ohlcv("KRW-BTC", "day")

        assert result is not None
        assert len(result) == len(sample_ohlcv_data)
        assert "open" in result.columns

    def test_load_ohlcv_not_found(self, data_source: UpbitDataSource) -> None:
        """Test loading OHLCV when file doesn't exist."""
        result = data_source.load_ohlcv("KRW-BTC", "day")

        assert result is None

    def test_load_ohlcv_custom_filepath(
        self, data_source: UpbitDataSource, sample_ohlcv_data: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Test loading OHLCV data with custom filepath."""
        custom_path = tmp_path / "custom.parquet"
        sample_ohlcv_data.to_parquet(custom_path)

        result = data_source.load_ohlcv("KRW-BTC", "day", filepath=str(custom_path))

        assert result is not None
        assert len(result) == len(sample_ohlcv_data)

    @patch("src.data.upbit_source.pd.read_parquet")
    def test_load_ohlcv_error(
        self,
        mock_read_parquet: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test loading OHLCV data when read fails (lines 190-192)."""
        filepath = data_source._get_filepath("KRW-BTC", "day")
        sample_ohlcv_data.to_parquet(filepath)  # Create file so exists() check passes

        mock_read_parquet.side_effect = Exception("Read error")

        result = data_source.load_ohlcv("KRW-BTC", "day")

        assert result is None

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    def test_update_ohlcv_new_data(
        self,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data when no existing file."""
        mock_get_ohlcv.return_value = sample_ohlcv_data

        result = data_source.update_ohlcv("KRW-BTC", "day")

        assert result is not None
        assert len(result) == len(sample_ohlcv_data)
        filepath = data_source._get_filepath("KRW-BTC", "day")
        assert filepath.exists()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_incremental(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data with existing file (incremental update)."""
        from datetime import datetime

        # Save existing data
        filepath = data_source._get_filepath("KRW-BTC", "day")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # New data (includes existing and new)
        new_df = sample_ohlcv_data.copy()
        mock_get_ohlcv.return_value = new_df
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        result = data_source.update_ohlcv("KRW-BTC", "day")

        assert result is not None
        # Should have combined data
        assert len(result) >= len(existing_df)

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_minute_interval(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data with minute interval (lines 233-238)."""
        from datetime import datetime

        # Save existing data with minute interval
        filepath = data_source._get_filepath("KRW-BTC", "minute240")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # New data
        new_df = sample_ohlcv_data.copy()
        mock_get_ohlcv.return_value = new_df
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        result = data_source.update_ohlcv("KRW-BTC", "minute240")

        assert result is not None
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_minute_interval_value_error(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data with invalid minute interval (lines 239-240)."""
        from datetime import datetime

        # Save existing data with invalid minute interval format
        filepath = data_source._get_filepath("KRW-BTC", "minuteinvalid")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # New data
        new_df = sample_ohlcv_data.copy()
        mock_get_ohlcv.return_value = new_df
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        # Should handle ValueError and use default count=200
        result = data_source.update_ohlcv("KRW-BTC", "minuteinvalid")

        assert result is not None
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_other_interval(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data with other interval type (line 241-242)."""
        from datetime import datetime

        # Save existing data with week interval
        filepath = data_source._get_filepath("KRW-BTC", "week")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # New data
        new_df = sample_ohlcv_data.copy()
        mock_get_ohlcv.return_value = new_df
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        result = data_source.update_ohlcv("KRW-BTC", "week")

        assert result is not None
        # Should use default count=200 for other intervals
        mock_get_ohlcv.assert_called_once()

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_no_new_data(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data when no new data is available (lines 248-250)."""
        from datetime import datetime

        # Save existing data
        filepath = data_source._get_filepath("KRW-BTC", "day")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # API returns None (no new data)
        mock_get_ohlcv.return_value = None
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        result = data_source.update_ohlcv("KRW-BTC", "day")

        assert result is not None
        assert len(result) == len(existing_df)  # Should return existing data

    @patch("src.data.upbit_source.pyupbit.get_ohlcv")
    @patch("src.data.upbit_source.datetime")
    def test_update_ohlcv_empty_new_data(
        self,
        mock_datetime: MagicMock,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data when new data is empty after filtering (lines 255-257)."""
        from datetime import datetime

        # Save existing data
        filepath = data_source._get_filepath("KRW-BTC", "day")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.index.max()
        existing_df.to_parquet(filepath)

        # New data with all timestamps before latest_timestamp (will be filtered out)
        new_df = sample_ohlcv_data.iloc[:2].copy()  # Older data
        mock_get_ohlcv.return_value = new_df
        mock_datetime.now.return_value = datetime(2024, 1, 10)

        result = data_source.update_ohlcv("KRW-BTC", "day")

        assert result is not None
        assert len(result) == len(existing_df)  # Should return existing data (no new data to add)

    @patch("src.data.upbit_source.UpbitDataSource.get_ohlcv")
    def test_update_ohlcv_error(
        self,
        mock_get_ohlcv: MagicMock,
        data_source: UpbitDataSource,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        """Test updating OHLCV data when error occurs (lines 273-275)."""
        # Save existing data
        filepath = data_source._get_filepath("KRW-BTC", "day")
        existing_df = sample_ohlcv_data.iloc[:3].copy()
        existing_df.to_parquet(filepath)

        # get_ohlcv raises an exception
        mock_get_ohlcv.side_effect = Exception("Update error")

        result = data_source.update_ohlcv("KRW-BTC", "day")

        assert result is None
