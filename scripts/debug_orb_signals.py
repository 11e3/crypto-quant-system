"""Debug ORB strategy signal generation."""

import pandas as pd

from src.config import PROCESSED_DATA_DIR
from src.strategies.opening_range_breakout import ORBStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


def debug_orb_signals() -> None:
    """Debug why ORB strategy generates 0 signals."""

    # Load BTC data as test case
    ticker = "KRW-BTC"
    filepath = PROCESSED_DATA_DIR / f"{ticker}_minute30.parquet"

    print(f"Loading {ticker} data from {filepath}")
    df = pd.read_parquet(filepath)
    print(f"  Loaded {len(df)} candles")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print()

    # Create strategy with same parameters as backtest
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

    print("Strategy parameters:")
    print(f"  Breakout mode: {strategy.breakout_mode}")
    print(f"  k_multiplier: {strategy.k_multiplier}")
    print(f"  atr_window: {strategy.atr_window}")
    print(f"  noise_threshold: {strategy.noise_threshold}")
    print(f"  sma_window: {strategy.sma_window}")
    print()

    # Generate signals
    print("Generating signals...")
    result_df = strategy.generate_signals(df)

    print("\nGenerated DataFrame columns:")
    print(f"  {list(result_df.columns)}")
    print()

    print("DataFrame dtypes:")
    for col in ["entry_signal", "exit_signal", "atr", "trailing_stop_distance"]:
        if col in result_df.columns:
            print(f"  {col}: {result_df[col].dtype}")
    print()
    # Analyze each condition
    print("\n" + "=" * 80)
    print("CONDITION ANALYSIS")
    print("=" * 80)

    # Check if columns exist
    if "atr" in result_df.columns:
        print("\n[ATR]")
        print(f"  Mean: {result_df['atr'].mean():.2f}")
        print(f"  Median: {result_df['atr'].median():.2f}")
        print(f"  Non-null: {result_df['atr'].notna().sum()}/{len(result_df)}")

    if "noise" in result_df.columns:
        print("\n[Noise]")
        print(f"  Mean: {result_df['noise'].mean():.4f}")
        print(f"  Median: {result_df['noise'].median():.4f}")
        print(f"  Non-null: {result_df['noise'].notna().sum()}/{len(result_df)}")

        # Calculate noise_sma
        noise_sma = result_df["noise"].rolling(strategy.noise_window).mean()
        print(f"  noise_sma mean: {noise_sma.mean():.4f}")
        print(
            f"  noise_sma < 0.5: {(noise_sma < 0.5).sum()}/{len(noise_sma)} ({(noise_sma < 0.5).sum() / len(noise_sma) * 100:.1f}%)"
        )

    if "sma" in result_df.columns:
        print("\n[SMA]")
        print(f"  Mean: {result_df['sma'].mean():.2f}")
        print(f"  Non-null: {result_df['sma'].notna().sum()}/{len(result_df)}")

        # Trend filter: open > sma
        trend_ok = result_df["open"] > result_df["sma"]
        print(
            f"  open > sma: {trend_ok.sum()}/{len(trend_ok)} ({trend_ok.sum() / len(trend_ok) * 100:.1f}%)"
        )

    # Breakout condition
    if "atr" in result_df.columns:
        breakout_price = result_df["open"] + strategy.k_multiplier * result_df["atr"]
        breakout = result_df["high"] >= breakout_price
        print("\n[Breakout (ATR mode)]")
        print(f"  Formula: high >= open + {strategy.k_multiplier} * ATR")
        print(
            f"  Breakout signals: {breakout.sum()}/{len(breakout)} ({breakout.sum() / len(breakout) * 100:.1f}%)"
        )

        # Show some examples
        breakout_idx = result_df[breakout].head(5).index
        if len(breakout_idx) > 0:
            print("\n  First 5 breakout examples:")
            for idx in breakout_idx:
                row = result_df.loc[idx]
                target = row["open"] + strategy.k_multiplier * row["atr"]
                print(
                    f"    {idx}: high={row['high']:.0f}, target={target:.0f}, atr={row['atr']:.0f}"
                )

    # Entry signal
    if "entry_signal" in result_df.columns:
        print("\n[Entry Signal (combined)]")
        entry_count = result_df["entry_signal"].sum()
        print(
            f"  Total entry signals: {entry_count}/{len(result_df)} ({entry_count / len(result_df) * 100:.2f}%)"
        )

        if entry_count > 0:
            print("\n  First 5 entry signals:")
            entry_idx = result_df[result_df["entry_signal"]].head(5).index
            for idx in entry_idx:
                row = result_df.loc[idx]
                print(
                    f"    {idx}: open={row['open']:.0f}, high={row['high']:.0f}, close={row['close']:.0f}"
                )

            # Check signal data type
            print(f"\n  Signal dtype: {result_df['entry_signal'].dtype}")
            print(f"  Signal unique values: {result_df['entry_signal'].unique()}")

            # Check if signals are boolean True or int 1
            if result_df["entry_signal"].dtype == bool:
                print("  ✓ Signals are boolean type")
            else:
                print(f"  ⚠ Signals are {result_df['entry_signal'].dtype}, converting...")
                result_df["entry_signal"] = result_df["entry_signal"].astype(bool)
        else:
            print("\n  ❌ NO ENTRY SIGNALS GENERATED!")
            print("\n  Debugging individual conditions:")

            # Re-evaluate conditions manually
            from src.utils.indicators import calculate_atr, calculate_noise, sma

            df_test = result_df.copy()
            atr = calculate_atr(df_test, window=strategy.atr_window)
            noise = calculate_noise(df_test)
            noise_sma = noise.rolling(strategy.noise_window).mean()
            sma_line = sma(df_test["close"], period=strategy.sma_window)

            # Breakout
            breakout_price = df_test["open"] + strategy.k_multiplier * atr
            breakout = df_test["high"] >= breakout_price

            # Filters
            noise_ok = noise_sma < strategy.noise_threshold
            trend_ok = df_test["open"] > sma_line

            combined = breakout & noise_ok & trend_ok

            print(f"    Breakout only: {breakout.sum()}")
            print(f"    Noise filter only: {noise_ok.sum()}")
            print(f"    Trend filter only: {trend_ok.sum()}")
            print(f"    Breakout & Noise: {(breakout & noise_ok).sum()}")
            print(f"    Breakout & Trend: {(breakout & trend_ok).sum()}")
            print(f"    Noise & Trend: {(noise_ok & trend_ok).sum()}")
            print(f"    All combined: {combined.sum()}")

    # Exit signal
    if "exit_signal" in result_df.columns:
        print("\n[Exit Signal]")
        exit_count = result_df["exit_signal"].sum()
        print(f"  Total exit signals: {exit_count}/{len(result_df)}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    debug_orb_signals()
