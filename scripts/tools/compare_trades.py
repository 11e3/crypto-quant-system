"""
Compare trades between legacy/bt.py and new engine.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.backtester import BacktestConfig, run_backtest
from src.strategies.volatility_breakout.vbo import create_vbo_strategy


def run_legacy_bt_with_trades():
    """Run legacy/bt.py and extract trade information."""
    import importlib.util

    legacy_path = project_root / "legacy" / "bt.py"

    # Read and modify legacy code to capture trades
    with open(legacy_path, encoding="utf-8") as f:
        legacy_code = f.read()

    # Add trade recording
    modified_code = legacy_code.replace(
        'positions[coin] = {"amount": amount}',
        'positions[coin] = {"amount": amount, "entry_date": dt, "entry_price": buy_price}',
    )

    # Add trade list
    modified_code = modified_code.replace("positions = {}", "positions = {}\n    trades = []")

    # Add exit trade recording
    modified_code = modified_code.replace(
        "sold_coins.append(coin)",
        'sold_coins.append(coin)\n                if coin in positions:\n                    trades.append({\n                        "ticker": coin,\n                        "entry_date": positions[coin].get("entry_date"),\n                        "entry_price": positions[coin].get("entry_price"),\n                        "exit_date": dt,\n                        "exit_price": sell_price,\n                        "amount": pos["amount"]\n                    })',
    )

    # Execute modified code
    spec = importlib.util.spec_from_file_location("legacy_bt", legacy_path)
    legacy_module = importlib.util.module_from_spec(spec)

    # This approach is complex, let's use a simpler approach
    return None


def run_engine_backtest():
    """Run new engine backtest and return trades."""
    strategy = create_vbo_strategy(
        name="LegacyBT",
        sma_period=5,
        trend_sma_period=10,
        short_noise_period=5,
        long_noise_period=10,
        use_trend_filter=True,
        use_noise_filter=True,
        exclude_current=True,
    )

    config = BacktestConfig(
        initial_capital=1.0,
        fee_rate=0.0005,
        slippage_rate=0.0005,
        max_slots=4,
        use_cache=False,
    )

    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    return result


def compare_trades():
    """Compare trades between legacy and engine."""
    print("=" * 80)
    print("TRADE COMPARISON: Legacy vs Engine")
    print("=" * 80)

    # Get legacy trades
    print("\n[1] Running Legacy Backtest...")
    import subprocess

    legacy_result = subprocess.run(
        ["python", "scripts/legacy_bt_with_trades.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    print(legacy_result.stdout)
    if legacy_result.stderr:
        print("STDERR:", legacy_result.stderr)

    # Load legacy trades
    legacy_trades_path = project_root / "reports" / "legacy_trades.csv"
    if legacy_trades_path.exists():
        legacy_trades_df = pd.read_csv(legacy_trades_path)
        legacy_trades_df["entry_date"] = pd.to_datetime(legacy_trades_df["entry_date"])
        legacy_trades_df["exit_date"] = pd.to_datetime(
            legacy_trades_df["exit_date"], errors="coerce"
        )
        print(f"\n[Legacy] Total Trades: {len(legacy_trades_df)}")
        print(
            f"[Legacy] Closed Trades: {len(legacy_trades_df[legacy_trades_df['exit_date'].notna()])}"
        )
        print(
            f"[Legacy] Open Trades: {len(legacy_trades_df[legacy_trades_df['exit_date'].isna()])}"
        )
    else:
        legacy_trades_df = None
        print("\n[Legacy] Could not load trades!")

    # Get engine trades
    print("\n[2] Running Engine Backtest...")
    engine_result = run_engine_backtest()

    if engine_result.trades:
        engine_trades_df = pd.DataFrame(
            [
                {
                    "ticker": t.ticker,
                    "entry_date": t.entry_date,
                    "entry_price": t.entry_price,
                    "exit_date": t.exit_date,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "is_whipsaw": t.is_whipsaw,
                    "commission_cost": getattr(t, "commission_cost", 0.0),
                    "slippage_cost": getattr(t, "slippage_cost", 0.0),
                    "is_stop_loss": getattr(t, "is_stop_loss", False),
                    "is_take_profit": getattr(t, "is_take_profit", False),
                    "exit_reason": getattr(t, "exit_reason", "signal"),
                }
                for t in engine_result.trades
            ]
        )

        print(f"\n[Engine] Total Trades: {len(engine_trades_df)}")
        print(
            f"[Engine] Closed Trades: {len(engine_trades_df[engine_trades_df['exit_date'].notna()])}"
        )
        print(
            f"[Engine] Open Trades: {len(engine_trades_df[engine_trades_df['exit_date'].isna()])}"
        )

        # Show first 20 trades
        print("\n[Engine] First 20 Trades:")
        print(engine_trades_df.head(20).to_string())

        # Save to CSV
        # Make sure reports directory exists
        output_dir = project_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "engine_trades.csv"
        engine_trades_df.to_csv(output_path, index=False)
        print(f"\n[+] Engine trades saved to: {output_path}")

        # Analyze by ticker
        print("\n[Engine] Trades by Ticker:")
        print(engine_trades_df.groupby("ticker").size())

        # Analyze by date range
        if len(engine_trades_df) > 0:
            engine_trades_df["entry_date"] = pd.to_datetime(engine_trades_df["entry_date"])
            engine_trades_df["exit_date"] = pd.to_datetime(engine_trades_df["exit_date"])

            print("\n[Engine] Entry Date Range:")
            print(f"  Start: {engine_trades_df['entry_date'].min()}")
            print(f"  End: {engine_trades_df['entry_date'].max()}")

            print("\n[Engine] Monthly Trade Count:")
            monthly = engine_trades_df.groupby(
                engine_trades_df["entry_date"].dt.to_period("M")
            ).size()
            print(monthly.head(20))
    else:
        print("[Engine] No trades found!")

    # Compare trades
    if legacy_trades_df is not None and engine_trades_df is not None:
        print("\n" + "=" * 80)
        print("COMPARISON SUMMARY")
        print("=" * 80)

        print(
            f"\n[Legacy] Total: {len(legacy_trades_df)}, Closed: {len(legacy_trades_df[legacy_trades_df['exit_date'].notna()])}"
        )
        print(
            f"[Engine] Total: {len(engine_trades_df)}, Closed: {len(engine_trades_df[engine_trades_df['exit_date'].notna()])}"
        )

        # Compare closed trades
        legacy_closed = legacy_trades_df[legacy_trades_df["exit_date"].notna()].copy()
        engine_closed = engine_trades_df[engine_trades_df["exit_date"].notna()].copy()

        print(f"\n[Legacy] Closed Trades: {len(legacy_closed)}")
        print(f"[Engine] Closed Trades: {len(engine_closed)}")

        # Compare by ticker
        print("\n[Legacy] Closed Trades by Ticker:")
        print(legacy_closed.groupby("ticker").size())
        print("\n[Engine] Closed Trades by Ticker:")
        print(engine_closed.groupby("ticker").size())

        # Compare first few trades
        print("\n[Legacy] First 10 Closed Trades:")
        print(
            legacy_closed.head(10)[
                ["ticker", "entry_date", "entry_price", "exit_date", "exit_price", "pnl_pct"]
            ].to_string()
        )

        print("\n[Engine] First 10 Closed Trades:")
        print(
            engine_closed.head(10)[
                ["ticker", "entry_date", "entry_price", "exit_date", "exit_price", "pnl_pct"]
            ].to_string()
        )

        # Find matching trades
        print("\n" + "=" * 80)
        print("DETAILED COMPARISON")
        print("=" * 80)

        # Compare first 50 trades by date and ticker
        legacy_sample = legacy_closed.head(50).copy()
        engine_sample = engine_closed.head(50).copy()

        # Normalize dates to date only (remove time component)
        legacy_sample["entry_date_only"] = pd.to_datetime(legacy_sample["entry_date"]).dt.date
        engine_sample["entry_date_only"] = pd.to_datetime(engine_sample["entry_date"]).dt.date

        legacy_sample["key"] = (
            legacy_sample["ticker"] + "_" + legacy_sample["entry_date_only"].astype(str)
        )
        engine_sample["key"] = (
            engine_sample["ticker"] + "_" + engine_sample["entry_date_only"].astype(str)
        )

        matching = pd.merge(
            legacy_sample,
            engine_sample,
            on="key",
            suffixes=("_legacy", "_engine"),
            how="outer",
        )

        print(
            f"\nMatching trades (first 50): {len(matching[matching['ticker_legacy'].notna() & matching['ticker_engine'].notna()])}"
        )
        print(
            f"Legacy only: {len(matching[matching['ticker_legacy'].notna() & matching['ticker_engine'].isna()])}"
        )
        print(
            f"Engine only: {len(matching[matching['ticker_legacy'].isna() & matching['ticker_engine'].notna()])}"
        )

        matched = matching[matching["ticker_legacy"].notna() & matching["ticker_engine"].notna()]
        if len(matched) > 0:
            print("\nFirst 10 Matching Trades Comparison:")
            print(
                matched.head(10)[
                    [
                        "ticker_legacy",
                        "entry_date_legacy",
                        "entry_price_legacy",
                        "exit_price_legacy",
                        "pnl_pct_legacy",
                        "entry_price_engine",
                        "exit_price_engine",
                        "pnl_pct_engine",
                    ]
                ].to_string()
            )

            # Compare prices
            print("\nPrice Differences (Legacy - Engine):")
            matched["entry_price_diff"] = (
                matched["entry_price_legacy"] - matched["entry_price_engine"]
            )
            matched["exit_price_diff"] = matched["exit_price_legacy"] - matched["exit_price_engine"]
            matched["pnl_diff"] = matched["pnl_pct_legacy"] - matched["pnl_pct_engine"]
            print(
                f"Entry Price - Mean diff: {matched['entry_price_diff'].mean():.2f}, Max abs diff: {matched['entry_price_diff'].abs().max():.2f}"
            )
            print(
                f"Exit Price - Mean diff: {matched['exit_price_diff'].mean():.2f}, Max abs diff: {matched['exit_price_diff'].abs().max():.2f}"
            )
            print(
                f"PnL % - Mean diff: {matched['pnl_diff'].mean():.4f}%, Max abs diff: {matched['pnl_diff'].abs().max():.4f}%"
            )

            # Show trades with largest differences
            print("\nTrades with Largest Entry Price Differences:")
            largest_diff = matched.nlargest(5, "entry_price_diff", keep="all")
            print(
                largest_diff[
                    [
                        "ticker_legacy",
                        "entry_date_legacy",
                        "entry_price_legacy",
                        "entry_price_engine",
                        "entry_price_diff",
                    ]
                ].to_string()
            )
        else:
            print("\nNo matching trades found! Checking date format differences...")
            print(f"Legacy date sample: {legacy_sample['entry_date'].head(3).tolist()}")
            print(f"Engine date sample: {engine_sample['entry_date'].head(3).tolist()}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    compare_trades()
