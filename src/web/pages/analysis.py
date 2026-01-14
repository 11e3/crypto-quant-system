"""Analysis Dashboard page.

고급 분석 및 리스크 관리 대시보드.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.utils.logger import get_logger

logger = get_logger(__name__)

__all__ = ["render_analysis_page"]


def render_analysis_page() -> None:
    """분석 대시보드 페이지 렌더링."""
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📊 분석 대시보드</h1>
        <p>백테스트 결과의 심층 분석 및 리스크 평가</p>
    </div>
    """, unsafe_allow_html=True)

    # 백테스트 결과 확인
    if "backtest_result" not in st.session_state:
        st.warning("⚠️ 먼저 백테스트를 실행해주세요.")

        st.markdown("""
        <div class="summary-box" style="text-align: center;">
            <h3>📈 백테스트 먼저 실행하기</h3>
            <p style="color: #94a3b8;">
                분석을 위해서는 백테스트 결과가 필요합니다.<br>
                사이드바에서 "백테스트" 메뉴를 선택하고 실행해주세요.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 데모 데이터로 진행 옵션
        if st.button("🎮 데모 데이터로 분석 체험", type="primary"):
            _generate_demo_data()
            st.rerun()
        return

    result = st.session_state.backtest_result

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 요약",
        "📈 수익률 분석",
        "🛡️ 리스크 분석",
        "🎯 거래 분석",
        "🔬 고급 분석",
    ])

    with tab1:
        _render_summary_tab(result)

    with tab2:
        _render_returns_tab(result)

    with tab3:
        _render_risk_tab(result)

    with tab4:
        _render_trade_tab(result)

    with tab5:
        _render_advanced_tab(result)


def _generate_demo_data() -> None:
    """데모 데이터 생성."""
    from dataclasses import dataclass
    from datetime import date, timedelta

    @dataclass
    class DemoTrade:
        ticker: str
        entry_date: date
        exit_date: date
        entry_price: float
        exit_price: float
        amount: float
        pnl: float
        pnl_pct: float

    # 데모 에쿼티 곡선
    days = 365
    initial = 10_000_000
    returns = np.random.normal(0.001, 0.02, days)
    equity = initial * np.cumprod(1 + returns)

    # 데모 거래
    trades = []
    for i in range(50):
        entry = date(2024, 1, 1) + timedelta(days=np.random.randint(0, 300))
        exit_d = entry + timedelta(days=np.random.randint(1, 30))
        pnl_pct = np.random.normal(2, 10)
        trades.append(DemoTrade(
            ticker=np.random.choice(["BTC", "ETH", "SOL", "XRP"]),
            entry_date=entry,
            exit_date=exit_d,
            entry_price=np.random.uniform(30000, 50000),
            exit_price=np.random.uniform(30000, 50000),
            amount=0.1,
            pnl=pnl_pct * 1000,
            pnl_pct=pnl_pct,
        ))

    @dataclass
    class DemoResult:
        equity_curve: list
        dates: list
        trades: list
        total_return: float
        sharpe_ratio: float
        mdd: float

    st.session_state.backtest_result = DemoResult(
        equity_curve=equity.tolist(),
        dates=[date(2024, 1, 1) + timedelta(days=i) for i in range(days)],
        trades=trades,
        total_return=(equity[-1] / initial - 1) * 100,
        sharpe_ratio=np.random.uniform(1, 2),
        mdd=np.random.uniform(-20, -5),
    )


def _render_summary_tab(result) -> None:
    """요약 탭 렌더링."""
    st.markdown("### 📊 성과 요약")

    equity = np.array(result.equity_curve)
    initial = equity[0]
    final = equity[-1]

    # 핵심 메트릭 계산
    total_return = (final / initial - 1) * 100
    daily_returns = np.diff(equity) / equity[:-1]
    sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(365) if np.std(daily_returns) > 0 else 0
    cummax = np.maximum.accumulate(equity)
    drawdown = (cummax - equity) / cummax
    mdd = np.max(drawdown) * 100

    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("총 수익률", f"{total_return:.2f}%", "positive" if total_return > 0 else "negative"),
        ("Sharpe Ratio", f"{sharpe:.2f}", "positive" if sharpe > 1 else "neutral"),
        ("MDD", f"-{mdd:.2f}%", "negative" if mdd > 20 else "neutral"),
        ("총 거래수", str(len(result.trades)), "neutral"),
    ]

    for col, (label, value, vtype) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value {vtype}">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 에쿼티 곡선
    col1, col2 = st.columns([2, 1])

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(equity))),
            y=equity,
            mode="lines",
            name="Portfolio",
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.2)",
            line=dict(color="#6366f1", width=2),
        ))
        fig.update_layout(
            title="Portfolio Equity Curve",
            template="plotly_dark",
            height=350,
            xaxis_title="Days",
            yaxis_title="Value",
            yaxis_tickformat=",",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 수익률 분포
        fig = px.histogram(
            x=daily_returns * 100,
            nbins=50,
            title="Daily Returns Distribution",
            labels={"x": "Return (%)"},
            color_discrete_sequence=["#6366f1"],
        )
        fig.add_vline(x=0, line_dash="dash", line_color="white")
        fig.update_layout(
            template="plotly_dark",
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_returns_tab(result) -> None:
    """수익률 분석 탭 렌더링."""
    st.markdown("### 📈 수익률 분석")

    equity = np.array(result.equity_curve)
    daily_returns = np.diff(equity) / equity[:-1]

    col1, col2 = st.columns(2)

    with col1:
        # 누적 수익률
        cumulative = (equity / equity[0] - 1) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=cumulative,
            mode="lines",
            name="Cumulative Return",
            line=dict(color="#22c55e", width=2),
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            title="Cumulative Returns (%)",
            template="plotly_dark",
            height=350,
            yaxis_ticksuffix="%",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 롤링 Sharpe
        window = 30
        if len(daily_returns) > window:
            rolling_mean = pd.Series(daily_returns).rolling(window).mean()
            rolling_std = pd.Series(daily_returns).rolling(window).std()
            rolling_sharpe = (rolling_mean / rolling_std * np.sqrt(365)).fillna(0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=rolling_sharpe,
                mode="lines",
                name="Rolling Sharpe",
                line=dict(color="#f59e0b", width=2),
            ))
            fig.add_hline(y=1, line_dash="dash", line_color="#22c55e", annotation_text="Target")
            fig.update_layout(
                title=f"Rolling Sharpe Ratio ({window}-day)",
                template="plotly_dark",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

    # 월별/연도별 수익률
    st.markdown("#### 📅 기간별 수익률")

    # 월별 수익률 히트맵 (간단 버전)
    if len(result.dates) > 30:
        dates = pd.to_datetime(result.dates)
        df = pd.DataFrame({"date": dates, "equity": equity})
        df["month"] = df["date"].dt.to_period("M")
        monthly = df.groupby("month")["equity"].agg(["first", "last"])
        monthly["return"] = (monthly["last"] / monthly["first"] - 1) * 100

        fig = px.bar(
            x=[str(p) for p in monthly.index],
            y=monthly["return"],
            title="Monthly Returns",
            color=monthly["return"],
            color_continuous_scale="RdYlGn",
        )
        fig.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)


def _render_risk_tab(result) -> None:
    """리스크 분석 탭 렌더링."""
    st.markdown("### 🛡️ 리스크 분석")

    equity = np.array(result.equity_curve)
    daily_returns = np.diff(equity) / equity[:-1]

    # 드로다운 분석
    cummax = np.maximum.accumulate(equity)
    drawdown = (cummax - equity) / cummax * 100

    col1, col2 = st.columns(2)

    with col1:
        # 드로다운 곡선
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=-drawdown,
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.3)",
            line=dict(color="#ef4444", width=1),
            name="Drawdown",
        ))
        fig.update_layout(
            title="Underwater (Drawdown) Chart",
            template="plotly_dark",
            height=350,
            yaxis_ticksuffix="%",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # VaR 분석
        var_95 = np.percentile(daily_returns, 5) * 100
        var_99 = np.percentile(daily_returns, 1) * 100
        cvar_95 = daily_returns[daily_returns <= np.percentile(daily_returns, 5)].mean() * 100

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=daily_returns * 100,
            nbinsx=50,
            name="Returns",
            marker_color="#6366f1",
        ))
        fig.add_vline(x=var_95, line_dash="dash", line_color="#f59e0b", annotation_text="VaR 95%")
        fig.add_vline(x=var_99, line_dash="dash", line_color="#ef4444", annotation_text="VaR 99%")
        fig.update_layout(
            title="Value at Risk (VaR) Analysis",
            template="plotly_dark",
            height=350,
            xaxis_title="Daily Return (%)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # 리스크 메트릭
    st.markdown("#### 📊 리스크 메트릭")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("VaR (95%)", f"{var_95:.2f}%")
    with col2:
        st.metric("VaR (99%)", f"{var_99:.2f}%")
    with col3:
        st.metric("CVaR (95%)", f"{cvar_95:.2f}%")
    with col4:
        st.metric("Max Drawdown", f"-{np.max(drawdown):.2f}%")


def _render_trade_tab(result) -> None:
    """거래 분석 탭 렌더링."""
    st.markdown("### 🎯 거래 분석")

    if not result.trades:
        st.warning("거래 내역이 없습니다.")
        return

    trades = result.trades
    pnl_list = [t.pnl_pct for t in trades if hasattr(t, "pnl_pct")]

    if not pnl_list:
        st.warning("거래 수익률 데이터가 없습니다.")
        return

    # 승률 계산
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p <= 0]
    win_rate = len(wins) / len(pnl_list) * 100 if pnl_list else 0

    col1, col2 = st.columns(2)

    with col1:
        # 거래 수익률 분포
        fig = px.histogram(
            x=pnl_list,
            nbins=30,
            title="Trade P&L Distribution",
            labels={"x": "P&L (%)"},
            color_discrete_sequence=["#6366f1"],
        )
        fig.add_vline(x=0, line_dash="dash", line_color="white")
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 승/패 파이 차트
        fig = go.Figure(data=[go.Pie(
            labels=["Wins", "Losses"],
            values=[len(wins), len(losses)],
            hole=0.5,
            marker_colors=["#22c55e", "#ef4444"],
        )])
        fig.update_layout(
            title=f"Win Rate: {win_rate:.1f}%",
            template="plotly_dark",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 거래 메트릭
    st.markdown("#### 📊 거래 통계")

    col1, col2, col3, col4 = st.columns(4)

    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0

    with col1:
        st.metric("총 거래수", len(pnl_list))
    with col2:
        st.metric("평균 수익", f"{avg_win:.2f}%")
    with col3:
        st.metric("평균 손실", f"{avg_loss:.2f}%")
    with col4:
        st.metric("Profit Factor", f"{profit_factor:.2f}")


def _render_advanced_tab(result) -> None:
    """고급 분석 탭 렌더링."""
    st.markdown("### 🔬 고급 분석")

    equity = np.array(result.equity_curve)
    daily_returns = np.diff(equity) / equity[:-1]

    # Monte Carlo 시뮬레이션
    st.markdown("#### 🎲 Monte Carlo 시뮬레이션")

    n_simulations = st.slider("시뮬레이션 횟수", 100, 1000, 500)

    if st.button("Monte Carlo 실행", type="primary"):
        with st.spinner("시뮬레이션 중..."):
            simulations = []
            for _ in range(n_simulations):
                shuffled = np.random.choice(daily_returns, size=len(daily_returns), replace=True)
                sim_equity = equity[0] * np.cumprod(1 + shuffled)
                simulations.append(sim_equity)

            simulations = np.array(simulations)

            # 결과 시각화
            fig = go.Figure()

            # 개별 시뮬레이션 (일부만)
            for i in range(min(100, n_simulations)):
                fig.add_trace(go.Scatter(
                    y=simulations[i],
                    mode="lines",
                    line=dict(color="#6366f1", width=0.5),
                    opacity=0.1,
                    showlegend=False,
                ))

            # 실제 에쿼티
            fig.add_trace(go.Scatter(
                y=equity,
                mode="lines",
                line=dict(color="#22c55e", width=3),
                name="Actual",
            ))

            # 신뢰구간
            p5 = np.percentile(simulations, 5, axis=0)
            p95 = np.percentile(simulations, 95, axis=0)

            fig.add_trace(go.Scatter(
                y=p95,
                mode="lines",
                line=dict(color="#f59e0b", width=1, dash="dash"),
                name="95th Percentile",
            ))
            fig.add_trace(go.Scatter(
                y=p5,
                mode="lines",
                line=dict(color="#ef4444", width=1, dash="dash"),
                name="5th Percentile",
            ))

            fig.update_layout(
                title=f"Monte Carlo Simulation ({n_simulations} paths)",
                template="plotly_dark",
                height=450,
                yaxis_tickformat=",",
            )
            st.plotly_chart(fig, use_container_width=True)

            # 결과 통계
            final_values = simulations[:, -1]
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("평균 최종가치", f"{np.mean(final_values):,.0f}")
            with col2:
                st.metric("5% 최악", f"{np.percentile(final_values, 5):,.0f}")
            with col3:
                st.metric("95% 최선", f"{np.percentile(final_values, 95):,.0f}")
            with col4:
                prob_profit = np.mean(final_values > equity[0]) * 100
                st.metric("수익 확률", f"{prob_profit:.1f}%")

    # 추가 분석 도구
    st.markdown("---")
    st.markdown("#### 🔧 추가 분석 도구")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📊</div>
            <h4>Walk-Forward Analysis</h4>
            <p>과적합 방지를 위한 롤링 윈도우 분석</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🎯</div>
            <h4>순열 검정</h4>
            <p>전략의 통계적 유의성 검증</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📈</div>
            <h4>요인 분석</h4>
            <p>수익의 원천 분석 (알파/베타)</p>
        </div>
        """, unsafe_allow_html=True)
