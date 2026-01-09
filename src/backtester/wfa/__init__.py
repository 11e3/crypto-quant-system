"""
Walk-Forward Analysis subpackage.

Contains modules for walk-forward analysis and validation.
"""

from src.backtester.wfa.walk_forward import (
    WalkForwardAnalyzer as WFAnalyzer,
)
from src.backtester.wfa.walk_forward import (
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward_analysis,
)
from src.backtester.wfa.walk_forward_auto import WalkForwardAnalyzer
from src.backtester.wfa.wfa_backtest import simple_backtest
from src.backtester.wfa.wfa_models import WFAReport, WFASegment

__all__ = [
    # Main walk-forward
    "WFAnalyzer",
    "WalkForwardAnalyzer",
    "WalkForwardPeriod",
    "WalkForwardResult",
    "run_walk_forward_analysis",
    # WFA models
    "WFAReport",
    "WFASegment",
    "simple_backtest",
]
