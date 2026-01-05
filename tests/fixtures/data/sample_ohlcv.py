"""
Sample OHLCV data generators for testing.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_ohlcv_data(
    periods: int = 100,
    start_date: str | None = None,
    base_price: float = 50_000_000.0,
    volatility: float = 0.02,
    seed: int | None = 42,
) -> pd.DataFrame:
    """
    Generate realistic OHLCV data for testing.

    Args:
        periods: Number of periods to generate
        start_date: Start date (YYYY-MM-DD format). If None, uses 100 days ago.
        base_price: Starting price
        volatility: Daily volatility (standard deviation of returns)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with OHLCV columns and datetime index
    """
    if seed is not None:
        np.random.seed(seed)

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=periods)).strftime("%Y-%m-%d")

    dates = pd.date_range(start=start_date, periods=periods, freq="D")

    # Generate realistic price data using random walk
    returns = np.random.normal(0, volatility, periods)
    prices = base_price * (1 + returns).cumprod()

    # Generate OHLCV data
    data = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.005, periods)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            "close": prices,
            "volume": np.random.uniform(100, 1000, periods),
        },
        index=dates,
    )

    # Ensure high >= close >= low and high >= open >= low
    data["high"] = data[["open", "high", "close"]].max(axis=1) * 1.01
    data["low"] = data[["open", "low", "close"]].min(axis=1) * 0.99

    return data


def generate_trending_data(
    periods: int = 100,
    start_price: float = 50_000_000.0,
    trend: float = 0.001,  # Daily trend (0.1% per day)
    volatility: float = 0.02,
    seed: int | None = 42,
) -> pd.DataFrame:
    """
    Generate OHLCV data with a clear trend.

    Args:
        periods: Number of periods
        start_price: Starting price
        trend: Daily trend (positive for uptrend, negative for downtrend)
        volatility: Daily volatility
        seed: Random seed

    Returns:
        DataFrame with trending OHLCV data
    """
    if seed is not None:
        np.random.seed(seed)

    dates = pd.date_range(start="2024-01-01", periods=periods, freq="D")

    # Generate prices with trend
    returns = np.random.normal(trend, volatility, periods)
    prices = start_price * (1 + returns).cumprod()

    data = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.005, periods)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            "close": prices,
            "volume": np.random.uniform(100, 1000, periods),
        },
        index=dates,
    )

    # Ensure high >= close >= low and high >= open >= low
    data["high"] = data[["open", "high", "close"]].max(axis=1) * 1.01
    data["low"] = data[["open", "low", "close"]].min(axis=1) * 0.99

    return data


def generate_volatile_data(
    periods: int = 100,
    base_price: float = 50_000_000.0,
    volatility: float = 0.05,  # Higher volatility
    seed: int | None = 42,
) -> pd.DataFrame:
    """
    Generate highly volatile OHLCV data for testing.

    Args:
        periods: Number of periods
        base_price: Starting price
        volatility: Daily volatility (higher than normal)
        seed: Random seed

    Returns:
        DataFrame with volatile OHLCV data
    """
    return generate_ohlcv_data(
        periods=periods,
        base_price=base_price,
        volatility=volatility,
        seed=seed,
    )


def generate_multiple_tickers_data(
    tickers: list[str],
    periods: int = 100,
    base_prices: dict[str, float] | None = None,
    seed: int | None = 42,
) -> dict[str, pd.DataFrame]:
    """
    Generate OHLCV data for multiple tickers.

    Args:
        tickers: List of ticker symbols
        periods: Number of periods per ticker
        base_prices: Optional dict of base prices per ticker
        seed: Random seed

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    if base_prices is None:
        base_prices = {
            "KRW-BTC": 50_000_000.0,
            "KRW-ETH": 3_000_000.0,
            "KRW-XRP": 500.0,
            "KRW-SOL": 200_000.0,
            "KRW-DOGE": 100.0,
            "KRW-TRX": 50.0,
        }

    result = {}
    for i, ticker in enumerate(tickers):
        base_price = base_prices.get(ticker, 1_000_000.0)
        result[ticker] = generate_ohlcv_data(
            periods=periods,
            base_price=base_price,
            seed=seed + i if seed is not None else None,
        )

    return result
