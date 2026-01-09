"""
Report generation subpackage for backtesting.

Contains modules for generating backtest reports, charts, and metrics.
"""

from src.backtester.report_pkg.report import (
    BacktestReport,
    PerformanceMetrics,
    generate_report,
)
from src.backtester.report_pkg.report_charts import (
    plot_drawdown,
    plot_equity_curve,
    plot_monthly_heatmap,
)
from src.backtester.report_pkg.report_metrics import calculate_metrics

__all__ = [
    "BacktestReport",
    "PerformanceMetrics",
    "generate_report",
    "plot_equity_curve",
    "plot_drawdown",
    "plot_monthly_heatmap",
    "calculate_metrics",
]
