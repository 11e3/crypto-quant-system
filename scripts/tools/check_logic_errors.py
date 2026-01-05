"""
Check for logic errors by comparing detailed execution between legacy and engine.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


import numpy as np
import pandas as pd


def check_equity_calculation():
    """Compare equity calculation logic in detail."""
    print("=" * 80)
    print("EQUITY CALCULATION LOGIC CHECK")
    print("=" * 80)

    # Load equity curves
    import json

    legacy_file = project_root / "reports" / "legacy_equity_curve.json"
    if legacy_file.exists():
        with open(legacy_file) as f:
            legacy_data = json.load(f)
        legacy_equity = legacy_data["equity_curve"]
        legacy_dates = [pd.to_datetime(d) for d in legacy_data["dates"]]
    else:
        print("[ERROR] Legacy equity curve not found!")
        return

    # Run engine to get equity curve
    from src.backtester import BacktestConfig, run_backtest
    from src.strategies.volatility_breakout.vbo import create_vbo_strategy

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

    engine_result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    engine_equity = engine_result.equity_curve
    engine_dates = engine_result.dates

    print("\n[1] Equity Curve Length Comparison:")
    print(f"  Legacy: {len(legacy_equity)}")
    print(f"  Engine: {len(engine_equity)}")
    print(f"  Difference: {len(engine_equity) - len(legacy_equity)}")

    # Find where differences start
    print("\n[2] Finding First Difference:")
    min_len = min(len(legacy_equity), len(engine_equity))

    for i in range(min(100, min_len)):
        if abs(legacy_equity[i] - engine_equity[i]) > 0.0001:
            print(f"  First difference at index {i}:")
            print(f"    Legacy: {legacy_equity[i]:.6f}")
            print(f"    Engine: {engine_equity[i]:.6f}")
            print(f"    Diff: {legacy_equity[i] - engine_equity[i]:.6f}")
            if i < len(legacy_dates):
                print(f"    Date: {legacy_dates[i]}")
            break
    else:
        print("  No significant differences in first 100 values")

    # Check initial values
    print("\n[3] Initial Values Check:")
    print(f"  Legacy first 5: {legacy_equity[:5]}")
    print(f"  Engine first 5: {engine_equity[:5]}")

    # Check if legacy starts with 1.0
    if legacy_equity[0] != 1.0:
        print(f"  [WARNING] Legacy doesn't start with 1.0, starts with {legacy_equity[0]}")

    if engine_equity[0] != 1.0:
        print(f"  [WARNING] Engine doesn't start with 1.0, starts with {engine_equity[0]}")

    # Find largest differences
    print("\n[4] Largest Differences:")
    aligned_len = min(len(legacy_equity), len(engine_equity))
    differences = np.array(legacy_equity[:aligned_len]) - np.array(engine_equity[:aligned_len])
    abs_diffs = np.abs(differences)

    top_5_indices = np.argsort(abs_diffs)[-5:][::-1]
    for idx in top_5_indices:
        print(f"  Index {idx}:")
        print(f"    Legacy: {legacy_equity[idx]:.6f}")
        print(f"    Engine: {engine_equity[idx]:.6f}")
        print(f"    Diff: {differences[idx]:.6f}")
        if idx < len(legacy_dates):
            print(f"    Date: {legacy_dates[idx]}")

    # Check if differences are systematic
    print("\n[5] Systematic Error Check:")
    positive_diffs = differences[differences > 0.01]
    negative_diffs = differences[differences < -0.01]

    print(f"  Positive differences (>0.01): {len(positive_diffs)}")
    print(f"  Negative differences (<-0.01): {len(negative_diffs)}")
    print(f"  Mean difference: {np.mean(differences):.6f}")
    print(f"  Std difference: {np.std(differences):.6f}")

    # Check final values
    print("\n[6] Final Values Check:")
    print(f"  Legacy final: {legacy_equity[-1]:.6f}")
    print(f"  Engine final: {engine_equity[-1]:.6f}")
    print(f"  Final diff: {legacy_equity[-1] - engine_equity[-1]:.6f}")

    if abs(legacy_equity[-1] - engine_equity[-1]) < 0.01:
        print("  [OK] Final values match!")
    else:
        print("  [ERROR] Final values don't match!")

    # Check date alignment
    print("\n[7] Date Alignment Check:")
    if len(legacy_dates) > 0 and len(engine_dates) > 0:
        print(f"  Legacy date range: {legacy_dates[0]} to {legacy_dates[-1]}")
        print(f"  Engine date range: {engine_dates[0]} to {engine_dates[-1]}")

        # Check if dates overlap
        legacy_date_set = set(legacy_dates)
        engine_date_set = set(engine_dates)

        common_dates = legacy_date_set & engine_date_set
        legacy_only = legacy_date_set - engine_date_set
        engine_only = engine_date_set - legacy_date_set

        print(f"  Common dates: {len(common_dates)}")
        print(f"  Legacy only: {len(legacy_only)}")
        print(f"  Engine only: {len(engine_only)}")

        if len(legacy_only) > 0:
            print(f"  Legacy only dates (first 10): {sorted(legacy_only)[:10]}")
        if len(engine_only) > 0:
            print(f"  Engine only dates (first 10): {sorted(engine_only)[:10]}")

    print("\n" + "=" * 80)


def check_trade_timing():
    """Check if trades occur at the same times."""
    print("\n" + "=" * 80)
    print("TRADE TIMING CHECK")
    print("=" * 80)

    # Load trades
    legacy_trades = pd.read_csv(project_root / "reports" / "legacy_trades.csv")
    engine_trades = pd.read_csv(project_root / "reports" / "engine_trades.csv")

    legacy_trades["entry_date"] = pd.to_datetime(legacy_trades["entry_date"])
    engine_trades["entry_date"] = pd.to_datetime(engine_trades["entry_date"])

    legacy_closed = legacy_trades[legacy_trades["exit_date"].notna()].copy()
    engine_closed = engine_trades[engine_trades["exit_date"].notna()].copy()

    legacy_closed["exit_date"] = pd.to_datetime(legacy_closed["exit_date"])
    engine_closed["exit_date"] = pd.to_datetime(engine_closed["exit_date"])

    print("\n[1] Trade Count Comparison:")
    print(f"  Legacy closed trades: {len(legacy_closed)}")
    print(f"  Engine closed trades: {len(engine_closed)}")

    # Compare entry dates
    legacy_entry_dates = set(legacy_closed["entry_date"].dt.date)
    engine_entry_dates = set(engine_closed["entry_date"].dt.date)

    print("\n[2] Entry Date Comparison:")
    print(f"  Legacy unique entry dates: {len(legacy_entry_dates)}")
    print(f"  Engine unique entry dates: {len(engine_entry_dates)}")
    print(f"  Common entry dates: {len(legacy_entry_dates & engine_entry_dates)}")
    print(f"  Legacy only: {len(legacy_entry_dates - engine_entry_dates)}")
    print(f"  Engine only: {len(engine_entry_dates - legacy_entry_dates)}")

    # Compare exit dates
    legacy_exit_dates = set(legacy_closed["exit_date"].dt.date)
    engine_exit_dates = set(engine_closed["exit_date"].dt.date)

    print("\n[3] Exit Date Comparison:")
    print(f"  Legacy unique exit dates: {len(legacy_exit_dates)}")
    print(f"  Engine unique exit dates: {len(engine_exit_dates)}")
    print(f"  Common exit dates: {len(legacy_exit_dates & engine_exit_dates)}")
    print(f"  Legacy only: {len(legacy_exit_dates - engine_exit_dates)}")
    print(f"  Engine only: {len(engine_exit_dates - legacy_exit_dates)}")

    # Check for trades on same day (entry and exit)
    print("\n[4] Same-Day Entry/Exit Check:")
    legacy_same_day = legacy_closed[
        legacy_closed["entry_date"].dt.date == legacy_closed["exit_date"].dt.date
    ]
    engine_same_day = engine_closed[
        engine_closed["entry_date"].dt.date == engine_closed["exit_date"].dt.date
    ]

    print(f"  Legacy same-day trades: {len(legacy_same_day)}")
    print(f"  Engine same-day trades: {len(engine_same_day)}")

    print("\n" + "=" * 80)


def check_data_processing():
    """Check data processing differences."""
    print("\n" + "=" * 80)
    print("DATA PROCESSING CHECK")
    print("=" * 80)

    # Load first ticker data
    btc_file = project_root / "data" / "raw" / "KRW-BTC_day.parquet"
    df = pd.read_parquet(btc_file)

    print("\n[1] Data File Info:")
    print(f"  Total rows: {len(df)}")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    print(f"  Columns: {df.columns.tolist()}")

    # Check how legacy processes data
    print("\n[2] Legacy Data Processing:")
    print("  - Skips first 10 days (max(5, 10, 10) = 10)")
    print("  - Processes from day 11 onwards")
    print("  - Uses date as key in dictionary")

    # Check how engine processes data
    print("\n[3] Engine Data Processing:")
    print("  - Uses pandas rolling with shift(1) for exclude_current=True")
    print("  - Filters NaN values")
    print("  - Uses unified timeline across all tickers")

    # Check date alignment
    print("\n[4] Date Alignment Issue:")
    print("  Legacy: Only processes dates where all tickers have valid data")
    print("  Engine: Creates unified timeline, fills NaN for missing dates")
    print("  This could cause equity curve length differences!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_equity_calculation()
    check_trade_timing()
    check_data_processing()
