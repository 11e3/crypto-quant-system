"""Simple test to verify ORB strategy generates trades."""

from src.backtester.engine import BacktestConfig, BacktestEngine
from src.config import PROCESSED_DATA_DIR
from src.strategies.opening_range_breakout import ORBStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_single_asset() -> None:
    """Test ORB on single asset to isolate the issue."""

    ticker = "KRW-BTC"

    # Create strategy
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

    # Configuration
    config = BacktestConfig(
        initial_capital=10_000_000.0,
        fee_rate=0.0005,
        slippage_rate=0.0,
        max_slots=1,
        trailing_stop_pct=0.05,
    )

    # File path
    data_files = {ticker: PROCESSED_DATA_DIR / f"{ticker}_minute30.parquet"}

    print(f"Running backtest on {ticker}...")
    print(f"  Strategy: {strategy.name}")
    print(f"  Max slots: {config.max_slots}")
    print(f"  Trailing stop: {config.trailing_stop_pct}")
    print()

    # Run backtest
    engine = BacktestEngine(config)
    result = engine.run(strategy, data_files)

    print("Results:")
    print(f"  Total Return: {result.total_return:.2f}%")
    print(f"  CAGR: {result.cagr:.2f}%")
    print(f"  Sharpe: {result.sharpe_ratio:.2f}")
    print(f"  MDD: {result.mdd:.2f}%")
    print(f"  Total Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.2f}%")
    print()

    if result.total_trades > 0:
        print("✓ Trades generated! First 5 trades:")
        for i, trade in enumerate(result.trades[:5]):
            print(
                f"  {i + 1}. {trade.ticker} {trade.entry_date} → {trade.exit_date}: {trade.pnl_pct:.2f}%"
            )
    else:
        print("❌ NO TRADES GENERATED")
        print("\nDebugging...")
        print(f"  Equity curve length: {len(result.equity_curve)}")
        print(f"  Dates length: {len(result.dates)}")
        if len(result.equity_curve) > 0:
            print(f"  Initial equity: {result.equity_curve[0]:.2f}")
            print(f"  Final equity: {result.equity_curve[-1]:.2f}")
            print(f"  Date range: {result.dates[0]} to {result.dates[-1]}")

            # Check if equity changed
            if result.equity_curve[0] != result.equity_curve[-1]:
                print(
                    f"\n  ⚠ Equity changed from {result.equity_curve[0]:.0f} to {result.equity_curve[-1]:.0f}"
                )
                print("     but no trades recorded! This shouldn't happen.")

                # Check equity curve changes
                changes = []
                for i in range(1, min(10, len(result.equity_curve))):
                    if result.equity_curve[i] != result.equity_curve[i - 1]:
                        changes.append(
                            f"    Day {i} ({result.dates[i]}): {result.equity_curve[i - 1]:.0f} → {result.equity_curve[i]:.0f}"
                        )

                if changes:
                    print("\n  First equity changes:")
                    for change in changes:
                        print(change)


if __name__ == "__main__":
    test_single_asset()
