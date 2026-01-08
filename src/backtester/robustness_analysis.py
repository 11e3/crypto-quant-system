"""
?�라미터 ?�정??(Robustness) 분석 ?�진.

최적 ?�라미터 주�??�서 ?�과 변?��? 분석?�여,
?�략???�라미터 변?�에 ?�마??민감?��? 검증합?�다.

분석 ?�??
1. Parameter Sweep: �??�라미터�?±30% 범위?�서 변??
2. Sensitivity Analysis: ?�라미터 조합�??�과 ?�트�?
3. Performance Distribution: ?�과 값의 분포 (?�탄?��?? 뾰족?��??)

과적???�호:
- 최적값에??조금�?벗어?�도 ?�과가 급격???�락 ??과적??
- ?��? 범위?�서 ?�정?�인 ?�과 ??건강???�략
"""

from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtester.engine import BacktestConfig, BacktestResult
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RobustnessResult:
    """?�일 ?�라미터 조합???�과."""

    params: dict[str, Any]
    total_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    trade_count: int

    def to_dict(self) -> dict[str, Any]:
        """?�셔?�리�?변??"""
        return {
            **self.params,
            "total_return": self.total_return,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "trade_count": self.trade_count,
        }


@dataclass
class RobustnessReport:
    """Robustness Analysis 종합 리포??"""

    optimal_params: dict[str, Any]
    results: list[RobustnessResult]

    # ?�계
    mean_return: float = 0.0
    std_return: float = 0.0
    min_return: float = 0.0
    max_return: float = 0.0

    # 최적�?주�? ?�정??(±20% 범위)
    neighbor_success_rate: float = 0.0  # 0.0-1.0

    # ?�라미터 민감??(�??�라미터�?
    sensitivity_scores: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.sensitivity_scores is None:
            self.sensitivity_scores = {}


