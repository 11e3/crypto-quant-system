"""Trade statistics calculation for backtest reports."""

from __future__ import annotations

import pandas as pd


def calculate_trade_statistics(trades_df: pd.DataFrame) -> dict[str, float | int]:
    """
    Calculate trade statistics from trades DataFrame.

    Args:
        trades_df: DataFrame with trade records

    Returns:
        Dictionary with trade statistics
    """
    if len(trades_df) == 0:
        return _empty_trade_stats()

    # Filter closed trades
    if "exit_date" in trades_df.columns:
        closed_trades = trades_df[trades_df["exit_date"].notna()]
    else:
        closed_trades = pd.DataFrame()

    total_trades = len(closed_trades)

    if total_trades == 0:
        return _empty_trade_stats()

    winning = closed_trades[closed_trades["pnl"] > 0]
    losing = closed_trades[closed_trades["pnl"] <= 0]

    winning_trades = len(winning)
    losing_trades = len(losing)
    win_rate_pct = (winning_trades / total_trades) * 100

    # Profit factor
    total_profit = winning["pnl"].sum() if len(winning) > 0 else 0
    total_loss = abs(losing["pnl"].sum()) if len(losing) > 0 else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

    # Average profit/loss
    avg_profit_pct = winning["pnl_pct"].mean() if len(winning) > 0 else 0.0
    avg_loss_pct = losing["pnl_pct"].mean() if len(losing) > 0 else 0.0
    avg_trade_pct = closed_trades["pnl_pct"].mean()

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "avg_profit_pct": avg_profit_pct,
        "avg_loss_pct": avg_loss_pct,
        "avg_trade_pct": avg_trade_pct,
    }


def _empty_trade_stats() -> dict[str, float | int]:
    """Return empty trade statistics."""
    return {
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "win_rate_pct": 0.0,
        "profit_factor": 0.0,
        "avg_profit_pct": 0.0,
        "avg_loss_pct": 0.0,
        "avg_trade_pct": 0.0,
    }
