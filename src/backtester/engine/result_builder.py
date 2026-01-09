"""Result builder for vectorized backtest engine."""

import numpy as np
import pandas as pd

from src.backtester.engine.metrics_calculator import calculate_metrics_vectorized
from src.backtester.engine.trade_simulator import SimulationState
from src.backtester.models import BacktestConfig, BacktestResult, Trade
from src.strategies.base import Strategy
from src.utils.memory import optimize_dtypes


def build_backtest_result(
    strategy: Strategy,
    state: SimulationState,
    sorted_dates: np.ndarray,
    config: BacktestConfig,
) -> BacktestResult:
    """Build BacktestResult from simulation state."""
    trades_df = _build_trades_dataframe(state)

    result = calculate_metrics_vectorized(
        state.equity_curve,
        sorted_dates,
        trades_df,
        config,
        asset_returns=state.asset_returns,
    )
    result.strategy_name = strategy.name

    if len(trades_df) > 0:
        result.trades = _convert_trades(trades_df)

    return result


def _build_trades_dataframe(state: SimulationState) -> pd.DataFrame:
    """Build trades DataFrame from state."""
    if not state.trades_list:
        return pd.DataFrame()

    trades_df = pd.DataFrame(state.trades_list)
    return optimize_dtypes(trades_df)


def _convert_trades(trades_df: pd.DataFrame) -> list[Trade]:
    """Convert trades DataFrame to list of Trade objects."""
    return [
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
            commission_cost=row.get("commission_cost", 0.0),
            slippage_cost=row.get("slippage_cost", 0.0),
            is_stop_loss=row.get("is_stop_loss", False),
            is_take_profit=row.get("is_take_profit", False),
            exit_reason=row.get("exit_reason", "signal"),
        )
        for _, row in trades_df.iterrows()
    ]
