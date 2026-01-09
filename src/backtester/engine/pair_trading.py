"""
Pair trading backtest implementation.

Specialized backtesting for pair trading strategies.
"""

from datetime import date
from typing import Any, cast

import numpy as np
import pandas as pd

from src.backtester.engine.pair_trading_data import (
    build_pair_arrays,
    filter_by_date_range,
    filter_pair_valid_dates,
    get_common_dates,
    prepare_ticker_signals,
)
from src.backtester.engine.pair_trading_helpers import (
    build_pair_result,
    calculate_pair_equity,
    process_pair_entries,
    process_pair_exits,
    track_pair_returns,
)
from src.backtester.models import BacktestConfig, BacktestResult
from src.strategies.base import Strategy
from src.utils.logger import get_logger
from src.utils.memory import get_float_dtype

logger = get_logger(__name__)


def run_pair_trading_backtest(
    strategy: Strategy,
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    ticker1: str,
    ticker2: str,
    config: BacktestConfig,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BacktestResult:
    """
    Run backtest for pair trading strategy.

    Args:
        strategy: PairTradingStrategy instance
        df1: DataFrame for first ticker
        df2: DataFrame for second ticker
        ticker1: First ticker symbol
        ticker2: Second ticker symbol
        config: Backtest configuration
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        BacktestResult with performance metrics
    """
    # Filter by date range if specified
    df1, df2 = filter_by_date_range(df1, df2, start_date, end_date)

    # Calculate spread indicators
    strategy_spread = cast(Any, strategy)
    merged_df = strategy_spread.calculate_spread_for_pair(df1, df2)
    merged_df = strategy.generate_signals(merged_df)

    # Create ticker-specific signals
    ticker_data = prepare_ticker_signals(df1, df2, merged_df, ticker1, ticker2, config)
    common_dates = get_common_dates(merged_df, df1, df2)

    if len(common_dates) == 0:
        logger.warning("No data available for pair trading backtest")
        return BacktestResult(strategy_name=strategy.name)

    # Build numpy arrays
    tickers = [ticker1, ticker2]
    arrays = build_pair_arrays(ticker_data, common_dates, tickers)

    # Filter to valid dates
    sorted_dates, arrays = filter_pair_valid_dates(
        arrays, common_dates, getattr(strategy, "lookback_period", 0)
    )

    if len(sorted_dates) == 0:
        return BacktestResult(strategy_name=strategy.name)

    # Run simulation
    state = _run_pair_simulation(sorted_dates, arrays, tickers, config)

    # Build result
    return build_pair_result(strategy, state, sorted_dates, config)


def _run_pair_simulation(
    sorted_dates: np.ndarray,
    arrays: dict[str, np.ndarray],
    tickers: list[str],
    config: BacktestConfig,
) -> dict[str, Any]:
    """Run pair trading simulation loop."""
    n_dates = len(sorted_dates)
    n_tickers = 2
    float_dtype = get_float_dtype()

    cash = config.initial_capital
    fee_rate = config.fee_rate
    max_slots = config.max_slots

    position_amounts = np.zeros(n_tickers, dtype=float_dtype)
    position_entry_prices = np.zeros(n_tickers, dtype=float_dtype)
    position_entry_dates = np.full(n_tickers, -1, dtype=np.int32)

    equity_curve = np.zeros(n_dates, dtype=float_dtype)
    trades_list: list[dict[str, Any]] = []
    asset_returns: dict[str, list[float]] = {ticker: [] for ticker in tickers}
    previous_closes = np.full(n_tickers, np.nan, dtype=float_dtype)

    closes = arrays["closes"]
    entry_signals = arrays["entry_signals"]
    exit_signals = arrays["exit_signals"]
    entry_prices = arrays["entry_prices"]
    exit_prices = arrays["exit_prices"]

    for d_idx in range(n_dates):
        current_date = sorted_dates[d_idx]
        valid_data = ~np.isnan(closes[:, d_idx])

        track_pair_returns(d_idx, tickers, closes, valid_data, previous_closes, asset_returns)

        if not np.all(valid_data):
            equity_curve[d_idx] = calculate_pair_equity(
                cash, position_amounts, closes, d_idx, valid_data
            )
            continue

        cash = process_pair_exits(
            d_idx,
            current_date,
            sorted_dates,
            tickers,
            position_amounts,
            position_entry_prices,
            position_entry_dates,
            exit_signals,
            exit_prices,
            fee_rate,
            trades_list,
            cash,
        )

        cash = process_pair_entries(
            d_idx,
            current_date,
            tickers,
            position_amounts,
            position_entry_prices,
            position_entry_dates,
            entry_signals,
            entry_prices,
            fee_rate,
            max_slots,
            trades_list,
            cash,
        )

        equity_curve[d_idx] = calculate_pair_equity(
            cash, position_amounts, closes, d_idx, valid_data
        )

    return {
        "equity_curve": equity_curve,
        "trades_list": trades_list,
        "asset_returns": asset_returns,
    }
