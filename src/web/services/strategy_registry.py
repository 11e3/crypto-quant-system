"""Strategy registry service.

Discover automatically registered strategies and provide metadata.
"""

import inspect
from importlib import import_module
from typing import Any

from src.strategies.base import Strategy
from src.utils.logger import get_logger
from src.web.services.parameter_models import ParameterSpec, StrategyInfo

logger = get_logger(__name__)

__all__ = ["StrategyRegistry"]


class StrategyRegistry:
    """Strategy auto-detection and registry.

    Scan all strategy modules to discover Strategy subclasses,
    and generate metadata by extracting parameters from __init__ signature.

    Example:
        >>> registry = StrategyRegistry()
        >>> strategies = registry.list_strategies()
        >>> for info in strategies:
        ...     print(f"{info.name}: {info.description}")
        >>>
        >>> params = registry.get_parameters("VanillaVBO")
        >>> strategy_class = registry.get_strategy_class("VanillaVBO")
    """

    STRATEGY_MODULES = [
        "src.strategies.volatility_breakout",
        "src.strategies.momentum",
        "src.strategies.mean_reversion",
        "src.strategies.opening_range_breakout",
    ]

    def __init__(self) -> None:
        """Initialize registry and discover strategies."""
        self._strategies: dict[str, StrategyInfo] = {}
        self._discover_strategies()

    def _discover_strategies(self) -> None:
        """Discover Strategy subclasses from all strategy modules."""
        for module_path in self.STRATEGY_MODULES:
            try:
                module = import_module(module_path)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if self._is_valid_strategy(obj):
                        self._register_strategy(name, obj, module_path)
            except ImportError as e:
                logger.warning(f"Failed to import module {module_path}: {e}")

    def _is_valid_strategy(self, cls: type) -> bool:
        """Check if it's a valid strategy class."""
        return issubclass(cls, Strategy) and cls is not Strategy and not inspect.isabstract(cls)

    def _register_strategy(self, name: str, cls: type, module_path: str) -> None:
        """Register strategy to the registry."""
        try:
            parameters = self._extract_parameters(cls)
            description = self._extract_description(cls)

            info = StrategyInfo(
                name=name,
                class_name=cls.__name__,
                module_path=module_path,
                strategy_class=cls,
                parameters=parameters,
                description=description,
            )

            self._strategies[name] = info
            logger.debug(f"Registered strategy: {name} with {len(parameters)} parameters")

        except Exception as e:
            logger.warning(f"Failed to register strategy {name}: {e}")

    def _extract_parameters(self, cls: type) -> dict[str, ParameterSpec]:
        """Extract parameters from __init__ signature."""
        sig = inspect.signature(cls.__init__)  # type: ignore[misc]
        params: dict[str, ParameterSpec] = {}

        for name, param in sig.parameters.items():
            if name in ("self", "name", "entry_conditions", "exit_conditions"):
                continue

            spec = self._create_parameter_spec(name, param)
            if spec:
                params[name] = spec

        return params

    def _create_parameter_spec(self, name: str, param: inspect.Parameter) -> ParameterSpec | None:
        """Create ParameterSpec from parameter information."""
        annotation = param.annotation
        default = param.default if param.default != inspect.Parameter.empty else None

        # Skip if default is None
        if default is None:
            return None

        # Infer type
        param_type = self._infer_type(annotation, default)
        if param_type is None:
            return None

        # Create spec by type
        if param_type == "int":
            return ParameterSpec(
                name=name,
                type="int",
                default=default,
                min_value=1,
                max_value=100,
                step=1,
                description=f"Integer parameter: {name}",
            )
        elif param_type == "float":
            return ParameterSpec(
                name=name,
                type="float",
                default=default,
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                description=f"Float parameter: {name}",
            )
        elif param_type == "bool":
            return ParameterSpec(
                name=name,
                type="bool",
                default=default,
                description=f"Boolean parameter: {name}",
            )

        return None

    def _infer_type(self, annotation: Any, default: Any) -> str | None:
        """Infer parameter type from type hint and default value."""
        # Check type hint
        if annotation != inspect.Parameter.empty:
            if annotation is int or annotation == "int":
                return "int"
            elif annotation is float or annotation == "float":
                return "float"
            elif annotation is bool or annotation == "bool":
                return "bool"

        # Infer from default value
        if isinstance(default, bool):
            return "bool"
        elif isinstance(default, int):
            return "int"
        elif isinstance(default, float):
            return "float"

        return None

    def _extract_description(self, cls: type) -> str:
        """Extract description from class docstring."""
        doc = inspect.getdoc(cls)
        if doc:
            # Use only first line
            return doc.split("\n")[0].strip()
        return f"{cls.__name__} strategy"

    def list_strategies(self) -> list[StrategyInfo]:
        """Return list of all registered strategies."""
        return list(self._strategies.values())

    def get_strategy(self, name: str) -> StrategyInfo | None:
        """Get StrategyInfo by strategy name."""
        return self._strategies.get(name)

    def get_strategy_class(self, name: str) -> type | None:
        """Get class by strategy name."""
        info = self._strategies.get(name)
        return info.strategy_class if info else None

    def get_parameters(self, name: str) -> dict[str, ParameterSpec]:
        """Get parameter spec by strategy name."""
        info = self._strategies.get(name)
        return info.parameters if info else {}

    def strategy_exists(self, name: str) -> bool:
        """Check if strategy is registered."""
        return name in self._strategies
