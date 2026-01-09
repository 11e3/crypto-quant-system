"""
Cache eviction and cleanup logic.

Handles LRU eviction policy and cache size/entry limits.
"""

import time
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def enforce_cache_limits(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
    max_entries: int,
    max_size_mb: float,
    ttl_days: int,
) -> None:
    """
    Enforce cache size and entry limits using LRU eviction.

    Args:
        metadata: Cache metadata dict
        access_times: OrderedDict of cache_key -> last access time
        cache_dir: Cache directory path
        max_entries: Maximum number of entries allowed
        max_size_mb: Maximum cache size in MB
        ttl_days: Time-to-live for entries in days

    Note:
        In parallel environments, file deletion may fail due to locks.
        This is handled gracefully by catching exceptions.
    """
    # Clean up expired entries first
    try:
        cleanup_expired(metadata, access_times, cache_dir, ttl_days)
    except (PermissionError, OSError) as e:
        logger.debug(f"Cache cleanup skipped due to file lock: {e}")
        return

    # Evict entries to meet entry limit
    _evict_to_entry_limit(metadata, access_times, cache_dir, max_entries)

    # Evict entries to meet size limit
    _evict_to_size_limit(metadata, access_times, cache_dir, max_size_mb)


def _evict_to_entry_limit(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
    max_entries: int,
) -> None:
    """Evict entries to meet entry count limit."""
    max_attempts = len(metadata)
    attempts = 0
    while len(metadata) > max_entries and attempts < max_attempts:
        attempts += 1
        if not access_times:
            break
        lru_key = next(iter(access_times))
        try:
            evict_entry(lru_key, metadata, access_times, cache_dir)
        except (PermissionError, OSError):
            access_times.pop(lru_key, None)
            continue


def _evict_to_size_limit(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
    max_size_mb: float,
) -> None:
    """Evict entries to meet size limit."""
    current_size_mb = get_total_size_mb(metadata, cache_dir)
    max_attempts = len(metadata)
    attempts = 0
    while current_size_mb > max_size_mb and metadata and attempts < max_attempts:
        attempts += 1
        if not access_times:
            break
        lru_key = next(iter(access_times))
        try:
            evicted_size = evict_entry(lru_key, metadata, access_times, cache_dir)
            current_size_mb -= evicted_size / (1024 * 1024)
        except (PermissionError, OSError):
            access_times.pop(lru_key, None)
            continue


def cleanup_expired(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
    ttl_days: int,
) -> int:
    """
    Remove cache entries that have expired (TTL).

    Args:
        metadata: Cache metadata dict
        access_times: Access times OrderedDict
        cache_dir: Cache directory
        ttl_days: Time-to-live in days

    Returns:
        Number of entries cleaned
    """
    if ttl_days <= 0:
        return 0  # TTL disabled

    current_time = time.time()
    ttl_seconds = ttl_days * 24 * 60 * 60
    expired_keys = []

    for key, meta in list(metadata.items()):
        created_at = meta.get("created_at", 0)
        if current_time - created_at > ttl_seconds:
            expired_keys.append(key)

    cleaned_count = 0
    for key in expired_keys:
        try:
            evict_entry(key, metadata, access_times, cache_dir)
            cleaned_count += 1
        except (PermissionError, OSError):
            continue

    if cleaned_count > 0:
        logger.debug(f"Cleaned up {cleaned_count} expired cache entries")

    return cleaned_count


def evict_entry(
    cache_key: str,
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
) -> int:
    """
    Evict a cache entry.

    Args:
        cache_key: Cache key to evict
        metadata: Cache metadata dict
        access_times: Access times OrderedDict
        cache_dir: Cache directory

    Returns:
        Size of evicted file in bytes
    """
    size = 0
    cache_path = cache_dir / f"{cache_key}.parquet"
    if cache_path.exists():
        try:
            size = cache_path.stat().st_size
            cache_path.unlink()
        except FileNotFoundError:
            pass
        except PermissionError:
            logger.debug(
                f"Could not delete cache file {cache_path.name}: "
                "file may be in use by another process"
            )
        except OSError as e:
            logger.debug(f"Could not delete cache file {cache_path.name}: {e}")

    # Remove from metadata even if file deletion failed
    metadata.pop(cache_key, None)
    access_times.pop(cache_key, None)

    return size


def get_total_size_mb(metadata: dict[str, Any], cache_dir: Path) -> float:
    """
    Calculate total cache size in MB.

    Args:
        metadata: Cache metadata dict
        cache_dir: Cache directory

    Returns:
        Total size in MB
    """
    total_size = 0
    for key in metadata:
        cache_path = cache_dir / f"{key}.parquet"
        if cache_path.exists():
            total_size += cache_path.stat().st_size
    return total_size / (1024 * 1024)
