"""Streamlit UI 스타일 및 테마 설정.

전체 앱에서 사용되는 공통 스타일 정의.
"""

import streamlit as st

__all__ = ["apply_custom_styles", "COLORS", "metric_card", "info_card"]

# 색상 팔레트
COLORS = {
    "primary": "#6366f1",       # Indigo
    "secondary": "#8b5cf6",     # Purple
    "success": "#22c55e",       # Green
    "danger": "#ef4444",        # Red
    "warning": "#f59e0b",       # Amber
    "info": "#3b82f6",          # Blue
    "dark": "#1e293b",          # Slate 800
    "light": "#f8fafc",         # Slate 50
    "muted": "#64748b",         # Slate 500
    "background": "#0f172a",    # Slate 900
    "card": "#1e293b",          # Slate 800
    "border": "#334155",        # Slate 700
}


def apply_custom_styles() -> None:
    """커스텀 CSS 스타일 적용."""
    st.markdown("""
    <style>
    /* 전체 페이지 스타일 */
    .main {
        padding-top: 1rem;
    }

    /* 헤더 스타일 */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }

    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* 메트릭 카드 스타일 */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .metric-card .label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-card .value {
        font-size: 1.75rem;
        font-weight: 700;
        color: white;
    }

    .metric-card .value.positive { color: #22c55e; }
    .metric-card .value.negative { color: #ef4444; }
    .metric-card .value.neutral { color: #3b82f6; }

    /* 정보 카드 스타일 */
    .info-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }

    .info-card.success { border-left-color: #22c55e; }
    .info-card.warning { border-left-color: #f59e0b; }
    .info-card.danger { border-left-color: #ef4444; }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e293b;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        background-color: transparent;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }

    /* 버튼 스타일 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background-color: #1e293b;
        border-radius: 8px;
        border: 1px solid #334155;
    }

    /* DataFrame 스타일 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* 진행 카드 그리드 */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    /* 요약 통계 박스 */
    .summary-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .summary-box h3 {
        color: #e2e8f0;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }

    /* 전략 선택 카드 */
    .strategy-card {
        background: #1e293b;
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .strategy-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }

    .strategy-card.selected {
        border-color: #6366f1;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    }

    /* 통계 테이블 */
    .stats-table {
        width: 100%;
        border-collapse: collapse;
    }

    .stats-table th,
    .stats-table td {
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 1px solid #334155;
    }

    .stats-table th {
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
    }

    .stats-table td {
        color: #e2e8f0;
    }

    /* 히어로 섹션 */
    .hero-section {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
    }

    .hero-section h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    /* 피처 카드 */
    .feature-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
        transition: transform 0.2s;
    }

    .feature-card:hover {
        transform: translateY(-4px);
    }

    .feature-card h3 {
        color: #e2e8f0;
        margin-bottom: 0.75rem;
    }

    .feature-card p {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    .feature-card .icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    /* 로딩 애니메이션 */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    </style>
    """, unsafe_allow_html=True)


def metric_card(
    label: str,
    value: str,
    value_type: str = "neutral",
    delta: str | None = None,
) -> str:
    """메트릭 카드 HTML 생성.

    Args:
        label: 메트릭 라벨
        value: 메트릭 값
        value_type: 값 타입 (positive, negative, neutral)
        delta: 변화량 (선택)

    Returns:
        HTML 문자열
    """
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value {value_type}">{value}</div>
        {delta_html}
    </div>
    """


def info_card(message: str, card_type: str = "info") -> str:
    """정보 카드 HTML 생성.

    Args:
        message: 메시지 내용
        card_type: 카드 타입 (info, success, warning, danger)

    Returns:
        HTML 문자열
    """
    return f'<div class="info-card {card_type}">{message}</div>'
