"""
Unit tests for parameter optimization module.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.backtester.engine import BacktestConfig, BacktestResult
from src.backtester.optimization import (
    OptimizationResult,
    ParameterOptimizer,
    optimize_strategy_parameters,
)
from src.strategies.base import Strategy


@pytest.fixture
def mock_strategy_factory() -> MagicMock:
    """Mock strategy factory function."""
    mock_strategy = MagicMock(spec=Strategy)
    mock_strategy.name = "MockStrategy"
    mock_strategy.param1 = 10  # Example param for name generation
    mock_strategy.param2 = "A"  # Example param for name generation
    return MagicMock(return_value=mock_strategy)


@pytest.fixture
def mock_backtest_config() -> BacktestConfig:
    """Mock BacktestConfig instance."""
    return BacktestConfig(initial_capital=1000000)


@pytest.fixture
def mock_backtest_result() -> BacktestResult:
    """Mock BacktestResult instance."""
    result = MagicMock(spec=BacktestResult)
    result.cagr = 10.0
    result.sharpe_ratio = 1.5
    result.mdd = 0.05
    result.total_return = 0.1
    result.calmar_ratio = 2.0
    result.win_rate = 0.6
    result.profit_factor = 1.2
    return result


@pytest.fixture
def param_grid_simple() -> dict[str, list[Any]]:
    """A simple parameter grid for testing."""
    return {"p1": [1, 2], "p2": ["A", "B"]}


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass."""

    def test_initialization(self, mock_backtest_result: BacktestResult) -> None:
        result = OptimizationResult(
            best_params={"p1": 1},
            best_result=mock_backtest_result,
            best_score=1.5,
            all_results=[({"p1": 1}, mock_backtest_result, 1.5)],
            optimization_metric="sharpe_ratio",
        )
        assert result.best_params == {"p1": 1}
        assert result.best_score == 1.5

    def test_repr(self) -> None:
        result = OptimizationResult(
            best_params={"p1": 1},
            best_result=MagicMock(spec=BacktestResult),
            best_score=1.5,
            all_results=[],
            optimization_metric="sharpe_ratio",
        )
        assert repr(result) == "OptimizationResult(metric=sharpe_ratio, best_score=1.50)"


class TestParameterOptimizer:
    """Tests for ParameterOptimizer class."""

    @pytest.fixture
    def optimizer(
        self,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
    ) -> ParameterOptimizer:
        return ParameterOptimizer(
            strategy_factory=mock_strategy_factory,
            tickers=["KRW-BTC"],
            interval="day",
            config=mock_backtest_config,
        )

    def test_init(
        self,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
    ) -> None:
        optimizer = ParameterOptimizer(
            strategy_factory=mock_strategy_factory,
            tickers=["KRW-BTC"],
            interval="day",
            config=mock_backtest_config,
            n_workers=4,
        )
        assert optimizer.strategy_factory == mock_strategy_factory
        assert optimizer.n_workers == 4

    def test_optimize_grid_method(
        self,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
        param_grid_simple: dict[str, list[Any]],
    ) -> None:
        optimizer = ParameterOptimizer(
            strategy_factory=mock_strategy_factory,
            tickers=["KRW-BTC"],
            interval="day",
            config=mock_backtest_config,
        )
        with patch("src.backtester.optimization.grid_search") as mock_grid:
            mock_grid.return_value = OptimizationResult(
                best_params={"p1": 1},
                best_result=MagicMock(spec=BacktestResult),
                best_score=1.5,
                all_results=[],
                optimization_metric="sharpe_ratio",
            )
            result = optimizer.optimize(param_grid_simple, method="grid")
            mock_grid.assert_called_once()
            assert result.best_score == 1.5

    def test_optimize_random_method(
        self,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
        param_grid_simple: dict[str, list[Any]],
    ) -> None:
        optimizer = ParameterOptimizer(
            strategy_factory=mock_strategy_factory,
            tickers=["KRW-BTC"],
            interval="day",
            config=mock_backtest_config,
        )
        with patch("src.backtester.optimization.random_search") as mock_random:
            mock_random.return_value = OptimizationResult(
                best_params={"p1": 2},
                best_result=MagicMock(spec=BacktestResult),
                best_score=2.0,
                all_results=[],
                optimization_metric="sharpe_ratio",
            )
            result = optimizer.optimize(param_grid_simple, method="random")
            mock_random.assert_called_once()
            assert result.best_score == 2.0

    def test_optimize_unknown_method_raises_error(
        self,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
        param_grid_simple: dict[str, list[Any]],
    ) -> None:
        """Test that unknown optimization method raises ValueError."""
        optimizer = ParameterOptimizer(
            strategy_factory=mock_strategy_factory,
            tickers=["KRW-BTC"],
            interval="day",
            config=mock_backtest_config,
        )
        with pytest.raises(ValueError, match="Unknown optimization method: invalid"):
            optimizer.optimize(param_grid_simple, method="invalid")


class TestOptimizeStrategyParameters:
    """Tests for optimize_strategy_parameters convenience function."""

    @patch("src.backtester.optimization.grid_search")
    def test_optimize_strategy_parameters(
        self,
        mock_grid_search: MagicMock,
        mock_strategy_factory: MagicMock,
        mock_backtest_config: BacktestConfig,
        param_grid_simple: dict[str, list[Any]],
    ) -> None:
        mock_optimization_result = OptimizationResult(
            best_params={"p1": 1},
            best_result=MagicMock(spec=BacktestResult),
            best_score=1.5,
            all_results=[],
            optimization_metric="cagr",
        )
        mock_grid_search.return_value = mock_optimization_result

        tickers = ["KRW-BTC"]
        interval = "day"

        result = optimize_strategy_parameters(
            strategy_factory=mock_strategy_factory,
            param_grid=param_grid_simple,
            tickers=tickers,
            interval=interval,
            config=mock_backtest_config,
            metric="cagr",
            maximize=False,
            method="grid",
            n_iter=50,
            n_workers=2,
        )

        assert result == mock_optimization_result
