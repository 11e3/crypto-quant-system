"""
Technical indicators for trading strategies.

Provides vectorized indicator calculations using pandas/numpy.
"""

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int, exclude_current: bool = False) -> pd.Series:
    """
    Simple Moving Average.

    Args:
        series: Price series
        period: Lookback period
        exclude_current: If True, exclude current bar (matching legacy/bt.py behavior)

    Returns:
        SMA series
    """
    if exclude_current:
        # Exclude current bar: use past 'period' bars (matching legacy/bt.py)
        # rolling(window=period) includes current bar, so we shift by 1
        return series.rolling(window=period, min_periods=period).mean().shift(1)
    else:
        return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        series: Price series
        period: Lookback period

    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Average True Range.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Lookback period

    Returns:
        ATR series
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean()


def volatility_range(high: pd.Series, low: pd.Series) -> pd.Series:
    """
    Daily volatility range (high - low).

    Args:
        high: High prices
        low: Low prices

    Returns:
        Range series
    """
    return high - low


def noise_ratio(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> pd.Series:
    """
    Noise ratio: measures how much of the range is "noise" vs directional movement.

    Formula: Noise = 1 - abs(close - open) / (high - low)

    Higher values indicate more noise (less directional movement).

    Args:
        open_: Open prices
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        Noise ratio series (0-1)
    """
    price_range = high - low
    body = (close - open_).abs()
    # Avoid division by zero
    result = np.where(price_range > 0, 1 - body / price_range, 0.0)
    return pd.Series(result, index=open_.index)


def noise_ratio_sma(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int,
    exclude_current: bool = False,
) -> pd.Series:
    """
    Simple Moving Average of noise ratio (K value for VBO).

    Args:
        open_: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        period: Lookback period
        exclude_current: If True, exclude current bar (matching legacy/bt.py behavior)

    Returns:
        SMA of noise ratio
    """
    nr = noise_ratio(open_, high, low, close)
    return pd.Series(sma(pd.Series(nr, index=open_.index), period, exclude_current=exclude_current))


def target_price(
    open_: pd.Series,
    prev_high: pd.Series,
    prev_low: pd.Series,
    k: pd.Series,
) -> pd.Series:
    """
    Calculate volatility breakout target price.

    Target = Open + (Prev_High - Prev_Low) * K

    Args:
        open_: Current open prices
        prev_high: Previous bar high prices
        prev_low: Previous bar low prices
        k: K value (noise ratio or constant)

    Returns:
        Target price series
    """
    prev_range = prev_high - prev_low
    return open_ + prev_range * k


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        series: Price series
        period: Lookback period

    Returns:
        RSI series (0-100)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.

    Args:
        series: Price series
        period: SMA period
        std_dev: Standard deviation multiplier

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle = sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Moving Average Convergence Divergence.

    Args:
        series: Price series
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    fast_ema = ema(series, fast_period)
    slow_ema = ema(series, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period
        d_period: %D period

    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period, min_periods=d_period).mean()

    return k, d


def add_vbo_indicators(
    df: pd.DataFrame,
    sma_period: int = 4,
    trend_sma_period: int = 8,
    short_noise_period: int = 4,
    long_noise_period: int = 8,
    exclude_current: bool = False,
) -> pd.DataFrame:
    """
    Add all indicators required for Volatility Breakout strategy.

    Args:
        df: DataFrame with OHLCV columns (open, high, low, close, volume)
        sma_period: Period for exit SMA
        trend_sma_period: Period for trend SMA
        short_noise_period: Period for short-term noise (K value)
        long_noise_period: Period for long-term noise baseline
        exclude_current: If True, exclude current bar from calculations (matching legacy/bt.py)

    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()

    # Noise ratios
    df["noise"] = noise_ratio(df["open"], df["high"], df["low"], df["close"])
    df["short_noise"] = sma(df["noise"], short_noise_period, exclude_current=exclude_current)
    df["long_noise"] = sma(df["noise"], long_noise_period, exclude_current=exclude_current)

    # Moving averages
    df["sma"] = sma(df["close"], sma_period, exclude_current=exclude_current)
    df["sma_trend"] = sma(df["close"], trend_sma_period, exclude_current=exclude_current)

    # Previous day values for target calculation
    df["prev_high"] = df["high"].shift(1)
    df["prev_low"] = df["low"].shift(1)
    df["prev_range"] = df["prev_high"] - df["prev_low"]

    # Target price (Volatility Breakout)
    df["target"] = df["open"] + df["prev_range"] * df["short_noise"]

    return df


# ===== Phase 2 Improvements (formerly indicators_v2) =====


def calculate_natr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Normalized Average True Range (NATR).

    NATR = (ATR / Close) * 100
    - Price-independent volatility metric
    - Useful for comparing volatility across different price levels

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR calculation period

    Returns:
        NATR series (percentage)
    """
    atr_values = atr(high, low, close, period)
    natr = (atr_values / close) * 100
    return natr


def calculate_volatility_regime(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14, window: int = 100
) -> pd.Series:
    """
    Classify volatility regime based on NATR.

    Classification:
    - 0 (Low): NATR < 33rd percentile
    - 1 (Medium): 33rd <= NATR < 67th percentile
    - 2 (High): NATR >= 67th percentile

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        window: Rolling window for percentile calculation

    Returns:
        Volatility regime series (0=Low, 1=Medium, 2=High)
    """
    natr = calculate_natr(high, low, close, period)

    # Calculate rolling percentiles
    actual_window = min(window, len(natr) // 4) if len(natr) > 0 else window
    p33 = natr.rolling(window=actual_window).quantile(0.33)
    p67 = natr.rolling(window=actual_window).quantile(0.67)

    # Classify regime
    regime = pd.Series(0, index=natr.index)
    regime[(natr >= p33) & (natr < p67)] = 1  # Medium
    regime[natr >= p67] = 2  # High

    return regime


def calculate_adaptive_noise(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    short_period: int = 4,
    long_period: int = 8,
    atr_period: int = 14,
) -> tuple[pd.Series, pd.Series]:
    """
    Calculate ATR-normalized adaptive noise.

    Traditional: noise = high.rolling().max() - low.rolling().min()
    Improved: noise_normalized = noise / ATR

    This adapts the filter strength based on market volatility.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        short_period: Short-term noise window
        long_period: Long-term noise window
        atr_period: ATR period for normalization

    Returns:
        Tuple of (short_noise_adaptive, long_noise_adaptive)
    """
    atr_values = atr(high, low, close, atr_period)

    # Raw noise calculation
    short_noise_raw = (
        high.rolling(window=short_period).max() - low.rolling(window=short_period).min()
    )
    long_noise_raw = high.rolling(window=long_period).max() - low.rolling(window=long_period).min()

    # Normalize by ATR (prevent division by zero)
    short_noise_adaptive = short_noise_raw / (atr_values + 1e-8)
    long_noise_adaptive = long_noise_raw / (atr_values + 1e-8)

    return short_noise_adaptive, long_noise_adaptive


def calculate_noise_ratio(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    short_period: int = 4,
    long_period: int = 8,
    atr_period: int = 14,
) -> pd.Series:
    """
    Calculate noise ratio (short / long).

    Interpretation:
    - Ratio >= 0.5: High short-term noise → exclude trade (low confidence)
    - Ratio < 0.5: Low short-term noise → high confidence

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        short_period: Short-term period
        long_period: Long-term period
        atr_period: ATR period

    Returns:
        Noise ratio series
    """
    short_noise, long_noise = calculate_adaptive_noise(
        high, low, close, short_period, long_period, atr_period
    )

    # Prevent division by zero
    ratio = short_noise / (long_noise + 1e-8)

    return ratio


def calculate_adaptive_k_value(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    base_k: float = 0.5,
    atr_period: int = 14,
    window: int = 100,
) -> pd.Series:
    """
    Calculate adaptive K-value based on volatility regime.

    Strategy:
    - Low volatility: K * 0.8 (increase sensitivity)
    - Medium volatility: K * 1.0 (maintain baseline)
    - High volatility: K * 1.3 (reduce false signals)

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        base_k: Base K value
        atr_period: ATR period
        window: Window for volatility regime classification

    Returns:
        Adaptive K value series
    """
    regime = calculate_volatility_regime(high, low, close, atr_period, window)

    k_values = pd.Series(base_k, index=regime.index)
    k_values[regime == 0] = base_k * 0.8  # Low volatility
    k_values[regime == 1] = base_k * 1.0  # Medium volatility
    k_values[regime == 2] = base_k * 1.3  # High volatility

    return k_values


def add_improved_indicators(
    df: pd.DataFrame,
    short_period: int = 4,
    long_period: int = 8,
    atr_period: int = 14,
    base_k: float = 0.5,
) -> pd.DataFrame:
    """
    Add Phase 2 improved indicators to DataFrame.

    Added columns:
    - atr: Average True Range
    - natr: Normalized ATR (%)
    - volatility_regime: Volatility classification (0/1/2)
    - short_noise_adaptive: ATR-normalized short-term noise
    - long_noise_adaptive: ATR-normalized long-term noise
    - noise_ratio: Short/long noise ratio
    - k_value_adaptive: Dynamic K-value

    Args:
        df: DataFrame with OHLC columns
        short_period: Short-term period
        long_period: Long-term period
        atr_period: ATR period
        base_k: Base K value for adaptive calculation

    Returns:
        DataFrame with added improved indicators
    """
    result = df.copy()

    # Basic indicators
    result["atr"] = atr(df["high"], df["low"], df["close"], atr_period)
    result["natr"] = calculate_natr(df["high"], df["low"], df["close"], atr_period)
    result["volatility_regime"] = calculate_volatility_regime(
        df["high"], df["low"], df["close"], atr_period
    )

    # Adaptive noise
    short_noise, long_noise = calculate_adaptive_noise(
        df["high"], df["low"], df["close"], short_period, long_period, atr_period
    )
    result["short_noise_adaptive"] = short_noise
    result["long_noise_adaptive"] = long_noise
    result["noise_ratio"] = calculate_noise_ratio(
        df["high"], df["low"], df["close"], short_period, long_period, atr_period
    )

    # Adaptive K-value
    result["k_value_adaptive"] = calculate_adaptive_k_value(
        df["high"], df["low"], df["close"], base_k, atr_period
    )

    return result
