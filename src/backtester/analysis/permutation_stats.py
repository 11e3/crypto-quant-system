"""Permutation Test 통계 유틸리티."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy import stats

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.backtester.analysis.permutation_test import PermutationTestResult

logger = get_logger(__name__)


def shuffle_data(data: pd.DataFrame, columns_to_shuffle: list[str]) -> pd.DataFrame:
    """
    Returns 기반 블록 부트스트랩으로 데이터 셔플.

    OHLC 관계를 유지하면서 시계열 순서를 재배열.
    Index (날짜)는 유지하고, 수익률을 블록 단위로 섞어 재구성.

    Args:
        data: OHLCV 데이터
        columns_to_shuffle: 셔플할 컬럼 리스트

    Returns:
        셔플된 데이터프레임
    """
    shuffled = data.copy()

    # close 기반 수익률 계산
    returns = shuffled["close"].pct_change().fillna(0).values

    # 블록 부트스트랩으로 수익률 재배열 (block_size=5)
    block_size = 5
    n = len(returns)
    resampled_returns: list[float] = []
    i = 0
    while i < n:
        start = np.random.randint(0, max(1, n - block_size))
        block = returns[start : start + block_size]
        resampled_returns.extend(block.tolist())
        i += block_size
    resampled_array = np.array(resampled_returns[:n])

    # 재구성된 수익률로 가격 재생성
    base_price = float(shuffled["close"].iloc[0])
    new_close: list[float] = [base_price]
    for r in resampled_array[1:]:
        new_close.append(new_close[-1] * (1 + r))

    shuffled["close"] = new_close

    # OHLC 일관성 유지
    shuffled["open"] = shuffled["close"].shift(1).fillna(shuffled["close"].iloc[0])
    shuffled["high"] = shuffled[["open", "close"]].max(axis=1) * 1.002
    shuffled["low"] = shuffled[["open", "close"]].min(axis=1) * 0.998

    # volume 셔플
    if "volume" in columns_to_shuffle and "volume" in shuffled.columns:
        volume_values = shuffled["volume"].values
        volume_array = np.array(volume_values, dtype=np.float64).copy()
        np.random.shuffle(volume_array)
        shuffled["volume"] = volume_array

    return shuffled


def compute_statistics(
    original_return: float,
    original_sharpe: float,
    original_win_rate: float,
    shuffled_returns: list[float],
    shuffled_sharpes: list[float],
    shuffled_win_rates: list[float],
    result_class: type[PermutationTestResult],
) -> PermutationTestResult:
    """
    Z-score와 p-value 계산.

    Args:
        original_return: 원본 수익률
        original_sharpe: 원본 샤프 비율
        original_win_rate: 원본 승률
        shuffled_returns: 셔플된 수익률 리스트
        shuffled_sharpes: 셔플된 샤프 비율 리스트
        shuffled_win_rates: 셔플된 승률 리스트
        result_class: PermutationTestResult 클래스

    Returns:
        PermutationTestResult 객체
    """
    result = result_class(
        original_return=original_return,
        original_sharpe=original_sharpe,
        original_win_rate=original_win_rate,
        shuffled_returns=shuffled_returns,
        shuffled_sharpes=shuffled_sharpes,
        shuffled_win_rates=shuffled_win_rates,
    )

    if not shuffled_returns:
        logger.error("No valid shuffled results")
        return result

    # Return 기반 Z-score 계산
    mean_shuffled = float(np.mean(shuffled_returns))
    std_shuffled = float(np.std(shuffled_returns))

    result.mean_shuffled_return = mean_shuffled
    result.std_shuffled_return = std_shuffled

    # Z-score = (X - μ) / σ
    if std_shuffled > 0:
        result.z_score = (original_return - mean_shuffled) / std_shuffled
    else:
        result.z_score = 0.0

    # P-value: 우연에 의해 original만큼 좋은 성과가 나올 확률 (양측 검정)
    result.p_value = float(2 * (1 - stats.norm.cdf(abs(result.z_score))))

    # 통계적 유의성 판정
    if result.p_value < 0.01:
        result.confidence_level = "1%"
        result.is_statistically_significant = True
    elif result.p_value < 0.05:
        result.confidence_level = "5%"
        result.is_statistically_significant = True
    else:
        result.confidence_level = "not significant"
        result.is_statistically_significant = False

    # 해석
    result.interpretation = interpret_results(result)

    return result


def interpret_results(result: PermutationTestResult) -> str:
    """결과 해석 문자열 생성."""
    if result.z_score < 0:
        return (
            f"⚠️ 원본 성과({result.original_return:.2%})가 "
            f"무작위 셔플 평균({result.mean_shuffled_return:.2%})보다 낮음. "
            f"전략이 실제 신호를 캡처하지 못하는 것으로 보임."
        )
    elif result.z_score < 1.0:
        return (
            f"❌ Z-score={result.z_score:.2f} < 1.0: "
            f"통계적으로 유의하지 않음 (p-value={result.p_value:.4f}). "
            f"이 성과는 우연일 가능성이 높음. 과적합 의심."
        )
    elif result.z_score < 2.0:
        return (
            f"⚠️ Z-score={result.z_score:.2f}: "
            f"약하게 유의함 (p-value={result.p_value:.4f}). "
            f"어느 정도 신호가 있으나 과적합 우려."
        )
    elif result.z_score < 3.0:
        return (
            f"✅ Z-score={result.z_score:.2f} ({result.confidence_level} 유의수준): "
            f"통계적으로 유의한 성과. 전략에 실제 신호가 있을 가능성 높음."
        )
    else:
        return (
            f"🎯 Z-score={result.z_score:.2f} ({result.confidence_level} 유의수준): "
            f"매우 강한 통계적 유의성. 전략의 신호 품질이 우수함."
        )
