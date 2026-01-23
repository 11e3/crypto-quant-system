"""
Backtest Automation DAG
=======================
Runs automated backtests and stores results.

Schedule: Weekly on Sunday at 2:00 AM KST
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

# Default arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=2),
}

SYMBOLS = ["BTC", "ETH", "XRP", "TRX", "ADA"]
STRATEGIES = ["vbo", "momentum", "mean_reversion"]


def check_data_availability(**context) -> str:
    """Check if required data is available for backtesting.

    Returns:
        Task ID to branch to
    """
    import os
    from pathlib import Path

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    features_path = data_dir / "processed" / "combined_features.parquet"

    if not features_path.exists():
        print("Combined features not found, skipping backtest")
        return "skip_backtest"

    import pandas as pd
    df = pd.read_parquet(features_path)

    if len(df) < 100:
        print(f"Insufficient data: {len(df)} rows")
        return "skip_backtest"

    print(f"Data available: {len(df)} rows")
    return "run_backtests"


def run_vbo_backtest(symbol: str, **context) -> dict:
    """Run VBO (Volatility Breakout) backtest for a symbol.

    Args:
        symbol: Trading symbol
        context: Airflow context

    Returns:
        Dictionary with backtest results
    """
    import os
    import pandas as pd
    import numpy as np

    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    input_path = data_dir / "raw" / "day" / f"{symbol}.parquet"

    if not input_path.exists():
        return {"symbol": symbol, "strategy": "vbo", "status": "no_data"}

    df = pd.read_parquet(input_path)

    # VBO Strategy Parameters
    ma_short = 5
    btc_ma = 20
    noise_ratio = 0.5
    fee = 0.0005

    # Calculate indicators
    df["ma"] = df["close"].rolling(ma_short).mean()
    df["range"] = df["high"].shift(1) - df["low"].shift(1)
    df["target"] = df["open"] + df["range"] * noise_ratio

    # Signals
    df["signal"] = (df["close"].shift(1) > df["ma"].shift(1)).astype(int)

    # Simulate trades
    df["entry"] = (df["high"] >= df["target"]) & (df["signal"] == 1)
    df["entry_price"] = df["target"].where(df["entry"], np.nan)

    # Calculate returns (simplified)
    df["daily_return"] = df["close"].pct_change()
    df["strategy_return"] = df["daily_return"].where(df["signal"].shift(1) == 1, 0)
    df["strategy_return"] = df["strategy_return"] - fee * 2  # Entry + exit fees

    # Cumulative returns
    df["cum_return"] = (1 + df["strategy_return"]).cumprod()
    df["cum_bh"] = (1 + df["daily_return"]).cumprod()  # Buy & Hold

    # Calculate metrics
    total_return = df["cum_return"].iloc[-1] - 1
    bh_return = df["cum_bh"].iloc[-1] - 1

    # Sharpe Ratio (annualized)
    daily_returns = df["strategy_return"].dropna()
    sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(365) if len(daily_returns) > 0 else 0

    # Max Drawdown
    rolling_max = df["cum_return"].cummax()
    drawdown = (df["cum_return"] - rolling_max) / rolling_max
    max_dd = drawdown.min()

    # CAGR
    years = len(df) / 365
    cagr = (df["cum_return"].iloc[-1]) ** (1 / years) - 1 if years > 0 else 0

    result = {
        "symbol": symbol,
        "strategy": "vbo",
        "status": "success",
        "total_return": total_return,
        "buy_hold_return": bh_return,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "trade_count": df["entry"].sum(),
        "data_rows": len(df),
        "backtest_date": datetime.now().isoformat(),
    }

    print(f"VBO Backtest {symbol}: Return={total_return:.2%}, Sharpe={sharpe:.2f}, MDD={max_dd:.2%}")

    return result


def aggregate_backtest_results(**context) -> dict:
    """Aggregate all backtest results.

    Returns:
        Dictionary with aggregated results
    """
    import os
    import json
    from pathlib import Path

    ti = context["ti"]
    data_dir = Path(os.environ.get("DATA_DIR", "/opt/airflow/data"))
    output_dir = data_dir / "backtest_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect results from upstream tasks
    results = []
    for symbol in SYMBOLS:
        result = ti.xcom_pull(task_ids=f"backtest_vbo_{symbol}")
        if result:
            results.append(result)

    if not results:
        return {"status": "no_results"}

    # Save results
    execution_date = context["execution_date"].strftime("%Y%m%d")
    output_path = output_dir / f"backtest_results_{execution_date}.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Calculate summary statistics
    import pandas as pd
    df = pd.DataFrame(results)

    summary = {
        "date": execution_date,
        "total_strategies": len(results),
        "avg_return": df["total_return"].mean(),
        "avg_sharpe": df["sharpe_ratio"].mean(),
        "avg_mdd": df["max_drawdown"].mean(),
        "best_symbol": df.loc[df["total_return"].idxmax(), "symbol"],
        "worst_symbol": df.loc[df["total_return"].idxmin(), "symbol"],
    }

    print(f"Backtest Summary: {summary}")

    return summary


def send_backtest_report(**context) -> None:
    """Send backtest report notification."""
    ti = context["ti"]
    summary = ti.xcom_pull(task_ids="aggregate_results")

    if not summary or summary.get("status") == "no_results":
        print("No backtest results to report")
        return

    report = f"""
    Weekly Backtest Report
    ======================
    Date: {summary.get('date')}

    Summary:
    - Strategies Tested: {summary.get('total_strategies')}
    - Average Return: {summary.get('avg_return', 0):.2%}
    - Average Sharpe: {summary.get('avg_sharpe', 0):.2f}
    - Average MDD: {summary.get('avg_mdd', 0):.2%}

    Best Performer: {summary.get('best_symbol')}
    Worst Performer: {summary.get('worst_symbol')}
    """

    print(report)

    # TODO: Send to Telegram/Slack/Email


# Create the DAG
with DAG(
    dag_id="crypto_backtest_automation",
    default_args=default_args,
    description="Run automated backtests weekly",
    schedule_interval="0 2 * * 0",  # Sunday 2:00 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-engineering", "crypto", "backtest"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # Check data availability
    check_data = BranchPythonOperator(
        task_id="check_data_availability",
        python_callable=check_data_availability,
    )

    # Skip placeholder
    skip = EmptyOperator(task_id="skip_backtest")

    # Run backtests placeholder
    run_backtests = EmptyOperator(task_id="run_backtests")

    # VBO Backtests for each symbol
    vbo_tasks = []
    for symbol in SYMBOLS:
        task = PythonOperator(
            task_id=f"backtest_vbo_{symbol}",
            python_callable=run_vbo_backtest,
            op_kwargs={"symbol": symbol},
        )
        vbo_tasks.append(task)

    # Aggregate results
    aggregate_task = PythonOperator(
        task_id="aggregate_results",
        python_callable=aggregate_backtest_results,
        trigger_rule="none_failed_min_one_success",
    )

    # Send report
    report_task = PythonOperator(
        task_id="send_report",
        python_callable=send_backtest_report,
    )

    # Set dependencies
    start >> check_data
    check_data >> skip >> end
    check_data >> run_backtests >> vbo_tasks >> aggregate_task >> report_task >> end
