"""Tests for src/cli/commands/compare_utils.py - strategy creation utilities."""

import pytest

from src.cli.commands.compare_utils import create_strategy_for_compare
from src.strategies.mean_reversion import MeanReversionStrategy, SimpleMeanReversionStrategy
from src.strategies.momentum import MomentumStrategy, SimpleMomentumStrategy


class TestCreateStrategyForCompare:
    """Tests for create_strategy_for_compare function."""

    def test_create_vanilla_strategy(self) -> None:
        """Test creating vanilla VBO strategy."""
        strategy = create_strategy_for_compare("vanilla")

        assert strategy is not None
        assert strategy.name == "VanillaVBO"

    def test_create_minimal_strategy(self) -> None:
        """Test creating minimal VBO strategy."""
        strategy = create_strategy_for_compare("minimal")

        assert strategy is not None
        assert strategy.name == "MinimalVBO"

    def test_create_legacy_strategy(self) -> None:
        """Test creating legacy VBO strategy."""
        strategy = create_strategy_for_compare("legacy")

        assert strategy is not None
        assert strategy.name == "LegacyBT"

    def test_create_momentum_strategy(self) -> None:
        """Test creating momentum strategy."""
        strategy = create_strategy_for_compare("momentum")

        assert strategy is not None
        assert isinstance(strategy, MomentumStrategy)

    def test_create_simple_momentum_strategy(self) -> None:
        """Test creating simple momentum strategy."""
        strategy = create_strategy_for_compare("simple-momentum")

        assert strategy is not None
        assert isinstance(strategy, SimpleMomentumStrategy)

    def test_create_mean_reversion_strategy(self) -> None:
        """Test creating mean reversion strategy."""
        strategy = create_strategy_for_compare("mean-reversion")

        assert strategy is not None
        assert isinstance(strategy, MeanReversionStrategy)

    def test_create_simple_mean_reversion_strategy(self) -> None:
        """Test creating simple mean reversion strategy."""
        strategy = create_strategy_for_compare("simple-mean-reversion")

        assert strategy is not None
        assert isinstance(strategy, SimpleMeanReversionStrategy)

    def test_create_unknown_strategy(self) -> None:
        """Test creating unknown strategy returns None."""
        strategy = create_strategy_for_compare("unknown-strategy")

        assert strategy is None
