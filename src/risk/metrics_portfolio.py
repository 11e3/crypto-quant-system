"""
Portfolio correlation and concentration metrics.
"""

import numpy as np
import pandas as pd

__all__ = [
    "calculate_portfolio_correlation",
    "calculate_position_concentration",
]


def calculate_portfolio_correlation(
    asset_returns: dict[str, np.ndarray],
) -> tuple[float, float, float, pd.DataFrame]:
    """
    Calculate correlation metrics between assets in portfolio.

    Args:
        asset_returns: Dictionary mapping ticker to returns array

    Returns:
        Tuple of (avg_correlation, max_correlation, min_correlation, correlation_matrix)
    """
    if len(asset_returns) < 2:
        return 0.0, 0.0, 0.0, pd.DataFrame()

    # Align returns by index (assuming same length or using common dates)
    returns_df = pd.DataFrame(asset_returns)

    # Calculate correlation matrix
    correlation_matrix = returns_df.corr()

    # Get upper triangle (excluding diagonal)
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
    correlations = correlation_matrix.where(mask).stack()

    if len(correlations) > 0:
        avg_correlation = float(correlations.mean())
        max_correlation = float(correlations.max())
        min_correlation = float(correlations.min())
    else:
        avg_correlation = max_correlation = min_correlation = 0.0

    return avg_correlation, max_correlation, min_correlation, correlation_matrix


def calculate_position_concentration(
    position_values: dict[str, float],
    total_portfolio_value: float,
) -> tuple[float, float]:
    """
    Calculate position concentration metrics.

    Args:
        position_values: Dictionary mapping ticker to position value
        total_portfolio_value: Total portfolio value

    Returns:
        Tuple of (max_position_pct, hhi)
        - max_position_pct: Maximum position as % of portfolio
        - hhi: Herfindahl-Hirschman Index (0-1, higher = more concentrated)
    """
    if total_portfolio_value == 0 or len(position_values) == 0:
        return 0.0, 0.0

    # Calculate position percentages
    position_pcts = {
        ticker: value / total_portfolio_value for ticker, value in position_values.items()
    }

    # Maximum position percentage
    max_position_pct = max(position_pcts.values()) if position_pcts else 0.0

    # Herfindahl-Hirschman Index (HHI)
    # Sum of squared position percentages
    hhi = sum(pct**2 for pct in position_pcts.values())

    return max_position_pct, hhi
