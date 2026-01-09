"""
WFA optimization and aggregation utilities.
"""

from collections.abc import Callable
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

from src.backtester.wfa.wfa_backtest import simple_backtest
from src.backtester.wfa.wfa_models import WFAReport, WFASegment
from src.utils.logger import get_logger

__all__ = ["optimize_parameters_grid", "aggregate_wfa_results"]

logger = get_logger(__name__)


def optimize_parameters_grid(
    data: pd.DataFrame,
    strategy_factory: Callable[..., Any],
    param_ranges: dict[str, list[Any]],
    initial_capital: float,
) -> dict[str, Any]:
    """
    Training 구간에서 파라미터 최적화 (Grid Search).

    목표: Training 수익률 최대화

    Args:
        data: Training 데이터
        strategy_factory: 파라미터를 받아 Strategy 생성하는 함수
        param_ranges: 테스트할 파라미터 범위
        initial_capital: 초기 자본

    Returns:
        최적 파라미터 딕셔너리
    """
    param_keys = list(param_ranges.keys())
    param_values = [param_ranges[key] for key in param_keys]

    best_params: dict[str, Any] | None = None
    best_return = -float("inf")

    for param_combo in product(*param_values):
        params = dict(zip(param_keys, param_combo, strict=False))

        try:
            strategy = strategy_factory(params)
            result = simple_backtest(data, strategy, initial_capital)

            if result.total_return > best_return:
                best_return = result.total_return
                best_params = params
        except Exception as e:
            logger.debug(f"Parameter combination {params} failed: {e}")
            continue

    if best_params is None:
        first_combo = [v[0] for v in param_values]
        best_params = dict(zip(param_keys, first_combo, strict=False))
        logger.warning("Optimization failed, using default parameters")

    return best_params


def aggregate_wfa_results(segments: list[WFASegment]) -> WFAReport:
    """
    모든 세그먼트 결과 집계.

    Args:
        segments: WFA 세그먼트 리스트

    Returns:
        WFAReport 집계 결과
    """
    report = WFAReport(segments=segments)

    if not segments:
        return report

    # 수익률 집계
    is_returns = [s.in_sample_result.total_return for s in segments if s.in_sample_result]
    oos_returns = [s.out_of_sample_result.total_return for s in segments if s.out_of_sample_result]

    report.in_sample_avg_return = float(np.mean(is_returns)) if is_returns else 0.0
    report.out_of_sample_avg_return = float(np.mean(oos_returns)) if oos_returns else 0.0

    # 과적합 비율
    if report.in_sample_avg_return > 0:
        report.overfitting_ratio = report.out_of_sample_avg_return / report.in_sample_avg_return

    # Sharpe 비율 집계
    is_sharpes = [s.in_sample_result.sharpe_ratio for s in segments if s.in_sample_result]
    oos_sharpes = [s.out_of_sample_result.sharpe_ratio for s in segments if s.out_of_sample_result]

    report.in_sample_sharpe = float(np.mean(is_sharpes)) if is_sharpes else 0.0
    report.out_of_sample_sharpe = float(np.mean(oos_sharpes)) if oos_sharpes else 0.0

    # MDD 집계
    is_mdds = [s.in_sample_result.mdd for s in segments if s.in_sample_result]
    oos_mdds = [s.out_of_sample_result.mdd for s in segments if s.out_of_sample_result]

    report.in_sample_mdd = float(np.mean(is_mdds)) if is_mdds else 0.0
    report.out_of_sample_mdd = float(np.mean(oos_mdds)) if oos_mdds else 0.0

    # 파라미터 안정성
    if segments and segments[0].optimal_params:
        for param_name in segments[0].optimal_params:
            param_values = [s.optimal_params[param_name] for s in segments if s.optimal_params]
            report.parameter_stability[param_name] = param_values

    return report
