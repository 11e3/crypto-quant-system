"""Metrics display component.

Extended metrics card and table display.
"""

import streamlit as st

from src.web.services.metrics_calculator import ExtendedMetrics

__all__ = ["render_metrics_cards", "render_metrics_table"]


def _format_value(value: float, suffix: str = "", precision: int = 2) -> str:
    """Format value."""
    if value == float("inf"):
        return "∞"
    if value == float("-inf"):
        return "-∞"
    return f"{value:.{precision}f}{suffix}"


def render_metrics_cards(metrics: ExtendedMetrics) -> None:
    """Render metrics cards.

    Display key metrics in card format.

    Args:
        metrics: Extended metrics data
    """
    st.subheader("📈 Performance Summary")

    # Row 1: Basic return metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Return",
            _format_value(metrics.total_return_pct, "%"),
            delta=None,
        )
    with col2:
        st.metric(
            "CAGR",
            _format_value(metrics.cagr_pct, "%"),
        )
    with col3:
        st.metric(
            "MDD",
            _format_value(metrics.max_drawdown_pct, "%"),
        )
    with col4:
        st.metric(
            "Volatility (Annual)",
            _format_value(metrics.volatility_pct, "%"),
        )

    # Row 2: Risk-adjusted returns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sharpe Ratio", _format_value(metrics.sharpe_ratio))
    with col2:
        st.metric("Sortino Ratio", _format_value(metrics.sortino_ratio))
    with col3:
        st.metric("Calmar Ratio", _format_value(metrics.calmar_ratio))
    with col4:
        st.metric("Trades", str(metrics.num_trades))

    # Row 3: VaR & CVaR
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VaR (95%)", _format_value(metrics.var_95_pct, "%"))
    with col2:
        st.metric("VaR (99%)", _format_value(metrics.var_99_pct, "%"))
    with col3:
        st.metric("CVaR (95%)", _format_value(metrics.cvar_95_pct, "%"))
    with col4:
        st.metric("CVaR (99%)", _format_value(metrics.cvar_99_pct, "%"))

    # Row 4: Trading metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Win Rate", _format_value(metrics.win_rate_pct, "%", 1))
    with col2:
        st.metric("Avg Win", _format_value(metrics.avg_win_pct, "%"))
    with col3:
        st.metric("Avg Loss", _format_value(metrics.avg_loss_pct, "%"))
    with col4:
        st.metric("Profit Factor", _format_value(metrics.profit_factor))

    # Row 5: Statistical metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Z-Score", _format_value(metrics.z_score))
    with col2:
        # P-value color indicator
        p_val = metrics.p_value
        significance = "✅" if p_val < 0.05 else "⚠️" if p_val < 0.1 else "❌"
        st.metric("P-Value", f"{significance} {p_val:.4f}")
    with col3:
        st.metric("Skewness", _format_value(metrics.skewness))
    with col4:
        st.metric("Kurtosis", _format_value(metrics.kurtosis))

    # Row 6: Volatility and period
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Upside Volatility", _format_value(metrics.upside_volatility_pct, "%"))
    with col2:
        st.metric("Downside Volatility", _format_value(metrics.downside_volatility_pct, "%"))
    with col3:
        st.metric("Trading Days", str(metrics.trading_days))
    with col4:
        st.metric("Period", _format_value(metrics.years, " years", 1))


