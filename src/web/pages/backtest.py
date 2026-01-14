"""Backtest page.

백테스트 실행 및 결과 표시 페이지.
"""

import json

import numpy as np
import pandas as pd
import streamlit as st

from src.backtester.models import BacktestConfig
from src.utils.logger import get_logger
from src.web.components.charts.equity_curve import render_equity_curve
from src.web.components.charts.monthly_heatmap import render_monthly_heatmap
from src.web.components.charts.underwater import render_underwater_curve
from src.web.components.charts.yearly_bar import render_yearly_bar_chart
from src.web.components.metrics.metrics_display import (
    render_metrics_cards,
    render_statistical_significance,
)
from src.web.components.sidebar.asset_selector import render_asset_selector
from src.web.components.sidebar.date_config import render_date_config
from src.web.components.sidebar.strategy_selector import render_strategy_selector
from src.web.components.sidebar.trading_config import render_trading_config
from src.web.services.backtest_runner import run_backtest_service
from src.web.services.data_loader import get_data_files, validate_data_availability
from src.web.services.metrics_calculator import calculate_extended_metrics

logger = get_logger(__name__)

__all__ = ["render_backtest_page"]


def render_backtest_page() -> None:
    """백테스트 페이지 렌더링."""
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📈 백테스트</h1>
        <p>이벤트 드리븐 엔진으로 전략을 테스트하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # ===== 사이드바 설정 =====
    with st.sidebar:
        st.markdown("### ⚙️ 백테스트 설정")
        st.markdown("---")

        # 1. 날짜 설정
        start_date, end_date = render_date_config()
        st.markdown("---")

        # 2. 거래 설정
        trading_config = render_trading_config()
        st.markdown("---")

        # 3. 전략 선택
        strategy_name, strategy_params = render_strategy_selector()
        st.markdown("---")

        # 4. 자산 선택
        selected_tickers = render_asset_selector()
        st.markdown("---")

        # 실행 버튼
        run_button = st.button(
            "🚀 백테스트 실행",
            type="primary",
            use_container_width=True,
        )

    # ===== 메인 화면 =====

    # 검증
    if not strategy_name:
        st.warning("⚠️ 전략을 선택하세요.")
        _show_empty_state(start_date, end_date, trading_config, strategy_name, strategy_params, selected_tickers)
        return

    if not selected_tickers:
        st.warning("⚠️ 최소 1개 이상의 자산을 선택하세요.")
        _show_empty_state(start_date, end_date, trading_config, strategy_name, strategy_params, selected_tickers)
        return

    # 데이터 가용성 체크
    available_tickers, missing_tickers = validate_data_availability(
        selected_tickers, trading_config.interval
    )

    if missing_tickers:
        st.warning(
            f"⚠️ 다음 자산의 데이터가 없습니다: {', '.join(missing_tickers)}\n\n"
            f"사용 가능한 자산: {', '.join(available_tickers) if available_tickers else '없음'}"
        )

        if not available_tickers:
            st.error("❌ 사용 가능한 데이터가 없습니다. 데이터 수집을 먼저 진행하세요.")
            st.code("uv run python scripts/collect_data.py")
            return

    # 백테스트 실행
    if run_button:
        with st.spinner("백테스트 실행 중..."):
            # BacktestConfig 생성
            config = BacktestConfig(
                initial_capital=trading_config.initial_capital,
                fee_rate=trading_config.fee_rate,
                slippage_rate=trading_config.slippage_rate,
                max_slots=trading_config.max_slots,
                stop_loss_pct=trading_config.stop_loss_pct,
                take_profit_pct=trading_config.take_profit_pct,
                trailing_stop_pct=trading_config.trailing_stop_pct,
            )

            # 데이터 파일 경로
            data_files = get_data_files(available_tickers, trading_config.interval)

            # 백테스트 실행 (캐시됨)
            result = run_backtest_service(
                strategy_name=strategy_name,
                strategy_params=strategy_params,
                data_files_dict={k: str(v) for k, v in data_files.items()},
                config_dict={
                    "initial_capital": config.initial_capital,
                    "fee_rate": config.fee_rate,
                    "slippage_rate": config.slippage_rate,
                    "max_slots": config.max_slots,
                    "stop_loss_pct": config.stop_loss_pct,
                    "take_profit_pct": config.take_profit_pct,
                    "trailing_stop_pct": config.trailing_stop_pct,
                },
                start_date_str=start_date.isoformat(),
                end_date_str=end_date.isoformat(),
            )

            if result:
                # 세션 스테이트에 저장
                st.session_state.backtest_result = result
                st.success("✅ 백테스트 완료!")
            else:
                st.error("❌ 백테스트 실행 실패. 로그를 확인하세요.")
                return

    # 결과 표시
    if "backtest_result" in st.session_state:
        result = st.session_state.backtest_result
        _display_results(result, strategy_name)
    else:
        _show_empty_state(start_date, end_date, trading_config, strategy_name, strategy_params, selected_tickers)


