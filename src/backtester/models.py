"""
Backtesting data models.

Common data structures used across backtesting engines.
"""

from dataclasses import dataclass, field
from datetime import date

import numpy as np

from src.config import (
    DEFAULT_FEE_RATE,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_MAX_SLOTS,
    DEFAULT_SLIPPAGE_RATE,
)
from src.risk.metrics import PortfolioRiskMetrics


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    fee_rate: float = DEFAULT_FEE_RATE
    slippage_rate: float = DEFAULT_SLIPPAGE_RATE
    max_slots: int = DEFAULT_MAX_SLOTS
    position_sizing: str = "equal"  # "equal", "volatility", "fixed-risk", "inverse-volatility", "mpt", "risk_parity", "kelly"
    position_sizing_risk_pct: float = 0.02  # Target risk per position (for fixed-risk method)
    position_sizing_lookback: int = 20  # Lookback period for volatility calculation
    use_cache: bool = True  # Cache indicator calculations

    # Advanced order settings
    stop_loss_pct: float | None = None  # Stop loss as percentage (e.g., 0.05 = 5%)
    take_profit_pct: float | None = None  # Take profit as percentage (e.g., 0.10 = 10%)
    trailing_stop_pct: float | None = None  # Trailing stop as percentage (e.g., 0.05 = 5%)

    # Portfolio optimization settings
    portfolio_optimization_method: str | None = (
        None  # "mpt", "risk_parity", "kelly" (None = use position_sizing)
    )
    risk_free_rate: float = 0.0  # Risk-free rate for MPT (annualized)
    max_kelly: float = 0.25  # Maximum Kelly percentage (fractional Kelly)


@dataclass
class Trade:
    """Record of a single trade."""

    ticker: str
    entry_date: date
    entry_price: float
    exit_date: date | None = None
    exit_price: float | None = None
    amount: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    is_whipsaw: bool = False
    commission_cost: float = 0.0
    slippage_cost: float = 0.0
    is_stop_loss: bool = False
    is_take_profit: bool = False
    exit_reason: str = "signal"  # "signal", "stop_loss", "take_profit", "trailing_stop", "open"

    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self.exit_date is not None


@dataclass
class BacktestResult:
    """Results from backtesting."""

    # Performance metrics
    total_return: float = 0.0
    cagr: float = 0.0
    mdd: float = 0.0
    calmar_ratio: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_trade_return: float = 0.0

    # Time series data
    equity_curve: np.ndarray = field(default_factory=lambda: np.array([]))
    dates: np.ndarray = field(default_factory=lambda: np.array([]))
    trades: list[Trade] = field(default_factory=list)

    # Additional info
    config: BacktestConfig | None = None
    strategy_name: str = ""
    interval: str = "day"  # Data interval (day, minute240, week)

    # Portfolio risk metrics
    risk_metrics: PortfolioRiskMetrics | None = None

    def summary(self) -> str:
        """Generate summary string.

        백테스트 결과를 읽기 쉬운 형식으로 표시:

        [CAGR (연율수익률)]
        의미: 매년 복리로 받은 평균 수익률
        해석:
        - 10% = 우수 (S&P 500 평균)
        - 20% = 매우 우수
        - 50% 이상 = 과적합 가능성 검토

        [MDD (최대낙폭)]
        의미: 최악의 상황에서 본 최대 손실률
        해석:
        - 20% = 정상 수준
        - 40% = 높은 위험
        - 60% 이상 = 매우 위험한 전략

        [Calmar Ratio]
        의미: CAGR / MDD (수익대비리스크)
        해석:
        - < 0.5 = 리스크 크다 (좋지 않음)
        - 0.5 ~ 1.0 = 중간 수준
        - 1.0 ~ 2.0 = 양호
        - 2.0 이상 = 우수 (높은 샤프비)

        [Sharpe Ratio]
        의미: 변동성 대비 초과수익
        해석:
        - 0.5 미만 = 낮음
        - 0.5 ~ 1.0 = 중간
        - 1.0 ~ 2.0 = 양호
        - 2.0 이상 = 우수

        [승률(Win Rate)]
        의미: 수익이 나는 거래의 비율
        해석:
        - 50% = 손익분기
        - 55% ~ 60% = 양호
        - 60% 이상 = 우수
        - 40% 이하 = 전략 재검토 필요

        [총 거래수]
        의미: 전체 기간동안의 총 거래 횟수
        해석:
        - 적음 (< 10) = 신호 부족, 데이터 부족 가능
        - 보통 (10~50) = 정상적인 거래빈도
        - 많음 (> 50) = 높은 거래빈도 → 수수료 영향 확인

        [최종 자본(Final Equity)]
        의미: 백테스트 마지막 날의 포트폴리오 가치
        계산: 초기자본 × (1 + total_return/100)
        """
        final_equity = self.equity_curve[-1] if len(self.equity_curve) > 0 else 0
        summary = (
            f"\n{'=' * 50}\n"
            f"Strategy: {self.strategy_name}\n"
            f"{'=' * 50}\n"
            f"CAGR: {self.cagr:.2f}%\n"
            f"MDD: {self.mdd:.2f}%\n"
            f"Calmar Ratio: {self.calmar_ratio:.2f}\n"
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"Win Rate: {self.win_rate:.2f}%\n"
            f"Total Trades: {self.total_trades}\n"
            f"Final Equity: {final_equity:.4f}\n"
        )

        # Add risk metrics if available
        if self.risk_metrics:
            summary += "\n--- Risk Metrics ---\n"
            summary += f"VaR (95%): {self.risk_metrics.var_95:.2%}\n"
            summary += f"CVaR (95%): {self.risk_metrics.cvar_95:.2%}\n"
            summary += f"Portfolio Volatility: {self.risk_metrics.portfolio_volatility:.2%}\n"

        summary += f"{'=' * 50}"
        return summary
