"""Walk-Forward Analysis data models and report types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.backtester.models import BacktestResult


@dataclass
class WFASegment:
    """Walk-Forward Analysis 한 구간 (Training + Test)."""

    period_start: "pd.Timestamp"
    period_end: "pd.Timestamp"
    train_start: "pd.Timestamp"
    train_end: "pd.Timestamp"
    test_start: "pd.Timestamp"
    test_end: "pd.Timestamp"

    in_sample_result: BacktestResult | None = None
    out_of_sample_result: BacktestResult | None = None
    optimal_params: dict[str, Any] | None = None

    @property
    def oos_is_ratio(self) -> float:
        """OOS/IS 수익률 비율 (과적합 지표)."""
        if self.in_sample_result is None or self.out_of_sample_result is None:
            return 0.0

        is_return = self.in_sample_result.total_return
        oos_return = self.out_of_sample_result.total_return

        if is_return <= 0:
            return 0.0

        return oos_return / is_return

    @property
    def overfitting_severity(self) -> str:
        """과적합 정도 판정."""
        ratio = self.oos_is_ratio
        if ratio > 0.3:
            return "정상"
        elif ratio > 0.1:
            return "경고"
        else:
            return "위험"


# Import pd.Timestamp for type hints
import pandas as pd  # noqa: E402


@dataclass
class WFAReport:
    """Walk-Forward Analysis 종합 리포트."""

    segments: list[WFASegment] = field(default_factory=list)

    # 집계 통계
    in_sample_avg_return: float = 0.0
    out_of_sample_avg_return: float = 0.0
    overfitting_ratio: float = 0.0

    in_sample_sharpe: float = 0.0
    out_of_sample_sharpe: float = 0.0

    in_sample_mdd: float = 0.0
    out_of_sample_mdd: float = 0.0

    parameter_stability: dict[str, list[float]] = field(default_factory=dict)

    generated_at: datetime = field(default_factory=datetime.now)


def generate_wfa_html(report: WFAReport) -> str:
    """Generate HTML report for Walk-Forward Analysis."""
    html_parts = []

    # Header
    html_parts.append("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Walk-Forward Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .warning { color: #FF9800; }
            .danger { color: #F44336; }
            .success { color: #4CAF50; }
        </style>
    </head>
    <body>
        <h1>Walk-Forward Analysis Report</h1>
    """)

    # Summary
    ovf_class = (
        "success"
        if report.overfitting_ratio > 0.3
        else "warning"
        if report.overfitting_ratio > 0.1
        else "danger"
    )
    html_parts.append(f"""
    <h2>Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>In-Sample Avg Return</td><td>{report.in_sample_avg_return:.2%}</td></tr>
        <tr><td>Out-of-Sample Avg Return</td><td>{report.out_of_sample_avg_return:.2%}</td></tr>
        <tr><td>Overfitting Ratio (OOS/IS)</td><td class="{ovf_class}">{report.overfitting_ratio:.2%}</td></tr>
        <tr><td>In-Sample Sharpe</td><td>{report.in_sample_sharpe:.2f}</td></tr>
        <tr><td>Out-of-Sample Sharpe</td><td>{report.out_of_sample_sharpe:.2f}</td></tr>
        <tr><td>In-Sample MDD</td><td>{report.in_sample_mdd:.2%}</td></tr>
        <tr><td>Out-of-Sample MDD</td><td>{report.out_of_sample_mdd:.2%}</td></tr>
    </table>
    """)

    # Segment table
    html_parts.append("""
    <h2>Detailed Results by Segment</h2>
    <table>
        <tr><th>Period</th><th>IS Return</th><th>OOS Return</th><th>OOS/IS Ratio</th><th>Overfitting</th></tr>
    """)

    for seg in report.segments:
        if seg.in_sample_result and seg.out_of_sample_result:
            seg_class = (
                "success"
                if seg.oos_is_ratio > 0.3
                else "warning"
                if seg.oos_is_ratio > 0.1
                else "danger"
            )
            html_parts.append(f"""
            <tr>
                <td>{seg.train_start.date()} ~ {seg.test_end.date()}</td>
                <td>{seg.in_sample_result.total_return:.2%}</td>
                <td>{seg.out_of_sample_result.total_return:.2%}</td>
                <td>{seg.oos_is_ratio:.2%}</td>
                <td class="{seg_class}">{seg.overfitting_severity}</td>
            </tr>
            """)

    html_parts.append("</table></body></html>")
    return "".join(html_parts)
