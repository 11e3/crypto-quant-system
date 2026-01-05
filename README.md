# 🚀 Upbit Quant System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tests](https://img.shields.io/badge/Tests-495%20passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-90%25-success.svg)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)

**Automated cryptocurrency trading system using volatility breakout strategy**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Overview

Upbit Quant System is a production-ready automated trading system for the Upbit cryptocurrency exchange. It implements a sophisticated volatility breakout (VBO) strategy with comprehensive backtesting capabilities, real-time trading execution, and extensive performance analytics.

### 🎯 Key Highlights

- **High-Performance Backtesting**: Vectorized engine using pandas/numpy for fast historical analysis
- **Modular Strategy System**: Composable conditions and filters for flexible strategy design
- **Production-Ready**: Full error handling, logging, monitoring, and Docker deployment
- **Well-Tested**: 90%+ test coverage with 495+ test cases
- **Modern Python**: Type hints, Pydantic settings, SOLID principles, clean architecture

## ✨ Features

### Core Functionality

- 🔄 **Volatility Breakout Strategy**: Automated entry/exit based on volatility patterns
- 📊 **Vectorized Backtesting**: Fast historical performance analysis
- 🤖 **Live Trading Bot**: Real-time execution with WebSocket integration
- 📈 **Performance Analytics**: Comprehensive metrics (CAGR, Sharpe, MDD, etc.)
- 🎨 **Visual Reports**: Equity curves, drawdown charts, monthly heatmaps

### Technical Excellence

- 🏗️ **Clean Architecture**: SOLID principles, dependency injection, separation of concerns
- 🧪 **High Test Coverage**: 90%+ coverage with unit and integration tests
- 📝 **Type Safety**: Full type hints with MyPy validation
- 🔒 **Security**: Environment-based configuration, no hardcoded secrets
- 🐳 **Docker Support**: Production-ready containerization for GCP/AWS deployment
- 📚 **Comprehensive Docs**: Architecture guides, API docs, contribution guidelines

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.10+**: Modern Python with type hints
- **pandas/numpy**: Data processing and vectorized operations
- **pydantic**: Type-safe configuration management
- **click**: CLI framework
- **pyupbit**: Upbit API integration

### Development Tools
- **uv**: Fast Python package manager
- **Ruff**: Linter and formatter (replaces Black)
- **MyPy**: Static type checking
- **pytest**: Testing framework with 85%+ coverage
- **pre-commit**: Git hooks for code quality

### Infrastructure
- **Docker**: Containerization
- **GCP**: Cloud deployment support
- **WebSocket**: Real-time market data

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/upbit-quant-system.git
cd upbit-quant-system

# Install uv (if not installed)
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra dev
```

### Backtesting

```bash
# Run backtest with default settings
upbit-quant backtest

# Custom backtest
upbit-quant backtest \
    --tickers KRW-BTC KRW-ETH \
    --interval day \
    --strategy legacy \
    --initial-capital 1000000 \
    --max-slots 4
```

### Live Trading (Requires API Keys)

```bash
# Set environment variables
export UPBIT_ACCESS_KEY="your-access-key"
export UPBIT_SECRET_KEY="your-secret-key"

# Run trading bot
upbit-quant run-bot
```

## 📊 Performance Results

### Backtest Results (Default Strategy)
- **Period**: 3,018 days (8+ years)
- **Total Return**: 38,331.40%
- **CAGR**: 105.40%
- **Max Drawdown**: 24.97%
- **Sharpe Ratio**: 1.97
- **Calmar Ratio**: 4.22
- **Win Rate**: 36.03%
- **Total Trades**: 705
- **Profit Factor**: 1.77

*Note: Past performance does not guarantee future results. These results are for educational purposes only.*

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                        │
│              (upbit-quant commands)                     │
└────────────────────┬──────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌────▼────┐
    │Backtest │            │Live Bot  │
    │ Engine  │            │Facade    │
    └────┬────┘            └────┬─────┘
         │                      │
    ┌────▼──────────────────────▼─────┐
    │      Strategy System             │
    │  (VanillaVBO, Conditions, etc.)  │
    └────┬─────────────────────────────┘
         │
    ┌────▼────────────┐
    │  Data Layer     │
    │  (Cache, Source) │
    └─────────────────┘
```

### Key Components

- **Backtesting Engine**: Vectorized calculations for fast historical analysis
- **Strategy System**: Modular conditions and filters for flexible strategy design
- **Execution Layer**: Order management, position tracking, signal handling
- **Data Layer**: Efficient caching, data collection, indicator calculation
- **Configuration**: Type-safe settings with environment variable support

## 📁 Project Structure

```
upbit-quant-system/
├── src/
│   ├── backtester/      # Backtesting engine
│   ├── execution/       # Live trading bot
│   ├── strategies/      # Trading strategies
│   ├── data/            # Data collection & caching
│   ├── exchange/        # Exchange API abstraction
│   ├── config/          # Configuration management
│   └── utils/           # Utilities
├── tests/               # Test suite (85%+ coverage)
├── docs/                # Comprehensive documentation
├── deploy/              # Docker & deployment configs
└── scripts/             # Utility scripts
```

## 📚 Documentation

### 📖 Guides
- [Getting Started](docs/guides/getting_started.md) - Installation and setup
- [Strategy Customization](docs/guides/strategy_customization.md) - Creating custom strategies
- [Configuration](docs/guides/configuration.md) - Configuration guide

### 🏗️ Architecture
- [System Architecture](docs/architecture.md) - Design principles and structure
- [Legacy vs New Bot Comparison](docs/comparison_legacy_vs_new_bot.md) - Migration guide

### 📋 Development
- [Test Coverage Plan](docs/TEST_COVERAGE_PLAN.md) - Testing strategy
- [Refactoring Standards](docs/refactoring/STANDARDS_COMPLIANCE_REPORT.md) - Code quality standards

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/unit/test_strategy.py
```

**Test Statistics:**
- Total Tests: 495+
- Coverage: 90%+ (Target: 90%)
- Test Types: Unit, Integration, Fixtures

## 🚢 Deployment

### Docker Deployment

```bash
cd deploy
docker-compose up -d
```

### GCP Deployment

See [deploy/README.md](deploy/README.md) for detailed GCP deployment instructions.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Code Quality

This project follows modern Python development standards:

- ✅ **SOLID Principles**: Clean architecture with dependency injection
- ✅ **Type Hints**: Full type coverage with MyPy validation
- ✅ **Testing**: 90%+ coverage with pytest
- ✅ **Linting**: Ruff for code quality
- ✅ **Documentation**: Comprehensive docs and docstrings

## ⚠️ Disclaimer

**This software is for educational and research purposes only.**

- Trading cryptocurrencies involves substantial risk of loss
- Past performance does not guarantee future results
- Always test thoroughly in backtesting before live trading
- Use at your own risk
- The authors are not responsible for any financial losses

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [pyupbit](https://github.com/sharebook-kr/pyupbit) for Upbit API integration
- Modern Python development community for best practices

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

<div align="center">

**Made with ❤️ for quantitative trading**

⭐ Star this repo if you find it useful!

</div>
