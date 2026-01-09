"""
Robustness Analysis 통계 함수.

이웃 파라미터 분석 및 민감도 계산 함수 제공.
"""

from typing import Any

import numpy as np

from src.backtester.analysis.robustness_models import RobustnessResult


def find_neighbors(
    optimal_params: dict[str, Any],
    results: list[RobustnessResult],
    tolerance: float = 0.20,
) -> list[RobustnessResult]:
    """
    최적값 주변의 파라미터 조합 찾기 (±tolerance%).

    예) optimal_param = 4, tolerance = 0.20
    → 3.2~4.8 범위의 파라미터를 가진 결과들

    Args:
        optimal_params: 최적 파라미터
        results: 모든 테스트 결과
        tolerance: 허용 범위 (0.20 = ±20%)

    Returns:
        이웃 파라미터 조합의 결과 목록
    """
    neighbors: list[RobustnessResult] = []

    for result in results:
        is_neighbor = True

        for param_name, optimal_value in optimal_params.items():
            if param_name not in result.params:
                continue

            actual_value = result.params[param_name]

            # 숫자 파라미터만 판단
            if not isinstance(actual_value, int | float):
                continue

            # 변화율 계산
            if optimal_value == 0:
                is_neighbor = actual_value == 0
            else:
                change_pct = abs(actual_value - optimal_value) / abs(optimal_value)

                if change_pct > tolerance:
                    is_neighbor = False
                    break

        if is_neighbor:
            neighbors.append(result)

    return neighbors


def calculate_sensitivity(results: list[RobustnessResult]) -> dict[str, float]:
    """
    파라미터별 민감도 계산 (0.0~1.0).

    1.0에 가까울수록 해당 파라미터에 민감 (값 변화 시 성과 변화 큼)
    0.0에 가까울수록 덜 민감 (값 변화 시 성과 변화 없음)

    Args:
        results: 모든 테스트 결과

    Returns:
        파라미터별 민감도 점수 (0.0~1.0)
    """
    if not results:
        return {}

    sensitivity: dict[str, float] = {}

    # 첫 번째 결과에서 파라미터 이름 추출
    param_names = list(results[0].params.keys())

    for param_name in param_names:
        # 각 파라미터의 모든 값과 해당 성과
        param_values: list[float] = []
        returns: list[float] = []

        for result in results:
            if param_name in result.params:
                value = result.params[param_name]

                # 숫자만 분석
                if isinstance(value, int | float):
                    param_values.append(float(value))
                    returns.append(result.total_return)

        if len(set(param_values)) < 2:
            # 파라미터 값이 다양하지 않음
            sensitivity[param_name] = 0.0
            continue

        # 상관계수 계산 (파라미터 변화와 성과 변화의 상관성)
        correlation = abs(np.corrcoef(param_values, returns)[0, 1])

        if np.isnan(correlation):
            sensitivity[param_name] = 0.0
        else:
            sensitivity[param_name] = float(correlation)

    return sensitivity


def calculate_neighbor_success_rate(
    optimal_params: dict[str, Any],
    results: list[RobustnessResult],
    tolerance: float = 0.20,
) -> float:
    """
    이웃 파라미터의 성공률 계산.

    최적값의 80% 이상 성과를 내는 이웃 비율.

    Args:
        optimal_params: 최적 파라미터
        results: 모든 테스트 결과
        tolerance: 이웃 범위 (0.20 = ±20%)

    Returns:
        성공률 (0.0~1.0)
    """
    neighbor_results = find_neighbors(optimal_params, results, tolerance)

    if not neighbor_results:
        return 0.0

    # 최적 파라미터의 성과 찾기
    optimal_returns = [r.total_return for r in results if r.params == optimal_params]

    if not optimal_returns:
        return 0.0

    optimal_return = max(optimal_returns)
    threshold = optimal_return * 0.80

    # 최적값의 80% 이상 성과를 내는 이웃 비율
    successful_neighbors = sum(1 for r in neighbor_results if r.total_return >= threshold)

    return successful_neighbors / len(neighbor_results)
