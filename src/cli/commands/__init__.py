"""
CLI commands package.
"""

from src.cli.commands.backtest import backtest
from src.cli.commands.collect import collect
from src.cli.commands.run_bot import run_bot

__all__ = ["collect", "backtest", "run_bot"]
