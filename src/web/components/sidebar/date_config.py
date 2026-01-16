"""Date configuration component.

UI component for selecting start and end dates.
"""

from datetime import date

import streamlit as st

from src.web.services.data_loader import get_data_date_range

__all__ = ["render_date_config"]


def render_date_config() -> tuple[date, date]:
    """Render date range selection UI.

    Returns:
        (start_date, end_date) tuple
    """
    st.subheader("📅 Period Configuration")

    # Get data date range for default values
    data_start, data_end = get_data_date_range("day")

    # Default: Full data range (or fallback to 2018-01-01 ~ today)
    default_start = data_start if data_start else date(2018, 1, 1)
    default_end = data_end if data_end else date.today()

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
