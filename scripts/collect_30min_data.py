"""Collect 30-minute candle data for ORB strategy."""

import pyupbit

from src.config import PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Collect 30-minute data for 4 assets."""
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {PROCESSED_DATA_DIR}")

    for ticker in tickers:
        print(f"Collecting {ticker} 30-minute data...")

        # Collect max candles (200 per request, so need multiple requests)
        df = pyupbit.get_ohlcv(ticker, interval="minute30", count=50000)

        if df is None or df.empty:
            print(f"  ✗ Failed to collect {ticker}")
            continue

        # Save to parquet
        filepath = PROCESSED_DATA_DIR / f"{ticker}_minute30.parquet"
        df.to_parquet(filepath)

        print(f"  ✓ {ticker}: {len(df)} candles → {filepath.name}")

    print("\nAll 30-minute data collected successfully!")


if __name__ == "__main__":
    main()
