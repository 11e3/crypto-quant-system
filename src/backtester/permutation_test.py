"""
Permutation Test: 과적합 통계적 검증.

원리:
1. 원본 데이터로 전략을 백테스트 → 성과 S_original
2. 데이터를 무작위로 섞어서 1000번 백테스트 → 성과들 S_shuffled
3. S_original이 우연에 비해 통계적으로 유의한가?

가설 검정:
- H0 (귀무가설): "성과는 우연" (전략이 작동하지 않음)
- H1 (대립가설): "성과는 의미 있음" (전략이 실제로 작동함)

판단:
- Z-score > 2.0 (5% 유의수준) → H1 채택: 유의한 성과
- Z-score < 1.0 → H0 채택: 우연일 가능성 높음 (과적합 의심)
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from src.backtester.engine import BacktestConfig, BacktestResult
from src.strategies.base import Strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PermutationTestResult:
    """Permutation Test 결과."""

    original_return: float
    original_sharpe: float
    original_win_rate: float

    shuffled_returns: list[float]
    shuffled_sharpes: list[float]
    shuffled_win_rates: list[float]

    mean_shuffled_return: float = 0.0
    std_shuffled_return: float = 0.0

    z_score: float = 0.0
    p_value: float = 0.0

    is_statistically_significant: bool = False
    confidence_level: str = ""  # "5%", "1%", "not significant"

    interpretation: str = ""


class PermutationTester:
    """
    Permutation Test를 통한 과적합 검증.

    사용 예:
    ```python
    tester = PermutationTester(
        data=ohlcv_df,
        strategy_factory=lambda: VanillaVBO()
    )

    result = tester.run(
        num_shuffles=1000,
        shuffle_columns=['close', 'volume']  # 섞을 컬럼
    )

    print(f"Z-score: {result.z_score:.2f}")
    print(f"P-value: {result.p_value:.4f}")
    print(result.interpretation)
    ```
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy_factory: Callable[[], Strategy],
        backtest_config: BacktestConfig | None = None,
    ):
        """
        Initialize Permutation Tester.

        Args:
            data: OHLCV 데이터
            strategy_factory: Strategy 객체 생성 함수 (파라미터 없음)
            backtest_config: 백테스트 설정
        """
        self.data = data
        self.strategy_factory = strategy_factory
        self.backtest_config = backtest_config or BacktestConfig()
        self.initial_capital = self.backtest_config.initial_capital

    def _simple_backtest(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        """
        간단한 벡터화 백테스트 (BacktestEngine 대신 직접 구현).

        Args:
            data: 백테스트할 데이터
            strategy: 트레이딩 전략
        """
        from src.backtester.engine import BacktestResult

        try:
            df = data.copy()

            # 지표 계산 및 신호 생성
            df = strategy.calculate_indicators(df)
            df = strategy.generate_signals(df)

            # 신호 확인
            if "signal" not in df.columns:
                result = BacktestResult()
                result.total_return = 0.0
                result.sharpe_ratio = 0.0
                result.mdd = 0.0
                result.total_trades = 0
                result.winning_trades = 0
                result.win_rate = 0.0
                return result

            # 포지션 추적
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

            # 보유 중인 포지션 정리
            if position != 0 and len(df) > 0:
                last_close = df.iloc[-1].get("close", entry_price)
                pnl = (last_close - entry_price) * position / entry_price
                trades.append(pnl)
                equity.append(equity[-1] * (1 + pnl))

            # 메트릭 계산
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

            # 승률
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

    def run(
        self,
        num_shuffles: int = 1000,
        shuffle_columns: list[str] | None = None,
        verbose: bool = True,
    ) -> PermutationTestResult:
        """
        Permutation Test 실행.

        Args:
            num_shuffles: 셔플 횟수
            shuffle_columns: 섞을 컬럼 (기본: 'close')
            verbose: 진행 상황 로깅

        Returns:
            PermutationTestResult: 검증 결과
        """
        if shuffle_columns is None:
            shuffle_columns = ["close"]

        # 1. 원본 데이터로 백테스트
        if verbose:
            logger.info("Step 1: Testing with original data")

        try:
            strategy_orig = self.strategy_factory()
            original_result = self._simple_backtest(self.data, strategy_orig)
        except Exception as e:
            logger.error(f"Failed to run original backtest: {e}")
            raise

        original_return = original_result.total_return
        original_sharpe = original_result.sharpe_ratio
        original_win_rate = (
            original_result.win_rate if hasattr(original_result, "win_rate") else 0.0
        )

        if verbose:
            logger.info(
                f"  Original return: {original_return:.2%}, "
                f"Sharpe: {original_sharpe:.2f}, "
                f"Win rate: {original_win_rate:.1%}"
            )

        # 2. 셔플 데이터로 여러 번 백테스트
        if verbose:
            logger.info(f"Step 2: Running {num_shuffles} permutations")

        shuffled_returns = []
        shuffled_sharpes = []
        shuffled_win_rates = []

        for i in range(num_shuffles):
            try:
                # 데이터 셔플
                shuffled_data = self._shuffle_data(self.data, shuffle_columns)

                # 백테스트
                strategy_shuffled = self.strategy_factory()
                shuffled_result = self._simple_backtest(shuffled_data, strategy_shuffled)

                shuffled_returns.append(shuffled_result.total_return)
                shuffled_sharpes.append(getattr(shuffled_result, "sharpe_ratio", 0.0))

                if hasattr(shuffled_result, "win_rate"):
                    shuffled_win_rates.append(shuffled_result.win_rate)

                if verbose and (i + 1) % max(1, num_shuffles // 10) == 0:
                    logger.info(f"  Completed {i + 1}/{num_shuffles} permutations")

            except Exception as e:
                logger.debug(f"Permutation {i} failed: {e}")
                continue

        # 3. 통계 계산
        if verbose:
            logger.info("Step 3: Computing statistics")

        result = self._compute_statistics(
            original_return=original_return,
            original_sharpe=original_sharpe,
            original_win_rate=original_win_rate,
            shuffled_returns=shuffled_returns,
            shuffled_sharpes=shuffled_sharpes,
            shuffled_win_rates=shuffled_win_rates,
        )

        if verbose:
            logger.info(
                f"  Z-score: {result.z_score:.2f}, "
                f"P-value: {result.p_value:.4f}, "
                f"Significance: {result.confidence_level}"
            )
            logger.info(f"  Interpretation: {result.interpretation}")

        return result

    def _shuffle_data(self, data: pd.DataFrame, columns_to_shuffle: list[str]) -> pd.DataFrame:
        """
        Returns 기반 블록 부트스트랩으로 데이터 셔플.

        OHLC 관계를 유지하면서 시계열 순서를 재배열하여
        보다 현실적인 랜덤 데이터 생성.

        Index (날짜)는 유지하고, 수익률을 블록 단위로 섞어 재구성.
        """
        shuffled = data.copy()

        # close 기반 수익률 계산
        returns = shuffled["close"].pct_change().fillna(0).values

        # 블록 부트스트랩으로 수익률 재배열 (block_size=5)
        block_size = 5
        n = len(returns)
        resampled_returns = []
        i = 0
        while i < n:
            start = np.random.randint(0, max(1, n - block_size))
            block = returns[start : start + block_size]
            resampled_returns.extend(block)
            i += block_size
        resampled_returns = np.array(resampled_returns[:n])  # type: ignore[assignment]

        # 재구성된 수익률로 가격 재생성
        base_price = shuffled["close"].iloc[0]
        new_close = [base_price]
        for r in resampled_returns[1:]:
            new_close.append(new_close[-1] * (1 + r))

        shuffled["close"] = new_close

        # OHLC 일관성 유지
        shuffled["open"] = shuffled["close"].shift(1).fillna(shuffled["close"].iloc[0])
        shuffled["high"] = shuffled[["open", "close"]].max(axis=1) * 1.002
        shuffled["low"] = shuffled[["open", "close"]].min(axis=1) * 0.998

        # volume은 원본 순서 유지 (또는 별도 셔플 가능)
        if "volume" in columns_to_shuffle and "volume" in shuffled.columns:
            volume_values = shuffled["volume"].values.copy()
            np.random.shuffle(volume_values)
            shuffled["volume"] = volume_values

        return shuffled

    def _compute_statistics(
        self,
        original_return: float,
        original_sharpe: float,
        original_win_rate: float,
        shuffled_returns: list[float],
        shuffled_sharpes: list[float],
        shuffled_win_rates: list[float],
    ) -> PermutationTestResult:
        """
        Z-score와 p-value 계산.
        """
        result = PermutationTestResult(
            original_return=original_return,
            original_sharpe=original_sharpe,
            original_win_rate=original_win_rate,
            shuffled_returns=shuffled_returns,
            shuffled_sharpes=shuffled_sharpes,
            shuffled_win_rates=shuffled_win_rates,
        )

        if not shuffled_returns:
            logger.error("No valid shuffled results")
            return result

        # Return 기반 Z-score 계산
        mean_shuffled = np.mean(shuffled_returns)
        std_shuffled = np.std(shuffled_returns)

        result.mean_shuffled_return = float(mean_shuffled)
        result.std_shuffled_return = float(std_shuffled)

        # Z-score = (X - μ) / σ
        if std_shuffled > 0:
            result.z_score = float((original_return - mean_shuffled) / std_shuffled)
        else:
            result.z_score = 0.0

        # P-value: 우연에 의해 original만큼 좋은 성과가 나올 확률
        # 양측 검정
        result.p_value = 2 * (1 - stats.norm.cdf(abs(result.z_score)))

        # 통계적 유의성 판정
        if result.p_value < 0.01:
            result.confidence_level = "1%"
            result.is_statistically_significant = True
        elif result.p_value < 0.05:
            result.confidence_level = "5%"
            result.is_statistically_significant = True
        else:
            result.confidence_level = "not significant"
            result.is_statistically_significant = False

        # 해석
        result.interpretation = self._interpret_results(result)

        return result

    def _interpret_results(self, result: PermutationTestResult) -> str:
        """
        결과 해석.
        """
        if result.z_score < 0:
            # 원본 성과가 셔플 평균보다 나쁨
            return (
                f"⚠️ 원본 성과({result.original_return:.2%})가 "
                f"무작위 셔플 평균({result.mean_shuffled_return:.2%})보다 낮음. "
                f"전략이 실제 신호를 캡처하지 못하는 것으로 보임."
            )
        elif result.z_score < 1.0:
            # 유의하지 않음
            return (
                f"❌ Z-score={result.z_score:.2f} < 1.0: "
                f"통계적으로 유의하지 않음 (p-value={result.p_value:.4f}). "
                f"이 성과는 우연일 가능성이 높음. 과적합 의심."
            )
        elif result.z_score < 2.0:
            # 약하게 유의
            return (
                f"⚠️ Z-score={result.z_score:.2f}: "
                f"약하게 유의함 (p-value={result.p_value:.4f}). "
                f"어느 정도 신호가 있으나 과적합 우려."
            )
        elif result.z_score < 3.0:
            # 유의함
            return (
                f"✅ Z-score={result.z_score:.2f} ({result.confidence_level} 유의수준): "
                f"통계적으로 유의한 성과. 전략에 실제 신호가 있을 가능성 높음."
            )
        else:
            # 매우 유의함
            return (
                f"🎯 Z-score={result.z_score:.2f} ({result.confidence_level} 유의수준): "
                f"매우 강한 통계적 유의성. 전략의 신호 품질이 우수함."
            )

    def export_report_html(self, result: PermutationTestResult, output_path: str) -> None:
        """HTML 리포트 생성."""
        html = self._generate_html(result)

        from pathlib import Path

        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"Permutation test report saved to {output_path}")

    def _generate_html(self, result: PermutationTestResult) -> str:
        """HTML 리포트 생성."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Permutation Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #2196F3; color: white; }}
                .significant {{ color: #4CAF50; font-weight: bold; }}
                .warning {{ color: #FF9800; font-weight: bold; }}
                .danger {{ color: #F44336; font-weight: bold; }}
                .interpretation {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #2196F3;
                    font-size: 14px;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <h1>Permutation Test Report</h1>
            <h2>Statistical Significance Test</h2>

            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Original Return</td>
                    <td>{result.original_return:.2%}</td>
                </tr>
                <tr>
                    <td>Original Sharpe</td>
                    <td>{result.original_sharpe:.2f}</td>
                </tr>
                <tr>
                    <td>Original Win Rate</td>
                    <td>{result.original_win_rate:.1%}</td>
                </tr>
                <tr>
                    <td colspan="2"><b>Shuffled Data Statistics (n={len(result.shuffled_returns)})</b></td>
                </tr>
                <tr>
                    <td>Mean Return</td>
                    <td>{result.mean_shuffled_return:.2%}</td>
                </tr>
                <tr>
                    <td>Std Dev Return</td>
                    <td>{result.std_shuffled_return:.2%}</td>
                </tr>
                <tr>
                    <td colspan="2"><b>Hypothesis Test</b></td>
                </tr>
                <tr>
                    <td>Z-score</td>
                    <td class="{"significant" if result.is_statistically_significant else "danger"}">
                        {result.z_score:.2f}
                    </td>
                </tr>
                <tr>
                    <td>P-value</td>
                    <td class="{"significant" if result.is_statistically_significant else "danger"}">
                        {result.p_value:.4f}
                    </td>
                </tr>
                <tr>
                    <td>Significance Level</td>
                    <td class="{"significant" if result.is_statistically_significant else "danger"}">
                        {result.confidence_level}
                    </td>
                </tr>
            </table>

            <h2>Interpretation</h2>
            <div class="interpretation">
                {result.interpretation}
            </div>

            <h2>Decision</h2>
            <div class="interpretation">
                {"✅ 전략에 통계적으로 유의한 신호가 있습니다." if result.is_statistically_significant else "❌ 전략의 성과가 우연일 가능성이 높습니다."}
            </div>
        </body>
        </html>
        """

        return html


if __name__ == "__main__":
    print("PermutationTester module loaded successfully")
