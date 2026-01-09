"""
VaR and CVaR calculation utilities.
"""

import numpy as np

__all__ = ["calculate_var", "calculate_cvar"]


def calculate_var(
    returns: np.ndarray,
    confidence_level: float = 0.95,
) -> float:
    """
    Calculate Value at Risk (VaR) using historical simulation.

    VaR represents the maximum expected loss over a given time period
    at a specified confidence level.

    Args:
        returns: Array of portfolio returns
        confidence_level: Confidence level (e.g., 0.95 for 95% VaR)

    Returns:
        VaR value (negative value representing loss)
    """
    if len(returns) == 0:
        return 0.0

    percentile = (1 - confidence_level) * 100
    var: float = float(-np.percentile(returns, percentile))

    return var


def calculate_cvar(
    returns: np.ndarray,
    confidence_level: float = 0.95,
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) using historical simulation.

    CVaR (also known as Expected Shortfall) is the expected loss
    given that the loss exceeds VaR.

    Args:
        returns: Array of portfolio returns
        confidence_level: Confidence level (e.g., 0.95 for 95% CVaR)

    Returns:
        CVaR value (negative value representing expected loss)
    """
    if len(returns) == 0:
        return 0.0

    var = calculate_var(returns, confidence_level)
    threshold = -var
    tail_losses = returns[returns <= threshold]

    cvar: float = float(-np.mean(tail_losses)) if len(tail_losses) > 0 else var

    return cvar