def render_metrics_table(metrics: ExtendedMetrics) -> None:
    """Render metrics table.

    Display all metrics in table format.

    Args:
        metrics: Extended metrics data
    """
    st.subheader("📊 Detailed Metrics")

    # Group metrics by category
    categories = {
        "📈 Return Metrics": [
            ("Total Return", _format_value(metrics.total_return_pct, "%")),
            ("CAGR", _format_value(metrics.cagr_pct, "%")),
            ("Expectancy", _format_value(metrics.expectancy, "%")),
        ],
        "📉 Risk Metrics": [
            ("Maximum Drawdown (MDD)", _format_value(metrics.max_drawdown_pct, "%")),
            ("Volatility (Annual)", _format_value(metrics.volatility_pct, "%")),
            ("Upside Volatility", _format_value(metrics.upside_volatility_pct, "%")),
            ("Downside Volatility", _format_value(metrics.downside_volatility_pct, "%")),
        ],
        "⚖️ Risk-Adjusted Returns": [
            ("Sharpe Ratio", _format_value(metrics.sharpe_ratio)),
            ("Sortino Ratio", _format_value(metrics.sortino_ratio)),
            ("Calmar Ratio", _format_value(metrics.calmar_ratio)),
        ],
        "🎯 VaR & CVaR": [
            ("VaR (95%)", _format_value(metrics.var_95_pct, "%")),
            ("VaR (99%)", _format_value(metrics.var_99_pct, "%")),
            ("CVaR (95%)", _format_value(metrics.cvar_95_pct, "%")),
            ("CVaR (99%)", _format_value(metrics.cvar_99_pct, "%")),
        ],
        "🔢 Statistical Analysis": [
            ("Z-Score", _format_value(metrics.z_score)),
            ("P-Value", f"{metrics.p_value:.6f}"),
            ("Skewness", _format_value(metrics.skewness)),
            ("Kurtosis", _format_value(metrics.kurtosis)),
        ],
        "💹 Trading Metrics": [
            ("Number of Trades", str(metrics.num_trades)),
            ("Win Rate", _format_value(metrics.win_rate_pct, "%", 1)),
            ("Average Win", _format_value(metrics.avg_win_pct, "%")),
            ("Average Loss", _format_value(metrics.avg_loss_pct, "%")),
            ("Profit Factor", _format_value(metrics.profit_factor)),
        ],
        "📅 Period Information": [
            ("Trading Days", str(metrics.trading_days)),
            ("Period (years)", _format_value(metrics.years, "", 2)),
        ],
    }

    # 2-column layout
    col1, col2 = st.columns(2)

    category_items = list(categories.items())
    for i, (category, items) in enumerate(category_items):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            st.markdown(f"**{category}**")
            for name, value in items:
                st.markdown(f"- {name}: **{value}**")
            st.markdown("---")


def render_statistical_significance(metrics: ExtendedMetrics) -> None:
    """Render statistical significance interpretation.

    Args:
        metrics: Extended metrics data
    """
    st.subheader("🔬 Statistical Significance Analysis")

    p_value = metrics.p_value
    z_score = metrics.z_score

    # Determine significance level
    if p_value < 0.01:
        significance = "Highly Significant (p < 0.01)"
        icon = "✅"
    elif p_value < 0.05:
        significance = "Significant (p < 0.05)"
        icon = "✅"
    elif p_value < 0.1:
        significance = "Weakly Significant (p < 0.10)"
        icon = "⚠️"
    else:
        significance = "Not Significant (p ≥ 0.10)"
        icon = "❌"

    st.markdown(f"""
    ### {icon} Result: {significance}

    | Metric | Value | Interpretation |
    |--------|-------|----------------|
    | Z-Score | {z_score:.4f} | {"Positive excess return" if z_score > 0 else "Negative excess return"} |
    | P-Value | {p_value:.6f} | Null hypothesis rejection {"possible" if p_value < 0.05 else "not possible"} |
    | Skewness | {metrics.skewness:.4f} | {"Right tail (positive)" if metrics.skewness > 0 else "Left tail (negative)"} |
    | Kurtosis | {metrics.kurtosis:.4f} | {"Fat tail (increased risk)" if metrics.kurtosis > 0 else "Thin tail"} |
    """)

    # Interpretation guide
    with st.expander("📖 Interpretation Guide"):
        st.markdown("""
        **Z-Score**: Measures how many standard deviations the average return is from zero
        - |Z| > 1.96: Significant at 95% confidence level
        - |Z| > 2.58: Significant at 99% confidence level

        **P-Value**: Probability of observing the result under the null hypothesis (return=0)
        - p < 0.05: Statistically significant returns
        - p < 0.01: Very strong evidence

        **Skewness**: Asymmetry of the return distribution
        - Positive: Large gains more common than large losses (desirable)
        - Negative: Large losses more common than large gains (risky)

        **Kurtosis**: Thickness of distribution tails
        - Positive: Fat tail (extreme events frequent)
        - Negative: Thin tail (extreme events rare)
        """)
