"""
Unit tests for Monte Carlo simulation module.
"""

import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.backtester.engine import BacktestConfig, BacktestResult
from src.backtester.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulator,
    run_monte_carlo,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def mock_backtest_result_for_mc() -> BacktestResult:
    """Mock BacktestResult instance suitable for Monte Carlo."""
    result = MagicMock(spec=BacktestResult)
    result.config = BacktestConfig(initial_capital=1000000)
    result.equity_curve = np.array(
        [1_000_000, 1_010_000, 1_005_000, 1_020_000, 1_015_000, 1_030_000]
    )
    result.dates = np.array(
        [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
            datetime.date(2023, 1, 3),
            datetime.date(2023, 1, 4),
            datetime.date(2023, 1, 5),
            datetime.date(2023, 1, 6),
        ]
    )
    return result


@pytest.fixture
def mock_empty_backtest_result_for_mc() -> BacktestResult:
    """Mock BacktestResult instance with empty equity curve for Monte Carlo."""
    result = MagicMock(spec=BacktestResult)
    result.config = BacktestConfig(initial_capital=1000000)
    result.equity_curve = np.array([])
    result.dates = np.array([])
    return result


class TestMonteCarloResult:
    """Tests for MonteCarloResult dataclass."""

    def test_initialization(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        mc_result = MonteCarloResult(
            original_result=mock_backtest_result_for_mc,
            n_simulations=10,
            simulated_returns=np.zeros((10, 5)),
            simulated_cagrs=np.ones(10) * 10,
            simulated_mdds=np.ones(10) * 5,
            simulated_sharpes=np.ones(10) * 1.0,
            mean_cagr=10.0,
            std_cagr=1.0,
            mean_mdd=5.0,
            std_mdd=0.5,
            mean_sharpe=1.0,
            std_sharpe=0.1,
            cagr_ci_lower=9.0,
            cagr_ci_upper=11.0,
            mdd_ci_lower=4.0,
            mdd_ci_upper=6.0,
            sharpe_ci_lower=0.9,
            sharpe_ci_upper=1.1,
            cagr_percentiles={5: 9.5, 50: 10.0, 95: 10.5},
            mdd_percentiles={5: 4.5, 50: 5.0, 95: 5.5},
        )
        assert mc_result.n_simulations == 10
        assert mc_result.mean_cagr == 10.0

    def test_repr(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        mc_result = MonteCarloResult(
            original_result=mock_backtest_result_for_mc,
            n_simulations=10,
            simulated_returns=np.zeros((10, 5)),
            simulated_cagrs=np.ones(10) * 10,
            simulated_mdds=np.ones(10) * 5,
            simulated_sharpes=np.ones(10) * 1.0,
            mean_cagr=10.0,
            std_cagr=1.0,
            mean_mdd=5.0,
            std_mdd=0.5,
            mean_sharpe=1.0,
            std_sharpe=0.1,
            cagr_ci_lower=9.0,
            cagr_ci_upper=11.0,
            mdd_ci_lower=4.0,
            mdd_ci_upper=6.0,
            sharpe_ci_lower=0.9,
            sharpe_ci_upper=1.1,
            cagr_percentiles={5: 9.5, 50: 10.0, 95: 10.5},
            mdd_percentiles={5: 4.5, 50: 5.0, 95: 5.5},
        )
        assert "MonteCarloResult(n_simulations=10, mean_cagr=10.00%)" == repr(mc_result)


class TestMonteCarloSimulator:
    """Tests for MonteCarloSimulator class."""

    def test_init_from_config_capital(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        assert simulator.initial_capital == 1000000
        expected_returns = np.array([0.01, -0.004950495, 0.014925373, -0.004901961, 0.014778325])
        assert np.allclose(simulator.daily_returns, expected_returns)

    def test_init_explicit_capital(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc, initial_capital=2000000)
        assert simulator.initial_capital == 2000000

    def test_init_empty_equity_curve(self, mock_empty_backtest_result_for_mc: BacktestResult) -> None:
        with patch("src.backtester.monte_carlo.logger.warning") as mock_warning:
            simulator = MonteCarloSimulator(mock_empty_backtest_result_for_mc)
            assert simulator.initial_capital == 1000000 # Falls back to default 1.0
            assert np.allclose(simulator.daily_returns, np.array([0.0]))
            mock_warning.assert_called_once_with("No valid returns found for Monte Carlo simulation")

    def test_init_single_point_equity_curve(self) -> None:
        result = MagicMock(spec=BacktestResult)
        result.config = BacktestConfig(initial_capital=1000000)
        result.equity_curve = np.array([1_000_000])
        with patch("src.backtester.monte_carlo.logger.warning") as mock_warning:
            simulator = MonteCarloSimulator(result)
            assert simulator.initial_capital == 1_000_000
            assert np.allclose(simulator.daily_returns, np.array([0.0])) # Should be 0.0
            mock_warning.assert_called_once_with("No valid returns found for Monte Carlo simulation")

    @patch("numpy.random.choice")
    def test_bootstrap_simulation(self, mock_choice: MagicMock, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        mock_choice.return_value = np.tile(simulator.daily_returns[:n_periods], (n_simulations, 1))

        mc_result = simulator._bootstrap_simulation(n_simulations, n_periods)
        assert isinstance(mc_result, MonteCarloResult)
        assert mc_result.n_simulations == n_simulations
        assert mc_result.simulated_returns.shape == (n_simulations, n_periods)
        mock_choice.assert_called_once()
        assert mc_result.mean_cagr > 0

    def test_bootstrap_simulation_empty_returns(self, mock_empty_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_empty_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        mc_result = simulator._bootstrap_simulation(n_simulations, n_periods)
        assert np.all(mc_result.simulated_returns == 0.0) # Should be all zeros

    @patch("numpy.random.normal")
    def test_parametric_simulation(self, mock_normal: MagicMock, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        mock_normal.return_value = np.zeros((n_simulations, n_periods)) # Simplistic mock

        mc_result = simulator._parametric_simulation(n_simulations, n_periods)
        assert isinstance(mc_result, MonteCarloResult)
        assert mc_result.n_simulations == n_simulations
        assert mc_result.simulated_returns.shape == (n_simulations, n_periods)
        mock_normal.assert_called_once()

    def test_parametric_simulation_empty_returns(self, mock_empty_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_empty_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        with patch("numpy.random.normal", return_value=np.zeros((n_simulations, n_periods))) as mock_normal:
            mc_result = simulator._parametric_simulation(n_simulations, n_periods)
            assert np.all(mc_result.simulated_returns == 0.0)
            mock_normal.assert_called_once()
            args, kwargs = mock_normal.call_args
            assert args[0] == 0.0 # Mean
            assert args[1] == 0.0 # Std (from np.std([0.0]))

    def test_process_simulations(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 3
        # Use simple returns to make calculations predictable
        simulated_returns = np.array(
            [
                [0.01, 0.01, 0.01],  # CAGR should be positive
                [-0.01, -0.01, -0.01],  # CAGR should be negative
                [0.02, -0.02, 0.01],  # Mixed
            ]
        )
        
        mc_result = simulator._process_simulations(simulated_returns, n_simulations)
        
        assert mc_result.simulated_cagrs.shape == (n_simulations,)
        assert mc_result.simulated_mdds.shape == (n_simulations,)
        assert mc_result.simulated_sharpes.shape == (n_simulations,)
        
        assert mc_result.mean_cagr == pytest.approx(np.mean(mc_result.simulated_cagrs))
        assert mc_result.std_cagr == pytest.approx(np.std(mc_result.simulated_cagrs))
        assert mc_result.cagr_ci_lower < mc_result.cagr_ci_upper
        assert 50 in mc_result.cagr_percentiles

        # Test specific CAGR calculation (e.g., first simulation)
        # 1.0M * (1.01)^3 - 1 = 3.0301% daily return, annualized
        # (1_000_000 * (1+0.01)**3 / 1_000_000 - 1) * 100 * (365/3)
        # CAGR = ((final / initial)^(365/num_periods) - 1) * 100
        initial_capital = simulator.initial_capital
        equity_final_sim1 = initial_capital * (1 + 0.01)**3
        expected_cagr_sim1 = ((equity_final_sim1 / initial_capital)**(365/3) - 1) * 100
        assert mc_result.simulated_cagrs[0] == pytest.approx(expected_cagr_sim1)

    def test_process_simulations_zero_periods(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 1
        simulated_returns = np.array([[]]) # Zero periods
        mc_result = simulator._process_simulations(simulated_returns, n_simulations)
        assert mc_result.simulated_cagrs[0] == pytest.approx(-100.0) # Should be -100%
        assert mc_result.simulated_mdds[0] == 0.0 # No drawdown with 0 periods
        assert mc_result.simulated_sharpes[0] == 0.0 # No sharpe with 0 periods

    def test_simulate_bootstrap_method(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        with patch.object(simulator, '_bootstrap_simulation') as mock_bootstrap:
            mock_bootstrap.return_value = MagicMock(spec=MonteCarloResult)
            mc_result = simulator.simulate(n_simulations, n_periods, method="bootstrap")
            mock_bootstrap.assert_called_once_with(n_simulations, n_periods)
            assert isinstance(mc_result, MonteCarloResult)

    def test_simulate_parametric_method(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        n_simulations = 10
        n_periods = 5
        with patch.object(simulator, '_parametric_simulation') as mock_parametric:
            mock_parametric.return_value = MagicMock(spec=MonteCarloResult)
            mc_result = simulator.simulate(n_simulations, n_periods, method="parametric")
            mock_parametric.assert_called_once_with(n_simulations, n_periods)
            assert isinstance(mc_result, MonteCarloResult)

    def test_simulate_unknown_method(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        with pytest.raises(ValueError, match="Unknown simulation method: invalid"):
            simulator.simulate(method="invalid")

    def test_simulate_random_seed(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator1 = MonteCarloSimulator(mock_backtest_result_for_mc)
        mc_result1 = simulator1.simulate(random_seed=42)
        simulator2 = MonteCarloSimulator(mock_backtest_result_for_mc)
        mc_result2 = simulator2.simulate(random_seed=42)
        assert np.array_equal(mc_result1.simulated_returns, mc_result2.simulated_returns)
        assert np.allclose(mc_result1.simulated_cagrs, mc_result2.simulated_cagrs)


    def test_probability_of_loss(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        mc_result = MagicMock(spec=MonteCarloResult)
        mc_result.simulated_cagrs = np.array([10, -5, 20, -10, 0])
        mc_result.n_simulations = 5
        assert simulator.probability_of_loss(mc_result) == 2 / 5

    def test_value_at_risk(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        mc_result = MagicMock(spec=MonteCarloResult)
        mc_result.simulated_cagrs = np.array([10, -5, 20, -10, 0, 30, -15, 5])
        assert simulator.value_at_risk(mc_result, confidence=0.95) == pytest.approx(np.percentile(mc_result.simulated_cagrs, 5)) # 1 - 0.95 = 0.05 = 5th percentile

    def test_conditional_value_at_risk(self, mock_backtest_result_for_mc: BacktestResult) -> None:
        simulator = MonteCarloSimulator(mock_backtest_result_for_mc)
        mc_result = MagicMock(spec=MonteCarloResult)
        mc_result.simulated_cagrs = np.array([10, -5, 20, -10, 0, 30, -15, 5])
        assert simulator.conditional_value_at_risk(mc_result, confidence=0.95) == pytest.approx(-15.0)


class TestRunMonteCarlo:
    """Tests for run_monte_carlo convenience function."""

    @patch("src.backtester.monte_carlo.MonteCarloSimulator")
    def test_run_monte_carlo(
        self, MockMonteCarloSimulator: MagicMock, mock_backtest_result_for_mc: BacktestResult
    ) -> None:
        """Test run_monte_carlo convenience function."""
        # Mock simulator instance and its simulate method
        mock_simulator_instance = MockMonteCarloSimulator.return_value
        mock_mc_result = MagicMock(spec=MonteCarloResult)
        mock_simulator_instance.simulate.return_value = mock_mc_result

        result = run_monte_carlo(
            result=mock_backtest_result_for_mc,
            n_simulations=500,
            method="parametric",
            random_seed=123,
        )

        MockMonteCarloSimulator.assert_called_once_with(
            mock_backtest_result_for_mc
        )
        mock_simulator_instance.simulate.assert_called_once_with(
            n_simulations=500, method="parametric", random_seed=123
        )
        assert result == mock_mc_result
