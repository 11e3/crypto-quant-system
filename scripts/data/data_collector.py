"""
Script entry point for Upbit data collection.

This script uses the UpbitDataCollector from src.data.collector.
"""

from src.data.collector import Interval, UpbitDataCollector
from src.utils.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main() -> None:
    """Main entry point for data collection."""
    # Default tickers and intervals
    tickers = [
        "KRW-BTC",
        "KRW-ETH",
        "KRW-XRP",
        "KRW-SOL",
        "KRW-DOGE",
        "KRW-TRX",
    ]

    intervals: list[Interval] = ["minute240", "day", "week"]

    collector = UpbitDataCollector()

    logger.info("Starting Upbit data collection...")
    logger.info(f"Tickers: {tickers}")
    logger.info(f"Intervals: {intervals}")

    results = collector.collect_multiple(tickers, intervals)

    # Summary
    logger.info("\n=== Collection Summary ===")
    total_new = 0
    for key, count in results.items():
        if count >= 0:
            logger.info(f"  {key}: +{count} candles")
            total_new += count
        else:
            logger.warning(f"  {key}: FAILED")

    logger.info(f"\nTotal new candles: {total_new}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
