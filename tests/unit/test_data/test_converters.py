"""
Unit tests for data converters module.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data.converters import (
    convert_csv_directory,
    convert_ticker_format,
    csv_to_parquet,
)


class TestConvertTickerFormat:
    """Test cases for convert_ticker_format function."""

    def test_convert_ticker_format(self) -> None:
        """Test converting ticker format."""
        result = convert_ticker_format("BTC_KRW.csv")
        assert result == "KRW-BTC"

    def test_convert_ticker_format_without_ext(self) -> None:
        """Test converting ticker format without extension."""
        result = convert_ticker_format("ETH_KRW.csv")
        assert result == "KRW-ETH"

    def test_convert_ticker_format_invalid(self) -> None:
        """Test converting ticker format with invalid format."""
        with pytest.raises(ValueError, match="Unexpected filename format"):
            convert_ticker_format("INVALID.csv")

    def test_convert_ticker_format_wrong_parts(self) -> None:
        """Test converting ticker format with wrong number of parts."""
        with pytest.raises(ValueError):
            convert_ticker_format("BTC.csv")


class TestCSVToParquet:
    """Test cases for csv_to_parquet function."""

    def test_csv_to_parquet(self, tmp_path: Path) -> None:
        """Test CSV to parquet conversion."""
        # Create test CSV file
        csv_dir = tmp_path / "1d"
        csv_dir.mkdir()
        csv_file = csv_dir / "BTC_KRW.csv"

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [95.0, 96.0, 97.0, 98.0, 99.0],
                "close": [102.0, 103.0, 104.0, 105.0, 106.0],
                "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
            },
            index=dates,
        )
        df.index.name = "datetime"
        df.to_csv(csv_file)

        # Convert to parquet
        output_dir = tmp_path / "output"
        result_path = csv_to_parquet(csv_file, output_dir=output_dir, interval="day")

        # Verify output
        assert result_path.exists()
        assert result_path.name == "KRW-BTC_day.parquet"

        # Verify parquet content
        df_parquet = pd.read_parquet(result_path)
        assert len(df_parquet) == len(df)
        assert "open" in df_parquet.columns

    def test_csv_to_parquet_with_interval_from_dir(self, tmp_path: Path) -> None:
        """Test CSV to parquet conversion inferring interval from directory."""
        csv_dir = tmp_path / "1w"
        csv_dir.mkdir()
        csv_file = csv_dir / "ETH_KRW.csv"

        dates = pd.date_range("2024-01-01", periods=3, freq="W")
        df = pd.DataFrame(
            {
                "open": [200.0, 201.0, 202.0],
                "high": [205.0, 206.0, 207.0],
                "low": [195.0, 196.0, 197.0],
                "close": [203.0, 204.0, 205.0],
                "volume": [2000.0, 2100.0, 2200.0],
            },
            index=dates,
        )
        df.index.name = "datetime"
        df.to_csv(csv_file)

        # Convert to parquet (interval inferred from parent directory)
        output_dir = tmp_path / "output"
        result_path = csv_to_parquet(csv_file, output_dir=output_dir)

        assert result_path.exists()
        assert result_path.name == "KRW-ETH_week.parquet"

    def test_csv_to_parquet_no_interval(self, tmp_path: Path) -> None:
        """Test CSV to parquet conversion without interval raises error."""
        csv_dir = tmp_path / "unknown"
        csv_dir.mkdir()
        csv_file = csv_dir / "BTC_KRW.csv"

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({"open": [100.0] * 5, "high": [105.0] * 5}, index=dates)
        df.index.name = "datetime"
        df.to_csv(csv_file)

        with pytest.raises(ValueError, match="Cannot determine interval"):
            csv_to_parquet(csv_file, output_dir=tmp_path / "output")


class TestConvertCSVDirectory:
    """Test cases for convert_csv_directory function."""

    def test_convert_csv_directory(self, tmp_path: Path) -> None:
        """Test converting CSV directory structure."""
        # Create directory structure
        source_dir = tmp_path / "source"
        interval_dir = source_dir / "1d"
        interval_dir.mkdir(parents=True)

        # Create CSV files
        for ticker in ["BTC_KRW", "ETH_KRW"]:
            csv_file = interval_dir / f"{ticker}.csv"
            dates = pd.date_range("2024-01-01", periods=3, freq="D")
            df = pd.DataFrame(
                {
                    "open": [100.0] * 3,
                    "high": [105.0] * 3,
                    "low": [95.0] * 3,
                    "close": [102.0] * 3,
                    "volume": [1000.0] * 3,
                },
                index=dates,
            )
            df.index.name = "datetime"
            df.to_csv(csv_file)

        # Convert directory
        output_dir = tmp_path / "output"
        count = convert_csv_directory(source_dir, output_dir=output_dir)

        assert count == 2
        assert (output_dir / "KRW-BTC_day.parquet").exists()
        assert (output_dir / "KRW-ETH_day.parquet").exists()

    def test_convert_csv_directory_multiple_intervals(self, tmp_path: Path) -> None:
        """Test converting CSV directory with multiple intervals."""
        source_dir = tmp_path / "source"
        for interval_dir_name in ["1d", "1w"]:
            interval_dir = source_dir / interval_dir_name
            interval_dir.mkdir(parents=True)
            csv_file = interval_dir / "BTC_KRW.csv"
            dates = pd.date_range("2024-01-01", periods=3, freq="D")
            df = pd.DataFrame(
                {
                    "open": [100.0] * 3,
                    "high": [105.0] * 3,
                    "low": [95.0] * 3,
                    "close": [102.0] * 3,
                    "volume": [1000.0] * 3,
                },
                index=dates,
            )
            df.index.name = "datetime"
            df.to_csv(csv_file)

        output_dir = tmp_path / "output"
        count = convert_csv_directory(source_dir, output_dir=output_dir)

        assert count == 2
        assert (output_dir / "KRW-BTC_day.parquet").exists()
        assert (output_dir / "KRW-BTC_week.parquet").exists()

    def test_convert_csv_directory_unknown_interval(self, tmp_path: Path) -> None:
        """Test converting CSV directory with unknown interval directory."""
        source_dir = tmp_path / "source"
        unknown_dir = source_dir / "unknown"
        unknown_dir.mkdir(parents=True)

        csv_file = unknown_dir / "BTC_KRW.csv"
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame({"open": [100.0] * 3}, index=dates)
        df.index.name = "datetime"
        df.to_csv(csv_file)

        output_dir = tmp_path / "output"
        count = convert_csv_directory(source_dir, output_dir=output_dir)

        # Unknown interval directory should be skipped
        assert count == 0

    def test_convert_csv_directory_skips_files(self, tmp_path: Path) -> None:
        """Test converting CSV directory skips files (not directories) (covers line 130)."""
        source_dir = tmp_path / "source"
        source_dir.mkdir(parents=True)

        # Create a file (not a directory) in source_dir
        file_in_source = source_dir / "some_file.txt"
        file_in_source.write_text("not a directory")

        # Create a valid interval directory
        interval_dir = source_dir / "1d"
        interval_dir.mkdir()
        csv_file = interval_dir / "BTC_KRW.csv"
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100.0] * 3,
                "high": [105.0] * 3,
                "low": [95.0] * 3,
                "close": [102.0] * 3,
                "volume": [1000.0] * 3,
            },
            index=dates,
        )
        df.index.name = "datetime"
        df.to_csv(csv_file)

        output_dir = tmp_path / "output"
        count = convert_csv_directory(source_dir, output_dir=output_dir)

        # File should be skipped, only directory processed
        assert count == 1
        assert (output_dir / "KRW-BTC_day.parquet").exists()

    def test_convert_csv_directory_error_handling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test converting CSV directory handles errors during file processing (covers lines 145-146)."""
        from unittest.mock import patch

        source_dir = tmp_path / "source"
        interval_dir = source_dir / "1d"
        interval_dir.mkdir(parents=True)

        csv_file = interval_dir / "BTC_KRW.csv"
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100.0] * 3,
                "high": [105.0] * 3,
                "low": [95.0] * 3,
                "close": [102.0] * 3,
                "volume": [1000.0] * 3,
            },
            index=dates,
        )
        df.index.name = "datetime"
        df.to_csv(csv_file)

        output_dir = tmp_path / "output"

        # Mock csv_to_parquet to raise an exception
        with patch("src.data.converters.csv_to_parquet", side_effect=Exception("Conversion error")):
            count = convert_csv_directory(source_dir, output_dir=output_dir)

        # Error should be caught and logged, count should be 0 (no successful conversions)
        assert count == 0
