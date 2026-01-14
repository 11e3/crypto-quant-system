"""
Trade execution helpers for trade simulation.

Contains exit execution and whipsaw handling logic.
"""

from datetime import date

import numpy as np

from src.backtester.engine.trade_simulator_state import SimulationState
from src.backtester.models import BacktestConfig
from src.execution.orders.advanced_orders import AdvancedOrderManager


def execute_exit(
    state: SimulationState,
    config: BacktestConfig,
    t_idx: int,
    d_idx: int,
    current_date: date,
    sorted_dates: np.ndarray,
    tickers: list[str],
    exit_prices: np.ndarray,
    order_manager: AdvancedOrderManager,
    is_stop_loss: bool,
    is_take_profit: bool,
    exit_reason: str,
) -> None:
    """Execute a single exit."""
    exit_price = exit_prices[t_idx, d_idx]
    amount = state.position_amounts[t_idx]
    entry_price = state.position_entry_prices[t_idx]

    revenue = amount * exit_price * (1 - config.fee_rate)
    state.cash += revenue

    pnl = revenue - (amount * entry_price)
    pnl_pct = (exit_price / entry_price - 1) * 100 if entry_price > 0 else 0.0
    commission = amount * entry_price * config.fee_rate + amount * exit_price * config.fee_rate
    slippage = amount * (entry_price + exit_price) * config.slippage_rate

    state.trades_list.append(
        {
            "ticker": tickers[t_idx],
            "entry_date": sorted_dates[state.position_entry_dates[t_idx]],
            "entry_price": entry_price,
            "exit_date": current_date,
            "exit_price": exit_price,
            "amount": amount,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "is_whipsaw": False,
            "commission_cost": commission,
            "slippage_cost": slippage,
            "is_stop_loss": is_stop_loss,
            "is_take_profit": is_take_profit,
            "exit_reason": exit_reason,
        }
    )

    order_manager.cancel_all_orders(ticker=tickers[t_idx])
    state.position_amounts[t_idx] = 0
    state.position_entry_prices[t_idx] = 0
    state.position_entry_dates[t_idx] = -1


def handle_whipsaw(
    state: SimulationState,
    t_idx: int,
    d_idx: int,
    current_date: date,
    tickers: list[str],
    arrays: dict[str, np.ndarray],
    invest_amount: float,
    buy_price: float,
    fee_rate: float,
    slippage_rate: float,
) -> None:
    """Handle whipsaw (same-day entry and exit)."""
    sell_price = arrays["exit_prices"][t_idx, d_idx]
    amount = (invest_amount / buy_price) * (1 - fee_rate)
    return_money = amount * sell_price * (1 - fee_rate)
    state.cash = state.cash - invest_amount + return_money

    pnl = return_money - invest_amount
    pnl_pct = (sell_price / buy_price - 1) * 100 if buy_price > 0 else 0.0
    commission = amount * (buy_price + sell_price) * fee_rate
    slippage = amount * (buy_price + sell_price) * slippage_rate

    state.trades_list.append(
        {
            "ticker": tickers[t_idx],
            "entry_date": current_date,
            "entry_price": buy_price,
            "exit_date": current_date,
            "exit_price": sell_price,
            "amount": amount,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "is_whipsaw": True,
            "commission_cost": commission,
            "slippage_cost": slippage,
            "is_stop_loss": False,
            "is_take_profit": False,
            "exit_reason": "whipsaw",
        }
    )


def handle_normal_entry(
    state: SimulationState,
    t_idx: int,
    d_idx: int,
    invest_amount: float,
    buy_price: float,
    fee_rate: float,
) -> None:
    """Handle normal entry (position opened)."""
    amount = (invest_amount / buy_price) * (1 - fee_rate)
    state.position_amounts[t_idx] = amount
    state.position_entry_prices[t_idx] = buy_price
    state.position_entry_dates[t_idx] = d_idx
    state.cash -= invest_amount
