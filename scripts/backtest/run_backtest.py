"""
Script to run backtests using the modular VBO strategy.

Demonstrates the flexibility of the strategy abstraction.

For individual strategy examples, see run_backtest_examples.py.
"""

import argparse
from pathlib import Path

from scripts.backtest.run_backtest_examples import (
    run_custom_vbo,
    run_dynamic_modification,
    run_minimal_vbo,
    run_vanilla_vbo,
)
from src.backtester import BacktestConfig, generate_report, run_backtest
from src.config import REPORTS_DIR
from src.strategies.volatility_breakout import VanillaVBO, create_vbo_strategy
from src.utils.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Ensure reports directory exists
REPORTS_DIR.mkdir(exist_ok=True)


def compare_strategies() -> None:
    """Compare multiple strategy configurations."""
    print("\n" + "=" * 60)
    print("Strategy Comparison")
    print("=" * 60)

    strategies = [
        create_vbo_strategy(
            name="VBO_AllFilters",
            use_trend_filter=True,
            use_noise_filter=True,
        ),
        create_vbo_strategy(
            name="VBO_TrendOnly",
            use_trend_filter=True,
            use_noise_filter=False,
        ),
        create_vbo_strategy(
            name="VBO_NoiseOnly",
            use_trend_filter=False,
            use_noise_filter=True,
        ),
        create_vbo_strategy(
            name="VBO_NoFilters",
            use_trend_filter=False,
            use_noise_filter=False,
        ),
    ]

    config = BacktestConfig(max_slots=4)
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    results = []
    for strategy in strategies:
        result = run_backtest(
            strategy=strategy,
            tickers=tickers,
            interval="day",
            config=config,
        )
        results.append(result)

    print("\n" + "-" * 70)
    print(f"{'Strategy':<20} {'CAGR':>10} {'MDD':>10} {'Calmar':>10} {'Trades':>10}")
    print("-" * 70)

    for result in results:
        print(
            f"{result.strategy_name:<20} "
            f"{result.cagr:>9.2f}% "
            f"{result.mdd:>9.2f}% "
            f"{result.calmar_ratio:>10.2f} "
            f"{result.total_trades:>10}"
        )


def run_legacy_bt_strategy(
    save_plots: bool = False,
    show_plots: bool = False,
    reports_dir: Path = REPORTS_DIR,
) -> None:
    """
    Run legacy/bt.py strategy exactly as implemented.

    Args:
        save_plots: Whether to save report plots
        show_plots: Whether to display plots
        reports_dir: Directory to save reports
    """
    print("\n" + "=" * 60)
    print("Running Legacy BT Strategy (Exact Implementation)")
    print("=" * 60)

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

    print(f"Strategy: {strategy}")
    print(f"Parameters: SMA={strategy.sma_period}, Trend SMA={strategy.trend_sma_period}")
    print(
        f"           Short Noise={strategy.short_noise_period}, "
        f"Long Noise={strategy.long_noise_period}"
    )
    print(f"Entry Conditions: {[c.name for c in strategy.entry_conditions.conditions]}")
    print(f"Exit Conditions: {[c.name for c in strategy.exit_conditions.conditions]}")

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

    print(result.summary())

    if save_plots or show_plots:
        save_path = reports_dir / "legacy_bt_report.png" if save_plots else None
        report = generate_report(
            result=result,
            save_path=save_path,
            show=show_plots,
        )

        if save_plots:
            metrics_df = report.to_dataframe()
            metrics_df.to_csv(reports_dir / "legacy_bt_metrics.csv", index=False)
            print(f"\n[+] Report saved to: {reports_dir}")


def run_with_full_report(
    save_plots: bool = True,
    show_plots: bool = True,
    reports_dir: Path = REPORTS_DIR,
) -> None:
    """
    Run VBO strategy with full performance report.

    Args:
        save_plots: Whether to save report plots
        show_plots: Whether to display plots
        reports_dir: Directory to save reports
    """
    print("\n" + "=" * 60)
    print("Running VBO with Full Performance Report")
    print("=" * 60)

    strategy = VanillaVBO(
        name="VBO_FullReport",
        sma_period=5,
        trend_sma_period=10,
        short_noise_period=5,
        long_noise_period=10,
        exclude_current=True,  # Prevent look-ahead bias (critical for realistic results)
    )

    config = BacktestConfig(
        initial_capital=1.0,
        fee_rate=0.0005,
        slippage_rate=0.0005,
        max_slots=4,
    )

    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    save_path = reports_dir / "vbo_report.png" if save_plots else None

    report = generate_report(
        result=result,
        save_path=save_path,
        show=show_plots,
    )

    if save_plots:
        metrics_df = report.to_dataframe()
        metrics_df.to_csv(reports_dir / "vbo_metrics.csv", index=False)
        print(f"\n[+] Report saved to: {reports_dir}")


def main() -> None:
    """Run all backtest demonstrations."""
    parser = argparse.ArgumentParser(description="Run VBO backtests")
    parser.add_argument(
        "--mode",
        choices=["all", "report", "compare", "vanilla", "legacy"],
        default="report",
        help="Backtest mode to run",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display plots (only save)",
    )
    args = parser.parse_args()

    if args.mode == "all":
        run_vanilla_vbo()
        run_minimal_vbo()
        run_custom_vbo()
        run_dynamic_modification()
        compare_strategies()
    elif args.mode == "report":
        run_with_full_report(save_plots=True, show_plots=not args.no_show)
    elif args.mode == "compare":
        compare_strategies()
    elif args.mode == "vanilla":
        run_vanilla_vbo()
    elif args.mode == "legacy":
        run_legacy_bt_strategy(save_plots=True, show_plots=not args.no_show)


if __name__ == "__main__":
    main()
