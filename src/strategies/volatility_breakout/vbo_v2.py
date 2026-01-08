"""
Vanilla Volatility Breakout v2 (VBO v2) Strategy - Phase 2 개선버전.

⚠️ DEPRECATED: This module will be removed in v2.0.0 (planned Q2 2026).

Migration Guide:
    # OLD (deprecated)
    from src.strategies.volatility_breakout.vbo_v2 import VanillaVBO_v2
    strategy = VanillaVBO_v2(...)

    # NEW (recommended)
    from src.strategies.volatility_breakout.vbo import VanillaVBO
    strategy = VanillaVBO(
        use_improved_noise=True,
        use_adaptive_k=True,
        use_dynamic_slippage=True,
        use_cost_calculator=True,
        ...
    )

개선사항:
1. ImprovedNoiseIndicator: ATR 기반 동적 필터링 (고정 범위 → 변동성 적응)
2. AdaptiveKValue: 동적 K-값 조정 (0.8x ~ 1.3x)
3. DynamicSlippageModel: 시장 조건 반영 슬리피지
4. TradeCostCalculator: 정확한 거래 비용 계산

VBO v2 = VanillaVBO + 노이즈 필터 강화 + 슬리피지/비용 통합
"""

from collections.abc import Sequence
import warnings

import pandas as pd

from src.backtester.slippage_model_v2 import DynamicSlippageModel, MarketCondition
from src.backtester.trade_cost_calculator import TradeCostCalculator
from src.strategies.base import Condition, Strategy
from src.strategies.volatility_breakout.conditions import (
    BreakoutCondition,
    NoiseCondition,
    PriceBelowSMACondition,
    SMABreakoutCondition,
    TrendCondition,
)
from src.utils.indicators import add_vbo_indicators
from src.utils.indicators_v2 import (
    AdaptiveKValue,
    ImprovedNoiseIndicator,
    apply_improved_indicators,
)

# Emit deprecation warning at module import time
warnings.warn(
    "vbo_v2 module is deprecated and will be removed in v2.0.0. "
    "Use VanillaVBO with use_improved_noise=True, use_adaptive_k=True, "
    "use_dynamic_slippage=True, and use_cost_calculator=True instead.",
    DeprecationWarning,
    stacklevel=2,
)


