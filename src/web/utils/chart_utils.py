"""Chart utility functions.

Utilities for chart rendering optimization:
- Data downsampling for large datasets
- Color schemes
- Layout presets
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["downsample_timeseries"]


def downsample_timeseries(
    dates: pd.DatetimeIndex | np.ndarray,
    values: np.ndarray,
    max_points: int = 1000,
) -> tuple[pd.DatetimeIndex | np.ndarray, np.ndarray]:
    """시계열 데이터를 다운샘플링하여 차트 렌더링 성능 향상.

    LTTB (Largest-Triangle-Three-Buckets) 알고리즘의 단순화 버전 사용.
    큰 데이터셋을 고정된 포인트 수로 줄이면서 중요한 특징 보존.

    Args:
        dates: 날짜/시간 배열
        values: 값 배열
        max_points: 최대 포인트 수 (기본: 1000)

    Returns:
        (downsampled_dates, downsampled_values) 튜플

    Examples:
        >>> dates = pd.date_range("2020-01-01", periods=10000, freq="1h")
        >>> values = np.random.randn(10000).cumsum()
        >>> ds_dates, ds_values = downsample_timeseries(dates, values, max_points=1000)
        >>> len(ds_dates)
        1000
    """
    n_points = len(values)

    # 이미 작은 데이터셋은 그대로 반환
    if n_points <= max_points:
        return dates, values

    # 균등 간격 샘플링
    # 시작점과 끝점은 항상 포함
    indices = np.linspace(0, n_points - 1, max_points, dtype=int)

    # 중복 제거 (혹시 있을 경우)
    indices = np.unique(indices)

    downsampled_dates = dates[indices] if isinstance(dates, np.ndarray) else dates[indices]
    downsampled_values = values[indices]

    return downsampled_dates, downsampled_values


def downsample_timeseries_lttb(
    dates: pd.DatetimeIndex | np.ndarray,
    values: np.ndarray,
    max_points: int = 1000,
) -> tuple[pd.DatetimeIndex | np.ndarray, np.ndarray]:
    """LTTB 알고리즘을 사용한 고급 다운샘플링.

    더 정교한 알고리즘으로, 시각적으로 중요한 포인트를 선택.
    급격한 변화나 피크를 보존하는 데 유리.

    Args:
        dates: 날짜/시간 배열
        values: 값 배열
        max_points: 최대 포인트 수

    Returns:
        (downsampled_dates, downsampled_values) 튜플
    """
    n_points = len(values)

    if n_points <= max_points:
        return dates, values

    # 버킷 크기 계산
    bucket_size = (n_points - 2) / (max_points - 2)

    # 결과 인덱스 저장
    sampled_indices: list[int] = [0]  # 첫 포인트는 항상 포함

    # 각 버킷에서 최대 삼각형 면적을 가지는 포인트 선택
    a_idx = 0
    for i in range(1, max_points - 1):
        # 현재 버킷 범위
        bucket_start = int((i - 1) * bucket_size) + 1
        bucket_end = int(i * bucket_size) + 1

        # 다음 버킷의 평균 포인트
        next_bucket_start = int(i * bucket_size) + 1
        next_bucket_end = min(int((i + 1) * bucket_size) + 1, n_points)
        next_avg_x = (next_bucket_start + next_bucket_end) / 2
        next_avg_y = np.mean(values[next_bucket_start:next_bucket_end])

        # 현재 버킷에서 최대 삼각형 면적을 가지는 포인트 찾기
        max_area = -1.0
        max_idx = bucket_start

        for idx in range(bucket_start, bucket_end):
            # 삼각형 면적 계산
            area = abs(
                (a_idx - next_avg_x) * (values[idx] - values[a_idx])
                - (a_idx - idx) * (next_avg_y - values[a_idx])
            )

            if area > max_area:
                max_area = area
                max_idx = idx

        sampled_indices.append(max_idx)
        a_idx = max_idx

    # 마지막 포인트는 항상 포함
    sampled_indices.append(n_points - 1)

    # 인덱스로 샘플링
    sampled_indices_array = np.array(sampled_indices)
    downsampled_dates = (
        dates[sampled_indices_array]
        if isinstance(dates, np.ndarray)
        else dates[sampled_indices_array]
    )
    downsampled_values = values[sampled_indices_array]

    return downsampled_dates, downsampled_values
