"""
Trade execution data models.

Contains data structures for trade execution information.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class TradeExecution:
    """거래 체결 정보."""

    timestamp: pd.Timestamp
    side: str  # 'buy' or 'sell'
    entry_price: float
    entry_size: float
    exit_price: float = 0.0
    exit_size: float = 0.0
    exit_time: pd.Timestamp | None = None

    # 비용 관련
    entry_slippage_pct: float = 0.0
    exit_slippage_pct: float = 0.0
    maker_fee_pct: float = 0.0
    taker_fee_pct: float = 0.05

    # 계산 결과
    gross_pnl: float = 0.0
    slippage_cost: float = 0.0
    fee_cost: float = 0.0
    net_pnl: float = 0.0
    net_pnl_pct: float = 0.0


class UpbitFeeStructure:
    """
    Upbit 거래소 수수료 구조.

    출처: Upbit 공식 문서

    현물 거래:
    - Maker (지정가): 0.05% (일부 0%)
    - Taker (시장가): 0.05%

    주요 특징:
    - KRW 수수료 지원 (KRW로 수수료 직접 차감)
    - VIP 프로그램 (거래량 기반 할인)
    - 마지막 분 거래 수수료 환급
    """

    # 기본 수수료율
    DEFAULT_MAKER_FEE = 0.05  # %
    DEFAULT_TAKER_FEE = 0.05  # %

    # VIP 등급별 수수료 (volume-based)
    VIP_TIERS = {
        0: {"maker": 0.05, "taker": 0.05},  # Default
        1: {"maker": 0.04, "taker": 0.05},  # 월 거래량 >= 100 BTC
        2: {"maker": 0.03, "taker": 0.04},  # >= 500 BTC
        3: {"maker": 0.02, "taker": 0.03},  # >= 1000 BTC
        4: {"maker": 0.01, "taker": 0.02},  # >= 5000 BTC
    }

    @staticmethod
    def get_fees(tier: int = 0) -> dict[str, float]:
        """
        VIP 등급에 따른 수수료 조회.

        Args:
            tier: VIP 등급 (0-4)

        Returns:
            {'maker': 0.XX%, 'taker': 0.XX%}
        """
        tier = max(0, min(tier, 4))
        return UpbitFeeStructure.VIP_TIERS[tier].copy()


__all__ = ["TradeExecution", "UpbitFeeStructure"]
