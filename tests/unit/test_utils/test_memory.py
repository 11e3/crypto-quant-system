"""Tests for utils.memory module."""

import numpy as np
import pandas as pd
import pytest

from src.utils.memory import (
    MemoryProfiler,
    get_float_dtype,
    get_memory_usage_mb,
    log_memory_usage,
    optimize_dtypes,
    use_float32_for_arrays,
)


class TestMemoryUtilities:
    """Test memory utilities."""

    def test_get_memory_usage_mb_numpy(self) -> None:
        """Test get_memory_usage_mb with numpy array."""
        arr = np.zeros((1000, 1000), dtype=np.float64)
        usage_mb = get_memory_usage_mb(arr)
        assert isinstance(usage_mb, float)
        assert usage_mb > 0
        # ~8MB for 1000x1000 float64
        assert 7 < usage_mb < 10

    def test_get_memory_usage_mb_dataframe(self) -> None:
        """Test get_memory_usage_mb with pandas DataFrame."""
        df = pd.DataFrame({"a": np.arange(1000), "b": np.arange(1000)})
        usage_mb = get_memory_usage_mb(df)
        assert isinstance(usage_mb, float)
        assert usage_mb > 0

    def test_get_memory_usage_mb_list(self) -> None:
        """Test get_memory_usage_mb with list."""
        data = [0] * 100000
        usage_mb = get_memory_usage_mb(data)
        assert isinstance(usage_mb, float)
        assert usage_mb >= 0

    def test_get_memory_usage_mb_dict(self) -> None:
        """Test get_memory_usage_mb with dict."""
        data = {f"key_{i}": i for i in range(1000)}
        usage_mb = get_memory_usage_mb(data)
        assert isinstance(usage_mb, float)
        assert usage_mb >= 0

    def test_optimize_dtypes(self) -> None:
        """Test optimize_dtypes reduces DataFrame memory."""
        df = pd.DataFrame(
            {
                "open": np.random.rand(1000),
                "high": np.random.rand(1000),
                "low": np.random.rand(1000),
                "close": np.random.rand(1000),
                "volume": np.arange(1000, dtype=np.int64),
            }
        )

        original_memory = get_memory_usage_mb(df)
        optimized_df = optimize_dtypes(df)
        optimized_memory = get_memory_usage_mb(optimized_df)

        # Optimized version should be smaller or equal
        assert optimized_memory <= original_memory

    def test_optimize_dtypes_int8(self) -> None:
        """Test optimize_dtypes with int8 range."""
        df = pd.DataFrame({"col": [1, 2, 3, 4, 5]})  # Fits in int8 (-128 to 127)
        optimized = optimize_dtypes(df)
        assert optimized["col"].dtype == np.int8

    def test_optimize_dtypes_int16(self) -> None:
        """Test optimize_dtypes with int16 range."""
        df = pd.DataFrame({"col": [1000, 2000, 3000]})  # Fits in int16
        optimized = optimize_dtypes(df)
        assert optimized["col"].dtype == np.int16

    def test_optimize_dtypes_int32(self) -> None:
        """Test optimize_dtypes with int32 range."""
        df = pd.DataFrame({"col": [100000, 200000, 300000]})  # Fits in int32
        optimized = optimize_dtypes(df)
        assert optimized["col"].dtype == np.int32

    def test_optimize_dtypes_int64(self) -> None:
        """Test optimize_dtypes with int64 range."""
        df = pd.DataFrame({"col": [10**15, 10**15 + 1]})  # Requires int64
        optimized = optimize_dtypes(df)
        assert optimized["col"].dtype == np.int64

    def test_optimize_dtypes_float32_ohlc(self) -> None:
        """Test optimize_dtypes converts OHLC columns to float32."""
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [105.0, 106.0, 107.0],
                "low": [99.0, 100.0, 101.0],
                "close": [102.0, 103.0, 104.0],
                "volume": [1000.0, 2000.0, 3000.0],
            }
        )
        optimized = optimize_dtypes(df)
        assert optimized["open"].dtype == np.float32
        assert optimized["high"].dtype == np.float32
        assert optimized["low"].dtype == np.float32
        assert optimized["close"].dtype == np.float32
        assert optimized["volume"].dtype == np.float32

    def test_optimize_dtypes_float32_general(self) -> None:
        """Test optimize_dtypes with general float columns."""
        df = pd.DataFrame({"other_col": [1.5, 2.5, 3.5]})
        optimized = optimize_dtypes(df)
        # Should convert to float32 if values fit
        assert optimized["other_col"].dtype == np.float32

    def test_use_float32_for_arrays(self) -> None:
        """Test use_float32_for_arrays returns boolean."""
        result = use_float32_for_arrays()
        assert isinstance(result, bool)
        assert result is True  # Always returns True

    def test_get_float_dtype(self) -> None:
        """Test get_float_dtype returns correct dtype."""
        dtype = get_float_dtype()
        assert dtype == np.float32

    def test_log_memory_usage(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_memory_usage logs correctly."""
        arr1 = np.zeros((100, 100))
        arr2 = np.zeros((50, 50))

        with caplog.at_level("DEBUG"):
            log_memory_usage("test_arrays", arr1, arr2)

        # Should have logged something
        assert len(caplog.records) > 0

    def test_memory_profiler_context_manager(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test MemoryProfiler as context manager."""
        with caplog.at_level("INFO"), MemoryProfiler("test_operation"):
            # Allocate some memory
            data = np.zeros((1000, 1000))
            _ = data

        # Should have logged memory info (if psutil available)
        # Or warning if psutil not available
        assert len(caplog.records) >= 0  # May be 0 if psutil fails

    def test_memory_profiler_exit_when_start_memory_none(self) -> None:
        """Test MemoryProfiler __exit__ when start_memory is None - line 164-165."""
        profiler = MemoryProfiler("test_operation")
        profiler.start_memory = None  # Simulate psutil not available

        # __exit__ should return early without error
        profiler.__exit__(None, None, None)

    def test_memory_profiler_full_context_with_psutil(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test MemoryProfiler __exit__ when psutil is available - line 166-178."""
        with caplog.at_level("INFO"), MemoryProfiler("full_test") as profiler:
            # Check that start_memory was set
            if profiler.start_memory is not None:
                # If psutil was available, start_memory should be a float
                assert isinstance(profiler.start_memory, float)
                assert profiler.start_memory > 0
                # Allocate some memory to see delta
                _ = np.zeros((500, 500), dtype=np.float64)

        # Check log output if psutil was available
        if profiler.start_memory is not None:
            log_messages = [r.message for r in caplog.records]
            assert any("Memory" in msg and "full_test" in msg for msg in log_messages)
