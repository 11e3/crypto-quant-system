"""
Data Collection DAG
===================
Collects OHLCV data from Upbit exchange for configured symbols.

Schedule: Daily at 9:30 AM KST (after market opens)
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup

# Default arguments for all tasks
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}

# Symbols to collect
SYMBOLS = ["BTC", "ETH", "XRP", "TRX", "ADA", "DOGE", "SOL", "AVAX"]
INTERVALS = ["day", "minute240"]  # Daily and 4-hour data


def collect_symbol_data(symbol: str, interval: str, **context) -> dict:
    """Collect OHLCV data for a single symbol.

    Args:
        symbol: Trading symbol (e.g., 'BTC')
        interval: Candle interval ('day', 'minute240', etc.)
        context: Airflow context

    Returns:
        Dictionary with collection results
    """
    import os
    import pandas as pd
    import pyupbit

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    output_dir = data_dir / "raw" / interval
    output_dir.mkdir(parents=True, exist_ok=True)

    ticker = f"KRW-{symbol}"
    output_path = output_dir / f"{symbol}.parquet"

    # Load existing data if available
    existing_df = None
    if output_path.exists():
        existing_df = pd.read_parquet(output_path)
        last_date = existing_df.index.max()
        print(f"Existing data for {symbol}: {len(existing_df)} rows, last date: {last_date}")
    else:
        print(f"No existing data for {symbol}")

    # Fetch new data
    try:
        df = pyupbit.get_ohlcv(ticker, interval=interval, count=200)

        if df is None or df.empty:
            print(f"No data returned for {ticker}")
            return {"symbol": symbol, "status": "no_data", "rows": 0}

        # Normalize columns
        df.columns = df.columns.str.lower()
        df.index.name = "timestamp"

        # Merge with existing data
        if existing_df is not None:
            df = pd.concat([existing_df, df])
            df = df[~df.index.duplicated(keep="last")]
            df = df.sort_index()

        # Save to parquet
        df.to_parquet(output_path)

        print(f"Saved {symbol}: {len(df)} total rows")

        return {
            "symbol": symbol,
            "interval": interval,
            "status": "success",
            "total_rows": len(df),
            "new_rows": len(df) - (len(existing_df) if existing_df is not None else 0),
        }

    except Exception as e:
        print(f"Error collecting {symbol}: {e}")
        raise


def validate_collected_data(**context) -> dict:
    """Validate all collected data files.

    Returns:
        Dictionary with validation results
    """
    import os
    from pathlib import Path

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    results = {"valid": [], "invalid": [], "missing": []}

    for interval in INTERVALS:
        interval_dir = data_dir / "raw" / interval

        for symbol in SYMBOLS:
            file_path = interval_dir / f"{symbol}.parquet"

            if not file_path.exists():
                results["missing"].append(f"{symbol}_{interval}")
                continue

            try:
                import pandas as pd
                df = pd.read_parquet(file_path)

                # Basic validation
                required_cols = {"open", "high", "low", "close", "volume"}
                if not required_cols.issubset(df.columns):
                    results["invalid"].append(f"{symbol}_{interval}: missing columns")
                    continue

                # Check for NaN values
                nan_count = df[list(required_cols)].isna().sum().sum()
                if nan_count > 0:
                    print(f"Warning: {symbol}_{interval} has {nan_count} NaN values")

                results["valid"].append(f"{symbol}_{interval}")

            except Exception as e:
                results["invalid"].append(f"{symbol}_{interval}: {str(e)}")

    print(f"Validation results: {len(results['valid'])} valid, "
          f"{len(results['invalid'])} invalid, {len(results['missing'])} missing")

    return results


def send_collection_report(**context) -> None:
    """Send collection report notification."""
    ti = context["ti"]

    # Collect results from upstream tasks
    validation_result = ti.xcom_pull(task_ids="validate_data")

    report = f"""
    Data Collection Report
    =====================
    Date: {context['execution_date']}

    Validation Results:
    - Valid: {len(validation_result.get('valid', []))}
    - Invalid: {len(validation_result.get('invalid', []))}
    - Missing: {len(validation_result.get('missing', []))}

    Invalid files: {validation_result.get('invalid', [])}
    Missing files: {validation_result.get('missing', [])}
    """

    print(report)

    # TODO: Send to Telegram/Slack/Email
    # send_telegram_message(report)


# Create the DAG
with DAG(
    dag_id="crypto_data_collection",
    default_args=default_args,
    description="Collect OHLCV data from Upbit exchange",
    schedule_interval="30 9 * * *",  # 9:30 AM daily (KST)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-engineering", "crypto", "collection"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # Create task groups for each interval
    for interval in INTERVALS:
        with TaskGroup(group_id=f"collect_{interval}") as collect_group:
            collect_tasks = []

            for symbol in SYMBOLS:
                task = PythonOperator(
                    task_id=f"collect_{symbol}",
                    python_callable=collect_symbol_data,
                    op_kwargs={"symbol": symbol, "interval": interval},
                )
                collect_tasks.append(task)

        start >> collect_group

    # Validation task
    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_collected_data,
    )

    # Report task
    report_task = PythonOperator(
        task_id="send_report",
        python_callable=send_collection_report,
    )

    # Set dependencies
    for interval in INTERVALS:
        dag.get_task_group(f"collect_{interval}") >> validate_task

    validate_task >> report_task >> end
