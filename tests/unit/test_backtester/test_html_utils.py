"""
Tests for HTML Report Utilities.
"""

import pandas as pd

from src.backtester.html.html_utils import extract_config_params, extract_strategy_params
from src.backtester.models import BacktestResult


class TestExtractStrategyParams:
    """Tests for extract_strategy_params function."""

    def test_none_strategy_returns_empty(self) -> None:
        """Test that None strategy returns empty string."""
        result = extract_strategy_params(None)
        assert result == ""

    def test_strategy_with_no_attributes(self) -> None:
        """Test strategy object with no matching attributes."""

        class DummyStrategy:
            pass

        result = extract_strategy_params(DummyStrategy())
        assert result == ""

    def test_strategy_with_tickers(self) -> None:
        """Test extraction with tickers."""

        class DummyStrategy:
            pass

        result = extract_strategy_params(DummyStrategy(), tickers=["BTC", "ETH"])
        assert "Tickers" in result
        assert "BTC, ETH" in result

    def test_vbo_strategy_attributes(self) -> None:
        """Test VBO strategy parameter extraction."""

        class VBOStrategy:
            sma_period = 20
            trend_sma_period = 50
            short_noise_period = 2
            long_noise_period = 20
            exclude_current = True

        strategy = VBOStrategy()
        result = extract_strategy_params(strategy)

        assert "SMA Period" in result
        assert "20" in result
        assert "Trend SMA Period" in result
        assert "50" in result

    def test_momentum_strategy_attributes(self) -> None:
        """Test Momentum strategy parameter extraction."""

        class MomentumStrategy:
            lookback_period = 10
            momentum_threshold = 0.05

        strategy = MomentumStrategy()
        result = extract_strategy_params(strategy)

        assert "Lookback Period" in result
        assert "10" in result
        assert "Momentum Threshold" in result

    def test_mean_reversion_strategy_attributes(self) -> None:
        """Test Mean Reversion strategy parameter extraction."""

        class MeanReversionStrategy:
            zscore_threshold = 2.0
            lookback_window = 20

        strategy = MeanReversionStrategy()
        result = extract_strategy_params(strategy)

        assert "Z-Score Threshold" in result
        assert "Lookback Window" in result


class TestExtractConfigParams:
    """Tests for extract_config_params function."""

    def test_none_config_returns_empty(self) -> None:
        """Test that None config returns empty string."""
        result = extract_config_params(None)
        assert result == ""

    def test_config_without_attributes(self) -> None:
        """Test config object with no matching attributes."""

        class DummyConfig:
            pass

        result = extract_config_params(DummyConfig())
        assert result == ""

    def test_config_with_capital_info(self) -> None:
        """Test config with initial capital."""

        class DummyConfig:
            initial_capital = 1000000

        result = extract_config_params(DummyConfig())
        assert "Initial Capital" in result
        assert "1,000,000" in result

    def test_config_with_fees(self) -> None:
        """Test config with fee information."""

        class DummyConfig:
            fee_rate = 0.001
            slippage_rate = 0.0005

        result = extract_config_params(DummyConfig())
        assert "Fee Rate" in result
        assert "0.100%" in result
        assert "Slippage Rate" in result

    def test_config_with_position_sizing(self) -> None:
        """Test config with position sizing."""

        class DummyConfig:
            max_slots = 5
            position_sizing = "equal"

        result = extract_config_params(DummyConfig())
        assert "Max Positions" in result
        assert "5" in result
        assert "Position Sizing" in result
        assert "equal" in result

    def test_config_with_dates(self) -> None:
        """Test config with date range from result."""

        class DummyConfig:
            initial_capital = 1000000

        result_obj = BacktestResult()
        result_obj.dates = pd.date_range("2023-01-01", periods=100, freq="D").tolist()

        result = extract_config_params(DummyConfig(), result=result_obj)
        assert "Start Date" in result
        assert "2023-01-01" in result
        assert "End Date" in result

    def test_config_with_tickers(self) -> None:
        """Test config with tickers."""

        class DummyConfig:
            initial_capital = 1000000

        result = extract_config_params(DummyConfig(), tickers=["BTC", "ETH", "SOL"])
        assert "Universe" in result
        assert "3 tickers" in result

    def test_stop_loss_and_take_profit(self) -> None:
        """Test config with stop loss and take profit."""

        class DummyConfig:
            stop_loss_pct = 0.05
            take_profit_pct = 0.10
            trailing_stop_pct = 0.02

        result = extract_config_params(DummyConfig())
        assert "Stop Loss" in result
        assert "5.0%" in result
        assert "Take Profit" in result
        assert "10.0%" in result
        assert "Trailing Stop" in result
