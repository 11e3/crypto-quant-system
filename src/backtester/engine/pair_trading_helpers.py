"""
Helper functions for pair trading simulation.

Contains utility functions for tracking returns, calculating equity,
and processing entries/exits in pair trading backtests.
"""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from src.backtester.engine.metrics_calculator import calculate_metrics_vectorized
from src.backtester.models import BacktestConfig, BacktestResult, Trade
from src.strategies.base import Strategy
from src.utils.memory import optimize_dtypes

__all__ = [
    "track_pair_returns",
    "calculate_pair_equity",
    "process_pair_exits",
    "process_pair_entries",
    "build_pair_result",
]


def track_pair_returns(
    d_idx: int,
    tickers: list[str],
    closes: np.ndarray,
    valid_data: np.ndarray,
    previous_closes: np.ndarray,
    asset_returns: dict[str, list[float]],
) -> None:
    """Track individual asset returns."""
    for t_idx in range(2):
        if valid_data[t_idx] and not np.isnan(closes[t_idx, d_idx]):
            current_close = closes[t_idx, d_idx]
            if not np.isnan(previous_closes[t_idx]):
                daily_return = (current_close - previous_closes[t_idx]) / previous_closes[t_idx]
                asset_returns[tickers[t_idx]].append(daily_return)
            previous_closes[t_idx] = current_close


def calculate_pair_equity(
    cash: float,
    position_amounts: np.ndarray,
    closes: np.ndarray,
    d_idx: int,
    valid_data: np.ndarray,
) -> float:
    """Calculate equity for pair trading."""
    valid_closes = np.where(valid_data, closes[:, d_idx], np.nan)
    positions_value: float = float(np.nansum(position_amounts * valid_closes))
    if np.isnan(positions_value):
        positions_value = 0.0
    return cash + positions_value


def process_pair_exits(
    d_idx: int,
    current_date: date,
    sorted_dates: np.ndarray,
    tickers: list[str],
    position_amounts: np.ndarray,
    position_entry_prices: np.ndarray,
    position_entry_dates: np.ndarray,
    exit_signals: np.ndarray,
    exit_prices: np.ndarray,
    fee_rate: float,
    trades_list: list[dict[str, Any]],
    cash: float,
) -> float:
    """Process pair trading exits."""
    in_position = position_amounts > 0

    if not np.any(exit_signals[:, d_idx] & in_position):
        return cash

    for t_idx in range(2):
        if position_amounts[t_idx] <= 0:
            continue

        exit_price = exit_prices[t_idx, d_idx]
        if np.isnan(exit_price):
            continue

        amount = position_amounts[t_idx]
        revenue = amount * exit_price * (1 - fee_rate)
        cash += revenue

        entry_price = position_entry_prices[t_idx]
        pnl = revenue - (amount * entry_price)
        pnl_pct = (exit_price / entry_price - 1) * 100

        for trade in trades_list:
            if (
                trade["ticker"] == tickers[t_idx]
                and trade["exit_date"] is None
                and trade["entry_date"] == sorted_dates[position_entry_dates[t_idx]]
            ):
                trade["exit_date"] = current_date
                trade["exit_price"] = exit_price
                trade["pnl"] = pnl
                trade["pnl_pct"] = pnl_pct
                break

        position_amounts[t_idx] = 0.0
        position_entry_prices[t_idx] = 0.0
        position_entry_dates[t_idx] = -1

    return cash


def process_pair_entries(
    d_idx: int,
    current_date: date,
    tickers: list[str],
    position_amounts: np.ndarray,
    position_entry_prices: np.ndarray,
    position_entry_dates: np.ndarray,
    entry_signals: np.ndarray,
    entry_prices: np.ndarray,
    fee_rate: float,
    max_slots: int,
    trades_list: list[dict[str, Any]],
    cash: float,
) -> float:
    """Process pair trading entries."""
    not_in_position = position_amounts == 0.0
    has_entry_signal = entry_signals[:, d_idx].astype(bool)

    if not (np.all(has_entry_signal) and np.all(not_in_position)):
        return cash

    current_positions = int(np.sum(position_amounts > 0))
    available_slots = max_slots - current_positions

    if available_slots < 2:
        return cash

    for t_idx in range(2):
        buy_price = entry_prices[t_idx, d_idx]
        if np.isnan(buy_price):
            continue

        invest_amount = cash / 2
        if invest_amount <= 0:
            continue

        amount = invest_amount / buy_price * (1 - fee_rate)
        cash -= invest_amount

        position_amounts[t_idx] = amount
        position_entry_prices[t_idx] = buy_price
        position_entry_dates[t_idx] = d_idx

        trades_list.append(
            {
                "ticker": tickers[t_idx],
                "entry_date": current_date,
                "entry_price": buy_price,
                "exit_date": None,
                "exit_price": None,
                "amount": amount,
                "pnl": 0.0,
                "pnl_pct": 0.0,
                "is_whipsaw": False,
            }
        )

    return cash


def build_pair_result(
    strategy: Strategy,
    state: dict[str, Any],
    sorted_dates: np.ndarray,
    config: BacktestConfig,
) -> BacktestResult:
    """Build BacktestResult from simulation state."""
    trades_df = pd.DataFrame(state["trades_list"]) if state["trades_list"] else pd.DataFrame()
    if not trades_df.empty:
        trades_df = optimize_dtypes(trades_df)

    result = calculate_metrics_vectorized(
        state["equity_curve"],
        sorted_dates,
        trades_df,
        config,
        asset_returns=state["asset_returns"],
    )
    result.strategy_name = strategy.name

    if len(trades_df) > 0:
        result.trades = [
            Trade(
                ticker=row["ticker"],
                entry_date=row["entry_date"],
                entry_price=row["entry_price"],
                exit_date=row["exit_date"],
                exit_price=row["exit_price"],
                amount=row["amount"],
                pnl=row["pnl"],
                pnl_pct=row["pnl_pct"],
                is_whipsaw=row["is_whipsaw"],
            )
            for _, row in trades_df.iterrows()
        ]

    return result
