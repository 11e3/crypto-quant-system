# Claude Code Guide for Crypto Quant System

**FOR CLAUDE CODE USE ONLY** - This guide provides essential context for AI-assisted development.

## Project Quick Reference

**Crypto Quant System** - Production-grade cryptocurrency trading platform with backtesting, live trading, and portfolio optimization.

**Tech Stack**: Python 3.14+ | MyPy (97.8% pass) | Pytest (80%+ coverage) | Ruff | uv

## Core Modules

| Module | Path | Purpose |
|--------|------|---------|
| Backtesting | [src/backtester/engine/](src/backtester/engine/) | Event-driven & vectorized engines |
| Strategies | [src/strategies/](src/strategies/) | VBO, Mean Reversion, Momentum, ORB |
| Live Bot | [src/execution/bot/](src/execution/bot/) | Production trading bot |
| Risk | [src/risk/](src/risk/) | Portfolio optimization, VaR/CVaR |
| Data | [src/data/](src/data/) | Upbit data collection & caching |
| Web UI | [src/web/](src/web/) | Streamlit multi-page app |
| Exchange | [src/exchange/](src/exchange/) | Exchange abstraction (Upbit) |

## Critical Development Workflow

### Test-Driven Development (TDD) - MANDATORY

**ALWAYS follow TDD for new features:**

1. **Write Tests First** (Red Phase)
   ```bash
   # Create test file first
   tests/unit/test_strategies/test_my_strategy.py

   # Write failing tests
   uv run pytest tests/unit/test_strategies/test_my_strategy.py -v
   # Expected: Tests fail (RED)
   ```

2. **Implement Feature** (Green Phase)
   ```python
   # Implement minimum code to pass tests
   src/strategies/my_strategy.py

   # Run tests again
   uv run pytest tests/unit/test_strategies/test_my_strategy.py -v
   # Expected: Tests pass (GREEN)
   ```

3. **Refactor** (Refactor Phase)
   ```bash
   # Improve code while keeping tests green
   # Run tests continuously
   uv run pytest tests/unit/test_strategies/test_my_strategy.py -v
   ```

### Quality Gate - Run After EVERY Code Change

**CRITICAL**: Run these checks after every unit of work (single feature/fix):

```bash
# 1. Format code (auto-fix)
uv run ruff format src/ tests/

# 2. Lint code (auto-fix when possible)
uv run ruff check --fix src/ tests/

# 3. Type check (no auto-fix - must resolve manually)
uv run mypy src/

# 4. Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# 5. Check coverage threshold (80%+ required)
uv run pytest --cov=src --cov-report=html --cov-fail-under=80
```

**All checks MUST pass before committing.**

### Git Workflow - Commit & Push Pattern

After passing quality gates:

```bash
# 1. Check git status
git status

# 2. Stage changes
git add .

# 3. Commit with conventional commit message
git commit -m "feat: Add RSI strategy with TDD"
# or
git commit -m "fix: Resolve type error in metrics calculator"
# or
git commit -m "test: Add integration tests for walk-forward analysis"
# or
git commit -m "refactor: Extract position sizer from engine"

# 4. Push to remote
git push origin <branch-name>

# Common branch patterns:
# - feature/rsi-strategy
# - fix/metrics-calculation-bug
# - refactor/split-large-module
```

**Conventional Commit Prefixes**:
- `feat:` - New feature
- `fix:` - Bug fix
- `test:` - Test additions/changes
- `refactor:` - Code restructuring (no behavior change)
- `docs:` - Documentation updates
- `style:` - Code style changes (formatting)
- `perf:` - Performance improvements
- `chore:` - Build/tooling changes

### Complete Development Cycle Example

