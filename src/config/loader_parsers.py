"""Helper functions for configuration value parsing."""

from typing import Any


def get_yaml_value(yaml_config: dict[str, Any], key: str) -> Any:
    """
    Get value from YAML config using dot notation.

    Args:
        yaml_config: YAML configuration dictionary
        key: Dot-notation key (e.g., "trading.fee_rate")

    Returns:
        Value from YAML config or None
    """
    parts = key.split(".")
    current: Any = yaml_config
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def parse_env_value(value: str) -> Any:
    """
    Parse environment variable string value to appropriate type.

    Args:
        value: String value from environment

    Returns:
        Parsed value (bool, int, float, list, or str)
    """
    lower_value = value.lower()
    if lower_value == "true":
        return True
    if lower_value == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    if "," in value:
        return [item.strip() for item in value.split(",")]

    return value
