"""Unit tests for monitoring threshold checks."""

from src.monitoring.checks import evaluate_thresholds


class TestThresholdEvaluation:
    """Test threshold evaluation logic."""

    def test_min_threshold_pass(self):
        """Test that metrics meeting min threshold pass."""
        metrics = {"cagr": 0.10, "sharpe": 1.5, "win_rate": 0.55}
        thresholds = {"min_cagr": 0.05, "min_sharpe": 1.0, "min_win_rate": 0.50}

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 0

    def test_min_threshold_fail(self):
        """Test that metrics below min threshold fail."""
        metrics = {"cagr": 0.03, "sharpe": 0.8, "win_rate": 0.45}
        thresholds = {"min_cagr": 0.05, "min_sharpe": 1.0, "min_win_rate": 0.50}

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 3
        # Check all three metrics failed
        issue_keys = [iss[0] for iss in issues]
        assert "min_cagr" in issue_keys
        assert "min_sharpe" in issue_keys
        assert "min_win_rate" in issue_keys

    def test_max_threshold_pass(self):
        """Test that metrics meeting max threshold pass."""
        # For drawdown: -0.10 is BETTER than -0.15 (less drawdown)
        # For whipsaw: 0.15 is BETTER than 0.20 (lower rate)
        metrics = {"max_drawdown": -0.10, "whipsaw_rate": 0.15}
        thresholds = {"max_max_drawdown": -0.15, "max_whipsaw_rate": 0.20}

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 0

    def test_max_threshold_fail(self):
        """Test that metrics exceeding max threshold fail."""
        # For drawdown: -0.30 is WORSE than -0.25 (more drawdown)
        # For whipsaw: 0.25 is WORSE than 0.20 (higher rate)
        metrics = {"max_drawdown": -0.30, "whipsaw_rate": 0.25}
        thresholds = {"max_max_drawdown": -0.15, "max_whipsaw_rate": 0.20}

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 2
        issue_keys = [iss[0] for iss in issues]
        assert "max_max_drawdown" in issue_keys
        assert "max_whipsaw_rate" in issue_keys

    def test_missing_metrics_ignored(self):
        """Test that missing metrics are silently ignored."""
        metrics = {"cagr": 0.10}
        thresholds = {"min_cagr": 0.05, "min_sharpe": 1.0, "min_win_rate": 0.50}

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 0  # Only cagr checked, others ignored

    def test_mixed_thresholds(self):
        """Test mixed min/max thresholds."""
        metrics = {
            "cagr": 0.08,
            "max_drawdown": -0.28,
            "sharpe": 1.2,
        }
        thresholds = {
            "min_cagr": 0.05,
            "max_max_drawdown": -0.15,  # -0.28 is worse than -0.15
            "min_sharpe": 1.0,
        }

        issues = evaluate_thresholds(metrics, thresholds)

        assert len(issues) == 1
        assert issues[0][0] == "max_max_drawdown"
