"""
Phase 2: 개선된 지표 (Indicators v2)

기존 문제점:
- noise = high.rolling() - low.rolling() 단순 범위만 사용
- 시장 변동성 변화에 적응하지 못함
- ATR(Average True Range) 미사용

개선사항:
- ATR 기반 동적 임계값
- 시간대별 변동성 조정 (인트라데이 vs 일일)
- 거래량 가중 변동성
- NATR (정규화 ATR) 도입

참고: 이 모듈은 VanillaVBO와 독립적으로 사용 가능
"""

import pandas as pd


class ImprovedNoiseIndicator:
    """
    개선된 노이즈 지표.

    기존: noise = high.rolling() - low.rolling()
    개선: ATR 기반 + 시장 변동성 적응
    """

    def __init__(self, atr_period: int = 14, natr_smooth: int = 20):
        """
        Args:
            atr_period: ATR 계산 기간
            natr_smooth: 정규화 ATR 평활 기간
        """
        self.atr_period = atr_period
        self.natr_smooth = natr_smooth

    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """
        Average True Range 계산.

        True Range = max(
            high - low,
            abs(high - close_prev),
            abs(low - close_prev)
        )

        Args:
            data: OHLC 데이터 (high, low, close 컬럼 필수)

        Returns:
            ATR 시리즈
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # True Range 계산
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR: True Range의 이동평균
        atr = tr.rolling(window=self.atr_period).mean()

        return atr

    def calculate_natr(self, data: pd.DataFrame) -> pd.Series:
        """
        정규화 ATR (Normalized ATR).

        NATR = (ATR / Close) * 100
        → 가격대와 무관한 상대 변동성 지표

        Args:
            data: OHLC 데이터

        Returns:
            NATR 시리즈 (%)
        """
        atr = self.calculate_atr(data)
        close = data["close"]

        natr = (atr / close) * 100

        return natr

    def calculate_volatility_regime(self, data: pd.DataFrame) -> pd.Series:
        """
        변동성 체제 분류 (Low / Medium / High).

        NATR 기반 변동성 분류:
        - Low: NATR < 33rd percentile
        - Medium: 33rd < NATR < 67th percentile
        - High: NATR > 67th percentile

        Args:
            data: OHLC 데이터

        Returns:
            변동성 레이블 시리즈 (0=Low, 1=Medium, 2=High)
        """
        natr = self.calculate_natr(data)

        # 이동 백분위수 계산 (윈도우 100)
        window = min(100, len(data) // 4)
        p33 = natr.rolling(window=window).quantile(0.33)
        p67 = natr.rolling(window=window).quantile(0.67)

        regime = pd.Series(0, index=data.index)
        regime[(natr >= p33) & (natr < p67)] = 1  # Medium
        regime[natr >= p67] = 2  # High

        return regime

    def calculate_adaptive_noise(
        self, data: pd.DataFrame, short_period: int = 4, long_period: int = 8
    ) -> tuple[pd.Series, pd.Series]:
        """
        적응형 노이즈 필터.

        기본: high.rolling() - low.rolling() (기존 방식)
        + ATR 정규화: noise_normalized = noise / ATR

        이를 통해 시장 변동성에 따라 필터 강도를 자동 조정.

        Args:
            data: OHLC 데이터
            short_period: 단기 노이즈 윈도우
            long_period: 장기 노이즈 윈도우

        Returns:
            (short_noise, long_noise) - ATR 정규화된 노이즈
        """
        high = data["high"]
        low = data["low"]
        atr = self.calculate_atr(data)

        # 기존 노이즈 계산
        short_noise_raw = (
            high.rolling(window=short_period).max() - low.rolling(window=short_period).min()
        )
        long_noise_raw = (
            high.rolling(window=long_period).max() - low.rolling(window=long_period).min()
        )

        # ATR로 정규화 (시장 변동성 적응)
        short_noise = short_noise_raw / (atr + 1e-8)
        long_noise = long_noise_raw / (atr + 1e-8)

        return short_noise, long_noise

    def calculate_noise_ratio(
        self, data: pd.DataFrame, short_period: int = 4, long_period: int = 8
    ) -> pd.Series:
        """
        노이즈 비율 = short_noise / long_noise.

        0.5 이상: 단기 변동성 높음 → 거래 제외 (과도한 노이즈)
        0.5 미만: 단기 변동성 낮음 → 거래 신뢰도 높음

        Args:
            data: OHLC 데이터
            short_period: 단기 기간
            long_period: 장기 기간

        Returns:
            노이즈 비율 시리즈
        """
        short_noise, long_noise = self.calculate_adaptive_noise(data, short_period, long_period)

        # 0으로 나누기 방지
        ratio = short_noise / (long_noise + 1e-8)

        return ratio


class AdaptiveKValue:
    """
    적응형 K값 (Breakout Threshold).

    기존: 고정 K값
    개선: 시장 조건별 동적 K값 조정

    - 높은 변동성: K값 증가 (거짓 신호 필터)
    - 낮은 변동성: K값 감소 (민감도 증가)
    """

    def __init__(self, base_k: float = 0.5, volatility_sensitive: bool = True):
        """
        Args:
            base_k: 기본 K값 (0.5)
            volatility_sensitive: 변동성 기반 조정 활성화
        """
        self.base_k = base_k
        self.volatility_sensitive = volatility_sensitive
        self.noise_indicator = ImprovedNoiseIndicator()

    def calculate_k_value(
        self, data: pd.DataFrame, short_period: int = 4, long_period: int = 8
    ) -> pd.Series:
        """
        동적 K값 계산.

        K = base_K * (1 + volatility_factor)

        volatility_factor:
        - NATR 낮음: -0.2 (K값 감소 → 민감도 증가)
        - NATR 중간: 0.0 (K값 유지)
        - NATR 높음: +0.3 (K값 증가 → 필터 강화)

        Args:
            data: OHLC 데이터
            short_period: 단기 기간
            long_period: 장기 기간

        Returns:
            K값 시리즈
        """
        if not self.volatility_sensitive:
            return pd.Series(self.base_k, index=data.index)

        # 변동성 체제 계산
        regime = self.noise_indicator.calculate_volatility_regime(data)

        # K값 조정
        k_values = pd.Series(self.base_k, index=data.index)

        # 체제별 조정
        k_values[regime == 0] = self.base_k * 0.8  # Low 변동성: K값 감소
        k_values[regime == 1] = self.base_k * 1.0  # Medium: 유지
        k_values[regime == 2] = self.base_k * 1.3  # High: K값 증가

        return k_values


def apply_improved_indicators(
    data: pd.DataFrame, short_period: int = 4, long_period: int = 8, atr_period: int = 14
) -> pd.DataFrame:
    """
    전체 개선 지표를 데이터에 적용.

    추가 컬럼:
    - atr: Average True Range
    - natr: Normalized ATR (%)
    - volatility_regime: 변동성 체제 (0/1/2)
    - short_noise_adaptive: ATR 정규화 단기 노이즈
    - long_noise_adaptive: ATR 정규화 장기 노이즈
    - noise_ratio: 노이즈 비율
    - k_value_adaptive: 동적 K값

    Args:
        data: OHLC 데이터
        short_period: 단기 기간
        long_period: 장기 기간

    Returns:
        개선 지표가 추가된 데이터프레임
    """
    result = data.copy()

    noise_ind = ImprovedNoiseIndicator(atr_period=atr_period)
    k_calculator = AdaptiveKValue()

    # 지표 계산
    result["atr"] = noise_ind.calculate_atr(data)
    result["natr"] = noise_ind.calculate_natr(data)
    result["volatility_regime"] = noise_ind.calculate_volatility_regime(data)

    short_noise, long_noise = noise_ind.calculate_adaptive_noise(data, short_period, long_period)
    result["short_noise_adaptive"] = short_noise
    result["long_noise_adaptive"] = long_noise
    result["noise_ratio"] = noise_ind.calculate_noise_ratio(data, short_period, long_period)

    result["k_value_adaptive"] = k_calculator.calculate_k_value(data, short_period, long_period)

    return result


if __name__ == "__main__":
    print("Indicators v2 module loaded successfully")
    print("Features: ATR, NATR, Adaptive Noise, Dynamic K-value")
