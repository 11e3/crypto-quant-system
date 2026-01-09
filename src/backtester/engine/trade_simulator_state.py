"""
Trade simulation state management.

Contains state container and initialization for vectorized backtesting.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SimulationState:
    """State container for trade simulation."""

    cash: float
    position_amounts: np.ndarray
    position_entry_prices: np.ndarray
    position_entry_dates: np.ndarray
    equity_curve: np.ndarray
    trades_list: list[dict[str, Any]]
    asset_returns: dict[str, list[float]]
    previous_closes: np.ndarray


def initialize_simulation_state(
    initial_capital: float,
    n_tickers: int,
    n_dates: int,
    tickers: list[str],
) -> SimulationState:
    """
    Initialize simulation state.

    Args:
        initial_capital: Starting capital
        n_tickers: Number of tickers
        n_dates: Number of trading dates
        tickers: List of ticker symbols

    Returns:
        Initialized SimulationState
    """
    from src.utils.memory import get_float_dtype

    float_dtype = get_float_dtype()

    return SimulationState(
        cash=initial_capital,
        position_amounts=np.zeros(n_tickers, dtype=float_dtype),
        position_entry_prices=np.zeros(n_tickers, dtype=float_dtype),
        position_entry_dates=np.full(n_tickers, -1, dtype=np.int32),
        equity_curve=np.zeros(n_dates, dtype=float_dtype),
        trades_list=[],
        asset_returns={ticker: [] for ticker in tickers},
        previous_closes=np.full(n_tickers, np.nan, dtype=float_dtype),
    )
