"""Performance metrics calculation for backtest reports.

Re-exports PerformanceMetrics for backward compatibility.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtester.report_pkg.report_metrics_models import PerformanceMetrics
from src.backtester.report_pkg.report_metrics_trade import calculate_trade_statistics
from src.backtester.report_pkg.report_returns import (
    calculate_monthly_returns,
    calculate_yearly_returns,
)
from src.config import ANNUALIZATION_FACTOR, RISK_FREE_RATE

__all__ = [
    "PerformanceMetrics",
    "calculate_metrics",
    "calculate_sortino_ratio",
    "calculate_monthly_returns",
    "calculate_yearly_returns",
    "metrics_to_dataframe",
]


def calculate_sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float = RISK_FREE_RATE,
    annualization: float = ANNUALIZATION_FACTOR,
) -> float:
    """
    Calculate Sortino ratio (downside deviation).

    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (daily)
        annualization: Annualization factor

    Returns:
        Sortino ratio
    """
    excess_returns = returns - risk_free_rate
    downside_returns = np.minimum(excess_returns, 0)
    downside_std = np.std(downside_returns)

    if downside_std <= 0:
        return 0.0

    mean_excess: float = float(np.mean(excess_returns))
    sqrt_annualization: float = float(np.sqrt(annualization))
    downside_std_float: float = float(downside_std)
    result: float = (mean_excess / downside_std_float) * sqrt_annualization
    return result


def calculate_metrics(
    equity_curve: np.ndarray,
    dates: np.ndarray,
    trades_df: pd.DataFrame,
    initial_capital: float = 1.0,
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics.

    Args:
        equity_curve: Array of equity values
        dates: Array of dates
        trades_df: DataFrame with trade records
        initial_capital: Starting capital

    Returns:
        PerformanceMetrics object
    """
    start_date = dates[0]
    end_date = dates[-1]
    total_days = (end_date - start_date).days

    final_equity = equity_curve[-1]
    total_return_pct = (final_equity / initial_capital - 1) * 100

    cagr_pct = _calculate_cagr(total_days, initial_capital, final_equity)
    daily_returns = _calculate_daily_returns(equity_curve)
    volatility_pct = np.std(daily_returns) * np.sqrt(ANNUALIZATION_FACTOR) * 100

    cummax = np.maximum.accumulate(equity_curve)
    drawdown = (cummax - equity_curve) / cummax
    mdd_pct = np.nanmax(drawdown) * 100

    sharpe_ratio = _calculate_sharpe(daily_returns)
    sortino_ratio = calculate_sortino_ratio(daily_returns)
    calmar_ratio = cagr_pct / mdd_pct if mdd_pct > 0 else 0.0

    trade_stats = calculate_trade_statistics(trades_df)

    return PerformanceMetrics(
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        total_return_pct=total_return_pct,
        cagr_pct=cagr_pct,
        mdd_pct=mdd_pct,
        volatility_pct=volatility_pct,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        total_trades=int(trade_stats["total_trades"]),
        winning_trades=int(trade_stats["winning_trades"]),
        losing_trades=int(trade_stats["losing_trades"]),
        win_rate_pct=float(trade_stats["win_rate_pct"]),
        profit_factor=float(trade_stats["profit_factor"]),
        avg_profit_pct=float(trade_stats["avg_profit_pct"]),
        avg_loss_pct=float(trade_stats["avg_loss_pct"]),
        avg_trade_pct=float(trade_stats["avg_trade_pct"]),
        equity_curve=equity_curve,
        drawdown_curve=drawdown * 100,
        dates=dates,
        daily_returns=daily_returns,
    )


def _calculate_cagr(total_days: int, initial: float, final: float) -> float:
    """Calculate CAGR percentage."""
    if total_days <= 0 or initial <= 0:
        return 0.0
    if final <= 0:
        return -100.0
    ratio = final / initial
    if ratio <= 0:
        return -100.0
    with np.errstate(over="ignore"):
        cagr_raw = (np.exp((365.0 / total_days) * np.log(ratio)) - 1) * 100
    return 1e18 if np.isinf(cagr_raw) else float(cagr_raw)


def _calculate_daily_returns(equity_curve: np.ndarray) -> np.ndarray:
    """Calculate daily returns from equity curve."""
    daily_returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.insert(daily_returns, 0, 0)


def _calculate_sharpe(daily_returns: np.ndarray) -> float:
    """Calculate Sharpe ratio."""
    if np.std(daily_returns) > 0:
        return float(
            (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(ANNUALIZATION_FACTOR)
        )
    return 0.0


def metrics_to_dataframe(metrics: PerformanceMetrics) -> pd.DataFrame:
    """Export PerformanceMetrics as DataFrame."""
    m = metrics
    return pd.DataFrame(
        {
            "Metric": [
                "Start Date",
                "End Date",
                "Total Days",
                "Total Return (%)",
                "CAGR (%)",
                "Max Drawdown (%)",
                "Volatility (%)",
                "Sharpe Ratio",
                "Sortino Ratio",
                "Calmar Ratio",
                "Total Trades",
                "Winning Trades",
                "Losing Trades",
                "Win Rate (%)",
                "Profit Factor",
                "Avg Profit (%)",
                "Avg Loss (%)",
                "Avg Trade (%)",
            ],
            "Value": [
                str(m.start_date),
                str(m.end_date),
                m.total_days,
                round(m.total_return_pct, 2),
                round(m.cagr_pct, 2),
                round(m.mdd_pct, 2),
                round(m.volatility_pct, 2),
                round(m.sharpe_ratio, 2),
                round(m.sortino_ratio, 2),
                round(m.calmar_ratio, 2),
                m.total_trades,
                m.winning_trades,
                m.losing_trades,
                round(m.win_rate_pct, 2),
                round(m.profit_factor, 2),
                round(m.avg_profit_pct, 2),
                round(m.avg_loss_pct, 2),
                round(m.avg_trade_pct, 2),
            ],
        }
    )
