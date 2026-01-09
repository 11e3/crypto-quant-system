"""
Optimization result models.

Contains data models for parameter optimization results.
"""

from dataclasses import dataclass
from typing import Any

from src.backtester.models import BacktestResult


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""

    best_params: dict[str, Any]
    best_result: BacktestResult
    best_score: float
    all_results: list[tuple[dict[str, Any], BacktestResult, float]]
    optimization_metric: str

    def __repr__(self) -> str:
        return (
            f"OptimizationResult(metric={self.optimization_metric}, "
            f"best_score={self.best_score:.2f})"
        )


__all__ = ["OptimizationResult"]
