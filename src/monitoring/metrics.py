from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass
class PerformanceMetrics:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    years: float
    n_trades: int
    win_rate: float
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    whipsaw_rate: float
    total_commission: float = 0.0
    total_slippage: float = 0.0
    avg_commission_per_trade: float = 0.0
    avg_slippage_per_trade: float = 0.0


def _parse_dates(
    df: pd.DataFrame, entry_col: str = "entry_date", exit_col: str = "exit_date"
) -> pd.DataFrame:
    df = df.copy()
    df[entry_col] = pd.to_datetime(df[entry_col], errors="coerce")
    if exit_col in df.columns:
        df[exit_col] = pd.to_datetime(df[exit_col], errors="coerce")
    return df


def _trade_returns(df: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    df = df.copy()
    # Use closed trades only (has exit_date)
    if "exit_date" in df.columns:
        df = df[~df["exit_date"].isna()].copy()
    # Prefer percentage column if available
    if "pnl_pct" in df.columns:
        # Expect percent values (e.g., 12.3 means 12.3%)
        rets = df["pnl_pct"].astype(float) / 100.0
    elif "pnl" in df.columns:
        # Fallback: treat pnl as fractional return (best effort)
        rets = df["pnl"].astype(float)
    else:
        raise ValueError("Input trades must contain either 'pnl_pct' or 'pnl' column")
    # Sanitize inf/nan
    rets = rets.replace([math.inf, -math.inf], pd.NA).fillna(0.0)
    return rets, df


def _compound_equity(returns: pd.Series) -> pd.Series:
    equity = (1.0 + returns).cumprod()
    return equity


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min() if len(dd) else 0.0)


def _annualize_sharpe(returns: pd.Series, years: float) -> float:
    if len(returns) < 2 or years <= 0:
        return 0.0
    # Per-trade Sharpe annualized by trades per year (proxy)
    mean = returns.mean()
    std = returns.std(ddof=1)
    if std == 0 or pd.isna(std):
        return 0.0
    trades_per_year = len(returns) / years
    return float((mean / std) * math.sqrt(max(trades_per_year, 1e-9)))


def compute_performance_from_trades(trades: pd.DataFrame) -> PerformanceMetrics:
    trades = _parse_dates(trades)
    rets, closed = _trade_returns(trades)
    if closed.empty:
        raise ValueError("No closed trades found to compute performance metrics")

    # Time span
    start_date = pd.to_datetime(closed["entry_date"].min())
    end_date = pd.to_datetime(closed["exit_date"].max())
    years = max((end_date - start_date).days / 365.25, 1e-9)

    # Equity and MDD
    equity = _compound_equity(rets.reset_index(drop=True))
    mdd = _max_drawdown(equity)

    # Aggregates
    n_trades = int(len(rets))
    win_rate = float((rets > 0).mean())
    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float((equity.iloc[-1]) ** (1.0 / years) - 1.0) if years > 0 else 0.0
    sharpe = _annualize_sharpe(rets, years)

    # Whipsaw rate if available
    whipsaw_rate = float(
        closed.get("is_whipsaw", pd.Series([False] * len(closed))).astype(bool).mean()
    )

    # Cost breakdown if available
    total_commission = float(closed.get("commission_cost", pd.Series([0.0] * len(closed))).sum())
    total_slippage = float(closed.get("slippage_cost", pd.Series([0.0] * len(closed))).sum())
    avg_commission = total_commission / n_trades if n_trades > 0 else 0.0
    avg_slippage = total_slippage / n_trades if n_trades > 0 else 0.0

    return PerformanceMetrics(
        start_date=start_date,
        end_date=end_date,
        years=years,
        n_trades=n_trades,
        win_rate=win_rate,
        total_return=total_return,
        cagr=cagr,
        sharpe=sharpe,
        max_drawdown=mdd,
        whipsaw_rate=whipsaw_rate,
        total_commission=total_commission,
        total_slippage=total_slippage,
        avg_commission_per_trade=avg_commission,
        avg_slippage_per_trade=avg_slippage,
    )


def to_dict(metrics: PerformanceMetrics) -> dict[str, float | str | int]:
    return {
        "start_date": str(metrics.start_date.date()),
        "end_date": str(metrics.end_date.date()),
        "years": round(metrics.years, 4),
        "n_trades": metrics.n_trades,
        "win_rate": round(metrics.win_rate, 4),
        "total_return": round(metrics.total_return, 6),
        "cagr": round(metrics.cagr, 6),
        "sharpe": round(metrics.sharpe, 4),
        "max_drawdown": round(metrics.max_drawdown, 6),
        "whipsaw_rate": round(metrics.whipsaw_rate, 4),
        "total_commission": round(metrics.total_commission, 2),
        "total_slippage": round(metrics.total_slippage, 2),
        "avg_commission_per_trade": round(metrics.avg_commission_per_trade, 4),
        "avg_slippage_per_trade": round(metrics.avg_slippage_per_trade, 4),
    }
