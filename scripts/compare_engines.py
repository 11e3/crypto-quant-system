"""
Compare VectorizedBacktestEngine vs EventDrivenBacktestEngine.

Tests both engines with identical configuration.
"""

from datetime import date

from src.backtester.engine import EventDrivenBacktestEngine, VectorizedBacktestEngine
from src.backtester.models import BacktestConfig
from src.config import RAW_DATA_DIR
from src.strategies.opening_range_breakout.orb import ORBStrategy


def main() -> None:
    """Compare both engines."""
    print("=" * 80)
    print("ENGINE COMPARISON: Vectorized vs EventDriven")
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
    )

    # Multi-asset data
    data_files = {
        "KRW-BTC": RAW_DATA_DIR / "KRW-BTC_minute240.parquet",
        "KRW-ETH": RAW_DATA_DIR / "KRW-ETH_minute240.parquet",
        "KRW-XRP": RAW_DATA_DIR / "KRW-XRP_minute240.parquet",
    }

    # Check files exist
    for _ticker, path in data_files.items():
        if not path.exists():
            print(f"ERROR: Data file not found: {path}")
            return

    # Backtest configuration
    config = BacktestConfig(
        initial_capital=10_000_000,
        fee_rate=0.0005,
        slippage_rate=0.0005,
        max_slots=3,
        trailing_stop_pct=0.05,
    )

    print(f"\nStrategy: {strategy.name}")
    print(f"Assets: {list(data_files.keys())}")
    print(f"Initial Capital: {config.initial_capital:,.0f}")
    print(f"Max Slots: {config.max_slots}")

    # Test 1: EventDrivenBacktestEngine
    print("\n" + "=" * 80)
    print("TEST 1: EventDrivenBacktestEngine")
    print("=" * 80)

    event_driven_engine = EventDrivenBacktestEngine(config)
    event_driven_result = event_driven_engine.run(
        strategy=strategy,
        data_files=data_files,
        start_date=date(2023, 3, 1),
        end_date=None,
    )

    print("\n" + event_driven_result.summary())
    print(f"\nTrades: {len(event_driven_result.trades)}")
    if event_driven_result.trades:
        print("First 3 trades:")
        for i, trade in enumerate(event_driven_result.trades[:3], 1):
            print(
                f"  {i}. {trade.ticker} {trade.entry_date} -> {trade.exit_date}: {trade.pnl_pct:+.2f}%"
            )

    # Test 2: VectorizedBacktestEngine
    print("\n" + "=" * 80)
    print("TEST 2: VectorizedBacktestEngine")
    print("=" * 80)

    vectorized_engine = VectorizedBacktestEngine(config)
    vectorized_result = vectorized_engine.run(
        strategy=strategy,
        data_files=data_files,
        start_date=date(2023, 3, 1),
        end_date=None,
    )

    print("\n" + vectorized_result.summary())
    print(f"\nTrades: {len(vectorized_result.trades)}")
    if vectorized_result.trades:
        print("First 3 trades:")
        for i, trade in enumerate(vectorized_result.trades[:3], 1):
            print(
                f"  {i}. {trade.ticker} {trade.entry_date} -> {trade.exit_date}: {trade.pnl_pct:+.2f}%"
            )

    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    print(f"\n{'Metric':<20} {'EventDriven':<20} {'Vectorized':<20}")
    print("-" * 60)
    print(
        f"{'Total Trades':<20} {event_driven_result.total_trades:<20} {vectorized_result.total_trades:<20}"
    )
    print(f"{'CAGR':<20} {event_driven_result.cagr:<20.2f} {vectorized_result.cagr:<20.2f}")
    print(f"{'MDD':<20} {event_driven_result.mdd:<20.2f} {vectorized_result.mdd:<20.2f}")
    print(
        f"{'Calmar Ratio':<20} {event_driven_result.calmar_ratio:<20.2f} {vectorized_result.calmar_ratio:<20.2f}"
    )
    print(
        f"{'Sharpe Ratio':<20} {event_driven_result.sharpe_ratio:<20.2f} {vectorized_result.sharpe_ratio:<20.2f}"
    )
    print(
        f"{'Win Rate':<20} {event_driven_result.win_rate:<20.2f} {vectorized_result.win_rate:<20.2f}"
    )

    final_event_driven = (
        event_driven_result.equity_curve[-1] if len(event_driven_result.equity_curve) > 0 else 0
    )
    final_vectorized = (
        vectorized_result.equity_curve[-1] if len(vectorized_result.equity_curve) > 0 else 0
    )
    print(f"{'Final Equity':<20} {final_event_driven:<20,.0f} {final_vectorized:<20,.0f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
