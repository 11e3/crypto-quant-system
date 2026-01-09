"""
HTML generation for risk metrics section.
"""

import numpy as np

from src.risk.metrics import PortfolioRiskMetrics


def generate_risk_metrics_html(risk_metrics: PortfolioRiskMetrics | None) -> str:
    """Generate HTML for risk metrics section."""
    if not risk_metrics:
        return ""

    html = f"""
        <div class="section">
            <h2 class="section-title">Risk Metrics</h2>
            <div class="risk-section">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">VaR (95%)</div>
                        <div class="metric-value negative">
                            {risk_metrics.var_95 * 100:.2f}%
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">CVaR (95%)</div>
                        <div class="metric-value negative">
                            {risk_metrics.cvar_95 * 100:.2f}%
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">VaR (99%)</div>
                        <div class="metric-value negative">
                            {risk_metrics.var_99 * 100:.2f}%
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">CVaR (99%)</div>
                        <div class="metric-value negative">
                            {risk_metrics.cvar_99 * 100:.2f}%
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Portfolio Volatility</div>
                        <div class="metric-value">
                            {risk_metrics.portfolio_volatility * 100:.2f}%
                        </div>
                    </div>
    """

    html += _generate_correlation_html(risk_metrics)
    html += _generate_position_html(risk_metrics)

    html += """
                </div>
            </div>
        </div>
    """

    return html


def _generate_correlation_html(risk_metrics: PortfolioRiskMetrics) -> str:
    """Generate HTML for correlation metrics."""
    if not hasattr(risk_metrics, "avg_correlation") or risk_metrics.avg_correlation is None:
        return ""

    if np.isnan(risk_metrics.avg_correlation):
        return ""

    return f"""
                    <div class="metric-card">
                        <div class="metric-label">Avg Correlation</div>
                        <div class="metric-value">{risk_metrics.avg_correlation:.3f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Max Correlation</div>
                        <div class="metric-value">{risk_metrics.max_correlation:.3f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Min Correlation</div>
                        <div class="metric-value">{risk_metrics.min_correlation:.3f}</div>
                    </div>
    """


def _generate_position_html(risk_metrics: PortfolioRiskMetrics) -> str:
    """Generate HTML for position metrics."""
    if not hasattr(risk_metrics, "max_position_pct") or risk_metrics.max_position_pct is None:
        return ""

    if risk_metrics.max_position_pct <= 0:
        return ""

    return f"""
                    <div class="metric-card">
                        <div class="metric-label">Max Position %</div>
                        <div class="metric-value">{risk_metrics.max_position_pct * 100:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Position HHI</div>
                        <div class="metric-value">{risk_metrics.position_concentration:.3f}</div>
                    </div>
    """


__all__ = [
    "generate_risk_metrics_html",
]
