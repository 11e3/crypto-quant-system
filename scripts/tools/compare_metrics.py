"""
Compare metrics calculation between legacy/bt.py and new engine.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


import numpy as np
import pandas as pd


# Legacy metrics calculation functions
def calculate_cagr_legacy(start_val, end_val, days):
    """Legacy CAGR calculation."""
    if days <= 0:
        return 0.0
    if start_val <= 0:
        return 0.0
    if end_val <= 0:
        return -100.0
    return (end_val / start_val) ** (365.0 / days) - 1.0


def calculate_mdd_legacy(cum_returns):
    """Legacy MDD calculation."""
    max_val = -float("inf")
    mdd = 0.0
    for val in cum_returns:
        if val > max_val:
            max_val = val
        if max_val > 0:
            dd = (max_val - val) / max_val
            if dd > mdd:
                mdd = dd
    return mdd * 100.0


def calculate_metrics_engine(equity_curve, dates, initial_capital=1.0):
    """Engine metrics calculation (from report.py)."""

    # Basic period info
    start_date = dates[0]
    end_date = dates[-1]
    total_days = (end_date - start_date).days

    # Returns
    final_equity = equity_curve[-1]
    total_return_pct = (final_equity / initial_capital - 1) * 100

    # CAGR
    if total_days > 0 and initial_capital > 0 and final_equity > 0:
        cagr_pct = ((final_equity / initial_capital) ** (365.0 / total_days) - 1) * 100
    else:
        cagr_pct = 0.0

    # Daily returns
    daily_returns = np.diff(equity_curve) / equity_curve[:-1]
    daily_returns = np.insert(daily_returns, 0, 0)  # First day has 0 return

    # MDD and drawdown curve
    cummax = np.maximum.accumulate(equity_curve)
    drawdown = (cummax - equity_curve) / cummax
    mdd_pct = np.nanmax(drawdown) * 100

    # Calmar ratio
    calmar_ratio = cagr_pct / mdd_pct if mdd_pct > 0 else 0.0

    return {
        "total_days": total_days,
        "initial_capital": initial_capital,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "mdd_pct": mdd_pct,
        "calmar_ratio": calmar_ratio,
        "equity_curve": equity_curve,
        "drawdown": drawdown,
    }


def run_legacy_simulation():
    """Run legacy simulation and return equity curve."""
    import json
    import subprocess

    # Run legacy simulation
    result = subprocess.run(
        ["python", "scripts/legacy_bt_with_trades.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Load equity curve from JSON
    equity_file = project_root / "reports" / "legacy_equity_curve.json"
    if equity_file.exists():
        with open(equity_file) as f:
            equity_data = json.load(f)
        equity_curve = equity_data["equity_curve"]
        dates = [pd.to_datetime(d) for d in equity_data["dates"]]
    else:
        # Fallback: extract from output
        equity_curve = []
        for line in result.stdout.split("\n"):
            if line.startswith("EQUITY_CURVE:"):
                equity_curve.append(float(line.split(":")[1]))
        dates = []

    # Extract metrics from output
    legacy_metrics = {}
    for line in result.stdout.split("\n"):
        if "PORTFOLIO FINAL" in line:
            parts = line.split("|")
            cagr_str = parts[0].split("CAGR:")[1].strip().replace("%", "")
            mdd_str = parts[1].split("MDD:")[1].strip().replace("%", "")
            calmar_str = parts[2].split("Calmar:")[1].strip()

            legacy_metrics = {
                "cagr": float(cagr_str),
                "mdd": float(mdd_str),
                "calmar": float(calmar_str),
            }
        elif line.startswith("Final Equity:"):
            legacy_metrics["final_equity"] = float(line.split(":")[1].strip())

    return equity_curve, legacy_metrics, dates


def run_engine_simulation():
    """Run engine simulation and return equity curve."""
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

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    return result


def compare_metrics():
    """Compare metrics calculation between legacy and engine."""
    print("=" * 80)
    print("METRICS CALCULATION COMPARISON")
    print("=" * 80)

    # Run legacy simulation
    print("\n[1] Running Legacy Simulation...")
    legacy_equity, legacy_metrics, legacy_dates = run_legacy_simulation()

    print(f"\n[Legacy] Equity Curve Length: {len(legacy_equity)}")
    print(f"[Legacy] First 10 values: {legacy_equity[:10]}")
    print(f"[Legacy] Last 10 values: {legacy_equity[-10:]}")
    print("\n[Legacy] Metrics:")
    cagr_val = legacy_metrics.get("cagr")
    mdd_val = legacy_metrics.get("mdd")
    calmar_val = legacy_metrics.get("calmar")
    final_val = legacy_metrics.get("final_equity")

    if cagr_val is not None:
        print(f"  CAGR: {cagr_val:.2f}%")
    else:
        print("  CAGR: N/A")
    if mdd_val is not None:
        print(f"  MDD: {mdd_val:.2f}%")
    else:
        print("  MDD: N/A")
    if calmar_val is not None:
        print(f"  Calmar: {calmar_val:.2f}")
    else:
        print("  Calmar: N/A")
    if final_val is not None:
        print(f"  Final Equity: {final_val:.2f}")
    else:
        print("  Final Equity: N/A")

    # Calculate legacy metrics using legacy functions
    if len(legacy_equity) > 0 and len(legacy_dates) > 0:
        initial_capital = 1.0
        final_equity = legacy_equity[-1]
        total_days = (legacy_dates[-1] - legacy_dates[0]).days

        legacy_cagr = calculate_cagr_legacy(initial_capital, final_equity, total_days) * 100
        legacy_mdd = calculate_mdd_legacy(legacy_equity)
        legacy_calmar = legacy_cagr / legacy_mdd if legacy_mdd > 0 else 0.0

        print("\n[Legacy] Calculated Metrics:")
        print(f"  Total Days: {total_days}")
        print(f"  CAGR: {legacy_cagr:.2f}%")
        print(f"  MDD: {legacy_mdd:.2f}%")
        print(f"  Calmar: {legacy_calmar:.2f}")

    # Run engine simulation
    print("\n[2] Running Engine Simulation...")
    engine_result = run_engine_simulation()

    engine_equity = engine_result.equity_curve
    engine_dates = engine_result.dates

    print(f"\n[Engine] Equity Curve Length: {len(engine_equity)}")
    print(f"[Engine] First 10 values: {engine_equity[:10]}")
    print(f"[Engine] Last 10 values: {engine_equity[-10:]}")
    print("\n[Engine] Metrics:")
    print(f"  CAGR: {engine_result.cagr:.2f}%")
    print(f"  MDD: {engine_result.mdd:.2f}%")
    print(f"  Calmar: {engine_result.calmar_ratio:.2f}")
    print(f"  Final Equity: {engine_equity[-1]:.2f}")

    # Calculate engine metrics using engine functions
    engine_metrics = calculate_metrics_engine(engine_equity, engine_dates)

    print("\n[Engine] Calculated Metrics:")
    print(f"  Total Days: {engine_metrics['total_days']}")
    print(f"  CAGR: {engine_metrics['cagr_pct']:.2f}%")
    print(f"  MDD: {engine_metrics['mdd_pct']:.2f}%")
    print(f"  Calmar: {engine_metrics['calmar_ratio']:.2f}")

    # Compare equity curves
    print("\n" + "=" * 80)
    print("EQUITY CURVE COMPARISON")
    print("=" * 80)

    if len(legacy_equity) > 0 and len(engine_equity) > 0:
        min_len = min(len(legacy_equity), len(engine_equity))

        legacy_aligned = legacy_equity[:min_len]
        engine_aligned = engine_equity[:min_len]

        differences = np.array(legacy_aligned) - np.array(engine_aligned)

        print(f"\nEquity Curve Length: Legacy={len(legacy_equity)}, Engine={len(engine_equity)}")
        print(f"Aligned Length: {min_len}")
        print("\nEquity Differences (Legacy - Engine):")
        print(f"  Mean: {np.mean(differences):.6f}")
        print(f"  Std: {np.std(differences):.6f}")
        print(f"  Max: {np.max(differences):.6f}")
        print(f"  Min: {np.min(differences):.6f}")
        print(f"  Max Abs: {np.max(np.abs(differences)):.6f}")

        # Find largest differences
        abs_diffs = np.abs(differences)
        max_diff_idx = np.argmax(abs_diffs)
        print(f"\nLargest Difference at index {max_diff_idx}:")
        print(f"  Legacy: {legacy_aligned[max_diff_idx]:.6f}")
        print(f"  Engine: {engine_aligned[max_diff_idx]:.6f}")
        print(f"  Diff: {differences[max_diff_idx]:.6f}")

        # Compare final values
        print("\nFinal Equity Comparison:")
        print(f"  Legacy: {legacy_equity[-1]:.6f}")
        print(f"  Engine: {engine_equity[-1]:.6f}")
        print(f"  Diff: {legacy_equity[-1] - engine_equity[-1]:.6f}")
        print(f"  Diff %: {(legacy_equity[-1] / engine_equity[-1] - 1) * 100:.4f}%")

    # Compare metrics calculation
    print("\n" + "=" * 80)
    print("METRICS CALCULATION COMPARISON")
    print("=" * 80)

    if len(legacy_equity) > 0 and len(engine_equity) > 0:
        # Calculate using same method
        initial = 1.0
        legacy_final = legacy_equity[-1]
        engine_final = engine_equity[-1]

        # Use engine's date calculation for both
        total_days = engine_metrics["total_days"]

        legacy_cagr_calc = calculate_cagr_legacy(initial, legacy_final, total_days) * 100
        engine_cagr_calc = calculate_cagr_legacy(initial, engine_final, total_days) * 100

        legacy_mdd_calc = calculate_mdd_legacy(legacy_equity)
        engine_mdd_calc = calculate_mdd_legacy(engine_equity)

        legacy_calmar_calc = legacy_cagr_calc / legacy_mdd_calc if legacy_mdd_calc > 0 else 0.0
        engine_calmar_calc = engine_cagr_calc / engine_mdd_calc if engine_mdd_calc > 0 else 0.0

        print("\nUsing Same Calculation Method:")
        print(f"  Legacy CAGR: {legacy_cagr_calc:.2f}%")
        print(f"  Engine CAGR: {engine_cagr_calc:.2f}%")
        print(f"  CAGR Diff: {legacy_cagr_calc - engine_cagr_calc:.2f}%")

        print(f"\n  Legacy MDD: {legacy_mdd_calc:.2f}%")
        print(f"  Engine MDD: {engine_mdd_calc:.2f}%")
        print(f"  MDD Diff: {legacy_mdd_calc - engine_mdd_calc:.2f}%")

        print(f"\n  Legacy Calmar: {legacy_calmar_calc:.2f}")
        print(f"  Engine Calmar: {engine_calmar_calc:.2f}")
        print(f"  Calmar Diff: {legacy_calmar_calc - engine_calmar_calc:.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    compare_metrics()
