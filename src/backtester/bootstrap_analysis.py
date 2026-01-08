"""
Bootstrap Analysis: Phase 3 Statistical Reliability

Resamples the dataset using block bootstrap to estimate confidence intervals
for strategy performance metrics (return, Sharpe) and risk (MDD).
"""

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtester.engine import BacktestConfig, BacktestResult, run_backtest
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BootstrapResult:
    returns: list[float]
    sharpes: list[float]
    mdds: list[float]
    mean_return: float = 0.0
    ci_return_95: tuple[float, float] = (0.0, 0.0)
    mean_sharpe: float = 0.0
    ci_sharpe_95: tuple[float, float] = (0.0, 0.0)
    mean_mdd: float = 0.0
    ci_mdd_95: tuple[float, float] = (0.0, 0.0)


class BootstrapAnalyzer:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy_factory: Callable[[dict[str, Any]], Strategy] | Callable[[], Strategy],
        backtest_config: BacktestConfig | None = None,
        ticker: str = "KRW-BTC",
        interval: str = "day",
    ):
        self.data = data
        self.strategy_factory = strategy_factory
        self.backtest_config = backtest_config or BacktestConfig()
        self.initial_capital = self.backtest_config.initial_capital
        self.ticker = ticker
        self.interval = interval

    def _simple_backtest(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        """Use engine-based backtest when possible for realistic metrics."""
        try:
            # Save resampled data to a temporary parquet file
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / f"{self.ticker}_{self.interval}.parquet"
                df_to_save = data.copy()
                if df_to_save.index.name is None:
                    df_to_save.index.name = "datetime"
                df_to_save.to_parquet(tmp_path)

                # Run backtest using official engine
                result = run_backtest(
                    strategy=strategy,
                    tickers=[self.ticker],
                    interval=self.interval,
                    data_dir=Path(tmpdir),
                    config=self.backtest_config,
                )
                return result
        except Exception as e:
            logger.debug(f"Engine backtest failed, fallback to simple: {e}")
            # Fallback to simple vectorized backtest
            return self._fallback_simple_backtest(data, strategy)

    def _fallback_simple_backtest(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        from src.backtester.engine import BacktestResult

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
            entry_price = 0
            equity = [self.initial_capital]
            for _, row in df.iterrows():
                signal = row.get("signal", 0)
                close = row.get("close", 0)
                if signal != 0 and position == 0:
                    entry_price = close
                    position = signal
                elif signal * position < 0:
                    if position != 0:
                        pnl = (close - entry_price) * position / entry_price
                        equity.append(equity[-1] * (1 + pnl))
                        position = signal
                        entry_price = close if signal != 0 else 0
                    else:
                        position = 0
                if position == 0 and len(equity) > 1:
                    equity.append(equity[-1])
            if position != 0 and len(df) > 0:
                last_close = df.iloc[-1].get("close", entry_price)
                pnl = (last_close - entry_price) * position / entry_price
                equity.append(equity[-1] * (1 + pnl))
            result = BacktestResult()
            result.total_return = (
                (equity[-1] - self.initial_capital) / self.initial_capital if equity else 0.0
            )
            if len(equity) > 1:
                returns = np.diff(equity) / equity[:-1]
                result.sharpe_ratio = (
                    np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
                    if np.std(returns) > 0
                    else 0.0
                )
                cummax = np.maximum.accumulate(equity)
                dd = (np.array(equity) - cummax) / cummax
                result.mdd = float(np.min(dd)) if len(dd) > 0 else 0.0
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

    def _block_bootstrap(self, returns: np.ndarray, n: int, block_size: int) -> np.ndarray:
        blocks = []
        i = 0
        while i < n:
            start = np.random.randint(0, max(1, n - block_size))
            block = returns[start : start + block_size]
            blocks.append(block)
            i += block_size
        return np.concatenate(blocks)[:n]

    def _resample_data(self, data: pd.DataFrame, block_size: int) -> pd.DataFrame:
        """
        Resample data using date-based block bootstrap (preserves temporal structure).

        Instead of resampling returns and reconstructing prices (which breaks trend),
        we resample date blocks directly to maintain OHLCV relationships.
        """
        df = data.copy()
        n = len(df)

        # Randomly select starting indices for blocks
        resampled_indices: list[int] = []
        while len(resampled_indices) < n:
            start_idx = np.random.randint(0, max(1, n - block_size + 1))
            block_indices = list(range(start_idx, min(start_idx + block_size, n)))
            resampled_indices.extend(block_indices)

        # Trim to original length
        resampled_indices = resampled_indices[:n]

        # Select rows by index (preserves OHLCV structure)
        resampled_df = df.iloc[resampled_indices].copy()

        # Reset index to maintain continuous datetime (for indicator calculations)
        resampled_df.index = pd.date_range(
            start=df.index[0],
            periods=len(resampled_df),
            freq=df.index.freq or pd.infer_freq(df.index) or "D",
        )

        return resampled_df

    def analyze(self, n_samples: int = 300, block_size: int = 30) -> BootstrapResult:
        rets: list[float] = []
        sharps: list[float] = []
        mdds: list[float] = []

        for i in range(n_samples):
            try:
                d = self._resample_data(self.data, block_size)
                try:
                    strategy = self.strategy_factory()  # type: ignore[call-arg]
                except TypeError:
                    strategy = self.strategy_factory()  # type: ignore[call-arg]
                r = self._simple_backtest(d, strategy)

                # Filter extreme outliers (likely due to resampling edge cases)
                # Keep returns within reasonable range for crypto: -100% to +100000% (1000x)
                total_ret = r.total_return
                sharpe = getattr(r, "sharpe_ratio", 0.0)
                mdd = getattr(r, "mdd", 0.0)

                if -1.0 <= total_ret <= 1000.0 and -10.0 <= sharpe <= 10.0:
                    rets.append(total_ret)
                    sharps.append(sharpe)
                    mdds.append(mdd)
                else:
                    logger.debug(
                        f"Filtered outlier sample {i}: return={total_ret:.2%}, sharpe={sharpe:.2f}"
                    )

            except Exception as e:
                logger.debug(f"Bootstrap sample {i} failed: {e}")
                continue

        if not rets:
            logger.warning("No valid bootstrap samples generated")
            return BootstrapResult(returns=[], sharpes=[], mdds=[])

        # Log filtering statistics
        filtered_pct = (1 - len(rets) / n_samples) * 100
        logger.info(
            f"Bootstrap: {len(rets)}/{n_samples} valid samples ({filtered_pct:.1f}% filtered)"
        )

        arr = np.array(rets)
        arr_s = np.array(sharps)
        arr_m = np.array(mdds)

        def ci95(a: np.ndarray) -> tuple[float, float]:
            return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))

        return BootstrapResult(
            returns=rets,
            sharpes=sharps,
            mdds=mdds,
            mean_return=float(np.mean(arr)),
            ci_return_95=ci95(arr),
            mean_sharpe=float(np.mean(arr_s)),
            ci_sharpe_95=ci95(arr_s),
            mean_mdd=float(np.mean(arr_m)),
            ci_mdd_95=ci95(arr_m),
        )
