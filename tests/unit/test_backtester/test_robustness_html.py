"""
Tests for Robustness Analysis HTML report generation.
"""

from unittest.mock import MagicMock

import pytest

from src.backtester.analysis.robustness_html import generate_robustness_html


@pytest.fixture
def mock_robustness_report() -> MagicMock:
    """Create mock RobustnessReport for testing."""
    report = MagicMock()
    report.mean_return = 0.15
    report.std_return = 0.20
    report.min_return = -0.05
    report.max_return = 0.35
    report.neighbor_success_rate = 0.75
    report.sensitivity_scores = {
        "sma_period": 0.3,
        "noise_threshold": 0.6,
        "volatility_target": 0.8,
    }
    return report


@pytest.fixture
def mock_negative_report() -> MagicMock:
    """Create mock RobustnessReport with negative returns."""
    report = MagicMock()
    report.mean_return = -0.05
    report.std_return = 0.40
    report.min_return = -0.25
    report.max_return = 0.10
    report.neighbor_success_rate = 0.40
    report.sensitivity_scores = {"param1": 0.5}
    return report


@pytest.fixture
def mock_report_no_sensitivity() -> MagicMock:
    """Create mock RobustnessReport without sensitivity scores."""
    report = MagicMock()
    report.mean_return = 0.10
    report.std_return = 0.15
    report.min_return = 0.0
    report.max_return = 0.20
    report.neighbor_success_rate = 0.60
    report.sensitivity_scores = None
    return report


class TestGenerateRobustnessHtml:
    """Tests for generate_robustness_html function."""

    def test_basic_html_structure(self, mock_robustness_report: MagicMock) -> None:
        """Test that HTML has correct basic structure."""
        html = generate_robustness_html(mock_robustness_report)

        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "<title>Robustness Analysis Report</title>" in html

    def test_summary_statistics_section(self, mock_robustness_report: MagicMock) -> None:
        """Test that summary statistics are included."""
        html = generate_robustness_html(mock_robustness_report)

        assert "Summary Statistics" in html
        assert "Mean Return" in html
        assert "Std Dev Return" in html
        assert "Min Return" in html
        assert "Max Return" in html
        assert "Neighbor Success Rate" in html

    def test_positive_return_assessment(self, mock_robustness_report: MagicMock) -> None:
        """Test assessment for positive returns."""
        html = generate_robustness_html(mock_robustness_report)

        assert "Profitable" in html
        assert 'class="success"' in html

    def test_negative_return_assessment(self, mock_negative_report: MagicMock) -> None:
        """Test assessment for negative returns."""
        html = generate_robustness_html(mock_negative_report)

        assert "Loss" in html
        assert 'class="danger"' in html

    def test_stable_volatility_assessment(self, mock_robustness_report: MagicMock) -> None:
        """Test assessment for stable (low) volatility."""
        html = generate_robustness_html(mock_robustness_report)

        assert "Stable" in html

    def test_volatile_assessment(self, mock_negative_report: MagicMock) -> None:
        """Test assessment for high volatility."""
        html = generate_robustness_html(mock_negative_report)

        assert "Volatile" in html

    def test_robust_assessment(self, mock_robustness_report: MagicMock) -> None:
        """Test assessment for robust strategy (high success rate)."""
        html = generate_robustness_html(mock_robustness_report)

        assert "Robust" in html

    def test_fragile_assessment(self, mock_negative_report: MagicMock) -> None:
        """Test assessment for fragile strategy (low success rate)."""
        html = generate_robustness_html(mock_negative_report)

        assert "Fragile" in html

    def test_moderate_assessment(self, mock_report_no_sensitivity: MagicMock) -> None:
        """Test assessment for moderate strategy (medium success rate)."""
        html = generate_robustness_html(mock_report_no_sensitivity)

        assert "Moderate" in html

    def test_sensitivity_section(self, mock_robustness_report: MagicMock) -> None:
        """Test that parameter sensitivity section is included."""
        html = generate_robustness_html(mock_robustness_report)

        assert "Parameter Sensitivity" in html
        assert "sma_period" in html
        assert "noise_threshold" in html
        assert "volatility_target" in html

    def test_sensitivity_interpretation_low(self, mock_robustness_report: MagicMock) -> None:
        """Test low sensitivity interpretation."""
        html = generate_robustness_html(mock_robustness_report)

        # sma_period has score 0.3 which is low
        assert "Low (Stable)" in html

    def test_sensitivity_interpretation_medium(self, mock_robustness_report: MagicMock) -> None:
        """Test medium sensitivity interpretation."""
        html = generate_robustness_html(mock_robustness_report)

        # noise_threshold has score 0.6 which is medium
        assert "Medium" in html

    def test_sensitivity_interpretation_high(self, mock_robustness_report: MagicMock) -> None:
        """Test high sensitivity interpretation."""
        html = generate_robustness_html(mock_robustness_report)

        # volatility_target has score 0.8 which is high
        assert "High (Risky)" in html

    def test_no_sensitivity_data(self, mock_report_no_sensitivity: MagicMock) -> None:
        """Test handling when no sensitivity data is available."""
        html = generate_robustness_html(mock_report_no_sensitivity)

        assert "No sensitivity data available" in html

    def test_percentage_formatting(self, mock_robustness_report: MagicMock) -> None:
        """Test that percentages are properly formatted."""
        html = generate_robustness_html(mock_robustness_report)

        # 15% mean return
        assert "15.00%" in html
        # 75% success rate
        assert "75.0%" in html

    def test_css_styles_included(self, mock_robustness_report: MagicMock) -> None:
        """Test that CSS styles are included."""
        html = generate_robustness_html(mock_robustness_report)

        assert "<style>" in html
        assert ".success" in html
        assert ".warning" in html
        assert ".danger" in html
