"""
Robustness Analysis 데이터 모델.

RobustnessResult, RobustnessReport 데이터클래스 정의.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RobustnessResult:
    """단일 파라미터 조합의 성과."""

    params: dict[str, Any]
    total_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    trade_count: int

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            **self.params,
            "total_return": self.total_return,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "trade_count": self.trade_count,
        }


@dataclass
class RobustnessReport:
    """Robustness Analysis 종합 리포트."""

    optimal_params: dict[str, Any]
    results: list[RobustnessResult]

    # 통계
    mean_return: float = 0.0
    std_return: float = 0.0
    min_return: float = 0.0
    max_return: float = 0.0

    # 최적값 주변 안정성 (±20% 범위)
    neighbor_success_rate: float = 0.0  # 0.0-1.0

    # 파라미터 민감도 (각 파라미터별)
    sensitivity_scores: dict[str, float] | None = None

    def __post_init__(self) -> None:
        """Post-initialization to set default sensitivity scores."""
        if self.sensitivity_scores is None:
            self.sensitivity_scores = {}
