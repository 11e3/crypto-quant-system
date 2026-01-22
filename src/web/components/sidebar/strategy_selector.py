"""Strategy selector component.

Strategy selection and dynamic parameter editing UI component.
"""

from typing import Any, cast

import streamlit as st

from src.strategies.base import Strategy
from src.utils.logger import get_logger
from src.web.services import ParameterSpec, StrategyRegistry

logger = get_logger(__name__)

__all__ = ["render_strategy_selector", "create_strategy_instance"]


@st.cache_resource  # Cache permanently - strategies don't change at runtime
def get_cached_registry() -> StrategyRegistry:
    """Return cached strategy registry."""
    logger.info("Creating new StrategyRegistry instance")
    registry = StrategyRegistry()
    logger.info(f"Registered {len(registry.list_strategies())} strategies")
    return registry


def render_strategy_selector() -> tuple[str, dict[str, Any]]:
    """Render strategy selection and dynamic parameters.

    Returns:
        (strategy_name, parameters) tuple
    """
    st.subheader("📈 Strategy Selection")

    registry = get_cached_registry()
    strategies = registry.list_strategies()

    if not strategies:
        st.error("⚠️ No strategies registered.")
        return "", {}

    # Strategy name list
    strategy_names = [s.name for s in strategies]

    # Strategy selection
    selected_name = st.selectbox(
        "Strategy",
        options=strategy_names,
        help="Select strategy to use for backtest",
    )

    # Selected strategy info
    selected_strategy = registry.get_strategy(selected_name)
    if not selected_strategy:
        st.error(f"⚠️ Strategy not found: {selected_name}")
        return "", {}

    # Display strategy description
    if selected_strategy.description:
        st.caption(f"ℹ️ {selected_strategy.description}")

    st.markdown("---")

    # Parameter editing
    st.subheader("🎛️ Strategy Parameters")

    parameters = selected_strategy.parameters

    if not parameters:
        st.info("📌 This strategy has no configurable parameters.")
        return selected_name, {}

    param_values: dict[str, Any] = {}

    # Render UI by parameter type
    for name, spec in parameters.items():
        param_values[name] = _render_parameter_input(name, spec)

    return selected_name, param_values


def _render_parameter_input(name: str, spec: ParameterSpec) -> Any:
    """Render input UI based on parameter type.

    Args:
        name: Parameter name
        spec: Parameter specification

    Returns:
        User input value
    """
    # Format name (snake_case -> Title Case)
    label = name.replace("_", " ").title()

    match spec.type:
        case "int":
            int_default = int(spec.default)
            int_min = int(spec.min_value or 1)
            # Ensure max_value is at least as large as default
            int_max = (
                int(spec.max_value) if spec.max_value is not None else max(100, int_default * 2)
            )
            return st.slider(
                label,
                min_value=int_min,
                max_value=int_max,
                value=int_default,
                step=int(spec.step or 1),
                help=spec.description or f"Integer parameter: {name}",
            )

        case "float":
            float_default = float(spec.default)
            float_min = float(spec.min_value or 0.0)
            # Ensure max_value is at least as large as default
            float_max = (
                float(spec.max_value) if spec.max_value is not None else max(1.0, float_default * 2)
            )
            return st.number_input(
                label,
                min_value=float_min,
                max_value=float_max,
                value=float_default,
                step=float(spec.step or 0.01),
                format="%.4f",
                help=spec.description or f"Float parameter: {name}",
            )

        case "bool":
            return st.checkbox(
                label,
                value=bool(spec.default),
                help=spec.description or f"Boolean parameter: {name}",
            )

        case "choice":
            choices = spec.choices or []
            default_index = choices.index(spec.default) if spec.default in choices else 0
            return st.selectbox(
                label,
                options=choices,
                index=default_index,
                help=spec.description or f"Choice parameter: {name}",
            )

        case _:
            logger.warning(f"Unknown parameter type: {spec.type}")
            return spec.default


def create_strategy_instance(strategy_name: str, parameters: dict[str, Any]) -> Strategy | None:
    """Create strategy instance.

    Args:
        strategy_name: Strategy name
        parameters: Parameters dictionary

    Returns:
        Strategy instance or None (on failure)
    """
    try:
        registry = get_cached_registry()
        strategy_class = registry.get_strategy_class(strategy_name)

        if not strategy_class:
            logger.error(f"Strategy class not found: {strategy_name}")
            return None

        # Create strategy instance
        strategy = strategy_class(**parameters)
        logger.info(f"Created strategy: {strategy_name} with params: {parameters}")
        return cast(Strategy, strategy)

    except Exception as e:
        logger.exception(f"Failed to create strategy {strategy_name}: {e}")
        return None
