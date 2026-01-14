"""
Simple backtest implementation for bootstrap analysis.
"""

import numpy as np
import pandas as pd

from src.backtester.models import BacktestResult
from src.strategies.base import Strategy
from src.utils.logger import get_logger

__all__ = ["simple_backtest_vectorized"]

logger = get_logger(__name__)


def simple_backtest_vectorized(
    data: pd.DataFrame,
    strategy: Strategy,
    initial_capital: float,
) -> BacktestResult:
    """
    Simple vectorized backtest for bootstrap sampling.

    Args:
        data: OHLCV DataFrame
        strategy: Strategy to backtest
        initial_capital: Initial capital

    Returns:
        BacktestResult with basic metrics
    """
    try:
        df = data.copy()
        df = strategy.calculate_indicators(df)
        df = strategy.generate_signals(df)

        if "signal" not in df.columns:
            result = BacktestResult()
            result.total_return = 0.0
            result.sharpe_ratio = 0.0
            result.mdd = 0.0
            result.total_trades = 0
            result.winning_trades = 0
            result.win_rate = 0.0
            return result

        position = 0
        entry_price = 0.0
        equity = [initial_capital]

        for _, row in df.iterrows():
            signal = row.get("signal", 0)
            close = row.get("close", 0)

            if signal != 0 and position == 0:
                entry_price = close
                position = signal
            elif signal * position < 0:
                if position != 0:
                    pnl = (close - entry_price) * position / entry_price if entry_price > 0 else 0.0
                    equity.append(equity[-1] * (1 + pnl))
                    position = signal
                    entry_price = close if signal != 0 else 0.0
                else:
                    position = 0

            if position == 0 and len(equity) > 1:
                equity.append(equity[-1])

        if position != 0 and len(df) > 0:
            last_close = df.iloc[-1].get("close", entry_price)
            pnl = (last_close - entry_price) * position / entry_price if entry_price > 0 else 0.0
            equity.append(equity[-1] * (1 + pnl))

        result = BacktestResult()
        result.total_return = (equity[-1] - initial_capital) / initial_capital if equity else 0.0

        if len(equity) > 1:
            equity_prev = np.array(equity[:-1])
            with np.errstate(divide="ignore", invalid="ignore"):
                returns = np.diff(equity) / np.where(equity_prev == 0, np.nan, equity_prev)
            result.sharpe_ratio = (
                float(np.nanmean(returns) / (np.nanstd(returns) + 1e-8) * np.sqrt(252))
                if np.nanstd(returns) > 0
                else 0.0
            )
            cummax = np.maximum.accumulate(equity)
            with np.errstate(divide="ignore", invalid="ignore"):
                dd = (np.array(equity) - cummax) / np.where(cummax == 0, np.nan, cummax)
            result.mdd = float(np.nanmin(dd)) if len(dd) > 0 else 0.0
        else:
            result.sharpe_ratio = 0.0
            result.mdd = 0.0

        return result
    except Exception as e:
        logger.error(f"Bootstrap backtest error: {e}")
        result = BacktestResult()
        result.total_return = 0.0
        result.sharpe_ratio = 0.0
        result.mdd = 0.0
        return result
