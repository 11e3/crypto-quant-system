# Screenshot renaming script
# This script renames the Korean-named screenshot files to English names for README

$imagesDir = "c:\Users\moons\dev\crypto-quant-system\docs\images"

# Array of old filenames (in order from your screenshots)
$oldNames = @(
    "스크린샷 2026-01-16 070944.png",  # 1. Home Dashboard
    "스크린샷 2026-01-16 072109.png",  # 2. Data Collection
    "스크린샷 2026-01-16 082021.png",  # 3. Backtest Settings (MinimalVBO - skip?)
    "스크린샷 2026-01-16 082454.png",  # 4. Backtest Settings (VanillaVBO)
    "스크린샷 2026-01-16 083433.png",  # 5. Backtest Results
    "스크린샷 2026-01-16 083831.png",  # 6. Equity Curve
    "스크린샷 2026-01-16 084044.png",  # 7. Drawdown
    "스크린샷 2026-01-16 102851.png",  # 8. Yearly Returns
    "스크린샷 2026-01-16 103323.png"   # 9. Statistics or Optimization or Monte Carlo
)

# Corresponding new filenames
# Edit these to match your screenshots
$newNames = @(
    "home_dashboard.png",
    "data_collection.png",
    "temp_minimal.png",           # Will skip this one
    "backtest_settings.png",
    "backtest_results.png",
    "equity_curve.png",
    "drawdown_chart.png",
    "yearly_returns.png",
    "statistical_analysis.png"    # Or optimization.png or monte_carlo.png - check which one
)

Write-Host "Screenshot Renaming Preview" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

for ($i = 0; $i -lt $oldNames.Length; $i++) {
    $oldPath = Join-Path $imagesDir $oldNames[$i]
    $newPath = Join-Path $imagesDir $newNames[$i]

    if (Test-Path $oldPath) {
        Write-Host "[$($i+1)] " -NoNewline -ForegroundColor Yellow
        Write-Host "Will rename:" -ForegroundColor White
        Write-Host "    FROM: $($oldNames[$i])" -ForegroundColor Gray
        Write-Host "    TO:   $($newNames[$i])" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[$($i+1)] " -NoNewline -ForegroundColor Red
        Write-Host "File not found: $($oldNames[$i])" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""
$response = Read-Host "Do you want to proceed with renaming? (y/n)"

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "Renaming files..." -ForegroundColor Cyan

    for ($i = 0; $i -lt $oldNames.Length; $i++) {
        $oldPath = Join-Path $imagesDir $oldNames[$i]
        $newPath = Join-Path $imagesDir $newNames[$i]

        if (Test-Path $oldPath) {
            # Skip the minimal VBO screenshot
            if ($newNames[$i] -eq "temp_minimal.png") {
                Write-Host "Skipping: $($oldNames[$i])" -ForegroundColor Yellow
                continue
            }

            Rename-Item -Path $oldPath -NewName $newNames[$i]
            Write-Host "✓ Renamed: $($newNames[$i])" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "Done! Files renamed successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "Current files in docs/images/:" -ForegroundColor Cyan
    Get-ChildItem $imagesDir -Filter "*.png" | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }

} else {
    Write-Host "Renaming cancelled." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