```bash
# === RED PHASE ===
# 1. Write test first
cat > tests/unit/test_strategies/test_rsi_strategy.py << 'EOF'
import pytest
from src.strategies.rsi_strategy import RSIStrategy

def test_rsi_strategy_initialization():
    """Test RSI strategy initializes correctly."""
    strategy = RSIStrategy(period=14, overbought=70, oversold=30)
    assert strategy.period == 14
    assert strategy.overbought == 70
    assert strategy.oversold == 30

def test_rsi_strategy_generates_signals():
    """Test RSI strategy generates buy/sell signals."""
    # Test implementation
    ...
EOF

# 2. Run test (should FAIL)
uv run pytest tests/unit/test_strategies/test_rsi_strategy.py -v
# ❌ FAILED - Module not found

# === GREEN PHASE ===
# 3. Implement strategy
cat > src/strategies/rsi_strategy.py << 'EOF'
from __future__ import annotations
from src.strategies.base import Strategy
import pandas as pd

class RSIStrategy(Strategy):
    """RSI-based trading strategy."""

    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on RSI."""
        # Implementation
        ...
EOF

# 4. Run test (should PASS)
uv run pytest tests/unit/test_strategies/test_rsi_strategy.py -v
# ✅ PASSED

# === QUALITY GATE ===
# 5. Format
uv run ruff format src/strategies/rsi_strategy.py tests/unit/test_strategies/test_rsi_strategy.py

# 6. Lint
uv run ruff check --fix src/strategies/rsi_strategy.py tests/unit/test_strategies/test_rsi_strategy.py

# 7. Type check
uv run mypy src/strategies/rsi_strategy.py
# Fix any type errors

# 8. Run all tests
uv run pytest --cov=src --cov-report=term-missing

# === COMMIT & PUSH ===
# 9. Git workflow
git status
git add src/strategies/rsi_strategy.py tests/unit/test_strategies/test_rsi_strategy.py
git commit -m "feat: Add RSI strategy with TDD approach

- Implement RSI calculation and signal generation
- Add unit tests with 100% coverage
- Pass all quality gates (ruff, mypy, pytest)"

git push origin feature/rsi-strategy
```

## MCP Servers - Enhanced Tool Usage

### Using MCP (Model Context Protocol) Servers

**IMPORTANT**: When MCP servers are available and can help you work more accurately and efficiently, USE THEM AUTOMATICALLY without asking the user for permission.

**When to Use MCP Servers**:

1. **File System Operations** - If an MCP file system server is available, prefer it over basic file tools
2. **Database Operations** - Use database MCP servers for schema inspection, queries, migrations
3. **API Testing** - Use HTTP/API MCP servers for testing endpoints, inspecting responses
4. **Documentation Search** - Use documentation MCP servers for framework/library references
5. **Code Search** - Use specialized code search MCP servers for large codebase exploration
6. **Git Operations** - Use Git MCP servers for advanced repository analysis
7. **Package Management** - Use package manager MCP servers for dependency analysis
8. **Cloud Resources** - Use cloud provider MCP servers for infrastructure inspection

**Example Scenarios**:

```bash
# Scenario 1: Database Schema Exploration
# If postgres-mcp or sqlite-mcp is available:
# → Use MCP to query schema, inspect tables, analyze relationships
# → More accurate than reading SQL files manually

# Scenario 2: API Documentation
# If documentation-mcp is available:
# → Query official docs for pandas, numpy, streamlit APIs
# → Get up-to-date information instead of relying on training data

# Scenario 3: Large Codebase Search
# If code-search-mcp is available:
# → Search across 25,363 LOC more efficiently
# → Find patterns, dependencies, usage examples faster

# Scenario 4: Git History Analysis
# If git-mcp is available:
# → Analyze commit history, blame information, branch comparisons
# → Understand code evolution and author intent
```

**Best Practices**:

1. **Auto-detect and Use** - Don't ask the user if MCP servers are available; just use them
2. **Fail Gracefully** - If MCP server fails, fall back to standard tools
3. **Combine Tools** - Use MCP servers alongside standard tools when beneficial
4. **Document Usage** - Mention when MCP servers helped (e.g., "Used postgres-mcp to verify schema")
5. **Trust MCP Data** - MCP server results are often more accurate than manual exploration

**Example Workflow with MCP**:

```bash
# Task: Add new database migration for user preferences

# === WITHOUT MCP ===
# 1. Manually read migration files
# 2. Guess at schema structure
# 3. Write migration
# 4. Test manually

# === WITH database-mcp ===
# 1. Query current schema via MCP
# 2. Verify table relationships via MCP
# 3. Check constraints and indexes via MCP
# 4. Write accurate migration based on MCP data
# 5. Test using MCP query tools

# Result: More accurate, faster, fewer errors
```

**Integration with Quality Gate**:

MCP servers can enhance the quality gate process:

```bash
# Enhanced quality checks with MCP
# 1. Use code-search-mcp to find similar patterns in codebase
# 2. Use documentation-mcp to verify API usage is correct
# 3. Use database-mcp to validate schema changes
# 4. Run standard quality gates (ruff, mypy, pytest)
# 5. Use git-mcp to verify no unintended files are being committed
```

