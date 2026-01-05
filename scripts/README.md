# Scripts Directory

This directory contains utility scripts organized by purpose.

## Structure

```
scripts/
├── tools/          # Development and analysis tools
├── backtest/       # Backtest-related scripts
└── data/           # Data management scripts (if needed)
```

## Main CLI

For most operations, use the CLI commands:

```bash
# Data collection
upbit-quant collect --tickers KRW-BTC KRW-ETH

# Backtesting
upbit-quant backtest --tickers KRW-BTC --interval day

# Run trading bot
upbit-quant run-bot
```

## Development Tools

Development tools in `tools/` are for debugging and analysis:
- Trade comparison
- Metrics comparison
- Logic verification

These are not part of the main CLI.
