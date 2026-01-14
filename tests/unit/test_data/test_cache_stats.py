"""Tests for src/data/cache/cache_stats.py - cache management functions."""

import tempfile
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

import pytest

from src.data.cache.cache_stats import (
    cleanup_cache,
    clear_cache,
    get_cache_stats,
    invalidate_cache,
)


class TestCleanupCache:
    """Tests for cleanup_cache function."""

    def test_cleanup_no_expired(self) -> None:
        """Test cleanup when no entries are expired."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            current_time = time.time()

            metadata: dict[str, Any] = {
                "key1": {"created_at": current_time - 100},
                "key2": {"created_at": current_time - 50},
            }
            access_times: OrderedDict[str, float] = OrderedDict()

            result = cleanup_cache(
                metadata=metadata,
                access_times=access_times,
                cache_dir=cache_dir,
                max_age_days=1,  # 1 day - nothing should be expired
                save_metadata_callback=None,
            )

            assert result["removed_entries"] == 0

    def test_cleanup_with_expired(self) -> None:
        """Test cleanup with expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            current_time = time.time()

            # Create a cache file
            cache_file = cache_dir / "old_key.parquet"
            cache_file.touch()

            metadata: dict[str, Any] = {
                "old_key": {"created_at": current_time - (3 * 24 * 60 * 60)},  # 3 days
                "new_key": {"created_at": current_time - 100},  # Recent
            }
            access_times: OrderedDict[str, float] = OrderedDict()

            save_called = [False]

            def save_callback() -> None:
                save_called[0] = True

            result = cleanup_cache(
                metadata=metadata,
                access_times=access_times,
                cache_dir=cache_dir,
                max_age_days=1,  # 1 day - old_key should be expired
                save_metadata_callback=save_callback,
            )

            assert result["removed_entries"] == 1
            assert save_called[0] is True

    def test_cleanup_missing_created_at(self) -> None:
        """Test cleanup when created_at is missing from metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {
                "key_without_timestamp": {},  # No created_at field
            }
            access_times: OrderedDict[str, float] = OrderedDict()

            result = cleanup_cache(
                metadata=metadata,
                access_times=access_times,
                cache_dir=cache_dir,
                max_age_days=1,
                save_metadata_callback=None,
            )

            # Should not crash, uses current_time as default
            assert result["removed_entries"] == 0


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_all_entries(self) -> None:
        """Test clearing all cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create some cache files
            (cache_dir / "key1.parquet").touch()
            (cache_dir / "key2.parquet").touch()

            metadata: dict[str, Any] = {
                "key1": {"created_at": time.time()},
                "key2": {"created_at": time.time()},
            }

            save_called = [False]

            def save_callback() -> None:
                save_called[0] = True

            result = clear_cache(
                metadata=metadata,
                cache_dir=cache_dir,
                save_metadata_callback=save_callback,
            )

            assert result == 2
            assert len(metadata) == 0
            assert save_called[0] is True

    def test_clear_empty_cache(self) -> None:
        """Test clearing empty cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            metadata: dict[str, Any] = {}

            result = clear_cache(
                metadata=metadata,
                cache_dir=cache_dir,
                save_metadata_callback=None,
            )

            assert result == 0


class TestInvalidateCache:
    """Tests for invalidate_cache function."""

    def test_invalidate_by_ticker(self) -> None:
        """Test invalidating entries by ticker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create cache files
            (cache_dir / "btc_1d.parquet").touch()
            (cache_dir / "eth_1d.parquet").touch()

            metadata: dict[str, Any] = {
                "btc_1d": {"ticker": "BTC", "interval": "1d"},
                "eth_1d": {"ticker": "ETH", "interval": "1d"},
            }

            result = invalidate_cache(
                metadata=metadata,
                cache_dir=cache_dir,
                ticker="BTC",
                save_metadata_callback=None,
            )

            assert result == 1
            assert "btc_1d" not in metadata
            assert "eth_1d" in metadata

    def test_invalidate_by_interval(self) -> None:
        """Test invalidating entries by interval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {
                "btc_1d": {"ticker": "BTC", "interval": "1d"},
                "btc_1h": {"ticker": "BTC", "interval": "1h"},
            }

            result = invalidate_cache(
                metadata=metadata,
                cache_dir=cache_dir,
                interval="1d",
                save_metadata_callback=None,
            )

            assert result == 1
            assert "btc_1d" not in metadata
            assert "btc_1h" in metadata

    def test_invalidate_all(self) -> None:
        """Test invalidating all entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {
                "key1": {"ticker": "BTC"},
                "key2": {"ticker": "ETH"},
            }

            result = invalidate_cache(
                metadata=metadata,
                cache_dir=cache_dir,
                save_metadata_callback=None,
            )

            assert result == 2
            assert len(metadata) == 0


class TestGetCacheStats:
    """Tests for get_cache_stats function."""

    def test_empty_cache_stats(self) -> None:
        """Test stats for empty cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            metadata: dict[str, Any] = {}

            result = get_cache_stats(
                metadata=metadata,
                cache_dir=cache_dir,
                max_size_mb=100.0,
                max_entries=1000,
            )

            assert result["entries"] == 0
            assert result["total_rows"] == 0
            assert result["usage_pct"] == 0.0

    def test_cache_stats_with_entries(self) -> None:
        """Test stats with cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {
                "key1": {"rows": 100, "created_at": time.time() - 86400},  # 1 day old
                "key2": {"rows": 200, "created_at": time.time() - 172800},  # 2 days old
            }

            result = get_cache_stats(
                metadata=metadata,
                cache_dir=cache_dir,
                max_size_mb=100.0,
                max_entries=1000,
            )

            assert result["entries"] == 2
            assert result["total_rows"] == 300
            assert result["max_entries"] == 1000
            assert result["max_size_mb"] == 100.0

    def test_cache_stats_usage_calculation(self) -> None:
        """Test usage percentage calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {
                f"key{i}": {"rows": 10} for i in range(100)
            }

            result = get_cache_stats(
                metadata=metadata,
                cache_dir=cache_dir,
                max_size_mb=100.0,
                max_entries=1000,
            )

            assert result["usage_pct"] == 10.0  # 100/1000 = 10%

    def test_cache_stats_zero_max_entries(self) -> None:
        """Test stats with zero max_entries (division by zero protection)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            metadata: dict[str, Any] = {"key1": {"rows": 100}}

            result = get_cache_stats(
                metadata=metadata,
                cache_dir=cache_dir,
                max_size_mb=100.0,
                max_entries=0,
            )

            assert result["usage_pct"] == 0.0

    def test_cache_stats_zero_max_size(self) -> None:
        """Test stats with zero max_size_mb (division by zero protection)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            metadata: dict[str, Any] = {"key1": {"rows": 100}}

            result = get_cache_stats(
                metadata=metadata,
                cache_dir=cache_dir,
                max_size_mb=0.0,
                max_entries=1000,
            )

            assert result["size_usage_pct"] == 0.0
