"""Streamlit Backtest UI - Main Entry Point.

백테스팅 웹 인터페이스 메인 애플리케이션.
"""

import streamlit as st

from src.utils.logger import get_logger, setup_logging
from src.web.components.styles import apply_custom_styles

# 로깅 초기화
setup_logging()
logger = get_logger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="Crypto Quant System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/11e3/crypto-quant-system",
        "Report a bug": "https://github.com/11e3/crypto-quant-system/issues",
        "About": "# Crypto Quant System\n이벤트 드리븐 백테스팅 엔진 기반 퀀트 시스템",
    },
)


def main() -> None:
    """메인 애플리케이션 진입점."""
    # 커스텀 스타일 적용
    apply_custom_styles()

    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="margin: 0; color: #e2e8f0;">📊 Crypto Quant</h2>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">
                Quantitative Trading System
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 네비게이션 메뉴
        pages = {
            "🏠 홈": "home",
            "📈 백테스트": "backtest",
            "🔧 파라미터 최적화": "optimization",
            "📊 분석 대시보드": "analysis",
        }

        selection = st.radio(
            "Navigation",
            list(pages.keys()),
            label_visibility="collapsed",
        )

        st.markdown("---")

        # 퀵 스탯
        st.markdown("### 📈 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전략", "5종")
        with col2:
            st.metric("자산", "100+")

        st.markdown("---")

        # 푸터
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; color: #64748b; font-size: 0.8rem;">
            <p>Built with Streamlit + Plotly</p>
            <p>© 2024 Crypto Quant System</p>
        </div>
        """, unsafe_allow_html=True)

    # 페이지 라우팅
    page_key = pages[selection]

    if page_key == "home":
        show_home()
    elif page_key == "backtest":
        show_backtest()
    elif page_key == "optimization":
        show_optimization()
    elif page_key == "analysis":
        show_analysis()


def show_home() -> None:
    """홈 페이지 - 대시보드 스타일."""
    # 히어로 섹션
    st.markdown("""
    <div class="hero-section">
        <h1>🚀 Crypto Quant System</h1>
        <p style="font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto;">
            이벤트 드리븐 백테스팅 엔진 기반의 암호화폐 퀀트 트레이딩 시스템
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 주요 기능 카드
    st.markdown("### ✨ 주요 기능")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📈</div>
            <h3>백테스트</h3>
            <p>이벤트 드리븐 엔진으로 정확한 백테스트 시뮬레이션</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🔧</div>
            <h3>최적화</h3>
            <p>Grid/Random Search로 최적 파라미터 탐색</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📊</div>
            <h3>분석</h3>
            <p>30+ 메트릭과 인터랙티브 차트로 깊은 분석</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🛡️</div>
            <h3>리스크 관리</h3>
            <p>VaR, CVaR, Monte Carlo 시뮬레이션</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 지원 전략
    st.markdown("### 📚 지원 전략")

    strategies = [
        {
            "name": "VBO (Volatility Breakout)",
            "desc": "변동성 돌파 전략 - 래리 윌리엄스",
            "icon": "📊",
            "tags": ["추세추종", "단기"],
        },
        {
            "name": "Momentum",
            "desc": "모멘텀 기반 추세 추종 전략",
            "icon": "🚀",
            "tags": ["추세추종", "중장기"],
        },
        {
            "name": "Mean Reversion",
            "desc": "평균 회귀 기반 역추세 전략",
            "icon": "🔄",
            "tags": ["역추세", "단기"],
        },
        {
            "name": "Pair Trading",
            "desc": "상관관계 기반 페어 트레이딩",
            "icon": "🔗",
            "tags": ["시장중립", "차익거래"],
        },
        {
            "name": "ORB (Opening Range Breakout)",
            "desc": "시가 범위 돌파 전략",
            "icon": "⏰",
            "tags": ["돌파", "단기"],
        },
    ]

    cols = st.columns(5)
    for i, strategy in enumerate(strategies):
        with cols[i]:
            tags_html = " ".join([
                f'<span style="background: #334155; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem;">{tag}</span>'
                for tag in strategy["tags"]
            ])
            st.markdown(f"""
            <div class="feature-card" style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{strategy["icon"]}</div>
                <h4 style="margin: 0.5rem 0; font-size: 0.95rem;">{strategy["name"]}</h4>
                <p style="font-size: 0.8rem; margin-bottom: 0.75rem;">{strategy["desc"]}</p>
                <div>{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 시작하기
    st.markdown("### 🎯 빠른 시작")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        <div class="summary-box">
            <h3>📋 3단계로 시작하기</h3>
            <ol style="color: #e2e8f0; padding-left: 1.5rem;">
                <li style="margin-bottom: 0.75rem;">
                    <strong>전략 선택</strong> - 5가지 전략 중 원하는 전략 선택
                </li>
                <li style="margin-bottom: 0.75rem;">
                    <strong>파라미터 설정</strong> - 기간, 자산, 거래 설정 구성
                </li>
                <li style="margin-bottom: 0.75rem;">
                    <strong>백테스트 실행</strong> - 결과 분석 및 최적화
                </li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="summary-box" style="text-align: center;">
            <h3>🚀 지금 시작하기</h3>
            <p style="color: #94a3b8; margin-bottom: 1rem;">
                사이드바에서 백테스트를 선택하세요
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📈 백테스트 시작", type="primary", use_container_width=True):
            st.session_state.page = "backtest"
            st.rerun()

    # 시스템 정보
    with st.expander("ℹ️ 시스템 정보"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Python Version", "3.11+")
        with col2:
            st.metric("Engine", "Event-Driven")
        with col3:
            st.metric("Visualization", "Plotly")
        with col4:
            st.metric("Framework", "Streamlit")


def show_backtest() -> None:
    """백테스트 페이지."""
    from src.web.pages.backtest import render_backtest_page

    render_backtest_page()


def show_optimization() -> None:
    """파라미터 최적화 페이지."""
    from src.web.pages.optimization import render_optimization_page

    render_optimization_page()


def show_analysis() -> None:
    """분석 대시보드 페이지."""
    from src.web.pages.analysis import render_analysis_page

    render_analysis_page()


if __name__ == "__main__":
    main()
