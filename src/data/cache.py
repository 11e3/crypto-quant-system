"""
Indicator cache system for backtesting optimization.

Caches calculated indicators to data/processed/ to avoid
recalculating on every backtest run.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import CACHE_METADATA_FILENAME, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IndicatorCache:
    """
    Manages caching of indicator calculations.

    Stores processed DataFrames with indicators in parquet format,
    with metadata to track calculation parameters.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """
        Initialize the indicator cache.

        Args:
            cache_dir: Directory for cached files. Defaults to data/processed/
        """
        self.cache_dir = cache_dir or PROCESSED_DATA_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / CACHE_METADATA_FILENAME
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> dict[str, Any]:
        """Load cache metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    data: Any = json.load(f)
                    if isinstance(data, dict):
                        return data
                    return {}
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata to JSON file."""
        with open(self.metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)

    def _generate_cache_key(
        self,
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
        # Create deterministic hash of parameters
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{ticker}_{interval}_{params_hash}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.parquet"

    def get(
        self,
        ticker: str,
        interval: str,
        params: dict[str, Any],
        raw_data_mtime: float | None = None,
    ) -> pd.DataFrame | None:
        """
        Retrieve cached indicators if valid.

        Args:
            ticker: Asset ticker
            interval: Data interval
            params: Indicator parameters used for calculation
            raw_data_mtime: Modification time of raw data file (for invalidation)

        Returns:
            Cached DataFrame with indicators, or None if cache miss
        """
        cache_key = self._generate_cache_key(ticker, interval, params)
        cache_path = self._get_cache_path(cache_key)

        # Check if cache file exists
        if not cache_path.exists():
            logger.debug(f"Cache miss (file not found): {cache_key}")
            return None

        # Check metadata
        if cache_key not in self._metadata:
            logger.debug(f"Cache miss (no metadata): {cache_key}")
            return None

        meta = self._metadata[cache_key]

        # Verify parameters match
        if meta.get("params") != params:
            logger.debug(f"Cache miss (params changed): {cache_key}")
            return None

        # Check if raw data was updated
        if raw_data_mtime is not None:
            cached_mtime = meta.get("raw_data_mtime", 0)
            if raw_data_mtime > cached_mtime:
                logger.debug(f"Cache miss (raw data updated): {cache_key}")
                return None

        # Load cached data
        try:
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index)
            logger.debug(f"Cache hit: {cache_key}")
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_key}: {e}")
            return None

    def set(
        self,
        ticker: str,
        interval: str,
        params: dict[str, Any],
        df: pd.DataFrame,
        raw_data_mtime: float | None = None,
    ) -> None:
        """
        Store calculated indicators in cache.

        Args:
            ticker: Asset ticker
            interval: Data interval
            params: Indicator parameters used for calculation
            df: DataFrame with calculated indicators
            raw_data_mtime: Modification time of raw data file
        """
        cache_key = self._generate_cache_key(ticker, interval, params)
        cache_path = self._get_cache_path(cache_key)

        # Save DataFrame
        df.to_parquet(cache_path, engine="pyarrow")

        # Update metadata
        self._metadata[cache_key] = {
            "ticker": ticker,
            "interval": interval,
            "params": params,
            "raw_data_mtime": raw_data_mtime or 0,
            "rows": len(df),
        }
        self._save_metadata()

        logger.debug(f"Cache saved: {cache_key} ({len(df)} rows)")

    def invalidate(
        self,
        ticker: str | None = None,
        interval: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            ticker: Invalidate only this ticker (or all if None)
            interval: Invalidate only this interval (or all if None)

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []

        for key, meta in self._metadata.items():
            if ticker and meta.get("ticker") != ticker:
                continue
            if interval and meta.get("interval") != interval:
                continue
            keys_to_remove.append(key)

        for key in keys_to_remove:
            # Remove file
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
            # Remove metadata
            del self._metadata[key]

        if keys_to_remove:
            self._save_metadata()

        logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
        return len(keys_to_remove)

    def clear(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of entries cleared
        """
        count = len(self._metadata)

        # Remove all parquet files
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()

        # Clear metadata
        self._metadata = {}
        self._save_metadata()

        logger.info(f"Cleared {count} cache entries")
        return count

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_rows = sum(m.get("rows", 0) for m in self._metadata.values())
        total_size = sum(
            self._get_cache_path(k).stat().st_size
            for k in self._metadata
            if self._get_cache_path(k).exists()
        )

        return {
            "entries": len(self._metadata),
            "total_rows": total_rows,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }


# Global cache instance
_cache: IndicatorCache | None = None


def get_cache() -> IndicatorCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = IndicatorCache()
    return _cache
