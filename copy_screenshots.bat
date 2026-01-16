@echo off
REM Screenshot copy helper script
REM Edit the SOURCE_DIR to match your screenshot location

SET SOURCE_DIR=C:\Users\moons\Pictures\screenshots
SET DEST_DIR=c:\Users\moons\dev\crypto-quant-system\docs\images

echo Copying screenshots to docs/images/...
echo.

REM Copy and rename screenshots
REM Edit the source filenames to match your actual screenshot names

copy "%SOURCE_DIR%\screenshot1.png" "%DEST_DIR%\home_dashboard.png"
copy "%SOURCE_DIR%\screenshot2.png" "%DEST_DIR%\data_collection.png"
copy "%SOURCE_DIR%\screenshot3.png" "%DEST_DIR%\backtest_settings.png"
copy "%SOURCE_DIR%\screenshot4.png" "%DEST_DIR%\backtest_results.png"
copy "%SOURCE_DIR%\screenshot5.png" "%DEST_DIR%\equity_curve.png"
copy "%SOURCE_DIR%\screenshot6.png" "%DEST_DIR%\drawdown_chart.png"
copy "%SOURCE_DIR%\screenshot7.png" "%DEST_DIR%\yearly_returns.png"
copy "%SOURCE_DIR%\screenshot8.png" "%DEST_DIR%\statistical_analysis.png"
copy "%SOURCE_DIR%\screenshot9.png" "%DEST_DIR%\optimization.png"
copy "%SOURCE_DIR%\screenshot10.png" "%DEST_DIR%\monte_carlo.png"

echo.
echo Done! Screenshots copied to docs/images/
echo.
echo Don't forget to capture the Monthly Heatmap screenshot!
pause
