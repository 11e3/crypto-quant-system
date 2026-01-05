"""
Script to run backtests using the modular VBO strategy.

Demonstrates the flexibility of the strategy abstraction.
"""

from src.backtester import BacktestConfig, generate_report, run_backtest
from src.config import REPORTS_DIR
from src.strategies.volatility_breakout import VanillaVBO, create_vbo_strategy
from src.strategies.volatility_breakout.conditions import (
    NoiseThresholdFilter,
    VolatilityRangeCondition,
    VolatilityThresholdCondition,
)
from src.utils.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Ensure reports directory exists
REPORTS_DIR.mkdir(exist_ok=True)


def run_vanilla_vbo() -> None:
    """Run vanilla VBO strategy with default settings."""
    print("\n" + "=" * 60)
    print("Running Vanilla VBO Strategy")
    print("=" * 60)

    strategy = VanillaVBO(
        sma_period=4,
        trend_sma_period=8,
        short_noise_period=4,
        long_noise_period=8,
    )

    print(f"Strategy: {strategy}")
    print(f"Entry Conditions: {[c.name for c in strategy.entry_conditions.conditions]}")
    print(f"Exit Conditions: {[c.name for c in strategy.exit_conditions.conditions]}")
    # Note: Filters are now part of entry_conditions in the unified architecture

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

    print(result.summary())


def run_minimal_vbo() -> None:
    """Run VBO without filters (baseline comparison)."""
    print("\n" + "=" * 60)
    print("Running Minimal VBO (No Filters)")
    print("=" * 60)

    strategy = create_vbo_strategy(
        name="MinimalVBO",
        use_trend_filter=False,
        use_noise_filter=False,
    )

    print(f"Strategy: {strategy}")
    print(f"Entry Conditions: {[c.name for c in strategy.entry_conditions.conditions]}")

    config = BacktestConfig(max_slots=4)
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    print(result.summary())


def run_custom_vbo() -> None:
    """Run custom VBO with extra conditions."""
    print("\n" + "=" * 60)
    print("Running Custom VBO with Extra Conditions")
    print("=" * 60)

    # Create VBO with additional conditions
    strategy = create_vbo_strategy(
        name="CustomVBO_Strict",
        extra_entry_conditions=[
            VolatilityThresholdCondition(min_range_pct=0.01),
        ],
        extra_filters=[
            NoiseThresholdFilter(max_noise=0.65),
        ],
    )

    print(f"Strategy: {strategy}")
    print(f"Entry Conditions: {[c.name for c in strategy.entry_conditions.conditions]}")
    # Note: Filters are now part of entry_conditions in the unified architecture

    config = BacktestConfig(max_slots=4)
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    print(result.summary())


def run_dynamic_modification() -> None:
    """Demonstrate dynamic strategy modification."""
    print("\n" + "=" * 60)
    print("Demonstrating Dynamic Strategy Modification")
    print("=" * 60)

    # Start with vanilla strategy
    strategy = VanillaVBO(name="DynamicVBO")
    print(f"Initial entry conditions: {[c.name for c in strategy.entry_conditions.conditions]}")

    # Remove noise condition (formerly NoiseFilter)
    noise_condition = next(
        (c for c in strategy.entry_conditions.conditions if c.name == "NoiseCondition"),
        None,
    )
    if noise_condition:
        strategy.remove_entry_condition(noise_condition)
    print(
        f"After removing NoiseCondition: {[c.name for c in strategy.entry_conditions.conditions]}"
    )

    # Add volatility condition (formerly VolatilityFilter)
    vol_condition = VolatilityRangeCondition(min_volatility_pct=0.005)
    strategy.add_entry_condition(vol_condition)
    print(
        f"After adding VolatilityRangeCondition: {[c.name for c in strategy.entry_conditions.conditions]}"
    )

    config = BacktestConfig(max_slots=4)
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    print(result.summary())


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

    # Print comparison table
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