def _show_empty_state(start_date, end_date, trading_config, strategy_name, strategy_params, selected_tickers) -> None:
    """백테스트 실행 전 빈 상태 표시."""
    st.markdown("""
    <div class="summary-box" style="text-align: center;">
        <h3>📋 설정을 완료하고 백테스트를 실행하세요</h3>
        <p style="color: #94a3b8;">
            왼쪽 사이드바에서 기간, 전략, 자산을 선택한 후<br>
            <strong>🚀 백테스트 실행</strong> 버튼을 클릭하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 설정 요약 표시
    st.markdown("### 📋 현재 설정")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="feature-card">
            <h4>📅 기간</h4>
            <p><strong>시작:</strong> {start_date}</p>
            <p><strong>종료:</strong> {end_date}</p>
            <p><strong>기간:</strong> {(end_date - start_date).days}일</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="feature-card">
            <h4>⚙️ 거래 설정</h4>
            <p><strong>인터벌:</strong> {trading_config.interval}</p>
            <p><strong>수수료:</strong> {trading_config.fee_rate:.2%}</p>
            <p><strong>슬리피지:</strong> {trading_config.slippage_rate:.2%}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="feature-card">
            <h4>📈 전략 & 자산</h4>
            <p><strong>전략:</strong> {strategy_name or '미선택'}</p>
            <p><strong>파라미터:</strong> {len(strategy_params)}개</p>
            <p><strong>자산:</strong> {len(selected_tickers) if selected_tickers else 0}개</p>
        </div>
        """, unsafe_allow_html=True)


def _display_results(result, strategy_name: str) -> None:
    """백테스트 결과 표시.

    Args:
        result: BacktestResult 객체
        strategy_name: 전략 이름
    """
    # 요약 카드
    equity = np.array(result.equity_curve)
    initial = equity[0]
    final = equity[-1]
    total_return = (final / initial - 1) * 100

    daily_returns = np.diff(equity) / equity[:-1]
    sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(365) if np.std(daily_returns) > 0 else 0

    cummax = np.maximum.accumulate(equity)
    drawdown = (cummax - equity) / cummax
    mdd = np.max(drawdown) * 100

    # 핵심 메트릭 상단 표시
    st.markdown("### 🎯 핵심 성과")

    col1, col2, col3, col4, col5 = st.columns(5)

    metrics_data = [
        ("전략", strategy_name, "neutral"),
        ("총 수익률", f"{total_return:.2f}%", "positive" if total_return > 0 else "negative"),
        ("Sharpe Ratio", f"{sharpe:.2f}", "positive" if sharpe > 1 else "neutral"),
        ("MDD", f"-{mdd:.2f}%", "negative" if mdd > 20 else "neutral"),
        ("거래수", str(len(result.trades)), "neutral"),
    ]

    for col, (label, value, vtype) in zip([col1, col2, col3, col4, col5], metrics_data):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value {vtype}">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 거래 수익률 추출
    trade_returns = [t.pnl_pct / 100 for t in result.trades if t.pnl_pct is not None]

    # 확장 메트릭 계산
    dates = np.array(result.dates) if hasattr(result, "dates") else np.arange(len(equity))

    extended_metrics = calculate_extended_metrics(
        equity=equity,
        trade_returns=trade_returns,
    )

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 개요",
        "📊 수익률 곡선",
        "📉 드로다운",
        "📅 월별 분석",
        "📆 연도별 분석",
        "🔬 통계 분석",
    ])

    with tab1:
        render_metrics_cards(extended_metrics)

        # 거래 내역
        if result.trades:
            with st.expander(f"📜 거래 내역 ({len(result.trades)}건)", expanded=False):
                trades_df = pd.DataFrame(
                    [
                        {
                            "티커": t.ticker,
                            "진입일": t.entry_date,
                            "진입가": f"{t.entry_price:,.0f}",
                            "청산일": t.exit_date or "-",
                            "청산가": f"{t.exit_price:,.0f}" if t.exit_price else "-",
                            "수량": f"{t.amount:.4f}",
                            "손익": f"{t.pnl:,.0f}",
                            "수익률": f"{t.pnl_pct:.2f}%",
                        }
                        for t in result.trades[:100]  # 최대 100개만 표시
                    ]
                )

                st.dataframe(trades_df, use_container_width=True, height=400)

    with tab2:
        render_equity_curve(dates, equity)

    with tab3:
        render_underwater_curve(dates, equity)

    with tab4:
        render_monthly_heatmap(dates, equity)

    with tab5:
        render_yearly_bar_chart(dates, equity)

    with tab6:
        render_statistical_significance(extended_metrics)

    # 결과 다운로드
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 에쿼티 CSV
        equity_df = pd.DataFrame({
            "date": dates,
            "equity": equity,
        })
        csv_equity = equity_df.to_csv(index=False)
        st.download_button(
            "📥 에쿼티 곡선 (CSV)",
            csv_equity,
            "equity_curve.csv",
            "text/csv",
            use_container_width=True,
        )

    with col2:
        # 거래 내역 CSV
        if result.trades:
            trades_export = pd.DataFrame([
                {
                    "ticker": t.ticker,
                    "entry_date": t.entry_date,
                    "entry_price": t.entry_price,
                    "exit_date": t.exit_date,
                    "exit_price": t.exit_price,
                    "amount": t.amount,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                }
                for t in result.trades
            ])
            csv_trades = trades_export.to_csv(index=False)
            st.download_button(
                "📥 거래 내역 (CSV)",
                csv_trades,
                "trades.csv",
                "text/csv",
                use_container_width=True,
            )

    with col3:
        # 메트릭 JSON
        metrics_dict = {
            "total_return_pct": extended_metrics.total_return_pct,
            "cagr_pct": extended_metrics.cagr_pct,
            "sharpe_ratio": extended_metrics.sharpe_ratio,
            "sortino_ratio": extended_metrics.sortino_ratio,
            "max_drawdown_pct": extended_metrics.max_drawdown_pct,
            "win_rate_pct": extended_metrics.win_rate_pct,
            "profit_factor": extended_metrics.profit_factor,
            "num_trades": extended_metrics.num_trades,
        }
        json_metrics = json.dumps(metrics_dict, indent=2)
        st.download_button(
            "📥 메트릭 (JSON)",
            json_metrics,
            "metrics.json",
            "application/json",
            use_container_width=True,
        )
