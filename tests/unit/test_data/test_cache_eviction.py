"""Tests for src/data/cache/cache_eviction.py - cache eviction functions."""

import tempfile
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.data.cache.cache_eviction import (
    cleanup_expired,
    enforce_cache_limits,
    evict_entry,
    get_total_size_mb,
    _evict_to_entry_limit,
    _evict_to_size_limit,
)


class TestEvictEntry:
    """Tests for evict_entry function."""

    def test_evict_existing_entry(self) -> None:
        """Test evicting an existing cache entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create a cache file with some data
            cache_file = cache_dir / "test_key.parquet"
            cache_file.write_bytes(b"x" * 1000)

            metadata: dict[str, Any] = {"test_key": {"rows": 100}}
            access_times: OrderedDict[str, float] = OrderedDict([("test_key", time.time())])

            size = evict_entry("test_key", metadata, access_times, cache_dir)

            assert size == 1000
            assert "test_key" not in metadata
            assert "test_key" not in access_times
            assert not cache_file.exists()

    def test_evict_nonexistent_entry(self) -> None:
        """Test evicting a non-existent cache entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"test_key": {"rows": 100}}
            access_times: OrderedDict[str, float] = OrderedDict([("test_key", time.time())])

            size = evict_entry("test_key", metadata, access_times, cache_dir)

            assert size == 0
            assert "test_key" not in metadata
            assert "test_key" not in access_times

    def test_evict_permission_error(self) -> None:
        """Test evicting when file cannot be deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            cache_file = cache_dir / "test_key.parquet"
            cache_file.write_bytes(b"x" * 1000)

            metadata: dict[str, Any] = {"test_key": {"rows": 100}}
            access_times: OrderedDict[str, float] = OrderedDict([("test_key", time.time())])

            with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
                size = evict_entry("test_key", metadata, access_times, cache_dir)

            # Metadata should still be removed even if file deletion failed
            assert "test_key" not in metadata
            assert "test_key" not in access_times

    def test_evict_file_not_found_race(self) -> None:
        """Test evicting when file disappears between check and delete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            cache_file = cache_dir / "test_key.parquet"
            cache_file.write_bytes(b"x" * 1000)

            metadata: dict[str, Any] = {"test_key": {"rows": 100}}
            access_times: OrderedDict[str, float] = OrderedDict([("test_key", time.time())])

            with patch.object(Path, "unlink", side_effect=FileNotFoundError()):
                size = evict_entry("test_key", metadata, access_times, cache_dir)

            assert "test_key" not in metadata

    def test_evict_os_error(self) -> None:
        """Test evicting when OS error occurs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            cache_file = cache_dir / "test_key.parquet"
            cache_file.write_bytes(b"x" * 1000)

            metadata: dict[str, Any] = {"test_key": {"rows": 100}}
            access_times: OrderedDict[str, float] = OrderedDict([("test_key", time.time())])

            with patch.object(Path, "unlink", side_effect=OSError("disk error")):
                size = evict_entry("test_key", metadata, access_times, cache_dir)

            assert "test_key" not in metadata


class TestCleanupExpired:
    """Tests for cleanup_expired function."""

    def test_cleanup_disabled_ttl(self) -> None:
        """Test cleanup when TTL is disabled (0 or negative)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"test_key": {"created_at": 0}}
            access_times: OrderedDict[str, float] = OrderedDict()

            result = cleanup_expired(metadata, access_times, cache_dir, ttl_days=0)

            assert result == 0
            assert "test_key" in metadata  # Not removed

    def test_cleanup_expired_entries(self) -> None:
        """Test cleaning up expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            current_time = time.time()

            # Create cache files
            (cache_dir / "old_key.parquet").write_bytes(b"x" * 100)

            metadata: dict[str, Any] = {
                "old_key": {"created_at": current_time - (10 * 24 * 60 * 60)},  # 10 days old
                "new_key": {"created_at": current_time - 100},  # Recent
            }
            access_times: OrderedDict[str, float] = OrderedDict([
                ("old_key", current_time - 1000),
                ("new_key", current_time),
            ])

            result = cleanup_expired(metadata, access_times, cache_dir, ttl_days=7)

            assert result == 1
            assert "old_key" not in metadata
            assert "new_key" in metadata

    def test_cleanup_error_handling(self) -> None:
        """Test cleanup handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            current_time = time.time()

            metadata: dict[str, Any] = {
                "old_key": {"created_at": current_time - (10 * 24 * 60 * 60)},
            }
            access_times: OrderedDict[str, float] = OrderedDict()

            with patch("src.data.cache.cache_eviction.evict_entry", side_effect=PermissionError()):
                result = cleanup_expired(metadata, access_times, cache_dir, ttl_days=7)

            # Should continue without raising
            assert result == 0


