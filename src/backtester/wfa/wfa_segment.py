"""
Walk-forward analysis segment processing helpers.
"""

from collections.abc import Callable
from typing import Any

import pandas as pd

from src.backtester.wfa.wfa_backtest import simple_backtest
from src.backtester.wfa.wfa_models import WFASegment
from src.backtester.wfa.wfa_utils import optimize_parameters_grid
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = ["process_wfa_segment"]


def process_wfa_segment(
    segment: WFASegment,
    data: pd.DataFrame,
    strategy_factory: Callable[[dict[str, Any]], Strategy],
    param_ranges: dict[str, Any],
    initial_capital: float,
    train_period: int,
    verbose: bool = True,
) -> WFASegment | None:
    """
    Process a single WFA segment: optimize on train, test on OOS.

    Args:
        segment: WFA segment to process
        data: Full OHLCV data
        strategy_factory: Function to create strategy from params
        param_ranges: Parameter ranges for optimization
        initial_capital: Initial capital for backtest
        train_period: Training period length
        verbose: Whether to log progress

    Returns:
        Processed segment or None if insufficient data
    """
    # Extract training data
    train_data = data[(data.index >= segment.train_start) & (data.index <= segment.train_end)]

    # Extract test data
    test_data = data[(data.index >= segment.test_start) & (data.index <= segment.test_end)]

    if len(train_data) < train_period * 0.9:
        logger.warning("Segment: Insufficient training data, skipping")
        return None

    # Optimize parameters on training data
    optimal_params = optimize_parameters_grid(
        train_data, strategy_factory, param_ranges, initial_capital
    )
    segment.optimal_params = optimal_params

    # Backtest on training data (In-Sample)
    strategy_is = strategy_factory(optimal_params)
    is_result = simple_backtest(train_data, strategy_is, initial_capital)
    segment.in_sample_result = is_result

    # Backtest on test data (Out-of-Sample)
    strategy_oos = strategy_factory(optimal_params)
    oos_result = simple_backtest(test_data, strategy_oos, initial_capital)
    segment.out_of_sample_result = oos_result

    if verbose:
        logger.info(
            f"  IS Return: {is_result.total_return:.2%}, "
            f"OOS Return: {oos_result.total_return:.2%}, "
            f"Ratio: {segment.oos_is_ratio:.2%} ({segment.overfitting_severity})"
        )

    return segment