**Remember**: MCP servers are PRODUCTIVITY ENHANCERS. Use them automatically when available to work faster and more accurately.

## Code Standards

### Type Hints (NON-NEGOTIABLE)

```python
from __future__ import annotations  # ALWAYS include

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0
) -> float:
    """Calculate Sharpe ratio."""
    ...
```

### Docstrings (Google Style)

```python
def run_backtest(
    strategy: Strategy,
    data_files: list[str],
    config: BacktestConfig,
) -> BacktestResult:
    """Run a backtest with the given strategy and data.

    Args:
        strategy: Trading strategy to backtest
        data_files: List of paths to OHLCV data files (Parquet format)
        config: Backtest configuration (capital, fees, slippage, etc.)

    Returns:
        BacktestResult containing performance metrics and trades

    Raises:
        DataLoadError: If data files cannot be loaded
        ValidationError: If configuration is invalid
    """
    ...
```

### Import Order (Enforced by isort)

```python
from __future__ import annotations  # 1. Future imports

import logging                       # 2. Standard library
from pathlib import Path
from typing import Protocol

import pandas as pd                  # 3. Third-party
import numpy as np

from src.backtester.models import BacktestConfig  # 4. Local
from src.strategies.base import Strategy
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `EventDrivenBacktestEngine` |
| Functions | snake_case | `calculate_metrics` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_FEE_RATE` |
| Private | _leading_underscore | `_internal_method` |
| Type Variables | TPascalCase | `TStrategy` |

## Architecture Patterns

### 1. Strategy Pattern (Composable Conditions)

```python
from src.strategies.base import Strategy
from src.strategies.base_conditions import Condition

class MyStrategy(Strategy):
    def __init__(self, param1: float):
        self.entry_condition = MyEntryCondition(param1)
        self.exit_condition = MyExitCondition()
```

### 2. Protocol Interfaces (Dependency Injection)

```python
from typing import Protocol

class BacktestEngineProtocol(Protocol):
    def run(self, strategy: Strategy, data: pd.DataFrame) -> BacktestResult: ...
```

### 3. Factory Pattern (Extensibility)

```python
from src.exchange import ExchangeFactory
exchange = ExchangeFactory.create("upbit", api_key, secret_key)
```

### 4. Event Bus Pattern (Decoupling)

```python
from src.execution.event_bus import EventBus, OrderFilledEvent
event_bus = EventBus()
event_bus.subscribe(OrderFilledEvent, handler)
event_bus.publish(OrderFilledEvent(...))
```

## Common Tasks

### Adding a New Strategy (TDD Approach)

```bash
# 1. Write test first (RED)
cat > tests/unit/test_strategies/test_my_strategy.py
uv run pytest tests/unit/test_strategies/test_my_strategy.py -v  # FAIL

# 2. Implement strategy (GREEN)
cat > src/strategies/my_strategy.py
uv run pytest tests/unit/test_strategies/test_my_strategy.py -v  # PASS

# 3. Quality gate
uv run ruff format src/strategies/my_strategy.py tests/unit/test_strategies/test_my_strategy.py
uv run ruff check --fix src/strategies/my_strategy.py tests/unit/test_strategies/test_my_strategy.py
uv run mypy src/strategies/my_strategy.py
uv run pytest --cov=src --cov-report=term-missing

# 4. Commit & push
git add src/strategies/my_strategy.py tests/unit/test_strategies/test_my_strategy.py
git commit -m "feat: Add My Strategy with TDD"
git push origin feature/my-strategy
```

Strategy auto-registers in web UI via `StrategyRegistry`.

### Adding a New Metric (TDD Approach)

```bash
# 1. Write test first
cat > tests/unit/test_backtester/test_new_metric.py

# 2. Update PerformanceMetrics dataclass
# src/backtester/models.py

# 3. Add calculation
# src/backtester/engine/metrics_calculator.py

# 4. Add display logic
# src/web/components/metrics/

# 5. Quality gate + commit
```

### Fixing a Bug (TDD Approach)

