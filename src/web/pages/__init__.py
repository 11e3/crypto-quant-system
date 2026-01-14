"""Pages package.

웹 UI 페이지 모듈.
"""

from src.web.pages.analysis import render_analysis_page
from src.web.pages.backtest import render_backtest_page
from src.web.pages.optimization import render_optimization_page

__all__ = [
    "render_backtest_page",
    "render_optimization_page",
    "render_analysis_page",
]
