"""
Phase 2: 동적 슬리피지 모델 (Slippage Model v2)

⚠️ DEPRECATED: This module will be removed in v2.0.0 (planned Q2 2026).

Migration Guide:
    # OLD (deprecated)
    from src.backtester.slippage_model_v2 import DynamicSlippageModel

    # NEW (recommended)
    from src.backtester.slippage_model import DynamicSlippageModel
    # Class will be moved to main slippage_model module

기존 문제점:
- 고정 슬리피지율 (0.05%)
- 시장 조건 무시
- 거래량 반영 안 됨

개선사항:
- 스프레드 기반 슬리피지 (호가 범위)
- 호가 변동성 적응
- 거래량 가중 슬리피지
- 시간대별 조정 (유동성 변화)
"""

import warnings
from dataclasses import dataclass
from enum import Enum

import pandas as pd

# Emit deprecation warning at module import time
warnings.warn(
    "slippage_model_v2 module is deprecated and will be removed in v2.0.0. "
    "DynamicSlippageModel will be moved to main slippage_model module.",
    DeprecationWarning,
    stacklevel=2,
)


class VolatilityLevel(Enum):
    """Market volatility classification."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2


# Market condition adjustment factors
class SlippageConstants:
    """Constants for slippage calculation.

    These values are calibrated based on Upbit market characteristics.
    Adjust based on empirical testing and market observations.
    """

    # Volatility impact multipliers
    HIGH_VOLATILITY_MULTIPLIER = 1.2  # +20% slippage in high volatility
    LOW_VOLATILITY_MULTIPLIER = 0.85  # -15% slippage in low volatility

    # Time-of-day liquidity adjustments
    HIGH_LIQUIDITY_DISCOUNT = 0.9  # -10% during peak hours (9-18 KST)
    LOW_LIQUIDITY_PREMIUM = 1.15  # +15% during off-peak hours (0-6 KST)

    # Volume impact scaling
    VOLUME_IMPACT_WEIGHT = 0.05  # 5% base weight for volume impact

    # Spread volatility contribution
    SPREAD_VOLATILITY_FACTOR = 0.5  # 50% contribution from spread volatility

    # Maximum volume impact cap (extreme conditions)
    MAX_VOLUME_IMPACT_PCT = 20.0


@dataclass
class MarketCondition:
    """시장 상황 정보."""

    spread_ratio: float  # 현재 스프레드 / 최근 평균 스프레드
    volume_ratio: float  # 현재 거래량 / 평균 거래량
    volatility_level: int  # 0=Low, 1=Medium, 2=High
    time_of_day: int  # 0-23 시간


class DynamicSlippageModel:
    """
    동적 슬리피지 모델.

    슬리피지 = 주문 체결 시 발생하는 가격 이동

    요인:
    1. 기본 스프레드 (호가차)
    2. 호가 변동성 (spread volatility)
    3. 거래량 (volume impact)
    4. 시장 조건 (market condition)
    """

    def __init__(
        self,
        base_spread: float = 0.01,  # Upbit 기본 스프레드 ~0.01%
        maker_fee: float = 0.0,  # Upbit maker fee
        taker_fee: float = 0.05,
    ):  # Upbit taker fee (0.05%)
        """
        Args:
            base_spread: 기본 스프레드 (%)
            maker_fee: Maker 수수료 (%)
            taker_fee: Taker 수수료 (%)
        """
        self.base_spread = base_spread
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def calculate_intrabar_range(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate intrabar price range (volatility measure).

        This represents price volatility within each bar, NOT the bid-ask spread.
        True bid-ask spread requires orderbook data.

        Args:
            data: OHLC 데이터

        Returns:
            Range ratio series (%) - represents volatility, not liquidity
        """
        high = data["high"]
        low = data["low"]
        mid = (high + low) / 2

        # Intrabar range as percentage of mid price
        # This measures VOLATILITY, not bid-ask spread
        range_pct = ((high - low) / mid) * 100

        return range_pct

    def estimate_bid_ask_spread(
        self, data: pd.DataFrame, volatility_proxy: float = 0.3
    ) -> pd.Series:
        """
        Estimate bid-ask spread from OHLCV data.

        ⚠️ WARNING: This is an approximation. Real spread requires orderbook data.

        Method: Assume spread correlates with volatility but at lower magnitude.
        Typical crypto spread: 0.01-0.1% of price in liquid markets

        Args:
            data: OHLCV data
            volatility_proxy: Scaling factor (typical spread = volatility * proxy)

        Returns:
            Estimated spread series (%)
        """
        # Use short-term volatility as proxy
        returns = data["close"].pct_change()
        rolling_vol = returns.rolling(window=20).std() * 100  # Convert to %

        # Spread is typically much smaller than volatility
        # Empirical factor: spread ≈ 0.3 * short_term_volatility for liquid crypto
        estimated_spread = rolling_vol * volatility_proxy

        # Cap at reasonable levels for Upbit (0.01% - 0.5%)
        estimated_spread = estimated_spread.clip(lower=0.01, upper=0.5)

        return estimated_spread

    def calculate_spread(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        Backward compatibility wrapper.

        ⚠️ DEPRECATED: Use estimate_bid_ask_spread() for spread estimation.
        This method actually measures volatility, not spread.

        Returns:
            Estimated bid-ask spread (%) - now uses improved estimation
        """
        warnings.warn(
            "calculate_spread() measures volatility, not true spread. "
            "Use estimate_bid_ask_spread() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.estimate_bid_ask_spread(data)

    def calculate_spread_volatility(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        Spread volatility - measures liquidity stability.

        Standard deviation of estimated spread over time.
        Higher spread volatility → less predictable execution → higher slippage buffer.

        Args:
            data: OHLC 데이터
            window: 슬라이딩 윈도우

        Returns:
            호가차 변동성 시리즈
        """
        spread = self.estimate_bid_ask_spread(data)
        spread_vol = spread.rolling(window=window).std()

        return spread_vol

    def calculate_volume_impact(
        self,
        data: pd.DataFrame,
        order_size: float = 1.0,  # BTC 개수
        window: int = 20,
    ) -> pd.Series:
        """
        거래량 영향도 (Volume Impact).

        volume_impact = order_size / avg_volume

        주문 크기가 클수록, 평균 거래량이 작을수록 슬리피지 증가.

        예:
        - 평균 거래량 100 BTC, 주문 1 BTC → impact 1%
        - 평균 거래량 100 BTC, 주문 10 BTC → impact 10%

        Args:
            data: OHLC 데이터 (volume 컬럼 필수)
            order_size: 주문 크기 (BTC)
            window: 평균 거래량 계산 윈도우

        Returns:
            거래량 영향도 시리즈 (%)
        """
        volume = data["volume"]
        avg_volume = volume.rolling(window=window).mean()

        # 거래량 영향도 (%)
        volume_impact = (order_size / (avg_volume + 1e-8)) * 100

        # Cap at maximum impact level (extreme conditions)
        volume_impact = volume_impact.clip(upper=SlippageConstants.MAX_VOLUME_IMPACT_PCT)

        return volume_impact

    def calculate_dynamic_slippage(
        self, data: pd.DataFrame, condition: MarketCondition, order_size: float = 1.0
    ) -> float:
        """
        동적 슬리피지 계산.

        Total Slippage = Base + Spread + Volume Impact + Condition Adjustment

        Base: Taker 수수료 (0.05%)
        Spread: 현재 호가차 * 시장 조건
        Volume Impact: 거래량 영향도
        Condition: 시장 상황 추가 조정

        Args:
            data: OHLC 데이터
            condition: 시장 조건 정보
            order_size: 주문 크기

        Returns:
            슬리피지율 (%)
        """
        # 1. 기본: Taker 수수료
        slippage = self.taker_fee

        # 2. Bid-ask spread + spread volatility
        spread = self.estimate_bid_ask_spread(data).iloc[-1]
        spread_vol = self.calculate_spread_volatility(data).iloc[-1]

        # Spread contribution: base spread + volatility-adjusted buffer
        spread_component = spread + (
            spread_vol * (1.0 + condition.spread_ratio * SlippageConstants.SPREAD_VOLATILITY_FACTOR)
        )
        slippage += spread_component

        # 3. Volume impact (market depth consideration)
        volume_impact = self.calculate_volume_impact(data, order_size).iloc[-1]
        slippage += volume_impact * SlippageConstants.VOLUME_IMPACT_WEIGHT * condition.volume_ratio

        # 4. Volatility regime adjustment
        if condition.volatility_level == VolatilityLevel.HIGH.value:
            slippage *= SlippageConstants.HIGH_VOLATILITY_MULTIPLIER
        elif condition.volatility_level == VolatilityLevel.LOW.value:
            slippage *= SlippageConstants.LOW_VOLATILITY_MULTIPLIER

        # 5. Time-of-day liquidity adjustment
        # Peak hours (9-18 KST): higher liquidity → lower slippage
        # Off-peak hours (0-6 KST): lower liquidity → higher slippage
        if 9 <= condition.time_of_day < 18:
            slippage *= SlippageConstants.HIGH_LIQUIDITY_DISCOUNT
        elif 0 <= condition.time_of_day < 6:
            slippage *= SlippageConstants.LOW_LIQUIDITY_PREMIUM

        return float(slippage)

    def estimate_execution_price(
        self,
        price: float,
        order_side: str,  # 'buy' or 'sell'
        slippage_pct: float,
    ) -> float:
        """
        슬리피지를 적용한 예상 체결가.

        Buy:  execution_price = price * (1 + slippage)
        Sell: execution_price = price * (1 - slippage)

        Args:
            price: 공시가
            order_side: 'buy' 또는 'sell'
            slippage_pct: 슬리피지율 (%)

        Returns:
            예상 체결가
        """
        slippage_ratio = slippage_pct / 100

        if order_side.lower() == "buy":
            return price * (1 + slippage_ratio)
        elif order_side.lower() == "sell":
            return price * (1 - slippage_ratio)
        else:
            raise ValueError(f"Invalid order_side: {order_side}")


class UpbitSlippageEstimator(DynamicSlippageModel):
    """
    Upbit 거래소 전용 슬리피지 추정기.

    Upbit 특성:
    - Maker fee: 0% (일부 조건)
    - Taker fee: 0.05%
    - 24/7 운영 (시간대 변동성 있음)
    - 암호화폐 특성상 변동성 높음
    """

    def __init__(self) -> None:
        super().__init__(
            base_spread=0.01,  # Upbit 평균 스프레드
            maker_fee=0.0,
            taker_fee=0.05,
        )

    def estimate_transaction_cost(
        self,
        entry_price: float,
        exit_price: float,
        entry_slippage: float,
        exit_slippage: float,
        position_size: float = 1.0,
    ) -> dict[str, float]:
        """
        왕복 거래 비용 계산.

        총 비용 = Entry 슬리피지 + Exit 슬리피지 + 수수료

        Args:
            entry_price: 진입가
            exit_price: 청산가
            entry_slippage: 진입 슬리피지율 (%)
            exit_slippage: 청산 슬리피지율 (%)
            position_size: 포지션 크기

        Returns:
            비용 분석 딕셔너리
        """
        # 1. Entry 비용
        actual_entry_price = entry_price * (1 + entry_slippage / 100)
        entry_cost = actual_entry_price * position_size

        # 2. Exit 비용
        actual_exit_price = exit_price * (1 - exit_slippage / 100)
        exit_value = actual_exit_price * position_size

        # 3. 수익률
        gross_pnl = exit_value - entry_cost
        gross_pnl_pct = (gross_pnl / entry_cost) * 100 if entry_cost > 0 else 0

        # 4. 총 슬리피지
        total_slippage_pct = (entry_slippage + exit_slippage) + (
            (actual_entry_price - entry_price) + (exit_price - actual_exit_price)
        ) / entry_price * 100

        return {
            "entry_price": entry_price,
            "actual_entry_price": actual_entry_price,
            "exit_price": exit_price,
            "actual_exit_price": actual_exit_price,
            "entry_cost": entry_cost,
            "exit_value": exit_value,
            "gross_pnl": gross_pnl,
            "gross_pnl_pct": gross_pnl_pct,
            "entry_slippage_pct": entry_slippage,
            "exit_slippage_pct": exit_slippage,
            "total_slippage_pct": total_slippage_pct,
        }


if __name__ == "__main__":
    print("Slippage Model v2 loaded successfully")
    print("Features: Dynamic spread, volume impact, time-based adjustment")
