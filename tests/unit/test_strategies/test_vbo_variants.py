"""
Tests for VBO strategy variants.
"""

from src.strategies.base import Condition
from src.strategies.volatility_breakout.conditions import (
    BreakoutCondition,
    NoiseThresholdCondition,
    VolatilityRangeCondition,
)
from src.strategies.volatility_breakout.vbo import VanillaVBO
from src.strategies.volatility_breakout.vbo_variants import (
    create_minimal_vbo,
    create_strict_vbo,
)


class TestCreateMinimalVBO:
    """Tests for create_minimal_vbo factory function."""

    def test_create_minimal_vbo_default(self) -> None:
        """Test create_minimal_vbo with default parameters."""
        strategy = create_minimal_vbo()

        assert isinstance(strategy, VanillaVBO)
        assert strategy.name == "MinimalVBO"
        assert strategy.sma_period == 4
        assert strategy.trend_sma_period == 8
        assert strategy.short_noise_period == 4
        assert strategy.long_noise_period == 8
        assert strategy.exclude_current is False

    def test_create_minimal_vbo_custom_name(self) -> None:
        """Test create_minimal_vbo with custom name."""
        strategy = create_minimal_vbo(name="CustomMinimal")
        assert strategy.name == "CustomMinimal"

    def test_create_minimal_vbo_custom_params(self) -> None:
        """Test create_minimal_vbo with custom parameters."""
        strategy = create_minimal_vbo(
            name="TestMinimal",
            sma_period=5,
            trend_sma_period=10,
            short_noise_period=3,
            long_noise_period=6,
            exclude_current=True,
        )

        assert strategy.name == "TestMinimal"
        assert strategy.sma_period == 5
        assert strategy.trend_sma_period == 10
        assert strategy.short_noise_period == 3
        assert strategy.long_noise_period == 6
        assert strategy.exclude_current is True

    def test_create_minimal_vbo_has_breakout_condition(self) -> None:
        """Test that minimal VBO has only breakout condition."""
        strategy = create_minimal_vbo()

        # Check entry conditions contain BreakoutCondition
        has_breakout = False
        for condition in strategy.entry_conditions.conditions:
            if isinstance(condition, BreakoutCondition):
                has_breakout = True
                break

        assert has_breakout


class TestCreateStrictVBO:
    """Tests for create_strict_vbo factory function."""

    def test_create_strict_vbo_default(self) -> None:
        """Test create_strict_vbo with default parameters."""
        strategy = create_strict_vbo()

        assert isinstance(strategy, VanillaVBO)
        assert strategy.name == "StrictVBO"
        assert strategy.sma_period == 4
        assert strategy.trend_sma_period == 8
        assert strategy.short_noise_period == 4
        assert strategy.long_noise_period == 8
        assert strategy.exclude_current is False

    def test_create_strict_vbo_custom_name(self) -> None:
        """Test create_strict_vbo with custom name."""
        strategy = create_strict_vbo(name="CustomStrict")
        assert strategy.name == "CustomStrict"

    def test_create_strict_vbo_custom_params(self) -> None:
        """Test create_strict_vbo with custom parameters."""
        strategy = create_strict_vbo(
            name="TestStrict",
            max_noise=0.5,
            min_volatility_pct=0.02,
            sma_period=6,
            trend_sma_period=12,
            short_noise_period=5,
            long_noise_period=10,
            exclude_current=True,
        )

        assert strategy.name == "TestStrict"
        assert strategy.sma_period == 6
        assert strategy.trend_sma_period == 12
        assert strategy.short_noise_period == 5
        assert strategy.long_noise_period == 10
        assert strategy.exclude_current is True

    def test_create_strict_vbo_has_noise_threshold(self) -> None:
        """Test that strict VBO has NoiseThresholdCondition."""
        strategy = create_strict_vbo(max_noise=0.7)

        has_noise_threshold = False
        for condition in strategy.entry_conditions.conditions:
            if isinstance(condition, NoiseThresholdCondition):
                has_noise_threshold = True
                assert condition.max_noise == 0.7
                break

        assert has_noise_threshold

    def test_create_strict_vbo_has_volatility_range(self) -> None:
        """Test that strict VBO has VolatilityRangeCondition."""
        strategy = create_strict_vbo(min_volatility_pct=0.015)

        has_volatility_range = False
        for condition in strategy.entry_conditions.conditions:
            if isinstance(condition, VolatilityRangeCondition):
                has_volatility_range = True
                assert condition.min_volatility_pct == 0.015
                break

        assert has_volatility_range

    def test_create_strict_vbo_with_extra_conditions(self) -> None:
        """Test create_strict_vbo with extra entry conditions."""

        class CustomCondition(Condition):
            """Custom condition for testing."""

            def __init__(self) -> None:
                super().__init__(name="custom")

            def evaluate(self, *args: object, **kwargs: object) -> bool:
                return True

        extra_conditions = [CustomCondition()]
        strategy = create_strict_vbo(extra_entry_conditions=extra_conditions)

        has_custom = False
        for condition in strategy.entry_conditions.conditions:
            if isinstance(condition, CustomCondition):
                has_custom = True
                break

        assert has_custom

    def test_create_strict_vbo_uses_default_conditions(self) -> None:
        """Test that strict VBO uses default conditions."""
        strategy = create_strict_vbo()

        # VanillaVBO with use_default_conditions=True should have
        # more conditions than just the extra ones
        assert len(strategy.entry_conditions.conditions) >= 2
