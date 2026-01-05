"""
Vectorized backtesting engine for trading strategies.

Uses pandas/numpy for high-performance backtesting with support for:
- Multiple assets with portfolio management
- Slotted position management
- Transaction costs and slippage
- Detailed performance metrics
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import (
    ANNUALIZATION_FACTOR,
    DEFAULT_FEE_RATE,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_MAX_SLOTS,
    DEFAULT_SLIPPAGE_RATE,
    RAW_DATA_DIR,
)
from src.data.cache import get_cache
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    fee_rate: float = DEFAULT_FEE_RATE
    slippage_rate: float = DEFAULT_SLIPPAGE_RATE
    max_slots: int = DEFAULT_MAX_SLOTS
    position_sizing: str = "equal"  # "equal" or "custom"
    use_cache: bool = True  # Cache indicator calculations


@dataclass
class Trade:
    """Record of a single trade."""

    ticker: str
    entry_date: date
    entry_price: float
    exit_date: date | None = None
    exit_price: float | None = None
    amount: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    is_whipsaw: bool = False

    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self.exit_date is not None


@dataclass
class BacktestResult:
    """Results from backtesting."""

    # Performance metrics
    total_return: float = 0.0
    cagr: float = 0.0
    mdd: float = 0.0
    calmar_ratio: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_trade_return: float = 0.0

    # Time series data
    equity_curve: np.ndarray = field(default_factory=lambda: np.array([]))
    dates: np.ndarray = field(default_factory=lambda: np.array([]))
    trades: list[Trade] = field(default_factory=list)

    # Additional info
    config: BacktestConfig | None = None
    strategy_name: str = ""

    def summary(self) -> str:
        """Generate summary string."""
        final_equity = self.equity_curve[-1] if len(self.equity_curve) > 0 else 0
        return (
            f"\n{'=' * 50}\n"
            f"Strategy: {self.strategy_name}\n"
            f"{'=' * 50}\n"
            f"CAGR: {self.cagr:.2f}%\n"
            f"MDD: {self.mdd:.2f}%\n"
            f"Calmar Ratio: {self.calmar_ratio:.2f}\n"
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"Win Rate: {self.win_rate:.2f}%\n"
            f"Total Trades: {self.total_trades}\n"
            f"Final Equity: {final_equity:.4f}\n"
            f"{'=' * 50}"
        )


class VectorizedBacktestEngine:
    """
    Vectorized backtesting engine using pandas/numpy.

    Pre-computes all signals and uses array operations for simulation.
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        """
        Initialize backtest engine.

        Args:
            config: Backtesting configuration
        """
        self.config = config or BacktestConfig()

    def load_data(self, filepath: Path) -> pd.DataFrame:
        """
        Load OHLCV data from parquet file.

        Args:
            filepath: Path to parquet file

        Returns:
            DataFrame with OHLCV data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is corrupted or invalid
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        try:
            df = pd.read_parquet(filepath)
            df.index = pd.to_datetime(df.index)
            df.columns = df.columns.str.lower()
            return df
        except Exception as e:
            raise ValueError(f"Error loading data from {filepath}: {e}") from e

    def _add_price_columns(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Add entry/exit price columns with slippage.

        Args:
            df: DataFrame with signals

        Returns:
            DataFrame with price columns added
        """
        df = df.copy()

        # Whipsaw: entry occurs but close < sma on same bar
        df["is_whipsaw"] = df["entry_signal"] & df["exit_signal"]

        # Entry price (target with slippage)
        df["entry_price"] = df["target"] * (1 + self.config.slippage_rate)

        # Exit price (close with slippage)
        df["exit_price"] = df["close"] * (1 - self.config.slippage_rate)

        return df

    def _calculate_metrics_vectorized(
        self,
        equity_curve: np.ndarray,
        dates: np.ndarray,
        trades_df: pd.DataFrame,
    ) -> BacktestResult:
        """Calculate performance metrics using vectorized operations."""
        result = BacktestResult(
            equity_curve=equity_curve,
            dates=dates,
            config=self.config,
        )

        if len(equity_curve) < 2:
            return result

        initial = self.config.initial_capital
        final = equity_curve[-1]

        # Total return
        result.total_return = (final / initial - 1) * 100

        # CAGR
        total_days = (dates[-1] - dates[0]).days
        if total_days > 0 and initial > 0 and final > 0:
            result.cagr = ((final / initial) ** (365.0 / total_days) - 1) * 100

        # MDD (vectorized)
        cummax = np.maximum.accumulate(equity_curve)
        drawdown = (cummax - equity_curve) / cummax
        result.mdd = np.nanmax(drawdown) * 100

        # Calmar Ratio
        result.calmar_ratio = result.cagr / result.mdd if result.mdd > 0 else 0.0

        # Sharpe Ratio (vectorized)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        if len(returns) > 0 and np.std(returns) > 0:
            result.sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(
                ANNUALIZATION_FACTOR
            )

        # Trade statistics
        if len(trades_df) > 0:
            closed = trades_df[trades_df["exit_date"].notna()]
            result.total_trades = len(closed)

            if len(closed) > 0:
                result.winning_trades = (closed["pnl"] > 0).sum()
                result.losing_trades = (closed["pnl"] <= 0).sum()
                result.win_rate = (result.winning_trades / len(closed)) * 100
                result.avg_trade_return = closed["pnl_pct"].mean()

                total_profit = closed.loc[closed["pnl"] > 0, "pnl"].sum()
                total_loss = abs(closed.loc[closed["pnl"] <= 0, "pnl"].sum())
                result.profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

        return result

    def _get_cache_params(self, strategy: Strategy) -> dict[str, Any]:
        """Extract cache parameters from strategy."""
        params: dict[str, Any] = {"strategy_name": strategy.name}

        # Extract VBO-specific parameters if available
        for attr in ["sma_period", "trend_sma_period", "short_noise_period", "long_noise_period"]:
            if hasattr(strategy, attr):
                params[attr] = getattr(strategy, attr)

        # Include entry/exit conditions in cache key
        if hasattr(strategy, "entry_conditions"):
            params["entry_conditions"] = [c.name for c in strategy.entry_conditions.conditions]
        if hasattr(strategy, "exit_conditions"):
            params["exit_conditions"] = [c.name for c in strategy.exit_conditions.conditions]

        return params

    def run(
        self,
        strategy: Strategy,
        data_files: dict[str, Path],
    ) -> BacktestResult:
        """
        Run vectorized backtest for a strategy on multiple assets.

        Args:
            strategy: Trading strategy to backtest
            data_files: Dictionary mapping ticker to data file path

        Returns:
            BacktestResult with performance metrics
        """
        # Get cache parameters
        cache_params = self._get_cache_params(strategy)
        cache = get_cache() if self.config.use_cache else None

        # Load and prepare data for all tickers
        ticker_data: dict[str, pd.DataFrame] = {}
        all_dates: set = set()

        for ticker, filepath in data_files.items():
            try:
                # Extract interval from filename (e.g., KRW-BTC_day.parquet -> day)
                interval = filepath.stem.split("_")[1] if "_" in filepath.stem else "unknown"
                raw_mtime = filepath.stat().st_mtime if filepath.exists() else None

                # Try to load from cache
                cached_df = None
                if cache is not None:
                    cached_df = cache.get(ticker, interval, cache_params, raw_mtime)

                if cached_df is not None:
                    # Use cached data (already has indicators and signals)
                    df = cached_df
                    logger.debug(f"Loaded {ticker} from cache")
                else:
                    # Calculate indicators and signals
                    df = self.load_data(filepath)
                    df = strategy.calculate_indicators(df)
                    df = strategy.generate_signals(df)

                    # Save to cache
                    if cache is not None:
                        cache.set(ticker, interval, cache_params, df, raw_mtime)
                        logger.debug(f"Saved {ticker} to cache")

                df = self._add_price_columns(df)
                df["ticker"] = ticker
                ticker_data[ticker] = df
                # Only add dates where indicators are valid (matching legacy: only dates in processed_data)
                # Legacy skips first 10 days per ticker, so only dates with valid indicators exist
                valid_mask = df["target"].notna() & df["sma"].notna() & df["close"].notna()
                valid_dates = df.index[valid_mask].date
                all_dates.update(valid_dates)
            except Exception as e:
                logger.error(f"Error processing {ticker} from {filepath}: {e}", exc_info=True)
                continue

        # Create unified timeline
        sorted_dates = np.array(sorted(all_dates))
        n_dates = len(sorted_dates)

        if n_dates == 0:
            logger.warning("No data available for backtesting")
            return BacktestResult()

        # Pre-build lookup arrays for each ticker
        # Shape: (n_tickers, n_dates) for each attribute
        tickers = list(ticker_data.keys())
        n_tickers = len(tickers)

        # Initialize arrays
        opens = np.full((n_tickers, n_dates), np.nan)
        highs = np.full((n_tickers, n_dates), np.nan)
        closes = np.full((n_tickers, n_dates), np.nan)
        targets = np.full((n_tickers, n_dates), np.nan)
        smas = np.full((n_tickers, n_dates), np.nan)
        entry_signals = np.zeros((n_tickers, n_dates), dtype=bool)
        exit_signals = np.zeros((n_tickers, n_dates), dtype=bool)
        whipsaws = np.zeros((n_tickers, n_dates), dtype=bool)
        entry_prices = np.full((n_tickers, n_dates), np.nan)
        exit_prices = np.full((n_tickers, n_dates), np.nan)
        short_noises = np.full((n_tickers, n_dates), np.nan)

        # Date to index mapping (using dictionary for O(1) lookup)
        date_to_idx = {d: i for i, d in enumerate(sorted_dates)}

        # Fill arrays using vectorized operations
        for t_idx, ticker in enumerate(tickers):
            df = ticker_data[ticker]

            # Get date indices for this ticker's data
            df_dates = pd.Series(df.index.date)
            df_idx = df_dates.map(date_to_idx)
            valid_mask = df_idx.notna()
            idx = df_idx[valid_mask].astype(int).values

            opens[t_idx, idx] = df.loc[valid_mask.values, "open"].values
            highs[t_idx, idx] = df.loc[valid_mask.values, "high"].values
            closes[t_idx, idx] = df.loc[valid_mask.values, "close"].values
            targets[t_idx, idx] = df.loc[valid_mask.values, "target"].values
            smas[t_idx, idx] = df.loc[valid_mask.values, "sma"].values
            entry_signals[t_idx, idx] = df.loc[valid_mask.values, "entry_signal"].values
            exit_signals[t_idx, idx] = df.loc[valid_mask.values, "exit_signal"].values
            whipsaws[t_idx, idx] = df.loc[valid_mask.values, "is_whipsaw"].values
            entry_prices[t_idx, idx] = df.loc[valid_mask.values, "entry_price"].values
            exit_prices[t_idx, idx] = df.loc[valid_mask.values, "exit_price"].values
            if "short_noise" in df.columns:
                short_noises[t_idx, idx] = df.loc[valid_mask.values, "short_noise"].values

        # Filter dates: Skip initial days where indicators are not available (matching legacy/bt.py)
        # Legacy skips first max(noise_period, trend_sma_period, long_noise_period) = 10 days per ticker
        # Then only processes dates that exist in processed_data (which excludes first 10 days)
        # So we need to filter to dates where at least one ticker has valid indicators
        # AND only process dates that would be in legacy's sorted_dates

        # Find dates where at least one ticker has valid indicators (non-NaN target, sma, etc.)
        # This matches legacy behavior where processed_data only contains dates after skip period
        valid_date_mask = np.zeros(n_dates, dtype=bool)
        for d_idx in range(n_dates):
            # Check if at least one ticker has valid indicators for this date
            # Legacy only includes dates in processed_data, which excludes first 10 days per ticker
            has_valid_target = ~np.isnan(targets[:, d_idx])
            has_valid_sma = ~np.isnan(smas[:, d_idx])
            has_valid_data = ~np.isnan(closes[:, d_idx])

            # Date is valid if at least one ticker has all required indicators
            # This matches legacy: dates only exist in market_data if they're in processed_data
            if np.any(has_valid_target & has_valid_sma & has_valid_data):
                valid_date_mask[d_idx] = True

        # Filter to only valid dates (matching legacy: only dates in processed_data)
        valid_indices = np.where(valid_date_mask)[0]
        if len(valid_indices) > 0:
            first_valid_idx = valid_indices[0]
            last_valid_idx = valid_indices[-1] + 1

            logger.debug(
                f"Filtering dates: keeping {len(valid_indices)} valid dates (matching legacy/bt.py)"
            )
            sorted_dates = sorted_dates[first_valid_idx:last_valid_idx]
            n_dates = len(sorted_dates)

            # Filter all arrays to valid date range
            opens = opens[:, first_valid_idx:last_valid_idx]
            highs = highs[:, first_valid_idx:last_valid_idx]
            closes = closes[:, first_valid_idx:last_valid_idx]
            targets = targets[:, first_valid_idx:last_valid_idx]
            smas = smas[:, first_valid_idx:last_valid_idx]
            entry_signals = entry_signals[:, first_valid_idx:last_valid_idx]
            exit_signals = exit_signals[:, first_valid_idx:last_valid_idx]
            whipsaws = whipsaws[:, first_valid_idx:last_valid_idx]
            entry_prices = entry_prices[:, first_valid_idx:last_valid_idx]
            exit_prices = exit_prices[:, first_valid_idx:last_valid_idx]
            short_noises = short_noises[:, first_valid_idx:last_valid_idx]

        # Simulation using numpy arrays
        cash = self.config.initial_capital
        max_slots = self.config.max_slots
        fee_rate = self.config.fee_rate

        # Position tracking: -1 means no position
        position_amounts = np.zeros(n_tickers)
        position_entry_prices = np.zeros(n_tickers)
        position_entry_dates = np.full(n_tickers, -1, dtype=int)

        equity_curve = np.zeros(n_dates)
        trades_list: list[dict] = []

        for d_idx in range(n_dates):
            current_date = sorted_dates[d_idx]

            # Get valid data mask for this date
            valid_data = ~np.isnan(closes[:, d_idx])

            # ---- PROCESS EXITS ----
            in_position = position_amounts > 0
            should_exit = exit_signals[:, d_idx] & in_position & valid_data

            if np.any(should_exit):
                exit_idx = np.where(should_exit)[0]
                for t_idx in exit_idx:
                    # Execute exit
                    exit_price = exit_prices[t_idx, d_idx]
                    amount = position_amounts[t_idx]
                    revenue = amount * exit_price * (1 - fee_rate)
                    cash += revenue

                    # Record trade
                    entry_price = position_entry_prices[t_idx]
                    pnl = revenue - (amount * entry_price)
                    pnl_pct = (exit_price / entry_price - 1) * 100

                    trades_list.append(
                        {
                            "ticker": tickers[t_idx],
                            "entry_date": sorted_dates[position_entry_dates[t_idx]],
                            "entry_price": entry_price,
                            "exit_date": current_date,
                            "exit_price": exit_price,
                            "amount": amount,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "is_whipsaw": False,
                        }
                    )

                    # Clear position
                    position_amounts[t_idx] = 0
                    position_entry_prices[t_idx] = 0
                    position_entry_dates[t_idx] = -1

            # ---- PROCESS ENTRIES ----
            not_in_position = position_amounts == 0
            can_enter = entry_signals[:, d_idx] & not_in_position & valid_data

            if np.any(can_enter):
                # Sort by noise (prefer lower noise)
                candidate_idx = np.where(can_enter)[0]
                noise_values = short_noises[candidate_idx, d_idx]
                sorted_order = np.argsort(noise_values)
                candidate_idx = candidate_idx[sorted_order]

                for t_idx in candidate_idx:
                    # Recalculate available_slots each iteration (matching legacy/bt.py)
                    current_positions = np.sum(position_amounts > 0)
                    available_slots = max_slots - current_positions

                    if (
                        available_slots <= 0
                    ):  # pragma: no cover (difficult to test - requires exact max_slots reached during loop)
                        break

                    targets[t_idx, d_idx]
                    sma_price = smas[t_idx, d_idx]
                    close_price = closes[t_idx, d_idx]
                    buy_price = entry_prices[t_idx, d_idx]

                    # Divide cash equally among available slots (matching legacy/bt.py)
                    invest_amount = cash / available_slots

                    # Check whipsaw: entry condition met but close < sma on same day
                    # (matching legacy/bt.py logic: if row["close"] < row["sma"])
                    is_whipsaw = close_price < sma_price

                    if is_whipsaw:
                        # Whipsaw: buy and sell same day
                        sell_price = exit_prices[t_idx, d_idx]
                        amount = (invest_amount / buy_price) * (1 - fee_rate)
                        return_money = amount * sell_price * (1 - fee_rate)
                        cash = cash - invest_amount + return_money

                        pnl = return_money - invest_amount
                        pnl_pct = (sell_price / buy_price - 1) * 100

                        trades_list.append(
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
                            }
                        )
                    else:
                        # Normal entry
                        amount = (invest_amount / buy_price) * (1 - fee_rate)

                        position_amounts[t_idx] = amount
                        position_entry_prices[t_idx] = buy_price
                        position_entry_dates[t_idx] = d_idx
                        cash -= invest_amount

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
                        # Note: available_slots is recalculated each iteration, no need to decrement

            # ---- CALCULATE DAILY EQUITY ----
            positions_value = np.nansum(position_amounts * closes[:, d_idx])
            equity_curve[d_idx] = cash + positions_value

        # Convert trades to DataFrame for vectorized metrics
        trades_df = pd.DataFrame(trades_list) if trades_list else pd.DataFrame()

        # Calculate metrics
        result = self._calculate_metrics_vectorized(equity_curve, sorted_dates, trades_df)
        result.strategy_name = strategy.name

        # Convert trades_df to Trade objects for compatibility
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


# Alias for backward compatibility
BacktestEngine = VectorizedBacktestEngine


def run_backtest(
    strategy: Strategy,
    tickers: list[str],
    interval: str = "day",
    data_dir: Path | None = None,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """
    Convenience function to run backtest.

    Args:
        strategy: Trading strategy
        tickers: List of tickers (e.g., ["KRW-BTC", "KRW-ETH"])
        interval: Data interval (e.g., "day", "minute240")
        data_dir: Data directory (defaults to data/raw/)
        config: Backtest configuration

    Returns:
        BacktestResult

    Raises:
        FileNotFoundError: If no data files are found
    """
    data_dir = data_dir or RAW_DATA_DIR

    # Build data file paths
    data_files = {ticker: data_dir / f"{ticker}_{interval}.parquet" for ticker in tickers}

    # Filter to existing files
    data_files = {k: v for k, v in data_files.items() if v.exists()}

    if not data_files:
        raise FileNotFoundError(
            f"No data files found in {data_dir} for tickers: {tickers}, interval: {interval}"
        )

    engine = VectorizedBacktestEngine(config)
    return engine.run(strategy, data_files)