class VanillaVBO_v2(Strategy):  # noqa: N801
    """
    Vanilla Volatility Breakout Strategy v2 (개선버전).

    기본 VBO + Phase 2 개선사항:
    1. 노이즈 필터 강화 (ATR 기반)
    2. 동적 슬리피지 모델
    3. 거래 비용 정확화

    효과:
    - 거짓 신호 감소 → 승률 증가
    - 실제 비용 반영 → 과낙관적 수익 시정
    - 변동성 적응형 → 시장 조건별 다른 성과
    """

    def __init__(
        self,
        name: str = "VanillaVBO_v2",
        sma_period: int = 4,
        trend_sma_period: int = 8,
        short_noise_period: int = 4,
        long_noise_period: int = 8,
        atr_period: int = 14,  # ATR 계산 기간
        use_improved_noise: bool = True,  # Phase 2.1 활성화
        use_adaptive_k: bool = True,  # Phase 2.1 K값 동적 조정
        use_dynamic_slippage: bool = True,  # Phase 2.2 활성화
        use_cost_calculator: bool = True,  # Phase 2.3 활성화
        vip_tier: int = 0,  # Upbit VIP 등급
        stop_loss_pct: float | None = 0.05,  # 손절 비율 (5%)
        take_profit_pct: float | None = 0.15,  # 익절 비율 (15%)
        min_hold_periods: int = 3,  # 최소 보유 기간 (whipsaw 방지)
        entry_conditions: Sequence[Condition] | None = None,
        exit_conditions: Sequence[Condition] | None = None,
        use_default_conditions: bool = True,
        exclude_current: bool = False,
    ) -> None:
        """
        Initialize VBO v2 strategy with Phase 2 improvements.

        Args:
            name: Strategy name
            sma_period: SMA 기간
            trend_sma_period: 장기 SMA 기간
            short_noise_period: 단기 노이즈 기간
            long_noise_period: 장기 노이즈 기간
            atr_period: ATR 계산 기간
            use_improved_noise: Phase 2.1 노이즈 필터 사용 여부
            use_adaptive_k: 동적 K-값 조정 여부
            use_dynamic_slippage: Phase 2.2 슬리피지 모델 사용 여부
            use_cost_calculator: Phase 2.3 비용 계산기 사용 여부
            vip_tier: Upbit VIP 등급
            entry_conditions: 커스텀 진입 조건
            exit_conditions: 커스텀 퇴출 조건
            use_default_conditions: 기본 조건 사용 여부
            exclude_current: 현재 바 제외 여부
        """
        # Phase 2 개선사항 설정
        self.atr_period = atr_period
        self.use_improved_noise = use_improved_noise
        self.use_adaptive_k = use_adaptive_k
        self.use_dynamic_slippage = use_dynamic_slippage
        self.use_cost_calculator = use_cost_calculator
        self.vip_tier = vip_tier

        # 리스크 관리 설정
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.min_hold_periods = min_hold_periods

        # 기본 지표 파라미터
        self.sma_period = sma_period
        self.trend_sma_period = trend_sma_period
        self.short_noise_period = short_noise_period
        self.long_noise_period = long_noise_period
        self.exclude_current = exclude_current

        # Phase 2 모듈 초기화
        if use_improved_noise:
            self.noise_indicator = ImprovedNoiseIndicator(atr_period=atr_period)

        if use_adaptive_k:
            self.adaptive_k = AdaptiveKValue()

        if use_dynamic_slippage:
            self.slippage_model = DynamicSlippageModel()

        if use_cost_calculator:
            self.cost_calculator = TradeCostCalculator(
                vip_tier=vip_tier, volatility_regime="medium"
            )

        # 기본 조건 구성
        default_entry: list[Condition] = []
        default_exit: list[Condition] = []

        if use_default_conditions:
            default_entry = [
                BreakoutCondition(),
                SMABreakoutCondition(),
                TrendCondition(),
                NoiseCondition(),
            ]
            default_exit = [
                PriceBelowSMACondition(),
            ]

        all_entry = list(entry_conditions or []) + default_entry
        all_exit = list(exit_conditions or []) + default_exit

        super().__init__(
            name=name,
            entry_conditions=all_entry,
            exit_conditions=all_exit,
        )

    def required_indicators(self) -> list[str]:
        """필요한 지표 목록."""
        base_indicators = [
            "noise",
            "short_noise",
            "long_noise",
            "sma",
            "sma_trend",
            "target",
            "prev_high",
            "prev_low",
            "prev_range",
        ]

        if self.use_improved_noise:
            base_indicators.extend(
                [
                    "atr",
                    "natr",
                    "volatility_regime",
                    "short_noise_adaptive",
                    "long_noise_adaptive",
                    "noise_ratio",
                ]
            )

        return base_indicators

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all VBO v2 indicators.

        단계:
        1. 기본 VBO 지표 (noise, sma, target 등)
        2. Phase 2.1: ImprovedNoiseIndicator (ATR 기반 필터링)
        3. Phase 2.1: AdaptiveKValue (동적 K-값)
        """
        # Step 1: 기본 VBO 지표
        df = add_vbo_indicators(
            df,
            sma_period=self.sma_period,
            trend_sma_period=self.trend_sma_period,
            short_noise_period=self.short_noise_period,
            long_noise_period=self.long_noise_period,
            exclude_current=self.exclude_current,
        )

        # Step 2: Phase 2.1 개선된 노이즈 지표
        if self.use_improved_noise:
            df = apply_improved_indicators(df, atr_period=self.atr_period)

        # Step 3: Phase 2.1 동적 K-값 조정
        if self.use_adaptive_k and self.use_improved_noise:
            # volatility_regime 기반 K-값 조정
            k_multipliers = (
                df["volatility_regime"]
                .map(
                    {
                        0: 0.8,
                        1: 1.0,
                        2: 1.3,
                    }
                )
                .fillna(1.0)
            )

            # 기본 K-값에 승수 적용
            df["adaptive_k"] = df["noise"] * k_multipliers

            # 동적 target 재계산
            df["target_adaptive"] = df["open"] + df["prev_range"] * df["adaptive_k"]

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry/exit signals with Phase 2 improvements.

        개선사항:
        1. 노이즈 필터: fixed noise → adaptive noise (ATR 기반)
        2. K-값: fixed K → adaptive K (변동성 기반)
        3. 신호 품질 향상으로 거짓신호 감소
        """
        df = df.copy()

        # 진입 신호 구성
        entry_signal = pd.Series(True, index=df.index)

        for condition in self.entry_conditions.conditions:
            if condition.name == "Breakout":
                # Phase 2 개선: adaptive_k 사용 (있으면)
                if self.use_adaptive_k and "target_adaptive" in df.columns:
                    entry_signal = entry_signal & (df["high"] >= df["target_adaptive"])
                else:
                    entry_signal = entry_signal & (df["high"] >= df["target"])

            elif condition.name == "SMABreakout":
                # Phase 2 개선: adaptive_k 사용
                if self.use_adaptive_k and "target_adaptive" in df.columns:
                    entry_signal = entry_signal & (df["target_adaptive"] > df["sma"])
                else:
                    entry_signal = entry_signal & (df["target"] > df["sma"])

            elif condition.name == "TrendCondition" or condition.name == "TrendFilter":
                # Phase 2 개선: adaptive_k 사용
                if self.use_adaptive_k and "target_adaptive" in df.columns:
                    entry_signal = entry_signal & (df["target_adaptive"] > df["sma_trend"])
                else:
                    entry_signal = entry_signal & (df["target"] > df["sma_trend"])

            elif condition.name == "NoiseCondition" or condition.name == "NoiseFilter":
                # Phase 2 개선: adaptive noise 사용 (있으면)
                if self.use_improved_noise and "noise_ratio" in df.columns:
                    # noise_ratio = short_noise_adaptive / long_noise_adaptive
                    # 작을수록 안정적 = 신호 신뢰도 높음
                    entry_signal = entry_signal & (df["noise_ratio"] < 1.0)
                else:
                    entry_signal = entry_signal & (df["short_noise"] < df["long_noise"])

        # 퇴출 신호
        exit_signal = pd.Series(False, index=df.index)
        for condition in self.exit_conditions.conditions:
            if condition.name == "PriceBelowSMA":
                exit_signal = exit_signal | (df["close"] < df["sma"])

        df["entry_signal"] = entry_signal
        df["exit_signal"] = exit_signal

        # 백테스트 엔진 호환: 단일 신호 컬럼 생성 (1=진입, -1=청산, 0=유지)
        signal = pd.Series(0, index=df.index, dtype=int)
        # 진입 우선 설정 후, 퇴출이 동일 시점에 발생하면 퇴출이 우선되도록 덮어쓰기
        signal[entry_signal] = 1
        signal[exit_signal] = -1

        # 리스크 관리: 최소 보유 기간 적용
        if self.min_hold_periods > 0:
            signal = self._apply_min_hold_period(signal)

        df["signal"] = signal
        df["entry_price"] = 0.0  # 엔진에서 진입가 기록용
        df["hold_periods"] = 0  # 보유 기간 추적용

        return df

    def _apply_min_hold_period(self, signal: pd.Series) -> pd.Series:
        """
        최소 보유 기간 적용하여 조기 청산 방지 (whipsaw 감소).

        Args:
            signal: 원본 신호 (1=진입, -1=청산, 0=유지)

        Returns:
            최소 보유 기간이 적용된 신호
        """
        adjusted_signal = signal.copy()
        position = 0
        entry_idx = -1

        for i in range(len(signal)):
            if signal.iloc[i] == 1 and position == 0:
                # 신규 진입
                position = 1
                entry_idx = i
                adjusted_signal.iloc[i] = 1
            elif signal.iloc[i] == -1 and position == 1:
                # 청산 시도
                hold_period = i - entry_idx
                if hold_period >= self.min_hold_periods:
                    # 최소 보유 기간 충족 → 청산 허용
                    adjusted_signal.iloc[i] = -1
                    position = 0
                    entry_idx = -1
                else:
                    # 최소 보유 기간 미달 → 청산 무시
                    adjusted_signal.iloc[i] = 0

        return adjusted_signal

    def estimate_trade_cost(
        self, entry_price: float, exit_price: float, market_condition: MarketCondition | None = None
    ) -> dict[str, float]:
        """
        Phase 2.2 & 2.3: 거래 비용 추정.

        Args:
            entry_price: 진입가
            exit_price: 청산가
            market_condition: 시장 조건 (선택)

        Returns:
            거래 비용 분석 딕셔너리
        """
        if not self.use_cost_calculator:
            return {}

        # 슬리피지 추정 (있으면)
        if self.use_dynamic_slippage and market_condition:
            entry_slippage = self.slippage_model.calculate_dynamic_slippage(
                data=None,  # 실제 구현에서는 데이터 패스
                condition=market_condition,
                order_size=1.0,
            )
            exit_slippage = entry_slippage  # 간단히 동일하게 가정
        else:
            entry_slippage = 0.02  # 기본값
            exit_slippage = 0.02

        # 비용 계산
        result = self.cost_calculator.calculate_net_pnl(
            entry_price=entry_price,
            exit_price=exit_price,
            entry_slippage=entry_slippage,
            exit_slippage=exit_slippage,
        )

        return result


if __name__ == "__main__":
    print("VanillaVBO_v2 loaded successfully")
    print("Phase 2 improvements: Noise filter + Slippage model + Cost calculator")
