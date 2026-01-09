"""
Cache statistics and management utilities.

Provides cache cleanup, statistics, and diagnostic functions.
"""

import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from src.data.cache.cache_eviction import evict_entry, get_total_size_mb
from src.utils.logger import get_logger

logger = get_logger(__name__)


def invalidate_cache(
    metadata: dict[str, Any],
    cache_dir: Path,
    ticker: str | None = None,
    interval: str | None = None,
    save_metadata_callback: Any = None,
) -> int:
    """
    Invalidate cache entries.

    Args:
        metadata: Cache metadata dict
        cache_dir: Cache directory
        ticker: Invalidate only this ticker (or all if None)
        interval: Invalidate only this interval (or all if None)
        save_metadata_callback: Callback to save metadata after invalidation

    Returns:
        Number of entries invalidated
    """
    keys_to_remove = []

    for key, meta in metadata.items():
        if ticker and meta.get("ticker") != ticker:
            continue
        if interval and meta.get("interval") != interval:
            continue
        keys_to_remove.append(key)

    for key in keys_to_remove:
        # Remove file
        cache_path = cache_dir / f"{key}.parquet"
        if cache_path.exists():
            cache_path.unlink()
        # Remove metadata
        del metadata[key]

    if keys_to_remove and save_metadata_callback:
        save_metadata_callback()

    logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    return len(keys_to_remove)


def clear_cache(
    metadata: dict[str, Any],
    cache_dir: Path,
    save_metadata_callback: Any = None,
) -> int:
    """
    Clear all cached data.

    Args:
        metadata: Cache metadata dict
        cache_dir: Cache directory
        save_metadata_callback: Callback to save metadata after clearing

    Returns:
        Number of entries cleared
    """
    count = len(metadata)

    # Remove all parquet files
    for f in cache_dir.glob("*.parquet"):
        f.unlink()

    # Clear metadata
    metadata.clear()
    if save_metadata_callback:
        save_metadata_callback()

    logger.info(f"Cleared {count} cache entries")
    return count


def cleanup_cache(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    cache_dir: Path,
    max_age_days: int,
    save_metadata_callback: Any = None,
) -> dict[str, int | float]:
    """
    Clean up cache by removing old or unused entries.

    Args:
        metadata: Cache metadata dict
        access_times: Access times OrderedDict
        cache_dir: Cache directory
        max_age_days: Remove entries older than this many days
        save_metadata_callback: Callback to save metadata after cleanup

    Returns:
        Dictionary with cleanup statistics
    """
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    expired_keys = []
    for key, meta in metadata.items():
        created_at = meta.get("created_at", current_time)
        if current_time - created_at > max_age_seconds:
            expired_keys.append(key)

    expired_count = 0
    expired_size = 0
    for key in expired_keys:
        size = evict_entry(key, metadata, access_times, cache_dir)
        expired_count += 1
        expired_size += size

    if expired_count > 0:
        if save_metadata_callback:
            save_metadata_callback()
        logger.info(
            f"Cleanup: removed {expired_count} entries ({expired_size / (1024 * 1024):.2f} MB)"
        )

    return {
        "removed_entries": expired_count,
        "removed_size_mb": expired_size / (1024 * 1024),
    }


def get_cache_stats(
    metadata: dict[str, Any],
    cache_dir: Path,
    max_size_mb: float,
    max_entries: int,
) -> dict[str, Any]:
    """
    Get cache statistics.

    Args:
        metadata: Cache metadata dict
        cache_dir: Cache directory
        max_size_mb: Maximum cache size setting
        max_entries: Maximum entries setting

    Returns:
        Dictionary with cache stats
    """
    total_rows = sum(m.get("rows", 0) for m in metadata.values())
    total_size_mb = get_total_size_mb(metadata, cache_dir)

    # Calculate age statistics
    current_time = time.time()
    ages: list[float] = []
    for meta in metadata.values():
        created_at = meta.get("created_at", current_time)
        ages.append((current_time - created_at) / (24 * 60 * 60))  # days

    return {
        "entries": len(metadata),
        "total_rows": total_rows,
        "total_size_mb": float(round(total_size_mb, 2)),
        "max_size_mb": max_size_mb,
        "max_entries": max_entries,
        "usage_pct": float(round((len(metadata) / max_entries) * 100, 1))
        if max_entries > 0
        else 0.0,
        "size_usage_pct": float(round((total_size_mb / max_size_mb) * 100, 1))
        if max_size_mb > 0
        else 0.0,
        "avg_age_days": float(round(sum(ages) / len(ages), 1)) if ages else 0.0,
        "oldest_entry_days": float(round(max(ages), 1)) if ages else 0.0,
        "cache_dir": str(cache_dir),
    }
