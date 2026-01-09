"""
Test ORB strategy with EventDrivenBacktestEngine.

Tests the new event-driven engine implementation.
"""

from datetime import date

from src.backtester.engine import EventDrivenBacktestEngine
from src.backtester.models import BacktestConfig
from src.config import RAW_DATA_DIR
from src.strategies.opening_range_breakout.orb import ORBStrategy


def main():
    """Run ORB backtest with EventDrivenBacktestEngine."""
    print("=" * 80)
    print("Testing ORB Strategy with EventDrivenBacktestEngine")
    print("=" * 80)

    # Create ORB strategy
    strategy = ORBStrategy(
        breakout_mode="atr",
        k_multiplier=0.5,
        atr_window=14,
        atr_multiplier=2.0,
        vol_target=0.02,
        noise_window=5,
        noise_threshold=0.5,
        sma_window=20,
        trend_price="open",
        atr_slippage=0.1,
    )

    print(f"\nStrategy: {strategy.name}")
    print(f"Breakout Mode: {strategy.breakout_mode}")
    print(f"K Multiplier: {strategy.k_multiplier}")
    print(f"ATR Window: {strategy.atr_window}")
    print(f"Volatility Target: {strategy.vol_target:.1%}")

    # Data files (single asset for debugging)
    data_files = {
        "KRW-BTC": RAW_DATA_DIR / "KRW-BTC_minute240.parquet",
    }

    # Check files exist
    for ticker, path in data_files.items():
        if not path.exists():
            print(f"ERROR: Data file not found: {path}")
            return
        print(f"\n{ticker}: {path.name}")

    # Backtest configuration
    config = BacktestConfig(
        initial_capital=10_000_000,
        fee_rate=0.0005,
        slippage_rate=0.0005,
        max_slots=1,
        position_sizing="equal",
        trailing_stop_pct=0.05,
    )

    print("\nBacktest Config:")
    print(f"  Initial Capital: {config.initial_capital:,.0f}")
    print(f"  Fee Rate: {config.fee_rate:.2%}")
    print(f"  Slippage Rate: {config.slippage_rate:.2%}")
    print(f"  Max Slots: {config.max_slots}")
    print(
        f"  Trailing Stop: {config.trailing_stop_pct:.1%}"
        if config.trailing_stop_pct
        else "  Trailing Stop: None"
    )

    # Create engine and run backtest
    engine = EventDrivenBacktestEngine(config)

    print("\n" + "=" * 80)
    print("Running Backtest...")
    print("=" * 80)

    result = engine.run(
        strategy=strategy,
        data_files=data_files,
        start_date=date(2023, 3, 1),
        end_date=None,
    )

    # Print results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(result.summary())

    # Print detailed trade information
    if result.trades:
        print("\n" + "=" * 80)
        print(f"TRADE DETAILS (First 10 of {len(result.trades)})")
        print("=" * 80)

        for i, trade in enumerate(result.trades[:10], 1):
            print(f"\nTrade {i}:")
            print(f"  Ticker: {trade.ticker}")
            print(f"  Entry: {trade.entry_date} @ {trade.entry_price:,.0f}")
            print(f"  Exit: {trade.exit_date} @ {trade.exit_price:,.0f}")
            print(f"  Amount: {trade.amount:.6f}")
            print(f"  PnL: {trade.pnl:+,.0f} ({trade.pnl_pct:+.2f}%)")
            print(f"  Exit Reason: {trade.exit_reason}")

    # Equity curve analysis
    if len(result.equity_curve) > 0:
        print("\n" + "=" * 80)
        print("EQUITY CURVE ANALYSIS")
        print("=" * 80)

        print(f"Initial Equity: {result.equity_curve[0]:,.0f}")
        print(f"Final Equity: {result.equity_curve[-1]:,.0f}")
        print(f"Min Equity: {result.equity_curve.min():,.0f}")
        print(f"Max Equity: {result.equity_curve.max():,.0f}")

        # Show first 10 days
        print("\nFirst 10 Days:")
        for i in range(min(10, len(result.dates))):
            print(f"  {result.dates[i]}: {result.equity_curve[i]:,.0f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