class RobustnessAnalyzer:
    """
    ?�라미터 ?�정??분석�?

    ?�용 ??
    ```python
    analyzer = RobustnessAnalyzer(
        data=ohlcv_df,
        strategy_factory=lambda p: VanillaVBO(**p)
    )

    report = analyzer.analyze(
        optimal_params={'sma_period': 4, 'noise_period': 8},
        parameter_ranges={
            'sma_period': [2, 3, 4, 5, 6],
            'noise_period': [6, 7, 8, 9, 10]
        }
    )
    ```
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy_factory: Callable[[dict[str, Any]], Strategy],
        backtest_config: BacktestConfig | None = None,
    ):
        """
        Initialize Robustness Analyzer.

        Args:
            data: OHLCV ?�이??
            strategy_factory: ?�라미터�?받아 Strategy ?�성
            backtest_config: 백테?�트 ?�정
        """
        self.data = data
        self.strategy_factory = strategy_factory
        self.backtest_config = backtest_config or BacktestConfig()
        self.initial_capital = self.backtest_config.initial_capital

    def _simple_backtest(self, strategy: Strategy) -> BacktestResult:
        """
        간단??벡터??백테?�트 (BacktestEngine ?�??직접 구현).
        """
        from src.backtester.engine import BacktestResult

        try:
            df = self.data.copy()

            # 지??계산 �??�호 ?�성
            df = strategy.calculate_indicators(df)
            df = strategy.generate_signals(df)

            # ?�호 ?�인
            if "signal" not in df.columns:
                result = BacktestResult()
                result.total_return = 0.0
                result.sharpe_ratio = 0.0
                result.mdd = 0.0
                result.total_trades = 0
                result.winning_trades = 0
                result.win_rate = 0.0
                return result

            # ?��???추적
            position = 0
            entry_price = 0
            trades = []
            equity = [self.initial_capital]

            for _idx, row in df.iterrows():
                signal = row.get("signal", 0)
                close = row.get("close", 0)

                if signal != 0 and position == 0:
                    entry_price = close
                    position = signal
                elif signal * position < 0:
                    if position != 0:
                        pnl = (close - entry_price) * position / entry_price
                        trades.append(pnl)
                        equity.append(equity[-1] * (1 + pnl))
                        position = signal
                        entry_price = close if signal != 0 else 0
                    else:
                        position = 0

                if position == 0 and len(equity) > 1:
                    equity.append(equity[-1])

            # 보유 중인 ?��????�리
            if position != 0 and len(df) > 0:
                last_close = df.iloc[-1].get("close", entry_price)
                pnl = (last_close - entry_price) * position / entry_price
                trades.append(pnl)
                equity.append(equity[-1] * (1 + pnl))

            # 메트�?계산
            total_return = (
                (equity[-1] - self.initial_capital) / self.initial_capital if equity else 0.0
            )

            # Sharpe 비율
            if len(equity) > 1:
                returns = np.diff(equity) / equity[:-1]
                sharpe = (
                    np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
                    if np.std(returns) > 0
                    else 0.0
                )
            else:
                sharpe = 0.0

            # Max Drawdown
            if len(equity) > 1:
                cummax = np.maximum.accumulate(equity)
                dd = (np.array(equity) - cummax) / cummax
                max_drawdown = np.min(dd) if len(dd) > 0 else 0.0
            else:
                max_drawdown = 0.0

            # ?�률
            if trades:
                winning_trades = sum(1 for t in trades if t > 0)
                win_rate = winning_trades / len(trades)
            else:
                win_rate = 0.0
                winning_trades = 0

            result = BacktestResult()
            result.total_return = total_return
            result.sharpe_ratio = sharpe
            result.mdd = max_drawdown
            result.total_trades = len(trades)
            result.winning_trades = winning_trades
            result.win_rate = win_rate
            result.equity_curve = np.array(equity)

            return result

        except Exception as e:
            logger.error(f"Simple backtest error: {e}")
            result = BacktestResult()
            result.total_return = 0.0
            result.sharpe_ratio = 0.0
            result.mdd = 0.0
            result.total_trades = 0
            result.winning_trades = 0
            result.win_rate = 0.0
            return result

    def analyze(
        self,
        optimal_params: dict[str, Any],
        parameter_ranges: dict[str, list[Any]],
        verbose: bool = True,
    ) -> RobustnessReport:
        """
        ?�라미터 ?�정??분석 ?�행.

        Args:
            optimal_params: 최적?�로 간주?�는 ?�라미터
            parameter_ranges: ?�스?�할 �??�라미터??�?리스??
            verbose: 진행 ?�황 로깅

        Returns:
            RobustnessReport: 분석 결과
        """
        results = []

        # ?�라미터 조합 ?�성
        param_keys = list(parameter_ranges.keys())
        param_values = [parameter_ranges[key] for key in param_keys]
        total_combinations = np.prod([len(v) for v in param_values])

        if verbose:
            logger.info(f"Testing {total_combinations} parameter combinations for robustness")

        # �?조합 ?�스??
        for idx, param_combo in enumerate(product(*param_values)):
            params = dict(zip(param_keys, param_combo, strict=False))

            try:
                strategy = self.strategy_factory(params)
                result = self._simple_backtest(strategy)

                robustness_result = RobustnessResult(
                    params=params,
                    total_return=result.total_return,
                    sharpe=result.sharpe_ratio,
                    max_drawdown=result.mdd,
                    win_rate=result.win_rate if hasattr(result, "win_rate") else 0.0,
                    trade_count=result.total_trades if hasattr(result, "total_trades") else 0,
                )
                results.append(robustness_result)

                if verbose and (idx + 1) % max(1, total_combinations // 10) == 0:  # type: ignore[operator]
                    logger.info(
                        f"  [{idx + 1}/{int(total_combinations)}] "
                        f"Params: {params}, Return: {result.total_return:.2%}"
                    )

            except Exception as e:
                logger.warning(f"Parameter combination {params} failed: {e}")
                continue

        # 결과 집계
        report = self._aggregate_results(optimal_params, results)

        if verbose:
            logger.info(
                f"Robustness analysis complete: "
                f"Mean return {report.mean_return:.2%} ± {report.std_return:.2%}, "
                f"Neighbor success rate: {report.neighbor_success_rate:.1%}"
            )

        return report

    def _aggregate_results(
        self, optimal_params: dict[str, Any], results: list[RobustnessResult]
    ) -> RobustnessReport:
        """결과 집계 �??�계 계산."""
        report = RobustnessReport(optimal_params=optimal_params, results=results)

        if not results:
            logger.error("No valid results from robustness analysis")
            return report

        # ?�익�??�계
        returns = [r.total_return for r in results]
        report.mean_return = float(np.mean(returns))
        report.std_return = float(np.std(returns))
        report.min_return = float(np.min(returns))
        report.max_return = float(np.max(returns))

        # 최적�?주�? ?�정??(±20% 범위 ??
        neighbor_results = self._find_neighbors(optimal_params, results, tolerance=0.20)

        if neighbor_results:
            [r.total_return for r in neighbor_results]
            optimal_return = max([r.total_return for r in results if r.params == optimal_params])

            # Success rate: 최적값의 80% ?�상???�웃??비율
            threshold = optimal_return * 0.80
            successful_neighbors = sum(1 for r in neighbor_results if r.total_return >= threshold)
            report.neighbor_success_rate = successful_neighbors / len(neighbor_results)

        # ?�라미터�?민감??
        report.sensitivity_scores = self._calculate_sensitivity(results)

        return report

    def _find_neighbors(
        self,
        optimal_params: dict[str, Any],
        results: list[RobustnessResult],
        tolerance: float = 0.20,
    ) -> list[RobustnessResult]:
        """
        최적�?주�????�라미터 조합 찾기 (±tolerance%).

        ?? optimal_param = 4, tolerance = 0.20
        ??3.2~4.8 범위???�라미터�?가�?결과??
        """
        neighbors = []

        for result in results:
            is_neighbor = True

            for param_name, optimal_value in optimal_params.items():
                if param_name not in result.params:
                    continue

                actual_value = result.params[param_name]

                # ?�자 ?�라미터�??�단
                if not isinstance(actual_value, (int, float)):
                    continue

                # 변?�율 계산
                if optimal_value == 0:
                    is_neighbor = actual_value == 0
                else:
                    change_pct = abs(actual_value - optimal_value) / abs(optimal_value)

                    if change_pct > tolerance:
                        is_neighbor = False
                        break

            if is_neighbor:
                neighbors.append(result)

        return neighbors

    def _calculate_sensitivity(self, results: list[RobustnessResult]) -> dict[str, float]:
        """
        ?�라미터�?민감??계산 (0.0~1.0).

        1.0??가까울?�록 ?�당 ?�라미터??민감??(�?변?????�과 변????
        0.0??가까울?�록 ??민감??(�?변?????�과 변???�음)
        """
        if not results:
            return {}

        sensitivity = {}

        # �?번째 결과?�서 ?�라미터 ?�름 추출
        param_names = list(results[0].params.keys())

        for param_name in param_names:
            # ???�라미터??모든 값과 ?�???�과
            param_values = []
            returns = []

            for result in results:
                if param_name in result.params:
                    value = result.params[param_name]

                    # ?�자�?분석
                    if isinstance(value, (int, float)):
                        param_values.append(value)
                        returns.append(result.total_return)

            if len(set(param_values)) < 2:
                # ?�라미터 값이 ?�양?��? ?�음
                sensitivity[param_name] = 0.0
                continue

            # ?��?계수 계산 (?�라미터 변?��? ?�과 변?�의 ?��???
            correlation = abs(np.corrcoef(param_values, returns)[0, 1])

            if np.isnan(correlation):
                sensitivity[param_name] = 0.0
            else:
                sensitivity[param_name] = float(correlation)

        return sensitivity

    def export_to_csv(self, report: RobustnessReport, output_path: str | Path) -> None:
        """결과�?CSV�??�??"""
        records = [r.to_dict() for r in report.results]
        df = pd.DataFrame(records)

        df.to_csv(output_path, index=False)
        logger.info(f"Robustness results saved to {output_path}")

    def export_report_html(self, report: RobustnessReport, output_path: str | Path) -> None:
        """HTML 리포???�성."""
        html = self._generate_html(report)

        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"Robustness report saved to {output_path}")

    def _generate_html(self, report: RobustnessReport) -> str:
        """HTML 리포???�성."""
        html_parts = []

        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Robustness Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #2196F3; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .success { color: #4CAF50; font-weight: bold; }
                .warning { color: #FF9800; font-weight: bold; }
                .danger { color: #F44336; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Robustness Analysis Report</h1>
        """)

        # ?�약
        html_parts.append(f"""
        <h2>Summary Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Assessment</th>
            </tr>
            <tr>
                <td>Mean Return</td>
                <td>{report.mean_return:.2%}</td>
                <td class="{"success" if report.mean_return > 0 else "danger"}">
                    {"Profitable" if report.mean_return > 0 else "Loss"}
                </td>
            </tr>
            <tr>
                <td>Std Dev Return</td>
                <td>{report.std_return:.2%}</td>
                <td class="{"success" if report.std_return < 0.30 else "warning"}">
                    {"Stable" if report.std_return < 0.30 else "Volatile"}
                </td>
            </tr>
            <tr>
                <td>Min Return</td>
                <td>{report.min_return:.2%}</td>
                <td></td>
            </tr>
            <tr>
                <td>Max Return</td>
                <td>{report.max_return:.2%}</td>
                <td></td>
            </tr>
            <tr>
                <td>Neighbor Success Rate</td>
                <td>{report.neighbor_success_rate:.1%}</td>
                <td class="{"success" if report.neighbor_success_rate > 0.70 else "warning" if report.neighbor_success_rate > 0.50 else "danger"}">
                    {"Robust" if report.neighbor_success_rate > 0.70 else "Fragile"}
                </td>
            </tr>
        </table>
        """)

        # ?�라미터 민감??
        html_parts.append("""
        <h2>Parameter Sensitivity (0.0 = Insensitive, 1.0 = Highly Sensitive)</h2>
        <table>
            <tr>
                <th>Parameter</th>
                <th>Sensitivity</th>
                <th>Interpretation</th>
            </tr>
        """)

        if report.sensitivity_scores is None:
            html_parts.append("<tr><td colspan='3'>No sensitivity data available</td></tr>")
        else:
            for param_name in sorted(report.sensitivity_scores.keys()):
                score = report.sensitivity_scores[param_name]
                interpretation = (
                    "High (Risky)" if score > 0.7 else "Medium" if score > 0.4 else "Low (Stable)"
                )

                html_parts.append(f"""
            <tr>
                <td>{param_name}</td>
                <td>{score:.3f}</td>
                <td>{interpretation}</td>
            </tr>
        """)

        html_parts.append("""
        </table>
        </body>
        </html>
        """)

        return "".join(html_parts)


if __name__ == "__main__":
    print("RobustnessAnalyzer module loaded successfully")
