"""
Example: ORB Strategy Backtest

Demonstrates ATR-based Opening Range Breakout strategy with:
- Multiple assets (BTC, ETH, XRP, TRX)
- 4-hour (minute240) timeframe
- Volatility-targeted position sizing
- ATR-based trailing stops
- EventDrivenBacktestEngine for clear trade execution
"""

from datetime import date

from src.backtester.engine import EventDrivenBacktestEngine
from src.backtester.models import BacktestConfig
from src.config import RAW_DATA_DIR
from src.strategies.opening_range_breakout.orb import ORBStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run ORB strategy backtest."""
    logger.info("=" * 80)
    logger.info("ORB Strategy Backtest - EventDrivenBacktestEngine")
    logger.info("=" * 80)

    # Asset universe
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]

    # Build file paths
    data_files = {}
    for ticker in tickers:
        filepath = RAW_DATA_DIR / f"{ticker}_minute30.parquet"
        if filepath.exists():
            data_files[ticker] = filepath
            logger.info(f"Data file found: {ticker}")
        else:
            logger.warning(f"Data file not found: {filepath}")

    if not data_files:
        logger.error("No data files found. Please collect data first.")
        return

    # Create strategy - ATR-based breakout
    strategy = ORBStrategy(
        breakout_mode="atr",
        k_multiplier=0.5,  # Breakout at open + 0.5 * ATR
        atr_window=14,
        atr_multiplier=2.0,  # Trailing stop at 2 * ATR
        vol_target=0.02,  # Target 2% volatility per position
        noise_window=5,
        noise_threshold=0.5,
        sma_window=20,
        trend_price="open",
        atr_slippage=0.1,  # 0.1 * ATR slippage
    )

    logger.info(f"\nStrategy: {strategy.name}")
    logger.info(f"Breakout Mode: {strategy.breakout_mode}")
    logger.info(f"K Multiplier: {strategy.k_multiplier}")
    logger.info(f"ATR Window: {strategy.atr_window}")

    # Backtest configuration
    config = BacktestConfig(
        initial_capital=10_000_000.0,  # 10M KRW
        fee_rate=0.0005,  # 0.05%
        slippage_rate=0.0005,  # 0.05%
        max_slots=len(data_files),  # One slot per asset
        trailing_stop_pct=0.05,  # 5% trailing stop
    )

    logger.info("\nBacktest Config:")
    logger.info(f"  Initial Capital: {config.initial_capital:,.0f}")
    logger.info(f"  Fee Rate: {config.fee_rate:.2%}")
    logger.info(f"  Max Slots: {config.max_slots}")

    # Run backtest with EventDrivenBacktestEngine
    logger.info(f"\nRunning backtest with {len(data_files)} assets...")
    engine = EventDrivenBacktestEngine(config)

    result = engine.run(
        strategy=strategy,
        data_files=data_files,
        start_date=date(2023, 3, 1),
        end_date=None,
    )

    # Print results
    logger.info("\n" + "=" * 80)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 80)
    logger.info(result.summary())

    # Trade details
    if result.trades:
        logger.info(f"\nTotal Trades: {len(result.trades)}")
        logger.info("First 5 trades:")
        for i, trade in enumerate(result.trades[:5], 1):
            logger.info(
                f"  {i}. {trade.ticker} {trade.entry_date} -> {trade.exit_date}: "
                f"{trade.pnl_pct:+.2f}% ({trade.exit_reason})"
            )

    logger.info("\n✓ ORB backtest completed!")


if __name__ == "__main__":
    main()
