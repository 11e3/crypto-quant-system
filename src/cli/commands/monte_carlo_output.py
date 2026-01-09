"""
Monte Carlo CLI output helpers.
"""

from pathlib import Path

from src.backtester.analysis.monte_carlo import MonteCarloResult, MonteCarloSimulator
from src.backtester.models import BacktestResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = ["print_monte_carlo_results", "save_monte_carlo_report"]


def print_monte_carlo_results(
    result: BacktestResult,
    mc_result: MonteCarloResult,
    n_simulations: int,
) -> None:
    """
    Print Monte Carlo simulation results to logger.

    Args:
        result: Original backtest result
        mc_result: Monte Carlo simulation result
        n_simulations: Number of simulations run
    """
    logger.info("\n=== Monte Carlo Simulation Results ===\n")
    logger.info("Original Backtest:")
    logger.info(f"  CAGR: {result.cagr:.2f}%")
    logger.info(f"  MDD: {result.mdd:.2f}%")
    logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")

    logger.info(f"\nSimulation Statistics ({n_simulations} runs):")
    logger.info(f"  Mean CAGR: {mc_result.mean_cagr:.2f}% (std: {mc_result.std_cagr:.2f}%)")
    logger.info(f"  Mean MDD: {mc_result.mean_mdd:.2f}% (std: {mc_result.std_mdd:.2f}%)")
    logger.info(f"  Mean Sharpe: {mc_result.mean_sharpe:.2f} (std: {mc_result.std_sharpe:.2f})")

    logger.info("\n95% Confidence Intervals:")
    logger.info(f"  CAGR: [{mc_result.cagr_ci_lower:.2f}%, {mc_result.cagr_ci_upper:.2f}%]")
    logger.info(f"  MDD: [{mc_result.mdd_ci_lower:.2f}%, {mc_result.mdd_ci_upper:.2f}%]")
    logger.info(f"  Sharpe: [{mc_result.sharpe_ci_lower:.2f}, {mc_result.sharpe_ci_upper:.2f}]")

    logger.info("\nPercentiles:")
    logger.info("  CAGR:")
    for p, val in mc_result.cagr_percentiles.items():
        logger.info(f"    {p}th: {val:.2f}%")
    logger.info("  MDD:")
    for p, val in mc_result.mdd_percentiles.items():
        logger.info(f"    {p}th: {val:.2f}%")

    # Risk metrics
    simulator = MonteCarloSimulator(result)
    prob_loss = simulator.probability_of_loss(mc_result)
    var_95 = simulator.value_at_risk(mc_result, confidence=0.95)
    cvar_95 = simulator.conditional_value_at_risk(mc_result, confidence=0.95)

    logger.info("\nRisk Metrics:")
    logger.info(f"  Probability of Loss: {prob_loss * 100:.1f}%")
    logger.info(f"  VaR (95%): {var_95:.2f}%")
    logger.info(f"  CVaR (95%): {cvar_95:.2f}%")


def save_monte_carlo_report(
    result: BacktestResult,
    output: str,
    strategy_obj: object,
    config: object,
    ticker_list: list[str],
) -> None:
    """
    Save Monte Carlo report to file.

    Args:
        result: Backtest result
        output: Output path
        strategy_obj: Strategy object
        config: Backtest config
        ticker_list: List of tickers
    """
    from datetime import datetime

    from src.backtester.report_pkg.report import generate_report

    output_path = Path(output)
    if output_path.is_dir() or not output_path.suffix:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path / f"monte_carlo_{timestamp}.html"
    else:
        output_path = Path(output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_report(
        result,
        save_path=output_path,
        show=False,
        format="html",
        strategy_obj=strategy_obj,
        config=config,
        tickers=ticker_list,
    )
    logger.info(f"\nReport saved: {output_path}")
