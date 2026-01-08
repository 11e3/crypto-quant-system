# API Reference - Real-time Monitoring Module

## Overview

Real-time monitoring module provides automated cryptocurrency strategy monitoring with Upbit API integration, threshold evaluation, and multi-channel alerts.

## Core Components

### 1. UpbitLiveMonitor

**Module**: `src/monitoring/live_monitor.py` (via `scripts/real_time_monitor.py`)

**Purpose**: Unified interface for real-time monitoring workflow.

#### Constructor
```python
UpbitLiveMonitor(
    config_path: Optional[Path] = None,
    output_dir: Path = None
)
```

**Parameters**:
- `config_path`: Path to monitoring.yaml config file
- `output_dir`: Directory for storing monitoring reports

#### Key Methods

##### `monitor(tickers: list[str], webhook_url: Optional[str] = None) -> None`

Run complete monitoring cycle:
1. Fetch live data from Upbit
2. Run backtest
3. Check thresholds
4. Generate alerts (console, file, Slack)

**Example**:
```python
monitor = UpbitLiveMonitor(output_dir=Path("reports"))
monitor.monitor(
    tickers=["KRW-BTC", "KRW-ETH"],
    webhook_url="https://hooks.slack.com/.../ABC123"
)
```

##### `fetch_live_data(tickers: list[str], interval: str = "day") -> dict[str, pd.DataFrame]`

Fetch latest OHLCV data from Upbit with incremental updates.

**Returns**: Dictionary mapping ticker → DataFrame

**Columns**: `date`, `open`, `high`, `low`, `close`, `volume`

##### `run_backtest(tickers: list[str]) -> dict`

Execute strategy backtest on live data.

**Returns**: Dictionary with metrics:
```python
{
    "total_return": float,           # Cumulative return
    "sharpe_ratio": float,           # Risk-adjusted return
    "mdd": float,                    # Max drawdown (negative)
    "total_trades": int,             # Trade count
    "winning_trades": int,           # Profitable trades
    "win_rate": float,               # Win rate (0-1)
    "last_trade_date": date,         # Last closed trade
    "total_commission": float,       # Commission costs
    "total_slippage": float,        # Slippage costs
}
```

##### `check_thresholds(metrics: dict) -> list[tuple]`

Evaluate metrics against configured thresholds.

**Returns**: List of violations `[(key, value, threshold), ...]`

**Thresholds** (from config):
```yaml
thresholds:
  min_win_rate: 0.30          # Minimum 30% win rate
  min_sharpe: 0.5             # Minimum 0.5 Sharpe ratio
  max_max_drawdown: -0.25     # Maximum 25% drawdown
```

---

### 2. Slack Alert Formatting

**Function**: `format_slack_alert(metrics: dict, violations: list) -> str`

Generate rich Slack messages using Block Kit format.

**Output Format**:
```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "🚨 *Monitoring Alert* ..."
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Performance Metrics*\n• Return: 24.29%\n..."
      }
    }
  ]
}
```

**Features**:
- Emoji indicators (✅ OK, 🚨 Alert)
- Structured metric display
- Violation details with thresholds
- Timestamp (UTC)

---

### 3. Task Scheduler Integration

**Module**: `scripts/setup_task_scheduler.py`

**Purpose**: Automate monitoring via Windows Task Scheduler.

#### Functions

##### `create_monitoring_task(...) -> None`

Create scheduled task for daily monitoring.

**Parameters**:
```python
create_monitoring_task(
    task_name: str = "CryptoQuantMonitoring",
    schedule_time: str = "10:00",
    tickers: list[str] = None,
    output_dir: str = None,
    slack_webhook: str = None
)
```

**Task Properties**:
- Trigger: Daily at specified time
- Run Level: Highest (admin)
- Settings: AllowStartIfOnBatteries, DontStopIfGoingOnBatteries

**Generated Files**:
- `setup_task_scheduler.ps1` - PowerShell script to register task
- `remove_task_scheduler.ps1` - Script to unregister task
- `check_task_scheduler.ps1` - Script to check task status

##### `remove_monitoring_task(task_name: str) -> None`

Remove scheduled monitoring task.

##### `get_task_status(task_name: str) -> None`

Check current task status and execution history.

---

## Configuration

### `config/monitoring.yaml`

