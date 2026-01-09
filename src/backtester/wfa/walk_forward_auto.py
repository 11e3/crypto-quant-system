"""
Walk-Forward Analysis (WFA) engine.

Validates overfitting through rolling training/testing windows.
OOS/IS ratio > 0.3: Normal | 0.1-0.3: Warning | < 0.1: Danger
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtester.models import BacktestConfig
from src.backtester.wfa.wfa_models import WFAReport, WFASegment, generate_wfa_html
from src.backtester.wfa.wfa_segment import process_wfa_segment
from src.backtester.wfa.wfa_utils import aggregate_wfa_results
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WalkForwardAnalyzer:
    """
    Walk-Forward Analysis 자동 실행기.

    사용 예:
    ```python
    analyzer = WalkForwardAnalyzer(
        data=ohlcv_df,
        train_period=252 * 2,  # 2년
        test_period=252,        # 1년
        step=63                 # 3개월 롤링
    )

    report = analyzer.run(
        strategy_factory=lambda params: VanillaVBO(**params),
        param_ranges={
            'sma_period': [3, 4, 5],
            'noise_period': [7, 8, 9]
        }
    )
    ```
    """

    def __init__(
        self,
        data: pd.DataFrame,
        train_period: int = 252 * 2,
        test_period: int = 252,
        step: int = 63,
    ):
        """
        Initialize Walk-Forward Analysis.

        Args:
            data: OHLCV 데이터 (index는 datetime, columns: open, high, low, close, volume)
            train_period: Training 기간 (거래일 단위)
            test_period: Test 기간 (거래일 단위)
            step: Rolling window step (거래일 단위)
        """
        self.data = data
        self.train_period = train_period
        self.test_period = test_period
        self.step = step

        self.segments: list[WFASegment] = []

        logger.info(
            f"WalkForwardAnalyzer initialized: "
            f"train={train_period}d, test={test_period}d, step={step}d"
        )

    def run(
        self,
        strategy_factory: Callable[[dict[str, Any]], Strategy],
        param_ranges: dict[str, list[Any]],
        backtest_config: BacktestConfig | None = None,
        verbose: bool = True,
    ) -> WFAReport:
        """
        Walk-Forward Analysis 실행.

        Args:
            strategy_factory: 파라미터를 받아 Strategy를 생성하는 함수
            param_ranges: 테스트할 파라미터 범위
            backtest_config: 백테스트 설정
            verbose: 진행 상황 로깅

        Returns:
            WFAReport: 분석 결과
        """
        if backtest_config is None:
            backtest_config = BacktestConfig()

        self.initial_capital = backtest_config.initial_capital

        # 1. 모든 WFA 구간 생성
        segments = self._generate_segments()

        if verbose:
            logger.info(f"Generated {len(segments)} WFA segments")

        # 2. 각 구간 처리
        for i, segment in enumerate(segments):
            if verbose:
                logger.info(
                    f"[{i + 1}/{len(segments)}] Processing segment: "
                    f"{segment.train_start.date()} ~ {segment.test_end.date()}"
                )

            processed = process_wfa_segment(
                segment=segment,
                data=self.data,
                strategy_factory=strategy_factory,
                param_ranges=param_ranges,
                initial_capital=self.initial_capital,
                train_period=self.train_period,
                verbose=verbose,
            )

            if processed is not None:
                self.segments.append(processed)

        # 3. 결과 집계
        report = aggregate_wfa_results(self.segments)

        if verbose:
            logger.info(
                f"WFA completed: "
                f"IS avg {report.in_sample_avg_return:.2%}, "
                f"OOS avg {report.out_of_sample_avg_return:.2%}, "
                f"Overfitting ratio: {report.overfitting_ratio:.2%}"
            )

        return report

    def _generate_segments(self) -> list[WFASegment]:
        """모든 WFA 구간 생성."""
        segments = []

        min_required_length = self.train_period + self.test_period

        if len(self.data) < min_required_length:
            raise ValueError(f"Data length ({len(self.data)}) < required ({min_required_length})")

        # Rolling window로 구간 생성
        for i in range(0, len(self.data) - min_required_length + 1, self.step):
            train_start_idx = i
            train_end_idx = i + self.train_period
            test_start_idx = train_end_idx
            test_end_idx = test_start_idx + self.test_period

            if test_end_idx > len(self.data):
                break

            segment = WFASegment(
                period_start=self.data.index[i],
                period_end=self.data.index[test_end_idx - 1],
                train_start=self.data.index[train_start_idx],
                train_end=self.data.index[train_end_idx - 1],
                test_start=self.data.index[test_start_idx],
                test_end=self.data.index[test_end_idx - 1],
            )
            segments.append(segment)

        return segments

    def export_report_html(self, report: WFAReport, output_path: str | Path) -> None:
        """WFA 리포트를 HTML로 저장."""
        html = generate_wfa_html(report)
        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"WFA report saved to {output_path}")


if __name__ == "__main__":
    # 테스트 코드
    print("WalkForwardAnalyzer module loaded successfully")
