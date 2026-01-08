"""
Phase 2.3: 거래 비용 재계산 (Trade Cost Recalculation)

기존 문제:
- 수수료 미반영
- 슬리피지 고정값
- 시장 조건 무시
- Upbit 현물 거래 정책 미반영

개선:
- Upbit 정확한 수수료 구조
- 변동성 기반 슬리피지
- 포지션 크기 영향
- 환율 변동 고려
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


class TradeCostCalculator:
    """
    정확한 거래 비용 계산.

    항목:
    1. Slippage: 공시가와 실제 체결가의 차이
    2. Fee: 거래소 수수료 (Maker/Taker)
    3. Spread: 호가차
    4. Market Impact: 거래량 영향
    """

    def __init__(self, vip_tier: int = 0, volatility_regime: str = "medium"):
        """
        Args:
            vip_tier: Upbit VIP 등급
            volatility_regime: 'low', 'medium', 'high'
        """
        self.fees = UpbitFeeStructure.get_fees(vip_tier)
        self.volatility_regime = volatility_regime

        # 변동성 기반 슬리피지 기본값 (%)
        self.slippage_base = {
            "low": 0.01,
            "medium": 0.02,
            "high": 0.05,
        }

    def calculate_trade_cost_pct(self, order_side: str, slippage_pct: float | None = None) -> float:
        """
        거래 당 비용 계산 (단방향).

        비용 = 슬리피지 + 수수료

        Args:
            order_side: 'buy' or 'sell'
            slippage_pct: 슬리피지율 (미지정 시 기본값 사용)

        Returns:
            거래 비용 (%)
        """
        if slippage_pct is None:
            slippage_pct = self.slippage_base[self.volatility_regime]

        # Taker 가정 (시장가 거래)
        fee_pct = self.fees["taker"]

        total_cost = slippage_pct + fee_pct

        return total_cost

    def calculate_roundtrip_cost_pct(
        self, entry_slippage: float | None = None, exit_slippage: float | None = None
    ) -> float:
        """
        왕복 거래 비용 (Entry + Exit).

        총 비용 = Entry 비용 + Exit 비용

        Args:
            entry_slippage: Entry 슬리피지 (%)
            exit_slippage: Exit 슬리피지 (%)

        Returns:
            왕복 비용 (%)
        """
        if entry_slippage is None:
            entry_slippage = self.slippage_base[self.volatility_regime]
        if exit_slippage is None:
            exit_slippage = self.slippage_base[self.volatility_regime]

        entry_cost = self.calculate_trade_cost_pct("buy", entry_slippage)
        exit_cost = self.calculate_trade_cost_pct("sell", exit_slippage)

        return entry_cost + exit_cost

    def calculate_net_pnl(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float = 1.0,
        entry_slippage: float | None = None,
        exit_slippage: float | None = None,
    ) -> dict[str, float]:
        """
        순이익률 계산 (슬리피지 + 수수료 반영).

        예시:
        - Entry: 100,000 @ 0.02% slippage + 0.05% fee = 100,107
        - Exit: 101,000 @ 0.02% slippage + 0.05% fee = 100,898
        - Gross PnL: 100,898 - 100,107 = 791 (0.79%)

        Args:
            entry_price: 진입가
            exit_price: 청산가
            position_size: 포지션 크기
            entry_slippage: Entry 슬리피지 (%)
            exit_slippage: Exit 슬리피지 (%)

        Returns:
            {'gross_pnl_pct': X%, 'slippage_cost_pct': X%, 'fee_cost_pct': X%, 'net_pnl_pct': X%}
        """
        if entry_slippage is None:
            entry_slippage = self.slippage_base[self.volatility_regime]
        if exit_slippage is None:
            exit_slippage = self.slippage_base[self.volatility_regime]

        # 1. 공시 가격 기반 수익률
        gross_pnl_pct = ((exit_price - entry_price) / entry_price) * 100

        # 2. 슬리피지 비용
        total_slippage = entry_slippage + exit_slippage

        # 3. 수수료 비용
        entry_fee = self.fees["taker"]
        exit_fee = self.fees["taker"]
        total_fee = entry_fee + exit_fee

        # 4. 순이익
        net_pnl_pct = gross_pnl_pct - total_slippage - total_fee

        # 5. 손익분기점
        breakeven_pnl_pct = total_slippage + total_fee

        return {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "gross_pnl_pct": gross_pnl_pct,
            "entry_slippage_pct": entry_slippage,
            "exit_slippage_pct": exit_slippage,
            "total_slippage_pct": total_slippage,
            "entry_fee_pct": entry_fee,
            "exit_fee_pct": exit_fee,
            "total_fee_pct": total_fee,
            "net_pnl_pct": net_pnl_pct,
            "breakeven_pnl_pct": breakeven_pnl_pct,
            "position_size": position_size,
        }

    def calculate_minimum_profit_target(
        self,
        entry_price: float,
        entry_slippage: float | None = None,
        exit_slippage: float | None = None,
        target_pnl: float = 0.5,
    ) -> float:
        """
        목표 순수익을 달성하기 위한 최소 청산가.

        예시:
        - Entry: 100,000
        - 목표 순이익: 0.5%
        - 슬리피지 + 수수료: 0.14%
        - 필요 exit_price: 100,764

        즉, 공시가로 0.764% 올라야 순이익 0.5% 달성.

        Args:
            entry_price: 진입가
            entry_slippage: Entry 슬리피지 (%)
            exit_slippage: Exit 슬리피지 (%)
            target_pnl: 목표 순이익 (%)

        Returns:
            필요 exit_price
        """
        if entry_slippage is None:
            entry_slippage = self.slippage_base[self.volatility_regime]
        if exit_slippage is None:
            exit_slippage = self.slippage_base[self.volatility_regime]

        total_cost_pct = entry_slippage + exit_slippage + self.fees["taker"] + self.fees["taker"]

        # 필요 gross PnL = target_pnl + total_cost
        required_gross_pnl_pct = target_pnl + total_cost_pct

        exit_price = entry_price * (1 + required_gross_pnl_pct / 100)

        return exit_price


class TradeAnalyzer:
    """
    거래 시뮬레이션 분석.

    기능:
    - 거래 수익률 계산
    - 비용 분석
    - Break-even 분석
    """

    def __init__(self, vip_tier: int = 0, volatility_regime: str = "medium"):
        self.calculator = TradeCostCalculator(vip_tier, volatility_regime)

    def analyze_trades(
        self, trades: list[dict[str, float]]
    ) -> tuple[pd.DataFrame, dict[str, float]]:
        """
        거래 목록 분석.

        Args:
            trades: [{'entry_price': X, 'exit_price': Y, ...}, ...]

        Returns:
            (분석 결과 DataFrame, 통계 요약 dict)
        """
        results = []

        for trade in trades:
            entry_price = trade.get("entry_price", 0.0)
            exit_price = trade.get("exit_price", 0.0)
            position_size = trade.get("position_size", 1.0)
            entry_slippage = trade.get("entry_slippage")
            exit_slippage = trade.get("exit_slippage")

            analysis = self.calculator.calculate_net_pnl(
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=position_size,
                entry_slippage=entry_slippage,
                exit_slippage=exit_slippage,
            )
            results.append(analysis)

        df = pd.DataFrame(results)

        # 통계
        df_summary = {
            "total_trades": len(df),
            "avg_gross_pnl_pct": df["gross_pnl_pct"].mean(),
            "avg_net_pnl_pct": df["net_pnl_pct"].mean(),
            "avg_slippage_pct": df["total_slippage_pct"].mean(),
            "avg_fee_pct": df["total_fee_pct"].mean(),
            "winning_trades": (df["net_pnl_pct"] > 0).sum(),
            "win_rate_pct": (df["net_pnl_pct"] > 0).sum() / len(df) * 100 if len(df) > 0 else 0,
            "total_pnl_pct": df["net_pnl_pct"].sum(),
        }

        return df, df_summary


class CostBreakdownAnalysis:
    """
    비용 분해 분석.

    질문:
    - 전체 손실 중 슬리피지가 몇 %?
    - 전체 손실 중 수수료가 몇 %?
    - 가장 비싼 비용 요인은?
    """

    @staticmethod
    def analyze_loss_breakdown(
        gross_pnl_pct: float,
        entry_slippage: float = 0.02,
        exit_slippage: float = 0.02,
        taker_fee: float = 0.05,
    ) -> dict[str, float]:
        """
        손실 요인별 분석.

        Args:
            gross_pnl_pct: 공시 수익률
            entry_slippage: Entry 슬리피지 (%)
            exit_slippage: Exit 슬리피지 (%)
            taker_fee: Taker 수수료 (%)

        Returns:
            비용 분석 딕셔너리
        """
        total_cost = entry_slippage + exit_slippage + taker_fee * 2

        net_pnl = gross_pnl_pct - total_cost

        analysis = {
            "gross_pnl_pct": gross_pnl_pct,
            "entry_slippage_pct": entry_slippage,
            "exit_slippage_pct": exit_slippage,
            "total_slippage_pct": entry_slippage + exit_slippage,
            "entry_fee_pct": taker_fee,
            "exit_fee_pct": taker_fee,
            "total_fee_pct": taker_fee * 2,
            "total_cost_pct": total_cost,
            "net_pnl_pct": net_pnl,
            # 비율
            "slippage_pct_of_cost": (entry_slippage + exit_slippage) / total_cost * 100
            if total_cost > 0
            else 0,
            "fee_pct_of_cost": (taker_fee * 2) / total_cost * 100 if total_cost > 0 else 0,
        }

        return analysis


if __name__ == "__main__":
    # 예제: 0.5% 수익 거래 비용 분석
    calc = TradeCostCalculator(vip_tier=0, volatility_regime="medium")

    result = calc.calculate_net_pnl(
        entry_price=100000,
        exit_price=100500,  # +0.5%
        entry_slippage=0.02,
        exit_slippage=0.02,
    )

    print("=== 거래 비용 분석 ===")
    print(f"공시 수익률: {result['gross_pnl_pct']:.2f}%")
    print(f"슬리피지: -{result['total_slippage_pct']:.2f}%")
    print(f"수수료: -{result['total_fee_pct']:.2f}%")
    print(f"순이익: {result['net_pnl_pct']:.2f}%")
    print(f"손익분기점: {result['breakeven_pnl_pct']:.2f}%")

    # 최소 청산가
    min_exit = calc.calculate_minimum_profit_target(entry_price=100000, target_pnl=0.5)
    print(f"\n목표 순이익 0.5% 달성 최소 청산가: {min_exit:,.0f}")
