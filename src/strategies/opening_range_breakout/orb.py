"""
Opening Range Breakout (ORB) Strategy.

ATR-based volatility targeting strategy with trailing stop exits.
Supports multiple assets with flexible position sizing.
"""

from typing import Any, Literal

import pandas as pd

from src.strategies.base import Strategy
from src.strategies.opening_range_breakout.conditions import (
    ATRORBCondition,
    NoiseFilterCondition,
    STDORBCondition,
    TrendFilterCondition,
)
from src.utils.indicators import calculate_atr, calculate_noise


class ORBStrategy(Strategy):
    """
    Opening Range Breakout Strategy with ATR-based position sizing.

    Features:
    - ATR or Standard breakout modes
    - Volatility-targeted position sizing
    - ATR-based trailing stop loss
    - ATR-based slippage modeling
    - Noise and trend filters

    Args:
        breakout_mode: 'atr' for ATR-based, 'std' for standard high breakout
        k_multiplier: ATR multiplier for breakout threshold (ATR mode only)
        atr_window: ATR calculation window
        atr_multiplier: ATR multiplier for trailing stop
        vol_target: Target volatility for position sizing (e.g., 0.02 for 2%)
        noise_window: Noise SMA window for filter
        noise_threshold: Maximum noise ratio for entry
        sma_window: SMA window for trend filter
        trend_price: Price column for trend filter ('open' or 'close')
        atr_slippage: Slippage as multiple of ATR
        name: Strategy name
    """

    def __init__(
        self,
        breakout_mode: Literal["atr", "std"] = "atr",
        k_multiplier: float = 0.5,
        atr_window: int = 14,
        atr_multiplier: float = 2.0,
        vol_target: float = 0.02,
        noise_window: int = 5,
        noise_threshold: float = 0.5,
        sma_window: int = 20,
        trend_price: Literal["open", "close"] = "open",
        atr_slippage: float = 0.1,
        name: str = "orb",
    ) -> None:
        super().__init__(name=name)

        # Strategy parameters
        self.breakout_mode = breakout_mode
        self.k_multiplier = k_multiplier
        self.atr_window = atr_window
        self.atr_multiplier = atr_multiplier
        self.vol_target = vol_target
        self.noise_window = noise_window
        self.noise_threshold = noise_threshold
        self.sma_window = sma_window
        self.trend_price = trend_price
        self.atr_slippage = atr_slippage

        # Initialize conditions based on breakout mode
        self.breakout_condition: ATRORBCondition | STDORBCondition
        if breakout_mode == "atr":
            self.breakout_condition = ATRORBCondition(
                k_multiplier=k_multiplier,
                atr_window=atr_window,
            )
        else:  # std mode
            self.breakout_condition = STDORBCondition()

        self.noise_filter: NoiseFilterCondition = NoiseFilterCondition(
            noise_window=noise_window,
            noise_threshold=noise_threshold,
        )

        self.trend_filter: TrendFilterCondition = TrendFilterCondition(
            sma_window=sma_window,
            price_column=trend_price,
        )

    def required_indicators(self) -> list[str]:
        """
        List of required indicators.

        Returns:
            List of indicator names
        """
        return ["atr", "noise", "sma"]

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate required indicators.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()

        # Calculate ATR
        df["atr"] = calculate_atr(df, window=self.atr_window)

        # Calculate noise
        df["noise"] = calculate_noise(df)

        # Calculate SMA
        from src.utils.indicators import sma

        df["sma"] = sma(df["close"], period=self.sma_window)

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry and exit signals.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with entry_signal, exit_signal, and metadata columns
        """
        df = data.copy()

        # Calculate ATR (needed for multiple purposes)
        atr = calculate_atr(df, window=self.atr_window)
        df["atr"] = atr

        # Entry signal: breakout + noise filter + trend filter
        breakout = self.breakout_condition.evaluate(df)
        noise_ok = self.noise_filter.evaluate(df)
        trend_ok = self.trend_filter.evaluate(df)

        df["entry_signal"] = breakout & noise_ok & trend_ok

        # Target price (entry price for VectorizedBacktestEngine)
        if self.breakout_mode == "atr":
            # ATR mode: target = open + k * ATR
            df["target"] = df["open"] + self.k_multiplier * atr
        else:
            # Standard mode: target = period high
            df["target"] = df["high"]

        # Exit signal: trailing stop (handled in backtest engine)
        # For now, mark as False (actual exit logic uses trailing_stop_distance)
        df["exit_signal"] = False

        # Trailing stop distance: atr_multiplier * ATR
        df["trailing_stop_distance"] = self.atr_multiplier * atr

        # Position size: volatility-targeted
        # qty = equity * vol_target / (atr * atr_multiplier)
        df["position_size_multiplier"] = self.vol_target / (atr * self.atr_multiplier)

        # Slippage: atr_slippage * ATR
        df["slippage_amount"] = self.atr_slippage * atr

        return df

    def get_parameters(self) -> dict[str, Any]:
        """
        Get strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """
        return {
            "breakout_mode": self.breakout_mode,
            "k_multiplier": self.k_multiplier,
            "atr_window": self.atr_window,
            "atr_multiplier": self.atr_multiplier,
            "vol_target": self.vol_target,
            "noise_window": self.noise_window,
            "noise_threshold": self.noise_threshold,
            "sma_window": self.sma_window,
            "trend_price": self.trend_price,
            "atr_slippage": self.atr_slippage,
        }

    def __repr__(self) -> str:
        """String representation of the strategy."""
        params = self.get_parameters()
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"{self.__class__.__name__}({param_str})"
