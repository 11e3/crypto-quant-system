# Screenshot Guide for README

This directory contains screenshots for the main README documentation.

## Required Screenshots

Save the following screenshots to this directory:

### 1. Home Dashboard (`home_dashboard.png`)
- **Page**: Home page
- **Crop**: Main content area (remove sidebar)
- **Focus**: Welcome message, key features, supported strategies
- **Recommended size**: 1200x800px

### 2. Data Collection Interface (`data_collection.png`)
- **Page**: Data Collection page
- **Crop**: Ticker selection + interval selection sections
- **Focus**: Show multiple tickers selected, various intervals
- **Recommended size**: 1200x700px

### 3. Backtest Settings (`backtest_settings.png`)
- **Page**: Backtest page > Settings tab
- **Crop**: Full settings panel
- **Focus**: Strategy selection, parameters, trading costs, portfolio settings
- **Recommended size**: 1200x900px

### 4. Backtest Results Overview (`backtest_results.png`)
- **Page**: Backtest page > Results tab > Overview
- **Crop**: Performance metrics section
- **Focus**: CAGR, Sharpe, MDD, and other key metrics
- **Recommended size**: 1200x600px

### 5. Interactive Equity Curve (`equity_curve.png`)
- **Page**: Backtest page > Results tab > Equity Curve
- **Crop**: Just the chart area
- **Focus**: Clean equity curve with time slider
- **Recommended size**: 1200x500px

### 6. Drawdown Chart (`drawdown_chart.png`)
- **Page**: Backtest page > Results tab > Drawdown
- **Crop**: Just the chart area
- **Focus**: Underwater curve with MDD marker
- **Recommended size**: 1200x500px

### 7. Monthly Returns Heatmap (`monthly_heatmap.png`)
- **Page**: Backtest page > Results tab > Monthly Analysis
- **Crop**: Heatmap + yearly totals at bottom
- **Focus**: Color-coded monthly returns with all months visible
- **Recommended size**: 1200x600px

### 8. Yearly Returns (`yearly_returns.png`)
- **Page**: Backtest page > Results tab > Yearly Analysis
- **Crop**: Bar chart + summary statistics
- **Focus**: Year-over-year performance bars
- **Recommended size**: 1200x600px

### 9. Statistical Analysis (`statistical_analysis.png`)
- **Page**: Backtest page > Results tab > Statistics
- **Crop**: Statistical significance section
- **Focus**: Z-Score, P-Value, Skewness, Kurtosis table
- **Recommended size**: 1200x400px

### 10. Parameter Optimization (`optimization.png`)
- **Page**: Optimization page
- **Crop**: Full optimization settings
- **Focus**: Parameter ranges, search method, configuration summary
- **Recommended size**: 1200x900px

### 11. Monte Carlo Simulation (`monte_carlo.png`)
- **Page**: Analysis page > Monte Carlo
- **Crop**: Simulation configuration
- **Focus**: Strategy selection, simulation settings, number of simulations
- **Recommended size**: 1200x800px

## Cropping Guidelines

### Using the Python Script

Run the automated cropping script:

```bash
# Make sure you have the screenshots in a temp directory
uv run python scripts/crop_screenshots.py
```

### Manual Cropping (if needed)

1. **Remove sidebar**: Crop left edge to remove navigation sidebar
2. **Remove header**: Crop top edge to remove browser chrome and page title
3. **Focus on content**: Center the main content area
4. **Consistent width**: Try to maintain 1200px width for consistency
5. **Optimize size**: Use PNG format with reasonable compression
6. **Dark mode**: Use the system's dark theme for screenshots

### Crop Coordinates (approximate)

For 1920x1080 screenshots:
- **Left edge**: ~150px (remove sidebar)
- **Top edge**: ~50-100px (remove header)
- **Right edge**: ~1450px (remove empty space)
- **Bottom edge**: Depends on content

### Screenshot Tool Recommendations

**Windows**:
- Snipping Tool (Win + Shift + S)
- ShareX (advanced)
- Greenshot (free)

**Browser Extensions**:
- FireShot
- Awesome Screenshot
- Nimbus Screenshot

## Optimization

After cropping, optimize images:

```bash
# Using Python PIL
python scripts/crop_screenshots.py

# Or manually using imagemagick
magick convert input.png -quality 85 -strip output.png
```

## File Naming Convention

- Use lowercase
- Use underscores for spaces
- Descriptive names matching feature
- PNG format for quality
- No version numbers in filename

## Update Checklist

When adding new screenshots:

1. [ ] Take screenshot in dark mode
2. [ ] Crop to remove sidebar and header
3. [ ] Resize to ~1200px width
4. [ ] Optimize file size
5. [ ] Save with descriptive filename
6. [ ] Update README.md with new image reference
7. [ ] Add caption describing the screenshot
8. [ ] Verify image displays correctly in GitHub

## Quality Standards

- **Resolution**: High enough to read text clearly
- **File size**: < 500KB per image (use compression)
- **Format**: PNG (for UI screenshots with text)
- **Theme**: Consistent dark theme across all screenshots
- **Content**: Show realistic data, not empty states
- **Focus**: Highlight the specific feature being documented
