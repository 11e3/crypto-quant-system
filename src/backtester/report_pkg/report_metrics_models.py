"""Performance metrics data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""

    # Period
    start_date: date
    end_date: date
    total_days: int

    # Returns
    total_return_pct: float
    cagr_pct: float

    # Risk
    mdd_pct: float
    volatility_pct: float

    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float

    # Per-trade
    avg_profit_pct: float
    avg_loss_pct: float
    avg_trade_pct: float

    # Equity data
    equity_curve: np.ndarray
    drawdown_curve: np.ndarray
    dates: np.ndarray
    daily_returns: np.ndarray
