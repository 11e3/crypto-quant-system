"""
HTML report generation subpackage.

Contains modules for generating HTML backtest reports.
"""

from src.backtester.html.html_report import generate_html_report
from src.backtester.html.html_report_charts import get_chart_js
from src.backtester.html.html_returns import calculate_monthly_returns_for_html
from src.backtester.html.html_risk import generate_risk_metrics_html
from src.backtester.html.html_styles import get_report_css
from src.backtester.html.html_utils import (
    extract_config_params,
    extract_strategy_params,
)

__all__ = [
    "generate_html_report",
    "get_chart_js",
    "calculate_monthly_returns_for_html",
    "generate_risk_metrics_html",
    "get_report_css",
    "extract_config_params",
    "extract_strategy_params",
]
