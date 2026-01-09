"""
Individual VBO strategy example functions.

Contains demonstration functions for different VBO configurations:
- run_vanilla_vbo: Default VBO settings
- run_minimal_vbo: VBO without filters (baseline)
- run_custom_vbo: VBO with extra conditions
- run_dynamic_modification: Dynamic strategy modification demo
"""

from src.backtester import BacktestConfig, run_backtest
from src.strategies.volatility_breakout import VanillaVBO, create_vbo_strategy
from src.strategies.volatility_breakout.conditions import (
    NoiseThresholdFilter,
    VolatilityRangeCondition,
    VolatilityThresholdCondition,
)


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

    strategy = VanillaVBO(name="DynamicVBO")
    print(f"Initial entry conditions: {[c.name for c in strategy.entry_conditions.conditions]}")

    noise_condition = next(
        (c for c in strategy.entry_conditions.conditions if c.name == "NoiseCondition"),
        None,
    )
    if noise_condition:
        strategy.remove_entry_condition(noise_condition)
    print(
        f"After removing NoiseCondition: {[c.name for c in strategy.entry_conditions.conditions]}"
    )

    vol_condition = VolatilityRangeCondition(min_volatility_pct=0.005)
    strategy.add_entry_condition(vol_condition)
    print(
        f"After adding VolatilityRangeCondition: "
        f"{[c.name for c in strategy.entry_conditions.conditions]}"
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
