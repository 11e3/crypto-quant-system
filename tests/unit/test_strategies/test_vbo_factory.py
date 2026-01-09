"""Tests for vbo_factory module."""

from src.strategies.base_conditions import Condition
from src.strategies.volatility_breakout.vbo_factory import create_vbo_strategy


class DummyExtraCondition(Condition):
    """Dummy condition for testing."""

    def check(self, current: dict, history: dict) -> bool:
        """Dummy check."""
        return True

    def evaluate(self, current: dict, history: dict) -> bool:
        """Implement abstract method."""
        return self.check(current, history)


class TestVBOFactory:
    """Test cases for create_vbo_strategy function."""

    def test_create_vbo_with_extra_entry_conditions(self) -> None:
        """Test creating VBO with extra entry conditions (covers line 80->82)."""
        extra_entry = [DummyExtraCondition()]
        strategy = create_vbo_strategy(
            name="VBO_Extra_Entry",
            extra_entry_conditions=extra_entry,
        )

        assert strategy.name == "VBO_Extra_Entry"
        # VBO strategy should be created successfully
        assert strategy is not None

    def test_create_vbo_with_extra_exit_conditions(self) -> None:
        """Test creating VBO with extra exit conditions (covers line 91->93)."""
        extra_exit = [DummyExtraCondition()]
        strategy = create_vbo_strategy(
            name="VBO_Extra_Exit",
            extra_exit_conditions=extra_exit,
        )

        assert strategy.name == "VBO_Extra_Exit"
        # VBO strategy should be created successfully
        assert strategy is not None

    def test_create_vbo_with_both_extra_conditions(self) -> None:
        """Test creating VBO with both extra entry and exit conditions."""
        extra_entry = [DummyExtraCondition()]
        extra_exit = [DummyExtraCondition()]

        strategy = create_vbo_strategy(
            name="VBO_Both_Extra",
            extra_entry_conditions=extra_entry,
            extra_exit_conditions=extra_exit,
        )

        assert strategy.name == "VBO_Both_Extra"
        assert strategy is not None

    def test_create_vbo_without_sma_breakout(self) -> None:
        """Test creating VBO without SMA breakout - covers line 80->82 False branch."""
        strategy = create_vbo_strategy(
            name="VBO_No_SMA_Breakout",
            use_sma_breakout=False,
        )

        assert strategy.name == "VBO_No_SMA_Breakout"
        assert strategy is not None

    def test_create_vbo_without_sma_exit(self) -> None:
        """Test creating VBO without SMA exit - covers line 91->93 False branch."""
        strategy = create_vbo_strategy(
            name="VBO_No_SMA_Exit",
            use_sma_exit=False,
        )

        assert strategy.name == "VBO_No_SMA_Exit"
        assert strategy is not None