```yaml
# Monitoring thresholds
thresholds:
  # Win rate (0-1)
  min_win_rate: 0.30
  
  # Sharpe ratio (annual)
  min_sharpe: 0.5
  
  # Max drawdown (negative, -1 to 0)
  max_max_drawdown: -0.25
```

---

## Output Files

### 1. Alerts Log
**Path**: `reports/monitoring_alerts.log`

**Format**: Text log with timestamp and violations
```
[ALERT 2026-01-08 01:09:57 UTC]
Monitoring threshold breaches:
- sharpe_ratio: value=0.289349, threshold=0.5
```

### 2. Metrics Snapshot
**Path**: `reports/metrics_YYYYMMDD_HHMMSS.json`

**Content**: Complete metrics and status at time of run
```json
{
  "total_return": "24.286068",
  "sharpe_ratio": 0.2893485387867662,
  "mdd": "30.912458",
  "total_trades": 381,
  "winning_trades": 115,
  "win_rate": 0.30183727034120733,
  "last_trade_date": "2026-01-07",
  "total_commission": 12.45107233338058,
  "total_slippage": 12.451072312891483
}
```

---

## Usage Examples

### Example 1: Manual Run with Slack

```bash
python -m scripts.real_time_monitor \
  --tickers KRW-BTC KRW-ETH \
  --output reports \
  --slack "https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_TOKEN"
```

### Example 2: Task Scheduler Setup

```powershell
# Generate setup scripts
python scripts/setup_task_scheduler.py --action create --schedule-time 08:30

# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1
```

### Example 3: Check Task Status

```powershell
# Generate status check script
python scripts/setup_task_scheduler.py --action status

# Run to see current state
powershell -ExecutionPolicy Bypass -File scripts/check_task_scheduler.ps1
```

### Example 4: Python API

```python
from pathlib import Path
from scripts.real_time_monitor import UpbitLiveMonitor

# Initialize monitor
monitor = UpbitLiveMonitor(
    config_path=Path("config/monitoring.yaml"),
    output_dir=Path("reports")
)

# Run monitoring
monitor.monitor(
    tickers=["KRW-BTC", "KRW-ETH", "KRW-XRP"],
    webhook_url=os.getenv("SLACK_WEBHOOK")
)
```

---

## Error Handling

### Common Issues

1. **No data fetched**
   - Check Upbit API connectivity
   - Verify ticker symbols (e.g., "KRW-BTC" not "BTCUSDT")
   - Check API rate limits (10 req/sec)

2. **Backtest failed**
   - Insufficient historical data
   - Strategy parameter validation errors
   - Check logs for details

3. **Slack webhook error**
   - Verify webhook URL format
   - Check webhook still active (may expire)
   - Network connectivity issue

### Logging

Monitor logs to `logs/monitoring.log`:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Monitoring started")
logger.error("Failed to fetch data: {error}")
```

---

## Performance Considerations

### Data Collection
- **Time**: ~1 second per ticker (Upbit API call)
- **Incremental**: Only new candles fetched since last run
- **Storage**: ~50KB per year per ticker (Parquet format)

### Backtest Execution
- **Time**: 1-5 seconds (381 trades, 3028 candles)
- **Memory**: ~100MB for full dataset
- **Optimization**: Uses cached indicators if `use_cache=True`

### Slack Alert
- **Time**: ~1 second (network latency)
- **Format**: Block Kit (rich formatting)
- **Retry**: Automatic on timeout

---

## Security Considerations

1. **Slack Webhook**
   - Store in environment variable (not source code)
   - Use `.env` file or Windows Secret Manager
   - Rotate webhooks regularly

2. **API Keys**
   - Not used for data collection (public Upbit API)
   - No authentication required

3. **Task Scheduler**
   - Runs with user account privileges
   - Logs stored locally
   - No external credential storage needed

---

## Future Enhancements

- [ ] Multi-exchange support (Binance, Coinbase)
- [ ] Web dashboard for monitoring
- [ ] Email notifications
- [ ] Discord/Telegram webhooks
- [ ] Custom alert rules (AND/OR logic)
- [ ] Trade signal alerts
- [ ] Performance trending

---

## Related Modules

- **src/monitoring/metrics.py**: Metric calculation
- **src/monitoring/checks.py**: Threshold evaluation
- **src/monitoring/alerts.py**: Alert dispatch
- **src/backtester/engine.py**: Strategy backtesting
- **src/data/collector.py**: Upbit data collection
