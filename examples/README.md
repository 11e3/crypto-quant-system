# Examples

This directory contains practical examples demonstrating how to use the Upbit Quant System.

## 📚 Available Examples

### 1. Basic Backtest (`basic_backtest.py`)
Simple backtest example with default settings.

**What it demonstrates**:
- Running a basic backtest
- Viewing results
- Understanding key metrics

**Run it**:
```bash
uv run python examples/basic_backtest.py
```

### 2. Custom Strategy (`custom_strategy.py`)
Create and test a custom trading strategy.

**What it demonstrates**:
- Strategy customization
- Adding custom conditions
- Parameter tuning

**Run it**:
```bash
uv run python examples/custom_strategy.py
```

### 3. Live Trading (`live_trading.py`)
Set up and run a live trading bot.

**What it demonstrates**:
- Live trading configuration
- Risk management
- Monitoring setup

**⚠️ Warning**: This example uses real money. Test thoroughly before using.

**Run it**:
```bash
uv run python examples/live_trading.py
```

### 4. Performance Analysis (`performance_analysis.py`)
Analyze and compare strategy performance.

**What it demonstrates**:
- Performance metrics calculation
- Risk analysis
- Strategy comparison

**Run it**:
```bash
uv run python examples/performance_analysis.py
```

### 5. Strategy Comparison (`strategy_comparison.py`)
Compare multiple strategies side-by-side.

**What it demonstrates**:
- Running multiple strategies
- Performance comparison
- Risk-return analysis

**Run it**:
```bash
uv run python examples/strategy_comparison.py
```

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   uv sync --extra dev
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run an example**:
   ```bash
   uv run python examples/basic_backtest.py
   ```

## 📖 Learning Path

**Beginner**:
1. Start with `basic_backtest.py`
2. Understand the results
3. Try `custom_strategy.py`

**Intermediate**:
1. Explore `performance_analysis.py`
2. Compare strategies with `strategy_comparison.py`
3. Customize strategies further

**Advanced**:
1. Set up `live_trading.py` (with caution!)
2. Create your own strategies
3. Optimize parameters

## 💡 Tips

- **Start Simple**: Begin with basic examples before moving to complex ones
- **Read the Code**: Examples are well-commented - read them to learn
- **Experiment**: Modify examples to see how changes affect results
- **Test First**: Always backtest before live trading

## 🐛 Troubleshooting

**Import Errors**: Make sure you've installed dependencies with `uv sync`

**Data Errors**: Ensure you have collected market data:
```bash
uv run upbit-quant collect
```

**Configuration Errors**: Check your `.env` file and `config/settings.yaml`

## 📚 Related Documentation

- [Getting Started Guide](../docs/guides/getting_started.md)
- [Strategy Customization](../docs/guides/strategy_customization.md)
- [Configuration Guide](../docs/guides/configuration.md)
- [Architecture Documentation](../docs/architecture.md)

## 🤝 Contributing

Found a bug or have a suggestion? Please open an issue or submit a PR!
