"""
Portfolio optimization result models.

Contains data models for portfolio weights and allocation results.
"""

from dataclasses import dataclass


@dataclass
class PortfolioWeights:
    """Portfolio allocation weights."""

    weights: dict[str, float]  # ticker -> weight (0.0 to 1.0)
    method: str  # "mpt", "risk_parity", "kelly"
    expected_return: float | None = None
    portfolio_volatility: float | None = None
    sharpe_ratio: float | None = None

    def __repr__(self) -> str:
        sharpe_str = f"{self.sharpe_ratio:.3f}" if self.sharpe_ratio is not None else "None"
        return (
            f"PortfolioWeights(method={self.method}, "
            f"assets={len(self.weights)}, sharpe={sharpe_str})"
        )


__all__ = ["PortfolioWeights"]
