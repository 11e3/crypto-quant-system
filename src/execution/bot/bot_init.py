"""Bot initialization and configuration logic."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.config.loader import get_config
from src.exchange import Exchange, ExchangeFactory
from src.execution.event_bus import get_event_bus
from src.execution.handlers.notification_handler import NotificationHandler
from src.execution.handlers.trade_handler import TradeHandler
from src.execution.order_manager import OrderManager
from src.execution.orders.advanced_orders import AdvancedOrderManager
from src.execution.position_manager import PositionManager
from src.execution.signal_handler import SignalHandler
from src.strategies.volatility_breakout import VanillaVBO
from src.utils.logger import get_logger
from src.utils.telegram import TelegramNotifier, get_notifier

if TYPE_CHECKING:
    from src.execution.event_bus import EventBus

logger = get_logger(__name__)

# Constants
MIN_DATA_POINTS = 10
API_RETRY_ATTEMPTS = 3

__all__ = [
    "BotComponents",
    "create_bot_components",
    "initialize_targets",
    "check_existing_holdings",
]


class BotComponents:
    """Container for bot components."""

    def __init__(
        self,
        exchange: Exchange,
        position_manager: PositionManager,
        order_manager: OrderManager,
        signal_handler: SignalHandler,
        strategy: VanillaVBO,
        advanced_order_manager: AdvancedOrderManager,
        telegram: TelegramNotifier,
        trade_handler: TradeHandler,
        notification_handler: NotificationHandler,
        event_bus: EventBus,
    ) -> None:
        """Initialize bot components."""
        self.exchange = exchange
        self.position_manager = position_manager
        self.order_manager = order_manager
        self.signal_handler = signal_handler
        self.strategy = strategy
        self.advanced_order_manager = advanced_order_manager
        self.telegram = telegram
        self.trade_handler = trade_handler
        self.notification_handler = notification_handler
        self.event_bus = event_bus


def create_bot_components(
    config_path: Path | None = None,
    exchange: Exchange | None = None,
    position_manager: PositionManager | None = None,
    order_manager: OrderManager | None = None,
    signal_handler: SignalHandler | None = None,
    strategy: VanillaVBO | None = None,
) -> tuple[BotComponents, dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    """
    Create and initialize bot components.

    Args:
        config_path: Path to configuration file
        exchange: Optional exchange instance for dependency injection
        position_manager: Optional position manager for DI
        order_manager: Optional order manager for DI
        signal_handler: Optional signal handler for DI
        strategy: Optional strategy for DI

    Returns:
        Tuple of (components, trading_config, strategy_config, bot_config, tickers)
    """
    config = get_config(config_path)
    trading_config = config.get_trading_config()
    strategy_config = config.get_strategy_config()
    bot_config = config.get_bot_config()

    # Initialize Exchange
    if exchange is None:
        exchange_name = config.get_exchange_name()
        exchange = ExchangeFactory.create(exchange_name)

    # Initialize Telegram
    telegram_config = config.get_telegram_config()
    telegram = get_notifier(
        token=telegram_config["token"],
        chat_id=telegram_config["chat_id"],
        enabled=telegram_config["enabled"],
    )

    # Initialize Strategy
    if strategy is None:
        strategy = VanillaVBO(
            name=strategy_config["name"],
            sma_period=strategy_config["sma_period"],
            trend_sma_period=strategy_config["trend_sma_period"],
            short_noise_period=strategy_config["short_noise_period"],
            long_noise_period=strategy_config["long_noise_period"],
            exclude_current=strategy_config.get("exclude_current", True),
        )

    # Initialize event bus and handlers
    event_bus = get_event_bus()
    trade_handler = TradeHandler()
    notification_handler = NotificationHandler(telegram)

    # Initialize Managers
    if position_manager is None:
        position_manager = PositionManager(exchange, publish_events=True)

    if order_manager is None:
        order_manager = OrderManager(exchange, publish_events=True)

    if signal_handler is None:
        signal_handler = SignalHandler(
            strategy=strategy,
            exchange=exchange,
            min_data_points=MIN_DATA_POINTS,
            publish_events=True,
        )

    advanced_order_manager = AdvancedOrderManager()

    components = BotComponents(
        exchange=exchange,
        position_manager=position_manager,
        order_manager=order_manager,
        signal_handler=signal_handler,
        strategy=strategy,
        advanced_order_manager=advanced_order_manager,
        telegram=telegram,
        trade_handler=trade_handler,
        notification_handler=notification_handler,
        event_bus=event_bus,
    )

    tickers = trading_config["tickers"]

    return components, trading_config, strategy_config, bot_config, tickers


def initialize_targets(
    tickers: list[str],
    signal_handler: SignalHandler,
    strategy_config: dict[str, Any],
    bot_config: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """
    Initialize target prices and metrics for all tickers.

    Args:
        tickers: List of trading pair tickers
        signal_handler: Signal handler instance
        strategy_config: Strategy configuration
        bot_config: Bot configuration

    Returns:
        Dictionary of ticker -> metrics
    """
    logger.info("Initializing targets...")
    target_info: dict[str, dict[str, float]] = {}
    required_period = strategy_config["trend_sma_period"]

    for ticker in tickers:
        for attempt in range(API_RETRY_ATTEMPTS):
            metrics = signal_handler.calculate_metrics(ticker, required_period)
            if metrics:
                target_info[ticker] = metrics
                logger.info(
                    f"[{ticker}] Target: {metrics['target']:.0f} | "
                    f"K: {metrics['k']:.2f} vs Base: {metrics['long_noise']:.2f} | "
                    f"SMA: {metrics['sma']:.0f} Trend: {metrics['sma_trend']:.0f}"
                )
                break
            if attempt < API_RETRY_ATTEMPTS - 1:
                time.sleep(bot_config["api_retry_delay"])

    return target_info


def check_existing_holdings(
    tickers: list[str],
    exchange: Exchange,
    position_manager: PositionManager,
    trading_config: dict[str, Any],
) -> None:
    """Check and recover existing holdings on bot restart."""
    logger.info("Checking existing holdings...")
    min_amount = trading_config["min_order_amount"]

    for ticker in tickers:
        try:
            currency = ticker.split("-")[1]
            balance = exchange.get_balance(currency)
            curr_price = exchange.get_current_price(ticker)

            if (
                balance.available > 0
                and curr_price > 0
                and (balance.available * curr_price > min_amount)
            ):
                position_manager.add_position(
                    ticker=ticker,
                    entry_price=curr_price,
                    amount=balance.available,
                )
                logger.info(f"✅ Recovered: Holding {ticker}")
        except Exception as e:
            logger.error(f"Error checking holdings for {ticker}: {e}", exc_info=True)
