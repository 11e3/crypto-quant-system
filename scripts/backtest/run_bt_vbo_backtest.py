"""Run VBO backtest using bt library integration.

Demonstrates ecosystem integration between crypto-quant-system and bt library.

Usage:
    python scripts/backtest/run_bt_vbo_backtest.py
    python scripts/backtest/run_bt_vbo_backtest.py --symbols BTC,ETH,XRP
    python scripts/backtest/run_bt_vbo_backtest.py --save-charts
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# bt library imports
from bt.config import settings as bt_settings
from bt.domain.models import BacktestConfig
from bt.domain.types import Amount, Fee, Percentage
from bt.engine.backtest import BacktestEngine
from bt.logging import get_logger, setup_logging
from bt.reporting.metrics import (
    calculate_performance_metrics,
    print_performance_report,
    print_sample_trades,
)
from bt.reporting.visualization import (
    plot_equity_curve,
    plot_yearly_returns,
    plot_market_regime_analysis,
    save_all_charts,
)
from bt.strategies.allocation import create_cash_partition_allocator
from bt.strategies.vbo import get_vbo_strategy

if TYPE_CHECKING:
    from bt.domain.models import PerformanceMetrics

# Default symbols available in crypto-quant-system
DEFAULT_SYMBOLS = ["BTC", "ETH", "XRP", "TRX"]
DATA_DIR = project_root / "data" / "raw"


def load_data_from_cqs(symbol: str, interval: str = "day") -> pd.DataFrame:
    """Load data from crypto-quant-system data directory.

    crypto-quant-system uses format: KRW-{symbol}_{interval}.parquet
    bt library expects: {symbol}.parquet in data/{interval}/ directory

    Args:
        symbol: Trading symbol (e.g., "BTC")
        interval: Time interval (default: "day")

    Returns:
        DataFrame with OHLCV data

    Raises:
        FileNotFoundError: If data file doesn't exist
    """
    # Map to crypto-quant-system file format
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

    # Validate required columns
    required_cols = ["datetime", "open", "high", "low", "close", "volume"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    return df


def run_vbo_backtest(
    symbols: list[str] | None = None,
    interval: str = "day",
    initial_cash: Decimal = Decimal("10000000"),
    fee: Decimal = Decimal("0.0005"),
    slippage: Decimal = Decimal("0.0005"),
    multiplier: int = 2,
    lookback: int = 5,
    save_charts: bool = False,
    output_dir: Path | None = None,
) -> PerformanceMetrics:
    """Run VBO strategy backtest using bt library.

    Args:
        symbols: List of symbols to trade (default: BTC, ETH, XRP, TRX)
        interval: Time interval (default: "day")
        initial_cash: Initial capital in KRW (default: 10,000,000)
        fee: Trading fee (default: 0.05%)
        slippage: Slippage (default: 0.05%)
        multiplier: Multiplier for long-term indicators
        lookback: Lookback period for short-term indicators
        save_charts: Whether to save visualization charts
        output_dir: Directory for saving charts

    Returns:
        PerformanceMetrics with backtest results
    """
    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    if output_dir is None:
        output_dir = project_root / "output" / "bt_backtest"

    logger = get_logger(__name__)

    print("=" * 70)
    print("VBO STRATEGY BACKTEST (bt library integration)")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Symbols:       {', '.join(symbols)}")
    print(f"  Interval:      {interval}")
    print(f"  Initial Cash:  {initial_cash:,.0f} KRW")
    print(f"  Fee:           {float(fee) * 100:.3f}%")
    print(f"  Slippage:      {float(slippage) * 100:.3f}%")
    print(f"  Multiplier:    {multiplier}")
    print(f"  Lookback:      {lookback}")
    print("-" * 70)

    # Create configuration
    config = BacktestConfig(
        initial_cash=Amount(initial_cash),
        fee=Fee(fee),
        slippage=Percentage(slippage),
        multiplier=multiplier,
        lookback=lookback,
        interval=interval,
    )

    # Initialize engine
    engine = BacktestEngine(config)

    # Load data for all symbols
    print("\nLoading market data...")
    loaded_symbols = []
    for symbol in symbols:
        try:
            df = load_data_from_cqs(symbol, interval)
            engine.load_data(symbol, df)
            loaded_symbols.append(symbol)
            print(f"  [OK] {symbol}: {len(df):,} rows ({df['datetime'].min().date()} ~ {df['datetime'].max().date()})")
        except FileNotFoundError as e:
            print(f"  [SKIP] {symbol}: {e}")
        except Exception as e:
            print(f"  [ERROR] {symbol}: {e}")

    if not loaded_symbols:
        print("\n❌ No data loaded. Please run data collection first:")
        print("   python scripts/fetch_data.py --symbols BTC,ETH,XRP,TRX --interval day")
        raise RuntimeError("No data loaded")

    # Get strategy configuration
    strategy = get_vbo_strategy()

    # Create allocation function
    allocation_func = create_cash_partition_allocator(loaded_symbols)

    # Run backtest
    print(f"\nRunning backtest with {len(loaded_symbols)} symbols...")
    engine.run(
        symbols=loaded_symbols,
        buy_conditions=strategy["buy_conditions"],
        sell_conditions=strategy["sell_conditions"],
        buy_price_func=strategy["buy_price_func"],
        sell_price_func=strategy["sell_price_func"],
        allocation_func=allocation_func,
    )

    # Calculate performance metrics
    print("Calculating performance metrics...")
    metrics = calculate_performance_metrics(
        equity_curve=engine.portfolio.equity_curve,
        dates=engine.portfolio.dates,
        trades=engine.portfolio.trades,
        _initial_cash=config.initial_cash,
    )

    # Display results
    print_performance_report(metrics)
    print_sample_trades(metrics.trades, max_trades=10)

    # Save visualizations
    if save_charts:
        print(f"\nSaving charts to {output_dir}...")
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = save_all_charts(
            metrics,
            output_dir=output_dir,
            prefix="vbo_bt",
        )
        for f in saved_files:
            print(f"  - {f}")

    return metrics


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run VBO backtest using bt library integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/backtest/run_bt_vbo_backtest.py
    python scripts/backtest/run_bt_vbo_backtest.py --symbols BTC,ETH
    python scripts/backtest/run_bt_vbo_backtest.py --save-charts
    python scripts/backtest/run_bt_vbo_backtest.py --initial-cash 50000000
        """,
    )

    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated list of symbols (default: BTC,ETH,XRP,TRX)",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="day",
        help="Time interval (default: day)",
    )
    parser.add_argument(
        "--initial-cash",
        type=int,
        default=10_000_000,
        help="Initial capital in KRW (default: 10,000,000)",
    )
    parser.add_argument(
        "--fee",
        type=float,
        default=0.0005,
        help="Trading fee (default: 0.0005 = 0.05%%)",
    )
    parser.add_argument(
        "--slippage",
        type=float,
        default=0.0005,
        help="Slippage (default: 0.0005 = 0.05%%)",
    )
    parser.add_argument(
        "--multiplier",
        type=int,
        default=2,
        help="Multiplier for long-term indicators (default: 2)",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=5,
        help="Lookback period for short-term indicators (default: 5)",
    )
    parser.add_argument(
        "--save-charts",
        action="store_true",
        help="Save visualization charts to output directory",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for charts (default: output/bt_backtest)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level="INFO", log_format="text")

    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]

    # Parse output directory
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)

    # Run backtest
    try:
        run_vbo_backtest(
            symbols=symbols,
            interval=args.interval,
            initial_cash=Decimal(str(args.initial_cash)),
            fee=Decimal(str(args.fee)),
            slippage=Decimal(str(args.slippage)),
            multiplier=args.multiplier,
            lookback=args.lookback,
            save_charts=args.save_charts,
            output_dir=output_dir,
        )
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
