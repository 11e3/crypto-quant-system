"""Tests for HTML styles module."""

from src.backtester.html.html_styles import get_report_css


class TestGetReportCss:
    """Tests for get_report_css function."""

    def test_get_report_css_returns_string(self) -> None:
        """Test that get_report_css returns a string."""
        css = get_report_css()
        assert isinstance(css, str)

    def test_get_report_css_contains_body_style(self) -> None:
        """Test that CSS contains body styling."""
        css = get_report_css()
        assert "body {" in css

    def test_get_report_css_contains_container(self) -> None:
        """Test that CSS contains container class."""
        css = get_report_css()
        assert ".container {" in css or "container" in css

    def test_get_report_css_not_empty(self) -> None:
        """Test that CSS is not empty."""
        css = get_report_css()
        assert len(css) > 100
