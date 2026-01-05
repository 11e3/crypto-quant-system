# Test Fixtures

This directory contains reusable test fixtures and sample data for the test suite.

## Structure

```
fixtures/
├── data/              # Sample OHLCV and market data generators
│   └── sample_ohlcv.py
├── config/            # Test configuration files
│   └── test_settings.yaml
├── mock_exchange.py   # Mock Exchange implementation
└── README.md          # This file
```

## Data Fixtures

### `sample_ohlcv.py`

Provides functions to generate realistic OHLCV data for testing:

- `generate_ohlcv_data()`: Generate standard OHLCV data with configurable parameters
- `generate_trending_data()`: Generate data with a clear trend (uptrend/downtrend)
- `generate_volatile_data()`: Generate highly volatile data for stress testing
- `generate_multiple_tickers_data()`: Generate data for multiple tickers simultaneously

**Usage:**
```python
from tests.fixtures.data.sample_ohlcv import generate_ohlcv_data

# Generate 100 days of data
df = generate_ohlcv_data(periods=100, base_price=50_000_000.0, seed=42)
```

## Configuration Fixtures

### `test_settings.yaml`

Test configuration file that mirrors the structure of `config/settings.yaml` but with:
- Test-safe values (no real API keys)
- Disabled external services (Telegram)
- Minimal ticker list for faster tests

**Usage:**
```python
from pathlib import Path
from src.config.loader import get_config

test_config_path = Path(__file__).parent / "fixtures" / "config" / "test_settings.yaml"
config = get_config(test_config_path)
```

## Mock Exchange

### `mock_exchange.py`

A complete mock implementation of the `Exchange` interface for testing:

- In-memory state management (balances, orders, prices)
- Configurable failure modes
- Realistic order execution simulation

**Usage:**
```python
from tests.fixtures.mock_exchange import MockExchange

exchange = MockExchange()
exchange.set_balance("KRW", 1_000_000.0)
exchange.set_price("KRW-BTC", 50_000_000.0)
```

## Pytest Fixtures

All fixtures are automatically available in tests via `conftest.py`:

- `sample_ohlcv_data`: Standard OHLCV DataFrame (100 periods)
- `trending_ohlcv_data`: Trending OHLCV DataFrame
- `volatile_ohlcv_data`: Volatile OHLCV DataFrame
- `multiple_tickers_data`: Dict of DataFrames for multiple tickers
- `mock_exchange`: MockExchange instance
- `vbo_strategy`: VanillaVBO strategy instance
- `sample_balance`: Sample Balance object
- `sample_order`: Sample Order object
- `sample_ticker`: Sample Ticker object
- `test_config_path`: Path to test configuration file

**Usage:**
```python
def test_my_function(sample_ohlcv_data, mock_exchange):
    # Use fixtures directly
    df = sample_ohlcv_data
    exchange = mock_exchange
    # ... test code
```
