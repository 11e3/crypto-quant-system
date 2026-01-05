"""
Trading bot for live execution using VBO strategy.

Uses configuration from config/settings.yaml and strategy from src/strategies/.

NOTE: This module is being refactored. For new code, use TradingBotFacade from bot_facade.py.
This module will be deprecated in favor of the facade pattern.
"""

import contextlib
import datetime
import time
from pathlib import Path

import pandas as pd
import pyupbit

from src.config.loader import get_config
from src.exchange import Exchange, UpbitExchange
from src.execution.order_manager import OrderManager
from src.execution.position_manager import PositionManager
from src.execution.signal_handler import SignalHandler
from src.strategies.volatility_breakout import VanillaVBO
from src.utils.logger import get_logger, setup_logging
from src.utils.telegram import get_notifier

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Constants
YESTERDAY_INDEX = -2  # Yesterday's confirmed candle (excluding today's incomplete)
MIN_DATA_POINTS = 10  # Minimum data points for reliable calculations
SMA_EXIT_PERIOD = 5  # SMA period for exit condition
API_RETRY_ATTEMPTS = 3  # Number of retry attempts for API calls
DAILY_RESET_WINDOW_SECONDS = 10  # Window for daily reset trigger


class TradingBot:
    """
    Trading bot using VBO strategy.

    .. deprecated:: 0.1.0
        Use :class:`TradingBotFacade` from :mod:`src.execution.bot_facade` instead.
        This class will be removed in a future version.

    .. warning::
        This class is deprecated. For new code, use :class:`TradingBotFacade`.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize trading bot.

        Args:
            config_path: Path to config file (defaults to config/settings.yaml)

        Raises:
            ValueError: If Upbit API keys are not configured
        """
        self.config = get_config(config_path)
        self.trading_config = self.config.get_trading_config()
        self.strategy_config = self.config.get_strategy_config()
        self.bot_config = self.config.get_bot_config()

        # Initialize Exchange
        access_key, secret_key = self.config.get_upbit_keys()
        if not access_key or not secret_key:
            raise ValueError(
                "Upbit API keys not found. Set UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY "
                "environment variables or configure in settings.yaml"
            )

        self.exchange: Exchange = UpbitExchange(access_key, secret_key)

        # Initialize Telegram
        telegram_config = self.config.get_telegram_config()
        self.telegram = get_notifier(
            token=telegram_config["token"],
            chat_id=telegram_config["chat_id"],
            enabled=telegram_config["enabled"],
        )

        # Initialize strategy
        self.strategy = VanillaVBO(
            name=self.strategy_config["name"],
            sma_period=self.strategy_config["sma_period"],
            trend_sma_period=self.strategy_config["trend_sma_period"],
            short_noise_period=self.strategy_config["short_noise_period"],
            long_noise_period=self.strategy_config["long_noise_period"],
            exclude_current=self.strategy_config.get("exclude_current", True),
        )

        # Initialize managers
        self.position_manager = PositionManager(self.exchange)
        self.order_manager = OrderManager(self.exchange)
        self.signal_handler = SignalHandler(
            strategy=self.strategy,
            exchange=self.exchange,
            min_data_points=MIN_DATA_POINTS,
        )

        # Position tracking (for backward compatibility during transition)
        self.tickers = self.trading_config["tickers"]
        self.target_info: dict[str, dict[str, float]] = {}  # Stores calculated metrics per ticker

    def get_krw_balance(self) -> float:
        """Get KRW balance."""
        try:
            balance = self.exchange.get_balance("KRW")
            return balance.available
        except Exception as e:
            logger.error(f"Error getting KRW balance: {e}", exc_info=True)
            return 0.0

    def sell_all(self, ticker: str) -> bool:
        """
        Sell all holdings for a ticker.

        Args:
            ticker: Trading pair ticker

        Returns:
            True if sold successfully
        """
        try:
            min_amount = self.trading_config["min_order_amount"]
            order = self.order_manager.sell_all(ticker, min_amount)

            if order and order.order_id:
                # Get current price for notification
                try:
                    curr_price = self.exchange.get_current_price(ticker)
                    currency = ticker.split("-")[1]
                    balance = self.exchange.get_balance(currency)
                    self.telegram.send_trade_signal(
                        "SELL",
                        ticker,
                        curr_price,
                        amount=balance.available,
                    )
                except Exception:
                    pass  # Notification is optional

                # Remove position
                self.position_manager.remove_position(ticker)
                logger.info(f"Sold all {ticker}")
                return True
        except Exception as e:
            logger.error(f"Sell error for {ticker}: {e}", exc_info=True)
        return False

    def _calculate_sma_exit(self, df: pd.DataFrame) -> float | None:
        """
        Calculate SMA for exit condition.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            SMA value or None if insufficient data
        """
        if df is None or len(df) < SMA_EXIT_PERIOD + 2:
            return None

        # Calculate SMA using last 5 days before yesterday
        # iloc[-7:-2] means last 7 to last 2 (5 days)
        sma_period = SMA_EXIT_PERIOD
        start_idx = -(sma_period + 2)
        end_idx = YESTERDAY_INDEX
        return float(df["close"].iloc[start_idx:end_idx].mean())

    def check_exit_conditions(self, ticker: str) -> bool:
        """
        Check if exit conditions are met for a ticker using signal handler.

        Args:
            ticker: Trading pair ticker

        Returns:
            True if should exit
        """
        return self.signal_handler.check_exit_signal(ticker)

    def check_entry_conditions(self, ticker: str, current_price: float) -> bool:
        """
        Check if entry conditions are met using signal handler.

        Args:
            ticker: Trading pair ticker
            current_price: Current market price

        Returns:
            True if entry conditions are met
        """
        metrics = self.target_info.get(ticker)
        target_price = metrics.get("target") if metrics else None
        return self.signal_handler.check_entry_signal(ticker, current_price, target_price)

    def initialize_targets(self) -> None:
        """Initialize target prices and metrics for all tickers."""
        logger.info("Initializing targets...")
        required_period = self.strategy_config["trend_sma_period"]

        for ticker in self.tickers:
            for attempt in range(API_RETRY_ATTEMPTS):
                metrics = self.signal_handler.calculate_metrics(ticker, required_period)
                if metrics:
                    self.target_info[ticker] = metrics
                    logger.info(
                        f"[{ticker}] Target: {metrics['target']:.0f} | "
                        f"K: {metrics['k']:.2f} vs Base: {metrics['long_noise']:.2f} | "
                        f"SMA: {metrics['sma']:.0f} Trend: {metrics['sma_trend']:.0f}"
                    )
                    break
                if attempt < API_RETRY_ATTEMPTS - 1:
                    time.sleep(self.bot_config["api_retry_delay"])

    def check_existing_holdings(self) -> None:
        """Check and recover existing holdings on bot restart."""
        logger.info("Checking existing holdings...")
        min_amount = self.trading_config["min_order_amount"]

        for ticker in self.tickers:
            try:
                currency = ticker.split("-")[1]
                balance = self.exchange.get_balance(currency)
                curr_price = self.exchange.get_current_price(ticker)

                if (
                    balance.available > 0
                    and curr_price > 0
                    and (balance.available * curr_price > min_amount)
                ):
                    # Recover position
                    self.position_manager.add_position(
                        ticker=ticker,
                        entry_price=curr_price,  # Use current price as approximation
                        amount=balance.available,
                    )
                    logger.info(f"✅ Recovered: Holding {ticker}")
            except Exception as e:
                logger.error(f"Error checking holdings for {ticker}: {e}", exc_info=True)

    def _process_exits(self) -> None:
        """Process exit conditions for all held positions."""
        positions = self.position_manager.get_all_positions()

        for ticker in positions:
            if self.check_exit_conditions(ticker):
                if self.sell_all(ticker):
                    # Send exit notification with details
                    try:
                        df = self.signal_handler.get_ohlcv_data(ticker, count=MIN_DATA_POINTS)
                        if df is not None:
                            df = self.strategy.calculate_indicators(df)
                            yesterday_close = float(df.iloc[YESTERDAY_INDEX]["close"])
                            sma_exit = self._calculate_sma_exit(df)
                            if sma_exit is not None:
                                self.telegram.send_trade_signal(
                                    "EXIT",
                                    ticker,
                                    yesterday_close,
                                    reason=f"Close {yesterday_close:.0f} < SMA {sma_exit:.0f}",
                                )
                    except Exception as e:
                        logger.error(
                            f"Error sending exit notification for {ticker}: {e}", exc_info=True
                        )
            else:
                self.telegram.send_trade_signal("HOLD", ticker, 0)

    def _recalculate_targets(self) -> None:
        """Recalculate target prices and metrics for all tickers."""
        self.target_info = {}
        msg = "[DAILY UPDATE]\n"
        required_period = self.strategy_config["trend_sma_period"]

        for ticker in self.tickers:
            for attempt in range(API_RETRY_ATTEMPTS):
                metrics = self.signal_handler.calculate_metrics(ticker, required_period)
                if metrics:
                    self.target_info[ticker] = metrics
                    msg += f"{ticker}: Target {metrics['target']:.0f}, K {metrics['k']:.2f}\n"
                    break
                if attempt < API_RETRY_ATTEMPTS - 1:
                    time.sleep(self.bot_config["api_retry_delay"])

        self.telegram.send(msg)
        logger.info(msg)

    def daily_reset(self) -> None:
        """Perform daily reset: check exits and recalculate targets."""
        logger.info("Performing daily reset...")
        self._process_exits()
        self._recalculate_targets()

    def _calculate_buy_amount(self) -> float:
        """
        Calculate buy amount based on available cash and slots.

        Returns:
            Buy amount in KRW, 0.0 if insufficient funds
        """
        krw_bal = self.get_krw_balance()
        min_amount = self.trading_config["min_order_amount"]

        if krw_bal <= min_amount:
            return 0.0

        current_positions = self.position_manager.get_position_count()
        max_slots = self.trading_config["max_slots"]
        available_slots = max_slots - current_positions

        if available_slots <= 0:
            return 0.0

        fee_rate = self.trading_config["fee_rate"]
        buy_amount = (krw_bal / available_slots) * (1 - fee_rate)

        return buy_amount if buy_amount > min_amount else 0.0

    def _execute_buy_order(self, ticker: str, current_price: float, buy_amount: float) -> bool:
        """
        Execute buy market order.

        Args:
            ticker: Trading pair ticker
            current_price: Current market price
            buy_amount: Amount to buy in KRW

        Returns:
            True if order executed successfully
        """
        try:
            min_amount = self.trading_config["min_order_amount"]
            order = self.order_manager.place_buy_order(ticker, buy_amount, min_amount)

            if order and order.order_id:
                # Add position (approximate amount will be updated when order fills)
                # For now, estimate based on buy_amount / current_price
                estimated_amount = buy_amount / current_price if current_price > 0 else 0.0
                self.position_manager.add_position(
                    ticker=ticker,
                    entry_price=current_price,
                    amount=estimated_amount,
                )

                metrics = self.target_info.get(ticker, {})
                self.telegram.send_trade_signal(
                    "BUY",
                    ticker,
                    current_price,
                    target=metrics.get("target", 0),
                    noise=f"{metrics.get('k', 0):.2f} < {metrics.get('long_noise', 0):.2f}",
                )
                logger.info(
                    f"🔥 BUY {ticker} @ {current_price:.0f} | "
                    f"Target: {metrics.get('target', 0):.0f}"
                )
                return True
            else:
                logger.warning(f"Buy failed for {ticker}: order not created")
                return False
        except Exception as e:
            logger.error(f"Buy error for {ticker}: {e}", exc_info=True)
            return False

    def process_ticker_update(self, ticker: str, current_price: float) -> None:
        """
        Process real-time ticker update and check for entry signals.

        Args:
            ticker: Trading pair ticker
            current_price: Current market price
        """
        # Skip if already holding
        if self.position_manager.has_position(ticker):
            return

        # Check entry conditions
        if not self.check_entry_conditions(ticker, current_price):
            return

        # Calculate and validate buy amount
        buy_amount = self._calculate_buy_amount()
        if buy_amount <= 0:
            return

        # Execute buy order
        self._execute_buy_order(ticker, current_price, buy_amount)

    def run(self) -> None:
        """Run the trading bot main loop."""
        logger.info("Starting Trading Bot (VBO Strategy)...")

        # Test API connection
        try:
            self.exchange.get_balance("KRW")
            logger.info("SUCCESS: API Keys are valid and working.")
        except Exception as e:
            logger.error(f"!!! API CONNECTION FAILED: {e}")
            time.sleep(3)
            return

        self.telegram.send("🚀 Bot Started: VBO Strategy")

        # Initialize
        self.initialize_targets()
        self.check_existing_holdings()

        logger.info("Entering Trading Loop...")

        # WebSocket connection
        try:
            wm = pyupbit.WebSocketManager(
                "ticker", self.tickers
            )  # pragma: no cover (WebSocket, difficult to test)
        except Exception as e:
            logger.error(f"WebSocket Connection Failed: {e}")  # pragma: no cover
            return  # pragma: no cover

        while True:  # pragma: no cover (infinite loop with WebSocket, difficult to test)
            try:
                data = wm.get()  # pragma: no cover
                if data["type"] == "ticker":  # pragma: no cover
                    ticker = data["code"]  # pragma: no cover
                    current_price = data["trade_price"]  # pragma: no cover

                    now = datetime.datetime.now()  # pragma: no cover

                    # Daily reset check
                    reset_hour = self.bot_config["daily_reset_hour"]  # pragma: no cover
                    reset_minute = self.bot_config["daily_reset_minute"]  # pragma: no cover

                    if (  # pragma: no cover
                        now.hour == reset_hour
                        and now.minute == reset_minute
                        and now.second <= DAILY_RESET_WINDOW_SECONDS
                    ):
                        wm.terminate()  # pragma: no cover
                        self.daily_reset()  # pragma: no cover
                        time.sleep(6)  # Wait before reconnecting  # pragma: no cover
                        wm = pyupbit.WebSocketManager("ticker", self.tickers)  # pragma: no cover
                        continue  # pragma: no cover

                    # Process ticker update
                    self.process_ticker_update(ticker, current_price)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                logger.error(f"Loop Error: {e}", exc_info=True)  # pragma: no cover
                time.sleep(self.bot_config["websocket_reconnect_delay"])  # pragma: no cover
                with contextlib.suppress(Exception):  # pragma: no cover
                    wm.terminate()  # pragma: no cover
                wm = pyupbit.WebSocketManager("ticker", self.tickers)  # pragma: no cover


def main() -> None:  # pragma: no cover (CLI entry point, tested via integration)
    """
    Main entry point.

    .. deprecated:: 0.1.0
        Use :func:`src.execution.bot_facade.create_bot` and :meth:`TradingBotFacade.run` instead.
    """
    import warnings

    warnings.warn(
        "TradingBot.main() is deprecated. Use TradingBotFacade instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    main()
