# Crypto Quant System

**Production-grade cryptocurrency trading platform with backtesting, live trading, and portfolio optimization.**

Part of: **[crypto-quant-system](https://github.com/11e3/crypto-quant-system)** -> [bt](https://github.com/11e3/bt) -> [crypto-bot](https://github.com/11e3/crypto-bot) -> [crypto-regime-classifier-ml](https://github.com/11e3/crypto-regime-classifier-ml)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-green.svg)](https://github.com/11e3/crypto-quant-system)
[![MyPy](https://img.shields.io/badge/mypy-97.8%25-brightgreen.svg)](https://mypy.readthedocs.io/)

## Ecosystem Role

```
+---------------------------------------------------------------------+
|                     Crypto Quant Ecosystem                          |
+----------------------------------+----------------------------------+
|  crypto-quant-system (this repo) |  Dashboard, Backtest, Data       |
|    +-- Data Pipeline             |  - Fetches OHLCV from Upbit      |
|    +-- Backtesting Engine        |  - Event-driven & Vectorized     |
|    +-- Strategy Library          |  - VBO, ORB, Momentum, MeanRev   |
|    +-- Web Dashboard             |  - Streamlit multi-page app      |
|    +-- Bot Monitor               |  - Reads logs from GCS           |
+----------------------------------+----------------------------------+
|  crypto-bot                      |  Live Trading Bot                |
|    +-- Logs to GCS               |  - Monitored via dashboard       |
+----------------------------------+----------------------------------+
|  crypto-regime-classifier-ml     |  Market Regime Classifier        |
|    +-- Models to GCS             |  - Viewable in dashboard         |
+----------------------------------+----------------------------------+
```

## Features

### 1. Data Pipeline

```python
# CLI data download
python scripts/fetch_data.py --symbols BTC,ETH,XRP --interval day

# Or use the collector programmatically
from src.data.collector import UpbitDataCollector

collector = UpbitDataCollector()
collector.collect("KRW-BTC", "day")
```

### 2. Backtesting Engine

Dual-engine architecture for flexibility:

```python
from src.backtester import EventDrivenBacktestEngine, BacktestConfig
from src.strategies.volatility_breakout import VanillaVBO

# Event-driven for accuracy
engine = EventDrivenBacktestEngine()
strategy = VanillaVBO(sma_period=5, trend_sma_period=10)
result = engine.run(strategy, data, BacktestConfig())

# Vectorized for speed (parameter optimization)
from src.backtester import VectorizedBacktestEngine
engine = VectorizedBacktestEngine()
```

### 3. Strategy Library

Built-in strategies with composable conditions:

| Strategy | Description |
|----------|-------------|
| **VBO** | Volatility Breakout with noise/trend filters |
| **ORB** | Opening Range Breakout |
| **Momentum** | Trend-following momentum |
| **Mean Reversion** | Statistical mean reversion |

### 4. Web Dashboard

Interactive Streamlit application with:
- Data collection UI
- Backtest execution with 30+ metrics
- Parameter optimization (Grid/Random search)
- Walk-forward analysis
- Bot monitoring via GCS

### 5. Bot Monitor (GCS Integration)

Real-time monitoring of `crypto-bot` via GCS:

```python
from src.data.storage import GCSStorage

storage = GCSStorage(bucket_name="your-quant-bucket")
trades = storage.get_bot_logs(date="2025-01-16", account="Main")
positions = storage.get_bot_positions(account="Main")
```

## Quick Start

### Installation

```bash
git clone <repository-url>
cd crypto-quant-system

# Install with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Run Dashboard

```bash
uv run streamlit run src/web/app.py
```

### Download Data

```bash
# Download specific symbols
python scripts/fetch_data.py --symbols BTC,ETH,XRP --interval day

# Update all existing data
python scripts/fetch_data.py --update

# List available data
python scripts/fetch_data.py --list

# Download with multiple intervals
python scripts/fetch_data.py --symbols BTC --interval day,minute240,minute30
```

### Run Backtest

```bash
# Via script
python scripts/backtest/run_backtest.py --mode report

# Or programmatically
python -c "
from src.backtester import run_backtest
from src.strategies.volatility_breakout import VanillaVBO
result = run_backtest(VanillaVBO(), ['KRW-BTC', 'KRW-ETH'])
print(result.summary())
"
```

## Project Structure

```
crypto-quant-system/
+-- src/                          # Main source code
|   +-- backtester/               # Backtest engines
|   |   +-- engine/               # Event-driven & vectorized engines
|   |   +-- analysis/             # Bootstrap, Monte Carlo, WFA
|   |   +-- html/                 # HTML report generation
|   |   +-- wfa/                  # Walk-forward analysis
|   |   +-- models.py             # BacktestConfig, BacktestResult
|   |   +-- metrics.py            # Performance metrics
|   |   +-- optimization.py       # Parameter optimization
|   |
|   +-- strategies/               # Trading strategies
|   |   +-- base.py               # Strategy base class
|   |   +-- volatility_breakout/  # VBO strategy
|   |   +-- opening_range_breakout/ # ORB strategy
|   |   +-- momentum/             # Momentum strategy
|   |   +-- mean_reversion/       # Mean reversion strategy
|   |
|   +-- data/                     # Data collection
|   |   +-- collector.py          # Upbit data collector
|   |   +-- storage.py            # GCS integration
|   |
|   +-- exchange/                 # Exchange abstraction
|   |   +-- upbit.py              # Upbit implementation
|   |
|   +-- execution/                # Live trading
|   |   +-- bot/                  # Trading bot
|   |   +-- order_manager.py      # Order management
|   |
|   +-- risk/                     # Risk management
|   |   +-- portfolio_optimization.py # MVO, HRP, etc.
|   |   +-- metrics_var.py        # VaR/CVaR
|   |
|   +-- web/                      # Streamlit dashboard
|   |   +-- app.py                # Main app
|   |   +-- pages/                # Multi-page app
|   |   |   +-- backtest.py       # Backtest UI
|   |   |   +-- data_collect.py   # Data collection
|   |   |   +-- optimization.py   # Parameter optimization
|   |   |   +-- analysis.py       # Advanced analysis
|   |   |   +-- monitor.py        # Bot monitor (GCS)
|   |   +-- components/           # Reusable UI components
|   |   +-- services/             # Business logic
|   |
|   +-- config/                   # Configuration
|   +-- utils/                    # Utilities
|
+-- scripts/                      # CLI tools
|   +-- fetch_data.py             # Data download CLI
|   +-- backtest/                 # Backtest scripts
|   +-- data/                     # Data collection scripts
|   +-- tools/                    # Analysis tools
|
+-- data/                         # Data storage
|   +-- raw/                      # Raw OHLCV data
|   +-- processed/                # Processed data
|
+-- tests/                        # Test suite
|   +-- unit/                     # Unit tests
|   +-- integration/              # Integration tests
|
+-- docs/                         # Documentation
+-- config/                       # Configuration examples
```

## Dashboard Pages

### Home
System overview and getting started guide.

### Data Collection
| Feature | Description |
|---------|-------------|
| Ticker selector | Choose coins from Upbit |
| Interval selector | 1min to monthly candles |
| Download button | Fetch data with progress |
| Data status | Show available data |

### Backtest
| Feature | Description |
|---------|-------------|
| Strategy selector | VBO, ORB, Momentum, MeanRev |
| Parameter config | Dynamic UI based on strategy |
| Multi-asset | Test multiple tickers |
| Metrics | CAGR, MDD, Sharpe, 30+ metrics |
| Charts | Equity curve, drawdown, heatmap |

### Optimization
| Feature | Description |
|---------|-------------|
| Grid search | Exhaustive parameter search |
| Random search | Fast exploration |
| Parallel | Multi-core support |
| Results table | Sortable by metric |

### Analysis
| Feature | Description |
|---------|-------------|
| Walk-Forward | Out-of-sample validation |
| Monte Carlo | Risk simulation |
| Bootstrap | Confidence intervals |

### Bot Monitor
| Feature | Description |
|---------|-------------|
| Live positions | Current holdings |
| Trade history | From GCS logs |
| PnL summary | Daily/weekly/monthly |
| Alerts | Error notifications |

## GCS Integration

### Configuration

```bash
# .env
GCS_BUCKET=your-quant-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Bucket Structure

```
gs://your-quant-bucket/
+-- logs/
|   +-- {account}/
|       +-- trades_2025-01-16.csv
|       +-- positions.json
+-- models/
|   +-- regime_classifier_v1.pkl
+-- data/
    +-- processed/
        +-- BTC_1d.parquet
```

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --all-extras

# Setup pre-commit hooks
pre-commit install
```

### Quality Gates

```bash
# Format
uv run ruff format src/ tests/

# Lint
uv run ruff check --fix src/ tests/

# Type check
uv run mypy src/

# Test with coverage
uv run pytest --cov=src --cov-fail-under=80
```

### Run Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/unit/test_backtester/

# With coverage report
uv run pytest --cov=src --cov-report=html
```

## Performance Metrics

The backtester calculates 30+ metrics:

| Category | Metrics |
|----------|---------|
| Returns | Total Return, CAGR, Monthly/Yearly |
| Risk | MDD, Volatility, VaR, CVaR |
| Risk-Adjusted | Sharpe, Sortino, Calmar |
| Trade Stats | Win Rate, Profit Factor, Avg Trade |
| Statistical | Skewness, Kurtosis, Hit Ratio |

## Roadmap

- [ ] Real-time price streaming
- [ ] Strategy builder UI
- [ ] Regime model integration
- [ ] Multi-account aggregation
- [ ] Alert configuration

## License

MIT License

---

**Version**: 2.0.0 | **Python**: 3.10+ | **Framework**: Streamlit
