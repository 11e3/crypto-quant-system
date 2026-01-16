@echo off
chcp 65001 >nul
echo ========================================
echo Screenshot Renaming Script
echo ========================================
echo.

cd /d "c:\Users\moons\dev\crypto-quant-system\docs\images"

echo Renaming screenshots...
echo.

REM Home Dashboard
if exist "스크린샷 2026-01-16 070944.png" (
    ren "스크린샷 2026-01-16 070944.png" "home_dashboard.png"
    echo ✓ home_dashboard.png
)

REM Data Collection
if exist "스크린샷 2026-01-16 072109.png" (
    ren "스크린샷 2026-01-16 072109.png" "data_collection.png"
    echo ✓ data_collection.png
)

REM Backtest Settings (use VanillaVBO, not MinimalVBO)
if exist "스크린샷 2026-01-16 082454.png" (
    ren "스크린샷 2026-01-16 082454.png" "backtest_settings.png"
    echo ✓ backtest_settings.png
)

REM Backtest Results
if exist "스크린샷 2026-01-16 083433.png" (
    ren "스크린샷 2026-01-16 083433.png" "backtest_results.png"
    echo ✓ backtest_results.png
)

REM Equity Curve
if exist "스크린샷 2026-01-16 083831.png" (
    ren "스크린샷 2026-01-16 083831.png" "equity_curve.png"
    echo ✓ equity_curve.png
)

REM Drawdown Chart
if exist "스크린샷 2026-01-16 084044.png" (
    ren "스크린샷 2026-01-16 084044.png" "drawdown_chart.png"
    echo ✓ drawdown_chart.png
)

REM Yearly Returns
if exist "스크린샷 2026-01-16 102851.png" (
    ren "스크린샷 2026-01-16 102851.png" "yearly_returns.png"
    echo ✓ yearly_returns.png
)

REM Statistical Analysis
if exist "스크린샷 2026-01-16 103323.png" (
    ren "스크린샷 2026-01-16 103323.png" "statistical_analysis.png"
    echo ✓ statistical_analysis.png
)

echo.
echo ========================================
echo Renaming complete!
echo ========================================
echo.
echo Current PNG files:
dir /b *.png
echo.

pause
