"""
Analysis subpackage for backtesting.

Contains modules for:
- Bootstrap analysis
- Monte Carlo simulation
- Permutation testing
- Robustness analysis
"""

from src.backtester.analysis.bootstrap_analysis import (
    BootstrapAnalyzer,
    BootstrapResult,
)
from src.backtester.analysis.bootstrap_backtest import simple_backtest_vectorized
from src.backtester.analysis.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulator,
    run_monte_carlo,
)
from src.backtester.analysis.permutation_test import (
    PermutationTester,
    PermutationTestResult,
)
from src.backtester.analysis.robustness_analysis import RobustnessAnalyzer
from src.backtester.analysis.robustness_models import RobustnessReport

__all__ = [
    # Bootstrap
    "BootstrapAnalyzer",
    "BootstrapResult",
    "simple_backtest_vectorized",
    # Monte Carlo
    "MonteCarloResult",
    "MonteCarloSimulator",
    "run_monte_carlo",
    # Permutation
    "PermutationTester",
    "PermutationTestResult",
    # Robustness
    "RobustnessAnalyzer",
    "RobustnessReport",
]
