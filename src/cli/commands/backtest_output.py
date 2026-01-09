"""Output formatting and report generation for backtest CLI.

Handles result logging and report generation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.backtester.models import BacktestConfig, BacktestResult
    from src.strategies.base import Strategy

logger = logging.getLogger(__name__)


def log_strategy_parameters(strategy_obj: Strategy) -> None:
    """Log strategy-specific parameters if available."""
    has_params = any(
        hasattr(strategy_obj, attr)
        for attr in ["sma_period", "trend_sma_period", "short_noise_period", "long_noise_period"]
    )
    if not has_params:
        return

    logger.info("--- Strategy Parameters ---")
    if hasattr(strategy_obj, "sma_period"):
        logger.info(f"SMA Period: {strategy_obj.sma_period}")
    if hasattr(strategy_obj, "trend_sma_period"):
        logger.info(f"Trend SMA Period: {strategy_obj.trend_sma_period}")
    if hasattr(strategy_obj, "short_noise_period"):
        logger.info(f"Short Noise Period: {strategy_obj.short_noise_period}")
    if hasattr(strategy_obj, "long_noise_period"):
        logger.info(f"Long Noise Period: {strategy_obj.long_noise_period}")
    if hasattr(strategy_obj, "exclude_current"):
        logger.info(f"Exclude Current: {strategy_obj.exclude_current}")
    logger.info("---------------------------")


def log_backtest_results(result: BacktestResult) -> None:
    """Log main backtest results summary."""
    logger.info("\n=== Backtest Results ===")
    period_days = (result.dates[-1] - result.dates[0]).days if len(result.dates) > 0 else 0
    logger.info(f"Period: {period_days} days")
    logger.info(f"Total Return: {result.total_return:.2f}%")
    logger.info(f"CAGR: {result.cagr:.2f}%")
    logger.info(f"MDD: {result.mdd:.2f}%")
    logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    logger.info(f"Calmar Ratio: {result.calmar_ratio:.2f}")
    logger.info(f"Trade Count: {result.total_trades}")
    logger.info(f"Win Rate: {result.win_rate:.2f}%")
    logger.info(f"Profit Factor: {result.profit_factor:.2f}")


def log_risk_metrics(result: BacktestResult) -> None:
    """Log risk metrics if available."""
    if not result.risk_metrics:
        return

    interval_str = result.interval or "day"
    period_label = {
        "day": "daily",
        "minute240": "4-hour",
        "week": "weekly",
    }.get(interval_str, interval_str)

    logger.info("\n--- Risk Metrics ---")
    logger.info(f"VaR (95%, {period_label}): {result.risk_metrics.var_95 * 100:.2f}%")
    logger.info(f"CVaR (95%, {period_label}): {result.risk_metrics.cvar_95 * 100:.2f}%")
    logger.info(f"VaR (99%, {period_label}): {result.risk_metrics.var_99 * 100:.2f}%")
    logger.info(f"CVaR (99%, {period_label}): {result.risk_metrics.cvar_99 * 100:.2f}%")
    logger.info(
        f"Portfolio Volatility (annualized): {result.risk_metrics.portfolio_volatility * 100:.2f}%"
    )

    _log_correlation_metrics(result)
    _log_position_metrics(result)

    if result.risk_metrics.portfolio_beta is not None:
        logger.info(f"Portfolio Beta: {result.risk_metrics.portfolio_beta:.2f}")


def _log_correlation_metrics(result: BacktestResult) -> None:
    """Log correlation metrics if calculated."""
    if not result.risk_metrics:
        return
    if result.risk_metrics.avg_correlation is not None and not np.isnan(
        result.risk_metrics.avg_correlation
    ):
        logger.info(f"Avg Correlation: {result.risk_metrics.avg_correlation:.3f}")
        logger.info(f"Max Correlation: {result.risk_metrics.max_correlation:.3f}")
        logger.info(f"Min Correlation: {result.risk_metrics.min_correlation:.3f}")


def _log_position_metrics(result: BacktestResult) -> None:
    """Log position concentration metrics if calculated."""
    if not result.risk_metrics:
        return
    if (
        result.risk_metrics.max_position_pct is not None
        and result.risk_metrics.max_position_pct > 0
    ):
        logger.info(f"Max Position %: {result.risk_metrics.max_position_pct * 100:.2f}%")
        logger.info(
            f"Position Concentration (HHI): {result.risk_metrics.position_concentration:.3f}"
        )


def generate_backtest_report(
    result: BacktestResult,
    output: str,
    strategy_obj: Strategy,
    config: BacktestConfig,
    ticker_list: list[str],
) -> None:
    """Generate and save backtest report.

    Args:
        result: Backtest result object
        output: Output path or "True" for auto-generated filename
        strategy_obj: Strategy object for report
        config: Backtest configuration
        ticker_list: List of tickers
    """
    from src.backtester.report_pkg.report import generate_report

    # If output is "True" or empty, auto-generate filename
    if output == "True" or output == "":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name_safe = result.strategy_name.replace(" ", "_").lower()
        save_path = Path(f"reports/{timestamp}_{strategy_name_safe}.html")
    else:
        save_path = Path(output)

    # Ensure reports directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine format from extension (default to HTML)
    format_type = _get_format_type(save_path)
    if not save_path.suffix:
        save_path = save_path.with_suffix(".html")

    generate_report(
        result,
        save_path=save_path,
        show=False,
        format=format_type,
        strategy_obj=strategy_obj,
        config=config,
        tickers=ticker_list,
    )
    logger.info(f"\nReport saved to: {save_path}")


def _get_format_type(save_path: Path) -> str:
    """Determine format type from file extension."""
    suffix = save_path.suffix.lower()
    if suffix in [".html", ".htm"]:
        return "html"
    elif suffix in [".png", ".jpg", ".jpeg"]:
        return "png"
    return "html"


__all__ = [
    "log_strategy_parameters",
    "log_backtest_results",
    "log_risk_metrics",
    "generate_backtest_report",
]
