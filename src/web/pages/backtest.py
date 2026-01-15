"""Backtest page.

Page for backtest execution and result display.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

import numpy as np
import streamlit as st

from src.backtester.models import BacktestConfig, BacktestResult
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.web.components.sidebar.trading_config import TradingConfig
from src.web.components.charts.equity_curve import render_equity_curve
from src.web.components.charts.monthly_heatmap import render_monthly_heatmap
from src.web.components.charts.underwater import render_underwater_curve
from src.web.components.charts.yearly_bar import render_yearly_bar_chart
from src.web.components.metrics.metrics_display import (
    render_metrics_cards,
    render_statistical_significance,
)
from src.web.components.sidebar.asset_selector import render_asset_selector
from src.web.components.sidebar.date_config import render_date_config
from src.web.components.sidebar.strategy_selector import render_strategy_selector
from src.web.components.sidebar.trading_config import render_trading_config
from src.web.services.backtest_runner import run_backtest_service
from src.web.services.data_loader import get_data_files, validate_data_availability
from src.web.services.metrics_calculator import calculate_extended_metrics

logger = get_logger(__name__)

__all__ = ["render_backtest_page"]


def render_backtest_page() -> None:
    """Render backtest page (tab-based UI)."""
    st.header("📈 Backtest")

    # Create tabs: Settings and Results
    if "backtest_result" in st.session_state:
        # Show both settings and results tabs if results exist
        tab1, tab2 = st.tabs(["⚙️ Settings", "📊 Results"])
    else:
        # Show only settings tab if no results
        tab1 = st.tabs(["⚙️ Settings"])[0]
        tab2 = None

    # ===== Settings Tab =====
    with tab1:
        _render_settings_tab()

    # ===== Results Tab =====
    if tab2 is not None:
        with tab2:
            if "backtest_result" in st.session_state:
                _display_results(st.session_state.backtest_result)
            else:
                st.info("Run backtest to see results here.")


def _render_settings_tab() -> None:
    """Render settings tab."""
    st.subheader("⚙️ Backtest Settings")

    # Split settings into 3 columns
    col1, col2, col3 = st.columns([1, 1, 1])

    # ===== Column 1: Date & Trading Settings =====
    with col1:
        st.markdown("### 📅 Period Settings")
        start_date, end_date = render_date_config()

        st.markdown("### 💰 Trading Settings")
        trading_config = render_trading_config()

    # ===== Column 2: Strategy Settings =====
    with col2:
        st.markdown("### 📈 Strategy Settings")
        strategy_name, strategy_params = render_strategy_selector()

    # ===== Column 3: Asset Selection =====
    with col3:
        st.markdown("### 🪙 Asset Selection")
        selected_tickers = render_asset_selector()

    st.markdown("---")

    # Settings Summary
    with st.expander("📋 Settings Summary", expanded=False):
        _show_config_summary(strategy_name, selected_tickers, trading_config, start_date, end_date)

    # Run Button
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        run_button = st.button(
            "🚀 Run Backtest",
            type="primary",
            use_container_width=True,
            disabled=not strategy_name or not selected_tickers,
        )

    # Validation
    if not strategy_name:
        st.warning("⚠️ Please select a strategy.")
        return

    if not selected_tickers:
        st.warning("⚠️ Please select at least one asset.")
        return

    # Check data availability
    available_tickers, missing_tickers = validate_data_availability(
        selected_tickers, trading_config.interval
    )

    if missing_tickers:
        st.warning(
            f"⚠️ Missing data for the following assets: {', '.join(missing_tickers)}\n\n"
            f"Available assets: {', '.join(available_tickers) if available_tickers else 'None'}"
        )

        if not available_tickers:
            st.error("❌ No available data. Please collect data first.")
            st.code("uv run python scripts/collect_data.py")
            return

    # Run backtest
    if run_button:
        with st.spinner("Running backtest..."):
            # Create BacktestConfig
            config = BacktestConfig(
                initial_capital=trading_config.initial_capital,
                fee_rate=trading_config.fee_rate,
                slippage_rate=trading_config.slippage_rate,
                max_slots=trading_config.max_slots,
                use_cache=False,
            )

            # Get data file paths
            data_files = get_data_files(available_tickers, trading_config.interval)

            if not data_files:
                st.error("❌ Data files not found.")
                return

            # Run backtest (convert to serializable types for caching)
            data_files_dict = {ticker: str(path) for ticker, path in data_files.items()}
            config_dict = {
                "initial_capital": config.initial_capital,
                "fee_rate": config.fee_rate,
                "slippage_rate": config.slippage_rate,
                "max_slots": config.max_slots,
                "use_cache": config.use_cache,
            }
            start_date_str = start_date.isoformat() if start_date else None
            end_date_str = end_date.isoformat() if end_date else None

            result = run_backtest_service(
                strategy_name=strategy_name,
                strategy_params=strategy_params,
                data_files_dict=data_files_dict,
                config_dict=config_dict,
                start_date_str=start_date_str,
                end_date_str=end_date_str,
            )

            if result:
                st.session_state.backtest_result = result
                st.success("✅ Backtest completed! Check the '📊 Results' tab.")
                st.rerun()  # Refresh page to show results tab
            else:
                st.error("❌ Backtest execution failed")


def _show_config_summary(
    strategy_name: str,
    selected_tickers: list[str],
    trading_config: TradingConfig,
    start_date: date_type | None,
    end_date: date_type | None,
) -> None:
    """Display settings summary."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            **📈 Strategy**
            - Strategy: {strategy_name}
            - Interval: {trading_config.interval}
            """
        )

    with col2:
        st.markdown(
            f"""
            **📅 Period**
            - Start: {start_date if start_date else "All"}
            - End: {end_date if end_date else "All"}
            """
        )

    with col3:
        st.markdown(
            f"""
            **⚙️ Portfolio**
            - Initial Capital: {trading_config.initial_capital:,.0f} KRW
            - Max Slots: {trading_config.max_slots}
            - Assets: {len(selected_tickers)}
            """
        )


def _display_results(result: BacktestResult) -> None:
    """Display backtest results.

    Args:
        result: BacktestResult object
    """
    st.subheader("📊 Backtest Results")

    # Extract trade returns
    trade_returns = [t.pnl_pct / 100 for t in result.trades if t.pnl_pct is not None]

    # Calculate extended metrics (cached in session state)
    equity = np.array(result.equity_curve)
    dates = np.array(result.dates) if hasattr(result, "dates") else np.arange(len(equity))

    # Generate cache key (cache metrics by equity hash)
    cache_key = f"metrics_{hash(equity.tobytes())}"

    if cache_key not in st.session_state:
        # Calculate metrics (only once)
        st.session_state[cache_key] = calculate_extended_metrics(
            equity=equity,
            trade_returns=trade_returns,
        )

    extended_metrics = st.session_state[cache_key]

    # Tab configuration
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📈 Overview",
            "📊 Equity Curve",
            "📉 Drawdown",
            "📅 Monthly Analysis",
            "📆 Yearly Analysis",
            "🔬 Statistics",
        ]
    )

    with tab1:
        # Metrics cards
        render_metrics_cards(extended_metrics)

        # Trade history
        if result.trades:
            st.markdown("### 📋 Trade History")

            import pandas as pd

            trades_df = pd.DataFrame(
                [
                    {
                        "Ticker": t.ticker,
                        "Entry Date": str(t.entry_date),
                        "Entry Price": f"{t.entry_price:,.0f}",
                        "Exit Date": str(t.exit_date) if t.exit_date else "-",
                        "Exit Price": f"{t.exit_price:,.0f}" if t.exit_price else "-",
                        "P&L": f"{t.pnl:,.0f}",
                        "P&L %": f"{t.pnl_pct:.2f}%",
                    }
                    for t in result.trades[-100:]  # Last 100 trades only
                ]
            )

            st.dataframe(trades_df, width="stretch", height=400)

    with tab2:
        render_equity_curve(dates, equity)

    with tab3:
        render_underwater_curve(dates, equity)

    with tab4:
        render_monthly_heatmap(dates, equity)

    with tab5:
        render_yearly_bar_chart(dates, equity)

    with tab6:
        render_statistical_significance(extended_metrics)
