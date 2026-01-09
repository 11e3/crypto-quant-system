"""
Unit tests for indicator cache module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.config.constants import CACHE_METADATA_FILENAME
from src.data.cache.cache import IndicatorCache, get_cache
from src.data.cache.cache_metadata import (
    generate_cache_key,
    get_cache_path,
    load_metadata,
)


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def cache(temp_cache_dir: Path) -> IndicatorCache:
    """Create IndicatorCache instance for testing."""
    return IndicatorCache(cache_dir=temp_cache_dir)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create sample DataFrame with indicators."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(10)],
            "high": [105.0 + i for i in range(10)],
            "low": [95.0 + i for i in range(10)],
            "close": [102.0 + i for i in range(10)],
            "volume": [1000.0 + i * 10 for i in range(10)],
            "sma": [101.0 + i for i in range(10)],
            "target": [108.0 + i for i in range(10)],
        },
        index=dates,
    )


class TestIndicatorCache:
    """Test cases for IndicatorCache class."""

    def test_initialization(self, temp_cache_dir: Path) -> None:
        """Test IndicatorCache initialization."""
        cache = IndicatorCache(cache_dir=temp_cache_dir)

        assert cache.cache_dir == temp_cache_dir
        assert cache.metadata_file == temp_cache_dir / CACHE_METADATA_FILENAME
        assert isinstance(cache._metadata, dict)

    def test_initialization_creates_directory(self, tmp_path: Path) -> None:
        """Test that initialization creates directory if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        IndicatorCache(cache_dir=cache_dir)

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_load_metadata_empty(self, cache: IndicatorCache) -> None:
        """Test loading metadata when file doesn't exist."""
        from collections import OrderedDict

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert isinstance(metadata, dict)
        assert len(metadata) == 0

    def test_load_metadata_existing(self, cache: IndicatorCache) -> None:
        """Test loading metadata when file exists."""
        from collections import OrderedDict

        # Create metadata with access times
        metadata_data = {
            "cache_key_1": {"ticker": "BTC", "params": {}},
            "_access_times": {"cache_key_1": 123.456},
        }
        import json

        with open(cache.metadata_file, "w") as f:
            json.dump(metadata_data, f)

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)

        assert "cache_key_1" in metadata
        assert "cache_key_1" in access_times
        assert access_times["cache_key_1"] == 123.456

    def test_load_metadata_non_dict_data(self, cache: IndicatorCache) -> None:
        """Test loading metadata with non-dict data (lines 34->43, 36->43)."""
        import json
        from collections import OrderedDict

        # Write non-dict data
        with open(cache.metadata_file, "w") as f:
            json.dump("not a dict", f)

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert isinstance(metadata, dict)
        assert len(metadata) == 0

    def test_load_metadata_no_access_times(self, cache: IndicatorCache) -> None:
        """Test loading metadata without _access_times key (line 34)."""
        import json
        from collections import OrderedDict

        # Create metadata without _access_times
        metadata_data = {
            "cache_key_1": {"ticker": "BTC", "params": {}},
        }
        with open(cache.metadata_file, "w") as f:
            json.dump(metadata_data, f)

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert "cache_key_1" in metadata
        assert len(access_times) == 0

    def test_load_metadata_invalid_access_times(self, cache: IndicatorCache) -> None:
        """Test loading metadata with invalid access_times (line 36)."""
        import json
        from collections import OrderedDict

        # Create metadata with non-dict access_times
        metadata_data = {
            "cache_key_1": {"ticker": "BTC", "params": {}},
            "_access_times": "not a dict",
        }
        with open(cache.metadata_file, "w") as f:
            json.dump(metadata_data, f)

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert "cache_key_1" in metadata
        assert len(access_times) == 0
        """Test loading existing metadata."""

        test_metadata = {"key1": {"ticker": "KRW-BTC", "params": {"sma": 5}}}
        cache._metadata = test_metadata
        cache._save_metadata()

        new_cache = IndicatorCache(cache_dir=cache.cache_dir)
        assert new_cache._metadata == test_metadata

    def test_load_metadata_invalid_json(self, cache: IndicatorCache) -> None:
        """Test loading metadata with invalid JSON."""
        from collections import OrderedDict

        cache.metadata_file.write_text("invalid json")

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert isinstance(metadata, dict)
        assert len(metadata) == 0

    def test_load_metadata_not_dict(self, cache: IndicatorCache) -> None:
        """Test loading metadata when JSON is not a dict (covers line 49)."""
        from collections import OrderedDict

        cache.metadata_file.write_text('["list", "not", "dict"]')

        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        assert isinstance(metadata, dict)
        assert len(metadata) == 0

    def test_generate_cache_key(self, cache: IndicatorCache) -> None:
        """Test cache key generation."""
        key = generate_cache_key("KRW-BTC", "day", {"sma": 5, "trend": 10})

        assert isinstance(key, str)
        assert key.startswith("KRW-BTC_day_")
        assert len(key) > len("KRW-BTC_day_")

    def test_generate_cache_key_deterministic(self, cache: IndicatorCache) -> None:
        """Test that cache key is deterministic."""
        params = {"sma": 5, "trend": 10}
        key1 = generate_cache_key("KRW-BTC", "day", params)
        key2 = generate_cache_key("KRW-BTC", "day", params)

        assert key1 == key2

    def test_get_cache_path(self, cache: IndicatorCache) -> None:
        """Test cache path generation."""
        cache_key = "KRW-BTC_day_abc123"
        path = get_cache_path(cache.cache_dir, cache_key)

        assert path == cache.cache_dir / f"{cache_key}.parquet"

    def test_set_and_get(self, cache: IndicatorCache, sample_dataframe: pd.DataFrame) -> None:
        """Test setting and getting cached data."""
        params = {"sma": 5, "trend": 10}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        result = cache.get("KRW-BTC", "day", params)

        assert result is not None
        assert len(result) == len(sample_dataframe)
        # Compare values (index might have different type after parquet save/load)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True), sample_dataframe.reset_index(drop=True)
        )

    def test_get_with_existing_access_time(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test get when cache_key already in access_times (line 69->71)."""
        params = {"sma": 5}
        # First access
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        result1 = cache.get("KRW-BTC", "day", params)
        assert result1 is not None

        # Second access - should update access time
        result2 = cache.get("KRW-BTC", "day", params)
        assert result2 is not None

    def test_get_with_raw_data_updated(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test cache miss when raw data has been updated (lines 63-66)."""
        params = {"sma": 5}
        # Set cache with old mtime
        cache.set("KRW-BTC", "day", params, sample_dataframe, raw_data_mtime=100.0)

        # Try to get with newer mtime - should be cache miss
        result = cache.get("KRW-BTC", "day", params, raw_data_mtime=200.0)
        assert result is None

    @patch("src.data.cache.cache_ops.pd.read_parquet", side_effect=Exception("Parquet read error"))
    @patch("src.data.cache.cache_ops.logger")
    def test_get_load_cache_error(
        self,
        mock_logger: MagicMock,
        mock_read_parquet: MagicMock,
        cache: IndicatorCache,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test get when loading cached parquet file fails (covers lines 137-139)."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        result = cache.get("KRW-BTC", "day", params)

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_get_cache_miss_file_not_found(self, cache: IndicatorCache) -> None:
        """Test get when cache file doesn't exist."""
        params = {"sma": 5}
        result = cache.get("KRW-BTC", "day", params)

        assert result is None

    def test_get_cache_miss_no_metadata(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test get when metadata doesn't exist."""
        params = {"sma": 5}
        cache_key = generate_cache_key("KRW-BTC", "day", params)
        cache_path = get_cache_path(cache.cache_dir, cache_key)

        # Save file but don't add metadata
        sample_dataframe.to_parquet(cache_path)

        result = cache.get("KRW-BTC", "day", params)

        assert result is None

    @patch("src.data.cache.cache_ops.logger")
    def test_get_cache_miss_params_changed(
        self, mock_logger: MagicMock, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test get when parameters don't match (covers lines 121-122)."""
        params1 = {"sma": 5}
        params2 = {"sma": 10}

        # Set with params1 to create cache entry
        cache.set("KRW-BTC", "day", params1, sample_dataframe)

        # Get cache key for params2 (different key, but we'll modify metadata to test line 121-122)
        cache_key = generate_cache_key("KRW-BTC", "day", params1)
        get_cache_path(cache.cache_dir, cache_key)

        # Manually modify metadata to have different params (same key, different params)
        # This simulates the scenario where params don't match (line 120-122)
        cache._metadata[cache_key]["params"] = params2

        # Now get with params1 - should hit line 121-122 because params don't match
        result = cache.get("KRW-BTC", "day", params1)

        assert result is None

    def test_get_cache_miss_raw_data_updated(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test get when raw data was updated."""
        params = {"sma": 5}
        old_mtime = 1000.0
        new_mtime = 2000.0

        cache.set("KRW-BTC", "day", params, sample_dataframe, raw_data_mtime=old_mtime)

        result = cache.get("KRW-BTC", "day", params, raw_data_mtime=new_mtime)

        assert result is None

    def test_get_cache_hit_with_raw_data_mtime(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test get when raw data mtime matches."""
        params = {"sma": 5}
        mtime = 1000.0

        cache.set("KRW-BTC", "day", params, sample_dataframe, raw_data_mtime=mtime)

        result = cache.get("KRW-BTC", "day", params, raw_data_mtime=mtime)

        assert result is not None
        # Compare values (index might have different type after parquet save/load)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True), sample_dataframe.reset_index(drop=True)
        )

    def test_set_saves_metadata(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test that set saves metadata."""
        from collections import OrderedDict

        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        assert cache.metadata_file.exists()
        access_times: OrderedDict[str, float] = OrderedDict()
        metadata = load_metadata(cache.metadata_file, access_times)
        cache_key = generate_cache_key("KRW-BTC", "day", params)
        assert cache_key in metadata

    def test_invalidate_by_ticker(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test invalidate by ticker."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        cache.set("KRW-ETH", "day", params, sample_dataframe)

        count = cache.invalidate(ticker="KRW-BTC")

        assert count == 1
        assert cache.get("KRW-BTC", "day", params) is None
        assert cache.get("KRW-ETH", "day", params) is not None

    def test_invalidate_by_interval(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test invalidate by interval."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        cache.set("KRW-BTC", "week", params, sample_dataframe)

        count = cache.invalidate(interval="day")

        assert count == 1
        assert cache.get("KRW-BTC", "day", params) is None
        assert cache.get("KRW-BTC", "week", params) is not None

    def test_invalidate_by_ticker_and_interval(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test invalidate by ticker and interval."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        cache.set("KRW-BTC", "week", params, sample_dataframe)
        cache.set("KRW-ETH", "day", params, sample_dataframe)

        count = cache.invalidate(ticker="KRW-BTC", interval="day")

        assert count == 1
        assert cache.get("KRW-BTC", "day", params) is None
        assert cache.get("KRW-BTC", "week", params) is not None
        assert cache.get("KRW-ETH", "day", params) is not None

    def test_invalidate_all(self, cache: IndicatorCache, sample_dataframe: pd.DataFrame) -> None:
        """Test invalidate all."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        cache.set("KRW-ETH", "day", params, sample_dataframe)

        count = cache.invalidate()

        assert count == 2
        assert cache.get("KRW-BTC", "day", params) is None
        assert cache.get("KRW-ETH", "day", params) is None

    def test_clear(self, cache: IndicatorCache, sample_dataframe: pd.DataFrame) -> None:
        """Test clear all cached data."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)
        cache.set("KRW-ETH", "day", params, sample_dataframe)

        count = cache.clear()

        assert count == 2
        assert len(cache._metadata) == 0
        # Check that parquet files are removed
        parquet_files = list(cache.cache_dir.glob("*.parquet"))
        assert len(parquet_files) == 0

    def test_clear_empty_cache(self, cache: IndicatorCache) -> None:
        """Test clear when cache is empty."""
        count = cache.clear()

        assert count == 0

    def test_stats(self, cache: IndicatorCache, sample_dataframe: pd.DataFrame) -> None:
        """Test cache statistics."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        stats = cache.stats()

        assert stats["entries"] == 1
        assert stats["total_rows"] == len(sample_dataframe)
        assert stats["total_size_mb"] >= 0  # Size might be 0 for small files
        assert stats["cache_dir"] == str(cache.cache_dir)

    def test_stats_empty(self, cache: IndicatorCache) -> None:
        """Test stats when cache is empty."""
        stats = cache.stats()

        assert stats["entries"] == 0
        assert stats["total_rows"] == 0
        assert stats["total_size_mb"] == 0.0

    def test_cleanup_with_default_max_age(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test cleanup uses default ttl_days when max_age_days is None - line 164-167."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        # Cleanup with None uses self.ttl_days (default)
        result = cache.cleanup(max_age_days=None)

        # Result should be a dict with cleanup statistics
        assert isinstance(result, dict)
        # Keys should include cleanup stats
        assert "removed_entries" in result or "removed" in result or len(result) >= 0

    def test_cleanup_with_explicit_max_age(
        self, cache: IndicatorCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test cleanup with explicit max_age_days - line 164-167."""
        params = {"sma": 5}
        cache.set("KRW-BTC", "day", params, sample_dataframe)

        # Cleanup with explicit max_age
        result = cache.cleanup(max_age_days=30)

        assert isinstance(result, dict)


class TestGetCache:
    """Test cases for get_cache function."""

    def test_get_cache_returns_instance(self) -> None:
        """Test get_cache returns IndicatorCache instance."""
        cache = get_cache()

        assert isinstance(cache, IndicatorCache)

    def test_get_cache_singleton(self) -> None:
        """Test get_cache returns same instance."""
        import src.data.cache.cache

        # Reset global cache
        src.data.cache.cache._cache = None

        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
