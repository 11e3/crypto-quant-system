"""
Cache metadata utilities.

Handles loading, saving, and key generation for cache metadata.
"""

import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any


def load_metadata(
    metadata_file: Path,
    access_times: OrderedDict[str, float],
) -> dict[str, Any]:
    """
    Load cache metadata from JSON file.

    Args:
        metadata_file: Path to metadata JSON file
        access_times: OrderedDict to populate with access times

    Returns:
        Loaded metadata dict
    """
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                data: Any = json.load(f)
                if isinstance(data, dict):
                    # Separate metadata and access times
                    if "_access_times" in data:
                        access_times_data = data.pop("_access_times")
                        if isinstance(access_times_data, dict):
                            access_times.clear()
                            for k, v in sorted(
                                access_times_data.items(),
                                key=lambda x: x[1],
                            ):
                                access_times[k] = v
                    return data
                return {}
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_metadata(
    metadata: dict[str, Any],
    access_times: OrderedDict[str, float],
    metadata_file: Path,
) -> None:
    """
    Save cache metadata to JSON file.

    Args:
        metadata: Cache metadata dict
        access_times: Access times OrderedDict
        metadata_file: Path to save metadata
    """
    data_to_save = metadata.copy()
    data_to_save["_access_times"] = dict(access_times)
    with open(metadata_file, "w") as f:
        json.dump(data_to_save, f, indent=2)


def generate_cache_key(
    ticker: str,
    interval: str,
    params: dict[str, Any],
) -> str:
    """
    Generate unique cache key from ticker, interval, and parameters.

    Args:
        ticker: Asset ticker
        interval: Data interval
        params: Indicator parameters

    Returns:
        Cache key string
    """
    params_str = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{ticker}_{interval}_{params_hash}"


def get_cache_path(cache_dir: Path, cache_key: str) -> Path:
    """
    Get file path for cache key.

    Args:
        cache_dir: Cache directory
        cache_key: Cache key

    Returns:
        Path to cache file
    """
    return cache_dir / f"{cache_key}.parquet"