def run_legacy_bt_strategy(save_plots: bool = False, show_plots: bool = False) -> None:
    """
    Run legacy/bt.py strategy exactly as implemented.

    Strategy parameters:
    - SMA_PERIOD = 5
    - N = 2
    - TREND_SMA_PERIOD = 10 (SMA_PERIOD * N)
    - SHORT_TERM_NOISE_PERIOD = 5 (SMA_PERIOD)
    - LONG_TERM_NOISE_PERIOD = 10 (SMA_PERIOD * N)

    Entry conditions:
    1. target > sma AND high >= target (Breakout + SMABreakout)
    2. target > sma_trend (Trend Filter)
    3. short_noise < long_noise (Noise Filter)

    Exit condition:
    - close < sma

    Args:
        save_plots: Whether to save report plots
        show_plots: Whether to display plots
    """
    print("\n" + "=" * 60)
    print("Running Legacy BT Strategy (Exact Implementation)")
    print("=" * 60)

    # Create strategy matching legacy/bt.py exactly
    # Note: exclude_current=True to match legacy/bt.py behavior (SMA excludes current bar)
    strategy = create_vbo_strategy(
        name="LegacyBT",
        sma_period=5,
        trend_sma_period=10,  # SMA_PERIOD * N = 5 * 2
        short_noise_period=5,  # SMA_PERIOD
        long_noise_period=10,  # SMA_PERIOD * N
        use_trend_filter=True,
        use_noise_filter=True,
        exclude_current=True,  # Match legacy/bt.py: exclude current bar from calculations
    )

    print(f"Strategy: {strategy}")
    print(f"Parameters: SMA={strategy.sma_period}, Trend SMA={strategy.trend_sma_period}")
    print(
        f"           Short Noise={strategy.short_noise_period}, Long Noise={strategy.long_noise_period}"
    )
    print(f"Entry Conditions: {[c.name for c in strategy.entry_conditions.conditions]}")
    print(f"Exit Conditions: {[c.name for c in strategy.exit_conditions.conditions]}")
    # Note: Filters are now part of entry_conditions in the unified architecture

    # Match legacy/bt.py config
    config = BacktestConfig(
        initial_capital=1.0,
        fee_rate=0.0005,  # FEE
        slippage_rate=0.0005,  # SLIPPAGE
        max_slots=4,  # TARGET_SLOTS
        use_cache=False,  # Disable cache to ensure fresh calculations
    )

    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    result = run_backtest(
        strategy=strategy,
        tickers=tickers,
        interval="day",
        config=config,
    )

    print(result.summary())

    # Generate report if requested
    if save_plots or show_plots:
        save_path = REPORTS_DIR / "legacy_bt_report.png" if save_plots else None
        report = generate_report(
            result=result,
            save_path=save_path,
            show=show_plots,
        )

        if save_plots:
            metrics_df = report.to_dataframe()
            metrics_df.to_csv(REPORTS_DIR / "legacy_bt_metrics.csv", index=False)
            print(f"\n[+] Report saved to: {REPORTS_DIR}")
            print("    - legacy_bt_report.png")
            print("    - legacy_bt_metrics.csv")


def run_with_full_report(save_plots: bool = True, show_plots: bool = True) -> None:
    """
    Run VBO strategy with full performance report.

    Generates:
    - Console summary with all metrics
    - Equity curve with drawdown overlay
    - Standalone drawdown chart
    - Monthly/yearly returns heatmap
    """
    print("\n" + "=" * 60)
    print("Running VBO with Full Performance Report")
    print("=" * 60)

    strategy = VanillaVBO(
        name="VBO_FullReport",
        sma_period=4,
        trend_sma_period=8,
        short_noise_period=4,
        long_noise_period=8,
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

    # Generate full report with visualizations
    save_path = REPORTS_DIR / "vbo_report.png" if save_plots else None

    report = generate_report(
        result=result,
        save_path=save_path,
        show=show_plots,
    )

    # Export metrics to CSV
    if save_plots:
        metrics_df = report.to_dataframe()
        metrics_df.to_csv(REPORTS_DIR / "vbo_metrics.csv", index=False)
        print(f"\n[+] Report saved to: {REPORTS_DIR}")
        print("    - vbo_report.png")
        print("    - vbo_metrics.csv")


def main() -> None:
    """Run all backtest demonstrations."""
    import argparse

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
