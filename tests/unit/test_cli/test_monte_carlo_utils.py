"""Tests for src/cli/commands/monte_carlo_utils.py - Monte Carlo strategy utilities."""

import pytest

from src.cli.commands.monte_carlo_utils import create_strategy_for_monte_carlo


class TestCreateStrategyForMonteCarlo:
    """Tests for create_strategy_for_monte_carlo function."""

    def test_create_vanilla_strategy(self) -> None:
        """Test creating vanilla VBO strategy."""
        strategy = create_strategy_for_monte_carlo("vanilla")

        assert strategy is not None
        assert strategy.name == "VanillaVBO"

    def test_create_minimal_strategy(self) -> None:
        """Test creating minimal VBO strategy."""
        strategy = create_strategy_for_monte_carlo("minimal")

        assert strategy is not None
        assert strategy.name == "MinimalVBO"

    def test_create_legacy_strategy(self) -> None:
        """Test creating legacy VBO strategy."""
        strategy = create_strategy_for_monte_carlo("legacy")

        assert strategy is not None
        assert strategy.name == "LegacyBT"

    def test_create_unknown_strategy(self) -> None:
        """Test creating unsupported strategy returns None."""
        strategy = create_strategy_for_monte_carlo("unsupported")

        assert strategy is None
