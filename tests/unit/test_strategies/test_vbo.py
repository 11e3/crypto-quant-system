"""
Unit tests for VanillaVBO strategy.
"""

import pandas as pd

from src.strategies.volatility_breakout import (
    MinimalVBO,
    StrictVBO,
    VanillaVBO,
    create_vbo_strategy,
    quick_vbo,
)
from src.strategies.volatility_breakout.conditions import (
    BreakoutCondition,
    ConsecutiveUpCondition,
    PriceAboveSMACondition,
    PriceBelowSMACondition,
    SMABreakoutCondition,
    VolatilityThresholdCondition,
)


class TestVanillaVBO:
    """Test cases for VanillaVBO strategy."""

    def test_strategy_initialization(self, vbo_strategy: VanillaVBO) -> None:
        """Test strategy initialization."""
        assert vbo_strategy.sma_period == 4
        assert vbo_strategy.trend_sma_period == 8
        assert vbo_strategy.short_noise_period == 4
        assert vbo_strategy.long_noise_period == 8
        assert vbo_strategy.exclude_current is False
        assert vbo_strategy.name == "VanillaVBO"

    def test_strategy_initialization_custom_params(self) -> None:
        """Test strategy initialization with custom parameters."""
        strategy = VanillaVBO(
            name="CustomVBO",
            sma_period=5,
            trend_sma_period=10,
            short_noise_period=3,
            long_noise_period=6,
            exclude_current=True,
        )
        assert strategy.sma_period == 5
        assert strategy.trend_sma_period == 10
        assert strategy.short_noise_period == 3
        assert strategy.long_noise_period == 6
        assert strategy.exclude_current is True
        assert strategy.name == "CustomVBO"

    def test_strategy_initialization_without_default_conditions(self) -> None:
        """Test strategy initialization without default conditions."""
        strategy = VanillaVBO(use_default_conditions=False)
        assert len(strategy.entry_conditions.conditions) == 0
        assert len(strategy.exit_conditions.conditions) == 0

    def test_strategy_initialization_custom_conditions(self) -> None:
        """Test strategy initialization with custom conditions."""
        custom_entry = [BreakoutCondition()]
        custom_exit = [PriceBelowSMACondition()]
        strategy = VanillaVBO(
            entry_conditions=custom_entry,
            exit_conditions=custom_exit,
            use_default_conditions=False,
        )
        assert len(strategy.entry_conditions.conditions) == 1
        assert len(strategy.exit_conditions.conditions) == 1
        assert strategy.entry_conditions.conditions[0].name == "Breakout"
        assert strategy.exit_conditions.conditions[0].name == "PriceBelowSMA"

    def test_strategy_default_conditions(self, vbo_strategy: VanillaVBO) -> None:
        """Test that default conditions are added."""
        entry_names = [c.name for c in vbo_strategy.entry_conditions.conditions]
        exit_names = [c.name for c in vbo_strategy.exit_conditions.conditions]

        assert "Breakout" in entry_names
        assert "SMABreakout" in entry_names
        assert "TrendCondition" in entry_names or "TrendFilter" in entry_names
        assert "NoiseCondition" in entry_names or "NoiseFilter" in entry_names
        assert "PriceBelowSMA" in exit_names

    def test_required_indicators(self, vbo_strategy: VanillaVBO) -> None:
        """Test required_indicators method."""
        indicators = vbo_strategy.required_indicators()
        assert "sma" in indicators
        assert "sma_trend" in indicators
        assert "short_noise" in indicators
        assert "long_noise" in indicators
        assert "target" in indicators
        assert "prev_high" in indicators
        assert "prev_low" in indicators
        assert "prev_range" in indicators

    def test_calculate_indicators(
        self, vbo_strategy: VanillaVBO, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test indicator calculation."""
        df = vbo_strategy.calculate_indicators(sample_ohlcv_data.copy())

        # Check that indicators are added
        assert "sma" in df.columns
        assert "sma_trend" in df.columns
        assert "short_noise" in df.columns
        assert "long_noise" in df.columns
        assert "target" in df.columns
        assert "prev_high" in df.columns
        assert "prev_low" in df.columns
        assert "prev_range" in df.columns

        # Check that indicators are calculated (not all NaN)
        assert df["sma"].notna().sum() > 0
        assert df["sma_trend"].notna().sum() > 0

    def test_calculate_indicators_exclude_current(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test indicator calculation with exclude_current=True."""
        strategy = VanillaVBO(exclude_current=True)
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())

        # Should still calculate indicators
        assert "sma" in df.columns
        assert "target" in df.columns

    def test_generate_signals(
        self, vbo_strategy: VanillaVBO, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test signal generation."""
        df = vbo_strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = vbo_strategy.generate_signals(df)

        # Check that signals are added
        assert "entry_signal" in df.columns
        assert "exit_signal" in df.columns

        # Check signal types
        assert df["entry_signal"].dtype == bool
        assert df["exit_signal"].dtype == bool

    def test_generate_signals_empty_conditions(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test signal generation with no conditions."""
        strategy = VanillaVBO(use_default_conditions=False)
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        # All entry signals should be True (no conditions = all pass)
        assert df["entry_signal"].all()
        # All exit signals should be False (no conditions = no exit)
        assert not df["exit_signal"].any()

    def test_generate_signals_breakout_condition(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test signal generation with only breakout condition."""
        strategy = VanillaVBO(
            entry_conditions=[BreakoutCondition()],
            use_default_conditions=False,
        )
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        # Entry signal should be True when high >= target
        entry_rows = df[df["entry_signal"]]
        if len(entry_rows) > 0:
            assert (entry_rows["high"] >= entry_rows["target"]).all()

    def test_generate_signals_sma_exit_condition(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test signal generation with SMA exit condition."""
        strategy = VanillaVBO(
            entry_conditions=[],
            exit_conditions=[PriceBelowSMACondition()],
            use_default_conditions=False,
        )
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        # Exit signal should be True when close < sma
        exit_rows = df[df["exit_signal"]]
        if len(exit_rows) > 0:
            assert (exit_rows["close"] < exit_rows["sma"]).all()

    def test_generate_signals_multiple_conditions(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test signal generation with multiple entry conditions."""
        strategy = VanillaVBO(
            entry_conditions=[
                BreakoutCondition(),
                SMABreakoutCondition(),
            ],
            use_default_conditions=False,
        )
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        entry_rows = df[df["entry_signal"]]
        if len(entry_rows) > 0:
            # All conditions must be met (AND logic)
            assert (entry_rows["high"] >= entry_rows["target"]).all()
            assert (entry_rows["target"] > entry_rows["sma"]).all()

    def test_generate_signals_volatility_threshold_condition(
        self, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test signal generation with VolatilityThreshold condition (covers lines 156-159)."""
        strategy = VanillaVBO(
            entry_conditions=[
                BreakoutCondition(),
                VolatilityThresholdCondition(min_range_pct=0.01),
            ],
            use_default_conditions=False,
        )
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        assert "entry_signal" in df.columns
        entry_rows = df[df["entry_signal"]]
        if len(entry_rows) > 0:
            # Entry signals should meet both breakout and volatility threshold conditions
            assert (entry_rows["high"] >= entry_rows["target"]).all()
            range_pct = entry_rows["prev_range"] / entry_rows["open"]
            assert (range_pct >= 0.01).all()

    def test_entry_condition(
        self, vbo_strategy: VanillaVBO, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test entry condition logic."""
        df = vbo_strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = vbo_strategy.generate_signals(df)

        # Entry signal should be boolean
        entry_signals = df["entry_signal"]
        assert entry_signals.dtype == bool

        # If there are entry signals, verify they occur when conditions are met
        if entry_signals.any():
            entry_rows = df[entry_signals]
            # Basic sanity check: entry signals should have valid indicators
            assert entry_rows["sma"].notna().all()
            assert entry_rows["target"].notna().all()

    def test_exit_condition(
        self, vbo_strategy: VanillaVBO, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test exit condition logic."""
        df = vbo_strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = vbo_strategy.generate_signals(df)

        # Exit signal should be boolean
        exit_signals = df["exit_signal"]
        assert exit_signals.dtype == bool

    def test_target_price_calculation(
        self, vbo_strategy: VanillaVBO, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test target price calculation."""
        df = vbo_strategy.calculate_indicators(sample_ohlcv_data.copy())

        # Target price should be calculated
        assert "target" in df.columns
        target_prices = df["target"]

        # Target prices should be positive when calculated
        valid_targets = target_prices[target_prices.notna()]
        if len(valid_targets) > 0:
            assert (valid_targets > 0).all()


class TestMinimalVBO:
    """Test cases for MinimalVBO strategy."""

    def test_minimal_vbo_initialization(self) -> None:
        """Test MinimalVBO initialization."""
        strategy = MinimalVBO()
        assert strategy.name == "MinimalVBO"
        assert len(strategy.entry_conditions.conditions) == 1
        assert strategy.entry_conditions.conditions[0].name == "Breakout"
        assert len(strategy.exit_conditions.conditions) == 0

    def test_minimal_vbo_custom_name(self) -> None:
        """Test MinimalVBO with custom name."""
        strategy = MinimalVBO(name="MyMinimalVBO")
        assert strategy.name == "MyMinimalVBO"

    def test_minimal_vbo_signals(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test MinimalVBO signal generation."""
        strategy = MinimalVBO()
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        assert "entry_signal" in df.columns
        assert "exit_signal" in df.columns

        # Entry signals should only depend on breakout condition
        entry_rows = df[df["entry_signal"]]
        if len(entry_rows) > 0:
            assert (entry_rows["high"] >= entry_rows["target"]).all()

    def test_minimal_vbo_inheritance(self) -> None:
        """Test that MinimalVBO inherits from VanillaVBO."""
        strategy = MinimalVBO()
        assert isinstance(strategy, VanillaVBO)
        assert strategy.sma_period == 4  # Default from VanillaVBO


class TestStrictVBO:
    """Test cases for StrictVBO strategy."""

    def test_strict_vbo_initialization(self) -> None:
        """Test StrictVBO initialization."""
        strategy = StrictVBO()
        assert strategy.name == "StrictVBO"
        # Should have default entry conditions plus extra conditions
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        assert "NoiseThresholdCondition" in entry_names or any(
            "NoiseThreshold" in name for name in entry_names
        )
        assert "VolatilityRangeCondition" in entry_names or any(
            "Volatility" in name for name in entry_names
        )

    def test_strict_vbo_custom_params(self) -> None:
        """Test StrictVBO with custom parameters."""
        strategy = StrictVBO(max_noise=0.5, min_volatility_pct=0.02)
        assert strategy.name == "StrictVBO"

    def test_strict_vbo_signals(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test StrictVBO signal generation."""
        strategy = StrictVBO()
        df = strategy.calculate_indicators(sample_ohlcv_data.copy())
        df = strategy.generate_signals(df)

        assert "entry_signal" in df.columns
        assert "exit_signal" in df.columns

    def test_strict_vbo_inheritance(self) -> None:
        """Test that StrictVBO inherits from VanillaVBO."""
        strategy = StrictVBO()
        assert isinstance(strategy, VanillaVBO)


class TestCreateVBOStrategy:
    """Test cases for create_vbo_strategy factory function."""

    def test_create_vbo_strategy_default(self) -> None:
        """Test create_vbo_strategy with default parameters."""
        strategy = create_vbo_strategy()
        assert strategy.name == "CustomVBO"
        assert len(strategy.entry_conditions.conditions) >= 2  # At least breakout and SMA breakout
        assert len(strategy.exit_conditions.conditions) == 1  # SMA exit

    def test_create_vbo_strategy_custom_name(self) -> None:
        """Test create_vbo_strategy with custom name."""
        strategy = create_vbo_strategy(name="MyCustomVBO")
        assert strategy.name == "MyCustomVBO"

    def test_create_vbo_strategy_without_breakout(self) -> None:
        """Test create_vbo_strategy without breakout condition."""
        strategy = create_vbo_strategy(use_breakout=False)
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        assert "Breakout" not in entry_names

    def test_create_vbo_strategy_without_trend_filter(self) -> None:
        """Test create_vbo_strategy without trend filter."""
        strategy = create_vbo_strategy(use_trend_filter=False)
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        assert "TrendCondition" not in entry_names and "TrendFilter" not in entry_names

    def test_create_vbo_strategy_without_noise_filter(self) -> None:
        """Test create_vbo_strategy without noise filter."""
        strategy = create_vbo_strategy(use_noise_filter=False)
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        assert "NoiseCondition" not in entry_names and "NoiseFilter" not in entry_names

    def test_create_vbo_strategy_extra_entry_conditions(self) -> None:
        """Test create_vbo_strategy with extra entry conditions."""
        extra = [ConsecutiveUpCondition(days=2)]
        strategy = create_vbo_strategy(extra_entry_conditions=extra)
        entry_names = [c.name for c in strategy.entry_conditions.conditions]
        assert "ConsecutiveUp" in entry_names

    def test_create_vbo_strategy_extra_exit_conditions(self) -> None:
        """Test create_vbo_strategy with extra exit conditions (covers line 303)."""
        # Test with actual exit conditions to cover the extend() call
        extra_exit = [PriceAboveSMACondition()]
        strategy = create_vbo_strategy(
            extra_exit_conditions=extra_exit,
            use_sma_exit=True,  # This adds PriceBelowSMACondition
        )
        # Should have both default SMA exit and extra exit condition
        assert len(strategy.exit_conditions.conditions) == 2
        exit_names = [c.name for c in strategy.exit_conditions.conditions]
        assert "PriceBelowSMA" in exit_names
        assert "PriceAboveSMA" in exit_names

    def test_create_vbo_strategy_exclude_current(self) -> None:
        """Test create_vbo_strategy with exclude_current parameter."""
        strategy = create_vbo_strategy(exclude_current=True)
        assert strategy.exclude_current is True

    def test_create_vbo_strategy_custom_periods(self) -> None:
        """Test create_vbo_strategy with custom periods."""
        strategy = create_vbo_strategy(
            sma_period=5,
            trend_sma_period=10,
            short_noise_period=3,
            long_noise_period=6,
        )
        assert strategy.sma_period == 5
        assert strategy.trend_sma_period == 10
        assert strategy.short_noise_period == 3
        assert strategy.long_noise_period == 6


class TestQuickVBO:
    """Test cases for quick_vbo convenience function."""

    def test_quick_vbo_default(self) -> None:
        """Test quick_vbo with default parameters."""
        strategy = quick_vbo()
        assert "VBO_SMA4_N2" in strategy.name
        assert strategy.sma_period == 4
        assert strategy.trend_sma_period == 8  # 4 * 2
        assert strategy.short_noise_period == 4
        assert strategy.long_noise_period == 8  # 4 * 2

    def test_quick_vbo_custom_params(self) -> None:
        """Test quick_vbo with custom parameters."""
        strategy = quick_vbo(sma=5, n=3)
        assert "VBO_SMA5_N3" in strategy.name
        assert strategy.sma_period == 5
        assert strategy.trend_sma_period == 15  # 5 * 3
        assert strategy.short_noise_period == 5
        assert strategy.long_noise_period == 15  # 5 * 3
