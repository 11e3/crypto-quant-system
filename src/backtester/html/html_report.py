"""
HTML report generator for backtest results.

Generates interactive HTML reports with performance metrics,
charts, and trade statistics.
"""

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from src.backtester.html.html_report_charts import get_chart_js
from src.backtester.html.html_report_templates import (
    get_css_styles,
    get_metrics_html,
    get_trade_stats_html,
)
from src.backtester.html.html_utils import (
    calculate_monthly_returns_for_html,
    extract_config_params,
    extract_strategy_params,
    generate_risk_metrics_html,
)
from src.backtester.report_pkg.report import BacktestReport
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_html_report(
    report: BacktestReport,
    save_path: Path | str,
    strategy_obj: object = None,
    config: object = None,
    tickers: list[str] | None = None,
) -> None:
    """
    Generate HTML report from BacktestReport.

    Args:
        report: BacktestReport instance
        save_path: Path to save HTML file
        strategy_obj: Strategy instance for parameter extraction
        config: BacktestConfig instance
        tickers: List of tickers traded
    """
    save_path = Path(save_path) if isinstance(save_path, str) else save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    m = report.metrics

    # Extract strategy and config parameters
    strategy_params_html = extract_strategy_params(strategy_obj, tickers=tickers)
    config_html = extract_config_params(config, result=report, tickers=tickers)

    # Prepare chart data
    chart_data = _prepare_chart_data(report)

    # Get risk metrics HTML
    risk_metrics_html = ""
    if hasattr(report, "risk_metrics") and report.risk_metrics:
        risk_metrics_html = generate_risk_metrics_html(report.risk_metrics)

    # Build and save HTML
    html_content = _build_html(
        report=report,
        m=m,
        strategy_params_html=strategy_params_html,
        config_html=config_html,
        risk_metrics_html=risk_metrics_html,
        chart_data=chart_data,
    )

    save_path.write_text(html_content, encoding="utf-8")
    logger.info(f"HTML report saved to: {save_path}")


def _prepare_chart_data(report: BacktestReport) -> dict[str, Any]:
    """Prepare data for charts."""
    dates_list = [d.isoformat() if isinstance(d, date) else str(d) for d in report.dates]
    dates_str = "[" + ", ".join([f"'{d}'" for d in dates_list]) + "]"
    equity_values = report.equity_curve.tolist()

    # Clean drawdown values
    dd_clean = report.metrics.drawdown_curve.copy()
    dd_clean = np.where(np.isnan(dd_clean), 0.0, dd_clean)
    dd_clean = np.where(np.isinf(dd_clean), 0.0, dd_clean)
    drawdown_values = (-dd_clean).tolist()
    drawdown_values = [v if np.isfinite(v) else 0.0 for v in drawdown_values]

    # Find MDD point
    mdd_idx = int(np.argmax(dd_clean))
    mdd_date = dates_list[mdd_idx] if mdd_idx < len(dates_list) else dates_list[-1]
    mdd_value = dd_clean[mdd_idx] if mdd_idx < len(dd_clean) else report.metrics.mdd_pct

    # Monthly returns data
    monthly_returns = calculate_monthly_returns_for_html(report.equity_curve, report.dates)

    return {
        "dates_str": dates_str,
        "equity_values": equity_values,
        "drawdown_values": drawdown_values,
        "mdd_pct": report.metrics.mdd_pct,
        "mdd_date": mdd_date,
        "mdd_value": mdd_value,
        "monthly_returns": monthly_returns,
    }


def _build_html(
    report: BacktestReport,
    m: Any,
    strategy_params_html: str,
    config_html: str,
    risk_metrics_html: str,
    chart_data: dict[str, Any],
) -> str:
    """Build complete HTML document."""
    css = get_css_styles()
    metrics_html = get_metrics_html(m)
    trade_stats_html = get_trade_stats_html(m)
    chart_js = get_chart_js(
        dates_str=chart_data["dates_str"],
        equity_values=chart_data["equity_values"],
        drawdown_values=chart_data["drawdown_values"],
        mdd_pct=chart_data["mdd_pct"],
        mdd_date=chart_data["mdd_date"],
        mdd_drawdown_value=chart_data["mdd_value"],
        monthly_returns=chart_data["monthly_returns"],
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report: {report.strategy_name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <h1>Backtest Report: {report.strategy_name}</h1>
        <div class="subtitle">
            Period: {m.start_date} to {m.end_date} ({m.total_days:,} days)
        </div>

        <div class="section" style="margin-top: 20px;">
            <h2 class="section-title">Strategy Configuration</h2>
            {strategy_params_html}
            {config_html}
        </div>

        <div class="section">
            <h2 class="section-title">Performance Metrics</h2>
            {metrics_html}
        </div>

        {risk_metrics_html}

        <div class="section">
            <h2 class="section-title">Equity Curve</h2>
            <div class="chart-container"><div id="equity-chart"></div></div>
        </div>

        <div class="section">
            <h2 class="section-title">Drawdown</h2>
            <div class="chart-container"><div id="drawdown-chart"></div></div>
        </div>

        <div class="section">
            <h2 class="section-title">Monthly Returns Heatmap</h2>
            <div class="chart-container"><div id="heatmap-chart"></div></div>
        </div>

        <div class="section">
            <h2 class="section-title">Trade Statistics</h2>
            {trade_stats_html}
        </div>
    </div>
    <script>{chart_js}</script>
</body>
</html>
"""


__all__ = ["generate_html_report"]
