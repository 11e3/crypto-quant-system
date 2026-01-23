"""
Feature Engineering DAG
=======================
Calculates technical indicators and features from raw OHLCV data.

Schedule: Daily at 10:00 AM KST (after data collection)
Depends on: crypto_data_collection DAG
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor

# Default arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=60),
}

SYMBOLS = ["BTC", "ETH", "XRP", "TRX", "ADA", "DOGE", "SOL", "AVAX"]


def calculate_features(symbol: str, **context) -> dict:
    """Calculate features for a single symbol.

    Args:
        symbol: Trading symbol
        context: Airflow context

    Returns:
        Dictionary with feature calculation results
    """
    import os
    import pandas as pd
    import numpy as np

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    input_path = data_dir / "raw" / "day" / f"{symbol}.parquet"
    output_dir = data_dir / "processed" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol}_features.parquet"

    if not input_path.exists():
        print(f"No raw data for {symbol}")
        return {"symbol": symbol, "status": "no_data"}

    # Load raw data
    df = pd.read_parquet(input_path)
    print(f"Loaded {symbol}: {len(df)} rows")

    # Calculate features
    features = pd.DataFrame(index=df.index)

    # Price features
    features["return_1d"] = df["close"].pct_change(1)
    features["return_5d"] = df["close"].pct_change(5)
    features["return_20d"] = df["close"].pct_change(20)

    # Moving averages
    features["ma_5"] = df["close"].rolling(5).mean()
    features["ma_20"] = df["close"].rolling(20).mean()
    features["ma_60"] = df["close"].rolling(60).mean()

    # MA ratios
    features["ma_5_20_ratio"] = features["ma_5"] / features["ma_20"]
    features["ma_20_60_ratio"] = features["ma_20"] / features["ma_60"]
    features["price_ma_20_ratio"] = df["close"] / features["ma_20"]

    # Volatility
    features["volatility_20d"] = df["close"].pct_change().rolling(20).std()
    features["volatility_60d"] = df["close"].pct_change().rolling(60).std()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    features["rsi_14"] = 100 - (100 / (1 + rs))

    # Volume features
    features["volume_ma_20"] = df["volume"].rolling(20).mean()
    features["volume_ratio"] = df["volume"] / features["volume_ma_20"]

    # ATR (Average True Range)
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    features["atr_14"] = tr.rolling(14).mean()
    features["atr_ratio"] = features["atr_14"] / df["close"]

    # Bollinger Bands
    bb_ma = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    features["bb_upper"] = bb_ma + 2 * bb_std
    features["bb_lower"] = bb_ma - 2 * bb_std
    features["bb_width"] = (features["bb_upper"] - features["bb_lower"]) / bb_ma
    features["bb_position"] = (df["close"] - features["bb_lower"]) / (
        features["bb_upper"] - features["bb_lower"]
    )

    # MA alignment (trend strength)
    features["ma_alignment"] = (
        (features["ma_5"] > features["ma_20"]).astype(int) +
        (features["ma_20"] > features["ma_60"]).astype(int)
    ) / 2

    # Add timestamp for tracking
    features["calculated_at"] = datetime.now()

    # Save features
    features.to_parquet(output_path)

    feature_count = len([c for c in features.columns if c != "calculated_at"])
    nan_ratio = features.isna().sum().sum() / (len(features) * feature_count)

    print(f"Saved {symbol} features: {len(features)} rows, {feature_count} features, "
          f"{nan_ratio:.2%} NaN ratio")

    return {
        "symbol": symbol,
        "status": "success",
        "rows": len(features),
        "features": feature_count,
        "nan_ratio": nan_ratio,
    }


def create_combined_features(**context) -> dict:
    """Combine all symbol features into a single dataset.

    Returns:
        Dictionary with combined dataset info
    """
    import os
    import pandas as pd

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    features_dir = data_dir / "processed" / "features"
    output_path = data_dir / "processed" / "combined_features.parquet"

    all_features = []

    for symbol in SYMBOLS:
        file_path = features_dir / f"{symbol}_features.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            df["symbol"] = symbol
            all_features.append(df)
            print(f"Loaded {symbol}: {len(df)} rows")

    if not all_features:
        print("No feature files found")
        return {"status": "no_data"}

    combined = pd.concat(all_features)
    combined.to_parquet(output_path)

    print(f"Combined features: {len(combined)} total rows, {len(SYMBOLS)} symbols")

    return {
        "status": "success",
        "total_rows": len(combined),
        "symbols": len(all_features),
    }


def validate_features(**context) -> dict:
    """Validate calculated features.

    Returns:
        Dictionary with validation results
    """
    import os
    import pandas as pd

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    combined_path = data_dir / "processed" / "combined_features.parquet"

    if not combined_path.exists():
        return {"status": "error", "message": "Combined features file not found"}

    df = pd.read_parquet(combined_path)

    # Validation checks
    issues = []

    # Check for infinite values
    inf_count = df.select_dtypes(include=["float64"]).apply(
        lambda x: x.isin([float("inf"), float("-inf")]).sum()
    ).sum()
    if inf_count > 0:
        issues.append(f"Found {inf_count} infinite values")

    # Check for high NaN ratio
    nan_ratio = df.isna().sum().sum() / (len(df) * len(df.columns))
    if nan_ratio > 0.3:
        issues.append(f"High NaN ratio: {nan_ratio:.2%}")

    # Check data freshness
    if "calculated_at" in df.columns:
        latest = pd.to_datetime(df["calculated_at"]).max()
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        if age_hours > 24:
            issues.append(f"Data is {age_hours:.1f} hours old")

    result = {
        "status": "valid" if not issues else "warning",
        "total_rows": len(df),
        "nan_ratio": nan_ratio,
        "issues": issues,
    }

    print(f"Validation: {result}")
    return result


# Create the DAG
with DAG(
    dag_id="crypto_feature_engineering",
    default_args=default_args,
    description="Calculate technical features from OHLCV data",
    schedule_interval="0 10 * * *",  # 10:00 AM daily (after data collection)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-engineering", "crypto", "features"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # Wait for data collection DAG
    wait_for_data = ExternalTaskSensor(
        task_id="wait_for_data_collection",
        external_dag_id="crypto_data_collection",
        external_task_id="end",
        mode="poke",
        timeout=3600,
        poke_interval=60,
    )

    # Calculate features for each symbol
    feature_tasks = []
    for symbol in SYMBOLS:
        task = PythonOperator(
            task_id=f"calculate_{symbol}_features",
            python_callable=calculate_features,
            op_kwargs={"symbol": symbol},
        )
        feature_tasks.append(task)

    # Combine features
    combine_task = PythonOperator(
        task_id="combine_features",
        python_callable=create_combined_features,
    )

    # Validate features
    validate_task = PythonOperator(
        task_id="validate_features",
        python_callable=validate_features,
    )

    # Set dependencies
    start >> wait_for_data >> feature_tasks >> combine_task >> validate_task >> end