```bash
# 1. Write failing test that reproduces bug (RED)
cat > tests/unit/test_bug_reproduction.py
uv run pytest tests/unit/test_bug_reproduction.py -v  # FAIL

# 2. Fix the bug (GREEN)
# Edit relevant source file
uv run pytest tests/unit/test_bug_reproduction.py -v  # PASS

# 3. Quality gate
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run mypy src/
uv run pytest --cov=src

# 4. Commit
git add <fixed_files> tests/unit/test_bug_reproduction.py
git commit -m "fix: Resolve calculation error in Sharpe ratio

- Add regression test for negative returns case
- Fix division by zero when std is 0
- All tests pass with 80%+ coverage"
git push origin fix/sharpe-ratio-bug
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Slower, multiple components
└── fixtures/          # Reusable test data
```

### Writing Tests (Pytest)

```python
import pytest
from src.backtester import EventDrivenBacktestEngine

def test_engine_initialization():
    """Test engine initializes with correct config."""
    config = BacktestConfig(initial_capital=1_000_000)
    engine = EventDrivenBacktestEngine(config)
    assert engine.config.initial_capital == 1_000_000

@pytest.mark.slow
def test_full_backtest_integration():
    """Integration test for full workflow."""
    # Marked as slow - runs separately
    ...
```

### Coverage Requirements

- **80%+ branch coverage** (enforced)
- Focus on business logic
- Use `pytest --cov=src --cov-report=html` to view coverage

## Performance Considerations

1. **Vectorize operations** - Use NumPy/Pandas, avoid Python loops
2. **Cache expensive computations** - Indicators, metrics
3. **Lazy load data** - Don't load everything at once
4. **Profile slow code** - `cProfile`, `py-spy`
5. **Use VectorizedBacktestEngine** - For parameter sweeps

## Security Best Practices

1. **Never commit API keys** - Use `.env` + `.gitignore`
2. **Validate all inputs** - Especially web UI
3. **Use read-only API keys** - For backtesting
4. **Audit bot before deployment** - Live trading is risky
5. **Monitor in real-time** - Set up alerts

## Troubleshooting

### MyPy Type Errors

```bash
# Check specific file
uv run mypy src/backtester/engine/event_driven.py

# Common fix: Third-party library without stubs
import pyupbit  # type: ignore
```

### Import Errors

```bash
uv sync --all-extras
uv run pip install -e .
```

### Test Failures

```bash
# Run specific test
uv run pytest tests/unit/test_backtester/test_engine.py::test_engine_initialization -v

# Run with verbose output
uv run pytest -vv

# Run with print statements visible
uv run pytest -s
```

## Key Principles for Claude Code

1. **TDD First** - Write tests before implementation
2. **Quality Gate Always** - ruff → mypy → pytest after every change
3. **Commit Frequently** - Small, atomic commits with conventional messages
4. **Type Safety** - 100% type coverage, no `Any` types
5. **Test Coverage** - 80%+ minimum, aim for 90%+
6. **SOLID Principles** - Recent refactoring focused on SRP, OCP, DIP
7. **Clean Architecture** - Service layer, protocols, dependency injection
8. **Documentation** - Self-documenting code with type hints + docstrings
9. **Performance** - Vectorized operations, caching, lazy loading
10. **Security** - No secrets in code, input validation, audit trails
11. **Use MCP Servers** - Automatically use available MCP servers for enhanced accuracy and efficiency

## Quick Commands Reference

```bash
# Setup
uv sync --all-extras
pre-commit install

# TDD Cycle
uv run pytest <test_file> -v           # Run specific test
uv run pytest -k <test_name> -v        # Run by name pattern

# Quality Gate (run ALL after every change)
uv run ruff format src/ tests/         # Format
uv run ruff check --fix src/ tests/    # Lint
uv run mypy src/                       # Type check
uv run pytest --cov=src --cov-fail-under=80  # Test + coverage

# Git
git status
git add .
git commit -m "feat: <message>"
git push origin <branch>

# Run app
uv run streamlit run src/web/app.py --server.runOnSave true
uv run python scripts/collect_30min_data.py
```

## Environment Setup

```bash
# Clone repo
git clone <repo-url>
cd crypto-quant-system

# Install dependencies
uv sync --all-extras

# Setup pre-commit hooks
pre-commit install

# Create .env file
cat > .env << 'EOF'
UPBIT_ACCESS_KEY=your_key
UPBIT_SECRET_KEY=your_secret
WEB_SERVER_PORT=8501
LOG_LEVEL=INFO
EOF

# Verify installation
uv run python -c "from src.backtester import EventDrivenBacktestEngine; print('✓ Setup complete')"
```

---

**Last updated**: 2026-01-16

**Remember**: TDD → Quality Gate → Commit → Push. Every. Single. Time.
