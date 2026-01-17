"""bt library backtest execution service.

Service for running backtests using the external bt library.
Integrates bt library's VBO strategy with crypto-quant-system dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from bt.domain.models import PerformanceMetrics

logger = get_logger(__name__)

__all__ = [
    "BtBacktestResult",
    "run_bt_backtest_service",
    "run_bt_backtest_regime_service",
    "is_bt_available",
    "get_available_bt_symbols",
    "get_default_model_path",
]

# Data directory for crypto-quant-system
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

# Models directory
MODELS_DIR = Path(__file__).resolve().parents[3] / "models"

# Default regime model
DEFAULT_MODEL_NAME = "regime_classifier_xgb_ultra5.joblib"


def get_default_model_path() -> Path:
    """Get the default regime model path."""
    return MODELS_DIR / DEFAULT_MODEL_NAME


@dataclass
class BtBacktestResult:
    """Result container for bt library backtest."""

    # Performance metrics
    total_return: float
    cagr: float
    mdd: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    num_trades: int
    avg_win_pct: float  # Average win rate (percentage)
    avg_loss_pct: float  # Average loss rate (percentage)
    final_equity: float

    # Time series data
    equity_curve: list[float]
    dates: list[datetime]
    yearly_returns: dict[int, float]

    # Trade data
    trades: list[dict]


def is_bt_available() -> bool:
    """Check if bt library is installed and available."""
    try:
        from bt.engine.backtest import BacktestEngine  # noqa: F401

        return True
    except ImportError:
        return False


def get_available_bt_symbols(interval: str = "day") -> list[str]:
    """Get list of symbols available for bt backtest.

    Args:
        interval: Time interval (default: "day")

    Returns:
        List of available symbol names (e.g., ["BTC", "ETH", "XRP"])
    """
    symbols = []
    if DATA_DIR.exists():
        for file in DATA_DIR.glob(f"KRW-*_{interval}.parquet"):
            # Extract symbol from KRW-{symbol}_{interval}.parquet
            symbol = file.stem.replace(f"_{interval}", "").replace("KRW-", "")
            symbols.append(symbol)
    return sorted(symbols)


def _load_data_for_bt(symbol: str, interval: str = "day") -> pd.DataFrame:
    """Load data from crypto-quant-system for bt library.

    Args:
        symbol: Trading symbol (e.g., "BTC")
        interval: Time interval

    Returns:
        DataFrame with OHLCV data

    Raises:
        FileNotFoundError: If data file doesn't exist
    """
    file_path = DATA_DIR / f"KRW-{symbol}_{interval}.parquet"

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    df = pd.read_parquet(file_path)

    # Ensure datetime column
    if "datetime" not in df.columns:
        if "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"])
        elif df.index.name == "datetime" or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df.rename(columns={df.columns[0]: "datetime"}, inplace=True)

    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


def _convert_bt_metrics_to_result(metrics: PerformanceMetrics) -> BtBacktestResult:
    """Convert bt library PerformanceMetrics to BtBacktestResult.

    Args:
        metrics: bt library PerformanceMetrics

    Returns:
        BtBacktestResult
    """
    # Convert trades to dict format and calculate avg win/loss percentages
    trades_list = []
    win_returns: list[float] = []
    loss_returns: list[float] = []

    for trade in metrics.trades:
        return_pct = float(trade.return_pct)
        trades_list.append(
            {
                "symbol": trade.symbol,
                "entry_date": trade.entry_date,
                "exit_date": trade.exit_date,
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "quantity": float(trade.quantity),
                "pnl": float(trade.pnl),
                "return_pct": return_pct,
            }
        )

        # Categorize by win/loss for average calculation
        if return_pct > 0:
            win_returns.append(return_pct)
        elif return_pct < 0:
            loss_returns.append(return_pct)

    # Calculate average win/loss percentages
    avg_win_pct = sum(win_returns) / len(win_returns) if win_returns else 0.0
    avg_loss_pct = sum(loss_returns) / len(loss_returns) if loss_returns else 0.0

    # Convert yearly returns
    yearly_returns_dict = {year: float(ret) for year, ret in metrics.yearly_returns.items()}

    return BtBacktestResult(
        total_return=float(metrics.total_return),
        cagr=float(metrics.cagr),
        mdd=float(metrics.mdd),
        sharpe_ratio=float(metrics.sharpe_ratio),
        sortino_ratio=float(metrics.sortino_ratio),
        win_rate=float(metrics.win_rate),
        profit_factor=float(metrics.profit_factor),
        num_trades=metrics.num_trades,
        avg_win_pct=avg_win_pct,
        avg_loss_pct=avg_loss_pct,
        final_equity=float(metrics.final_equity),
        equity_curve=[float(e) for e in metrics.equity_curve],
        dates=list(metrics.dates),
        yearly_returns=yearly_returns_dict,
        trades=trades_list,
    )


def run_bt_backtest_service(
    symbols: tuple[str, ...],
    interval: str = "day",
    initial_cash: int = 10_000_000,
    fee: float = 0.0005,
    slippage: float = 0.0005,
    multiplier: int = 2,
    lookback: int = 5,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BtBacktestResult | None:
    """Run VBO backtest using bt library.

    Args:
        symbols: Tuple of symbols to trade (tuple for caching)
        interval: Time interval
        initial_cash: Initial capital in KRW
        fee: Trading fee (0.0005 = 0.05%)
        slippage: Slippage (0.0005 = 0.05%)
        multiplier: Multiplier for long-term indicators
        lookback: Lookback period for short-term indicators
        start_date: Backtest start date (inclusive)
        end_date: Backtest end date (inclusive)

    Returns:
        BtBacktestResult or None on failure
    """
    if not is_bt_available():
        logger.error("bt library is not installed")
        return None

    try:
        # Import bt library components
        from bt.framework.facade import BacktestFacade

        symbols_list = list(symbols)

        # Initialize facade
        facade = BacktestFacade()

        # Load data for all symbols into dict
        data: dict[str, pd.DataFrame] = {}
        for symbol in symbols_list:
            try:
                df = _load_data_for_bt(symbol, interval)
                data[symbol] = df
                logger.info(f"Loaded {symbol}: {len(df)} rows")
            except FileNotFoundError:
                logger.warning(f"Data not found for {symbol}")
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")

        if not data:
            logger.error("No data loaded for any symbol")
            return None

        # Filter data by date range (in run_bt_backtest_service)
        if start_date or end_date:
            for symbol in list(data.keys()):
                df = data[symbol]
                if "datetime" in df.columns:
                    if start_date:
                        df = df[df["datetime"].dt.date >= start_date]
                    if end_date:
                        df = df[df["datetime"].dt.date <= end_date]
                    data[symbol] = df
                    logger.info(f"Filtered {symbol}: {len(df)} rows after date filter")

        loaded_symbols = list(data.keys())

        # Run backtest with VBO strategy
        logger.info(f"Running bt backtest with {len(loaded_symbols)} symbols...")
        backtest_config: dict[str, object] = {
            "initial_cash": initial_cash,
            "fee": fee,
            "slippage": slippage,
            "lookback": lookback,
            "multiplier": multiplier,
        }

        # Add date range to config if provided
        if start_date:
            backtest_config["start_date"] = start_date.isoformat()
        if end_date:
            backtest_config["end_date"] = end_date.isoformat()
        results = facade.run_backtest(
            strategy="vbo",
            symbols=loaded_symbols,
            data=data,
            config=backtest_config,
        )

        # Extract metrics from results (key is "performance", not "metrics")
        metrics = results.get("performance")
        if not metrics:
            logger.error("No metrics in backtest results")
            return None

        logger.info(
            f"bt backtest completed: CAGR={float(metrics.cagr):.2f}%, "
            f"MDD={float(metrics.mdd):.2f}%, Trades={metrics.num_trades}"
        )

        return _convert_bt_metrics_to_result(metrics)

    except Exception as e:
        logger.exception(f"bt backtest failed: {e}")
        return None


def run_bt_backtest_regime_service(
    symbols: tuple[str, ...],
    interval: str = "day",
    initial_cash: int = 10_000_000,
    fee: float = 0.0005,
    slippage: float = 0.0005,
    ma_short: int = 5,
    noise_ratio: float = 0.5,
    model_path: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BtBacktestResult | None:
    """Run VBO Regime backtest using bt library.

    Uses ML regime model instead of BTC MA20 for market filter.

    Args:
        symbols: Tuple of symbols to trade (tuple for caching)
        interval: Time interval
        initial_cash: Initial capital in KRW
        fee: Trading fee (0.0005 = 0.05%)
        slippage: Slippage (0.0005 = 0.05%)
        ma_short: Short MA period for individual coins (default: 5)
        noise_ratio: Volatility breakout multiplier (default: 0.5)
        model_path: Path to regime model (.joblib), uses default if None
        start_date: Backtest start date (inclusive)
        end_date: Backtest end date (inclusive)

    Returns:
        BtBacktestResult or None on failure
    """
    if not is_bt_available():
        logger.error("bt library is not installed")
        return None

    # Use default model path if not provided
    if model_path is None:
        model_path = str(get_default_model_path())

    # Verify model exists
    if not Path(model_path).exists():
        logger.error(f"Regime model not found: {model_path}")
        return None

    try:
        # Import bt library components
        from bt.framework.facade import BacktestFacade

        symbols_list = list(symbols)

        # Initialize facade
        facade = BacktestFacade()

        # Load data for all symbols into dict
        data: dict[str, pd.DataFrame] = {}
        for symbol in symbols_list:
            try:
                df = _load_data_for_bt(symbol, interval)
                data[symbol] = df
                logger.info(f"Loaded {symbol}: {len(df)} rows")
            except FileNotFoundError:
                logger.warning(f"Data not found for {symbol}")
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")

        if not data:
            logger.error("No data loaded for any symbol")
            return None

        # Filter data by date range
        if start_date or end_date:
            for symbol in list(data.keys()):
                df = data[symbol]
                if "datetime" in df.columns:
                    if start_date:
                        df = df[df["datetime"].dt.date >= start_date]
                    if end_date:
                        df = df[df["datetime"].dt.date <= end_date]
                    data[symbol] = df
                    logger.info(f"Filtered {symbol}: {len(df)} rows after date filter")

        loaded_symbols = list(data.keys())

        # Run backtest with VBO Regime strategy
        logger.info(f"Running bt regime backtest with {len(loaded_symbols)} symbols...")
        backtest_config: dict[str, object] = {
            "initial_cash": initial_cash,
            "fee": fee,
            "slippage": slippage,
            "ma_short": ma_short,
            "noise_ratio": noise_ratio,
            "model_path": model_path,
            "btc_symbol": "BTC",
        }

        # Add date range to config if provided
        if start_date:
            backtest_config["start_date"] = start_date.isoformat()
        if end_date:
            backtest_config["end_date"] = end_date.isoformat()

        results = facade.run_backtest(
            strategy="vbo_regime",
            symbols=loaded_symbols,
            data=data,
            config=backtest_config,
        )

        # Extract metrics from results
        metrics = results.get("performance")
        if not metrics:
            logger.error("No metrics in backtest results")
            return None

        logger.info(
            f"bt regime backtest completed: CAGR={float(metrics.cagr):.2f}%, "
            f"MDD={float(metrics.mdd):.2f}%, Trades={metrics.num_trades}"
        )

        return _convert_bt_metrics_to_result(metrics)

    except Exception as e:
        logger.exception(f"bt regime backtest failed: {e}")
        return None
