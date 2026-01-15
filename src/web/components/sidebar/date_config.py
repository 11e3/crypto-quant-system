"""Date configuration component.

UI component for selecting start and end dates.
"""

from datetime import date, timedelta

import streamlit as st

__all__ = ["render_date_config"]


def render_date_config() -> tuple[date, date]:
    """Render date range selection UI.

    Returns:
        (start_date, end_date) tuple
    """
    st.subheader("📅 Period Configuration")

    # Default: Last 1 year
    default_end = date.today()
    default_start = default_end - timedelta(days=365)

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=date(2017, 1, 1),  # Upbit start date
            max_value=default_end,
            help="Backtest start date (Upbit: 2017 onwards)",
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=default_end,
            min_value=start_date,
            max_value=date.today(),
            help="Backtest end date",
        )

    # Validation
    if start_date >= end_date:
        st.error("⚠️ Start date must be before end date.")
        return default_start, default_end

    # Display period
    days_diff = (end_date - start_date).days
    st.caption(f"📊 Backtest period: **{days_diff:,} days** ({start_date} ~ {end_date})")

    return start_date, end_date
