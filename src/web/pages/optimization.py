"""Optimization page.

파라미터 최적화 실행 및 결과 표시 페이지.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.utils.logger import get_logger
from src.web.components.sidebar.date_config import render_date_config
from src.web.components.sidebar.strategy_selector import render_strategy_selector
from src.web.components.sidebar.trading_config import render_trading_config
from src.web.components.sidebar.asset_selector import render_asset_selector

logger = get_logger(__name__)

__all__ = ["render_optimization_page"]


def render_optimization_page() -> None:
    """최적화 페이지 렌더링."""
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🔧 파라미터 최적화</h1>
        <p>Grid Search / Random Search로 최적 파라미터를 탐색합니다</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 최적화 설정")
        st.markdown("---")

        # 날짜 설정
        start_date, end_date = render_date_config()
        st.markdown("---")

        # 거래 설정
        trading_config = render_trading_config()
        st.markdown("---")

        # 전략 선택
        strategy_name, strategy_params = render_strategy_selector()
        st.markdown("---")

        # 자산 선택
        selected_tickers = render_asset_selector()

    # 메인 영역
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎯 최적화 방법 선택")

        opt_method = st.radio(
            "최적화 방법",
            ["Grid Search", "Random Search", "Bayesian Optimization"],
            horizontal=True,
            help="Grid: 모든 조합 탐색 | Random: 무작위 샘플링 | Bayesian: 지능적 탐색",
        )

    with col2:
        st.markdown("### 📊 최적화 목표")

        opt_metric = st.selectbox(
            "목표 메트릭",
            ["sharpe_ratio", "cagr", "calmar_ratio", "sortino_ratio"],
            format_func=lambda x: {
                "sharpe_ratio": "Sharpe Ratio",
                "cagr": "CAGR",
                "calmar_ratio": "Calmar Ratio",
                "sortino_ratio": "Sortino Ratio",
            }[x],
        )

    st.markdown("---")

    # 파라미터 범위 설정
    st.markdown("### 🔢 파라미터 범위 설정")

    if strategy_name:
        st.info(f"선택된 전략: **{strategy_name}**")

        # 파라미터별 범위 설정 UI
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**SMA Period**")
            sma_min = st.number_input("최소", value=3, min_value=2, max_value=20, key="sma_min")
            sma_max = st.number_input("최대", value=10, min_value=2, max_value=30, key="sma_max")
            sma_step = st.number_input("Step", value=1, min_value=1, max_value=5, key="sma_step")

        with col2:
            st.markdown("**Trend SMA Period**")
            trend_min = st.number_input("최소", value=5, min_value=3, max_value=30, key="trend_min")
            trend_max = st.number_input("최대", value=20, min_value=5, max_value=50, key="trend_max")
            trend_step = st.number_input("Step", value=5, min_value=1, max_value=10, key="trend_step")

        with col3:
            st.markdown("**K Factor**")
            k_min = st.number_input("최소", value=0.3, min_value=0.1, max_value=1.0, step=0.1, key="k_min")
            k_max = st.number_input("최대", value=0.8, min_value=0.2, max_value=1.5, step=0.1, key="k_max")
            k_step = st.number_input("Step", value=0.1, min_value=0.05, max_value=0.3, step=0.05, key="k_step")

        # 총 조합 수 계산
        sma_range = list(range(int(sma_min), int(sma_max) + 1, int(sma_step)))
        trend_range = list(range(int(trend_min), int(trend_max) + 1, int(trend_step)))
        k_range = [round(k_min + i * k_step, 2) for i in range(int((k_max - k_min) / k_step) + 1)]

        total_combinations = len(sma_range) * len(trend_range) * len(k_range)

        st.markdown("---")

        # 예상 정보
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("총 조합 수", f"{total_combinations:,}")
        with col2:
            est_time = total_combinations * 0.5  # 조합당 0.5초 가정
            st.metric("예상 소요시간", f"{est_time:.0f}초")
        with col3:
            st.metric("병렬 워커", "4")
        with col4:
            st.metric("자산 수", len(selected_tickers) if selected_tickers else 0)

        st.markdown("---")

        # 실행 버튼
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            run_opt = st.button(
                "🚀 최적화 실행",
                type="primary",
                use_container_width=True,
                disabled=not strategy_name or not selected_tickers,
            )

        if run_opt:
            _run_optimization_demo()

    else:
        st.warning("⚠️ 먼저 전략을 선택해주세요.")

    # 이전 결과 표시
    if "optimization_results" in st.session_state:
        _display_optimization_results(st.session_state.optimization_results)


def _run_optimization_demo() -> None:
    """최적화 데모 실행 (실제로는 최적화 엔진 호출)."""
    import numpy as np
    import time

    progress_bar = st.progress(0)
    status_text = st.empty()

    # 데모 결과 생성
    results = []
    total_steps = 20

    for i in range(total_steps):
        progress_bar.progress((i + 1) / total_steps)
        status_text.text(f"최적화 진행 중... ({i + 1}/{total_steps})")
        time.sleep(0.1)

        # 랜덤 결과 생성
        results.append({
            "sma_period": np.random.randint(3, 10),
            "trend_sma_period": np.random.randint(5, 20),
            "k_factor": round(np.random.uniform(0.3, 0.8), 2),
            "sharpe_ratio": round(np.random.uniform(0.5, 2.5), 3),
            "cagr": round(np.random.uniform(10, 50), 2),
            "mdd": round(np.random.uniform(-30, -5), 2),
            "total_trades": np.random.randint(50, 200),
            "win_rate": round(np.random.uniform(40, 70), 1),
        })

    progress_bar.empty()
    status_text.empty()

    st.session_state.optimization_results = pd.DataFrame(results)
    st.success("✅ 최적화 완료!")
    st.rerun()


def _display_optimization_results(results_df: pd.DataFrame) -> None:
    """최적화 결과 표시."""
    st.markdown("---")
    st.markdown("### 📊 최적화 결과")

    # 최적 파라미터
    best_idx = results_df["sharpe_ratio"].idxmax()
    best_params = results_df.loc[best_idx]

    # 최적 결과 카드
    st.markdown("#### 🏆 최적 파라미터 조합")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="label">SMA Period</div>
            <div class="value neutral">{}</div>
        </div>
        """.format(int(best_params["sma_period"])), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="label">Trend SMA</div>
            <div class="value neutral">{}</div>
        </div>
        """.format(int(best_params["trend_sma_period"])), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="label">K Factor</div>
            <div class="value neutral">{}</div>
        </div>
        """.format(best_params["k_factor"]), unsafe_allow_html=True)

    with col4:
        sharpe_class = "positive" if best_params["sharpe_ratio"] > 1 else "neutral"
        st.markdown("""
        <div class="metric-card">
            <div class="label">Sharpe Ratio</div>
            <div class="value {}">{:.3f}</div>
        </div>
        """.format(sharpe_class, best_params["sharpe_ratio"]), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📈 성능 분포", "🔥 히트맵", "📋 전체 결과"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            # Sharpe 분포
            fig = px.histogram(
                results_df,
                x="sharpe_ratio",
                nbins=20,
                title="Sharpe Ratio 분포",
                color_discrete_sequence=["#6366f1"],
            )
            fig.add_vline(
                x=best_params["sharpe_ratio"],
                line_dash="dash",
                line_color="#22c55e",
                annotation_text="Best",
            )
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # CAGR vs Sharpe 산점도
            fig = px.scatter(
                results_df,
                x="sharpe_ratio",
                y="cagr",
                color="mdd",
                size="total_trades",
                title="Sharpe vs CAGR (색상: MDD, 크기: 거래수)",
                color_continuous_scale="RdYlGn",
            )
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # 파라미터 히트맵
        pivot_data = results_df.pivot_table(
            values="sharpe_ratio",
            index="sma_period",
            columns="trend_sma_period",
            aggfunc="mean",
        )

        fig = px.imshow(
            pivot_data,
            title="SMA Period vs Trend SMA (Sharpe Ratio)",
            color_continuous_scale="RdYlGn",
            aspect="auto",
        )
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # 전체 결과 테이블
        st.dataframe(
            results_df.sort_values("sharpe_ratio", ascending=False),
            use_container_width=True,
            height=400,
        )

        # CSV 다운로드
        csv = results_df.to_csv(index=False)
        st.download_button(
            "📥 결과 다운로드 (CSV)",
            csv,
            "optimization_results.csv",
            "text/csv",
            use_container_width=True,
        )
