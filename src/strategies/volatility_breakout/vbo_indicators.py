"""
VBO indicator calculation utilities.
"""

import pandas as pd

from src.utils.indicators import add_improved_indicators, add_vbo_indicators

__all__ = ["calculate_vbo_indicators"]


def calculate_vbo_indicators(
    df: pd.DataFrame,
    sma_period: int,
    trend_sma_period: int,
    short_noise_period: int,
    long_noise_period: int,
    exclude_current: bool,
    use_improved_noise: bool = False,
    use_adaptive_k: bool = False,
    atr_period: int = 14,
    base_k: float = 0.5,
) -> pd.DataFrame:
    """
    Calculate all VBO indicators.

    VBO 전략의 핵심 지표 계산:

    1. 변동성 K값 (noise): (고가 - 저가) / max(고가, 저가)
    2. 목표가(target): 시가_오늘 + 어제_범위 × K
    3. SMA(sma_period): 단기 이동평균
    4. SMA_Trend(trend_sma_period): 장기 이동평균
    5. Short_Noise: 최근 K값들의 평균
    6. Long_Noise: 전체 K값들의 평균

    Args:
        df: OHLCV DataFrame
        sma_period: SMA period
        trend_sma_period: Trend SMA period
        short_noise_period: Short noise period
        long_noise_period: Long noise period
        exclude_current: Exclude current bar from calculations
        use_improved_noise: Enable ATR-normalized noise
        use_adaptive_k: Enable dynamic K-value adjustment
        atr_period: ATR period for improved indicators
        base_k: Base K value for adaptive calculation

    Returns:
        DataFrame with VBO indicators
    """
    df = add_vbo_indicators(
        df,
        sma_period=sma_period,
        trend_sma_period=trend_sma_period,
        short_noise_period=short_noise_period,
        long_noise_period=long_noise_period,
        exclude_current=exclude_current,
    )

    if use_improved_noise or use_adaptive_k:
        df = add_improved_indicators(
            df,
            short_period=short_noise_period,
            long_period=long_noise_period,
            atr_period=atr_period,
            base_k=base_k,
        )

        if use_improved_noise:
            df["short_noise"] = df["short_noise_adaptive"]
            df["long_noise"] = df["long_noise_adaptive"]

        if use_adaptive_k:
            df["target"] = df["open"] + df["prev_range"] * df["k_value_adaptive"]

    return df
