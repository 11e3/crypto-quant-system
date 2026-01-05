"""
Main CLI entry point.

Provides command-line interface for the trading system.
"""

import sys
from pathlib import Path

import click

from src.cli.commands.backtest import backtest
from src.cli.commands.collect import collect
from src.cli.commands.run_bot import run_bot

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@click.group()
@click.version_option(version="0.1.0", prog_name="upbit-quant")
def cli() -> None:
    """
    Upbit Quant System - Automated trading system using volatility breakout strategy.

    Provides commands for data collection, backtesting, and live trading.
    """
    pass


# Register commands
cli.add_command(collect)
cli.add_command(backtest)
cli.add_command(run_bot)


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
