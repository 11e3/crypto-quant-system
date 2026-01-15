"""Web application configuration.

Pydantic Settings-based web application configuration.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["WebAppSettings", "get_web_settings"]


class WebAppSettings(BaseSettings):
    """Web application settings.

    Load settings from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="WEB_",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields
    )

    # Streamlit server settings
    server_port: int = Field(default=8501, description="Streamlit server port")
    server_address: str = Field(default="localhost", description="Server address")
    server_headless: bool = Field(default=False, description="Run in headless mode")

    # Cache settings
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour)")
    enable_caching: bool = Field(default=True, description="Enable caching")

    # UI settings
    default_theme: str = Field(default="light", description="Default UI theme (light/dark)")
    show_debug_info: bool = Field(default=False, description="Show debug information")

    # Backtest settings
    max_parallel_workers: int = Field(
        default=4, description="Maximum parallel workers for optimization"
    )
    default_initial_capital: float = Field(
        default=10_000_000.0, description="Default initial capital (KRW)"
    )
    default_fee_rate: float = Field(default=0.0005, description="Default fee rate (0.05%)")
    default_slippage_rate: float = Field(
        default=0.0005, description="Default slippage rate (0.05%)"
    )


# Singleton instance
_settings: WebAppSettings | None = None


def get_web_settings() -> WebAppSettings:
    """Return web settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = WebAppSettings()
    return _settings