class TestEvictToEntryLimit:
    """Tests for _evict_to_entry_limit function."""

    def test_under_limit(self) -> None:
        """Test when under entry limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"key1": {}, "key2": {}}
            access_times: OrderedDict[str, float] = OrderedDict([
                ("key1", time.time()),
                ("key2", time.time()),
            ])

            _evict_to_entry_limit(metadata, access_times, cache_dir, max_entries=5)

            assert len(metadata) == 2

    def test_over_limit(self) -> None:
        """Test evicting entries when over limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create files
            for i in range(3):
                (cache_dir / f"key{i}.parquet").write_bytes(b"x" * 100)

            metadata: dict[str, Any] = {f"key{i}": {} for i in range(3)}
            access_times: OrderedDict[str, float] = OrderedDict([
                (f"key{i}", time.time() + i) for i in range(3)
            ])

            _evict_to_entry_limit(metadata, access_times, cache_dir, max_entries=1)

            assert len(metadata) == 1

    def test_empty_access_times(self) -> None:
        """Test when access_times is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"key1": {}, "key2": {}}
            access_times: OrderedDict[str, float] = OrderedDict()

            # Should not crash with empty access_times
            _evict_to_entry_limit(metadata, access_times, cache_dir, max_entries=1)

    def test_eviction_error_continues(self) -> None:
        """Test that eviction errors don't stop the process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"key1": {}, "key2": {}, "key3": {}}
            access_times: OrderedDict[str, float] = OrderedDict([
                ("key1", 1.0),
                ("key2", 2.0),
                ("key3", 3.0),
            ])

            call_count = [0]
            original_evict = evict_entry

            def mock_evict(*args: Any, **kwargs: Any) -> int:
                call_count[0] += 1
                if call_count[0] == 1:
                    raise PermissionError("locked")
                return original_evict(*args, **kwargs)

            with patch("src.data.cache.cache_eviction.evict_entry", mock_evict):
                _evict_to_entry_limit(metadata, access_times, cache_dir, max_entries=1)


class TestEvictToSizeLimit:
    """Tests for _evict_to_size_limit function."""

    def test_under_size_limit(self) -> None:
        """Test when under size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create small files
            (cache_dir / "key1.parquet").write_bytes(b"x" * 1000)

            metadata: dict[str, Any] = {"key1": {}}
            access_times: OrderedDict[str, float] = OrderedDict([("key1", time.time())])

            _evict_to_size_limit(metadata, access_times, cache_dir, max_size_mb=10.0)

            assert "key1" in metadata

    def test_over_size_limit(self) -> None:
        """Test evicting to meet size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create files totaling ~1 MB
            for i in range(3):
                (cache_dir / f"key{i}.parquet").write_bytes(b"x" * (500 * 1024))

            metadata: dict[str, Any] = {f"key{i}": {} for i in range(3)}
            access_times: OrderedDict[str, float] = OrderedDict([
                (f"key{i}", time.time() + i) for i in range(3)
            ])

            # Limit to 0.5 MB
            _evict_to_size_limit(metadata, access_times, cache_dir, max_size_mb=0.5)

            # Should have evicted at least one
            assert len(metadata) < 3

    def test_eviction_size_error_continues(self) -> None:
        """Test that eviction errors during size limit enforcement don't stop the process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            for i in range(3):
                (cache_dir / f"key{i}.parquet").write_bytes(b"x" * (500 * 1024))

            metadata: dict[str, Any] = {f"key{i}": {} for i in range(3)}
            access_times: OrderedDict[str, float] = OrderedDict([
                ("key0", 1.0),
                ("key1", 2.0),
                ("key2", 3.0),
            ])

            call_count = [0]
            original_evict = evict_entry

            def mock_evict(*args: Any, **kwargs: Any) -> int:
                call_count[0] += 1
                if call_count[0] == 1:
                    raise OSError("disk error")
                return original_evict(*args, **kwargs)

            with patch("src.data.cache.cache_eviction.evict_entry", mock_evict):
                _evict_to_size_limit(metadata, access_times, cache_dir, max_size_mb=0.5)


class TestEnforceCacheLimits:
    """Tests for enforce_cache_limits function."""

    def test_enforce_limits_normal(self) -> None:
        """Test normal enforcement of limits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            current_time = time.time()

            metadata: dict[str, Any] = {
                "key1": {"created_at": current_time - 100},
            }
            access_times: OrderedDict[str, float] = OrderedDict([("key1", current_time)])

            enforce_cache_limits(
                metadata=metadata,
                access_times=access_times,
                cache_dir=cache_dir,
                max_entries=100,
                max_size_mb=100.0,
                ttl_days=30,
            )

            # Should complete without error
            assert "key1" in metadata

    def test_enforce_limits_cleanup_error(self) -> None:
        """Test that cleanup errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"key1": {}}
            access_times: OrderedDict[str, float] = OrderedDict([("key1", time.time())])

            with patch("src.data.cache.cache_eviction.cleanup_expired", side_effect=PermissionError("locked")):
                # Should not raise
                enforce_cache_limits(
                    metadata=metadata,
                    access_times=access_times,
                    cache_dir=cache_dir,
                    max_entries=100,
                    max_size_mb=100.0,
                    ttl_days=30,
                )


class TestGetTotalSizeMb:
    """Tests for get_total_size_mb function."""

    def test_empty_cache(self) -> None:
        """Test size of empty cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            metadata: dict[str, Any] = {}

            result = get_total_size_mb(metadata, cache_dir)

            assert result == 0.0

    def test_with_files(self) -> None:
        """Test size calculation with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create files
            (cache_dir / "key1.parquet").write_bytes(b"x" * (1024 * 1024))  # 1 MB
            (cache_dir / "key2.parquet").write_bytes(b"x" * (512 * 1024))  # 0.5 MB

            metadata: dict[str, Any] = {"key1": {}, "key2": {}}

            result = get_total_size_mb(metadata, cache_dir)

            assert result == pytest.approx(1.5, rel=0.01)

    def test_missing_files(self) -> None:
        """Test when metadata has entries but files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            metadata: dict[str, Any] = {"missing_key": {}}

            result = get_total_size_mb(metadata, cache_dir)

            assert result == 0.0
