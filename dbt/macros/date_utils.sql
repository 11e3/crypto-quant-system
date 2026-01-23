-- Date utility macros for crypto analytics

{% macro trading_date_filter(column_name, start_date=none, end_date=none) %}
    {#
    Filter data by trading date range.

    Args:
        column_name: Date column to filter
        start_date: Start date (default: var('start_date'))
        end_date: End date (default: current_date)
    #}

    {% set start = start_date or var('start_date') %}
    {% set end = end_date or 'current_date' %}

    {{ column_name }} >= '{{ start }}'
    and {{ column_name }} <= {{ end }}

{% endmacro %}


{% macro kst_to_utc(timestamp_column) %}
    {#
    Convert KST timestamp to UTC.
    KST = UTC + 9 hours
    #}

    {{ timestamp_column }} - interval '9 hours'

{% endmacro %}


{% macro utc_to_kst(timestamp_column) %}
    {#
    Convert UTC timestamp to KST.
    KST = UTC + 9 hours
    #}

    {{ timestamp_column }} + interval '9 hours'

{% endmacro %}


{% macro trading_week(date_column) %}
    {#
    Get trading week number (Monday start).
    #}

    date_trunc('week', {{ date_column }})

{% endmacro %}
