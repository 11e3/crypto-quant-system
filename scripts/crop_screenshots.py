"""Crop screenshots for README documentation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def crop_screenshot(input_path: Path, output_path: Path, crop_box: tuple[int, int, int, int]) -> None:
    """Crop a screenshot to the specified box.

    Args:
        input_path: Path to input image
        output_path: Path to save cropped image
        crop_box: Tuple of (left, top, right, bottom) coordinates
    """
    img = Image.open(input_path)
    cropped = img.crop(crop_box)
    cropped.save(output_path, quality=85, optimize=True)
    print(f"✓ Created {output_path.name} ({cropped.width}x{cropped.height})")


def main() -> None:
    """Process all screenshots for README."""
    # Screenshot paths from the provided images
    screenshots = [
        "screenshot_home.png",
        "screenshot_data_collection.png",
        "screenshot_backtest_settings.png",
        "screenshot_backtest_results.png",
        "screenshot_equity_curve.png",
        "screenshot_drawdown.png",
        "screenshot_yearly_returns.png",
        "screenshot_statistics.png",
        "screenshot_optimization.png",
        "screenshot_monte_carlo.png",
    ]

    docs_dir = Path("docs/images")
    docs_dir.mkdir(parents=True, exist_ok=True)

    print("📸 Processing screenshots for README...\n")

    # Note: Since we don't have the actual screenshot files yet,
    # this script provides the structure for when they're available

    print(f"""
Screenshots should be saved in the repository and cropped using this script.

Expected screenshots:
{chr(10).join(f"  - {s}" for s in screenshots)}

To use this script:
1. Save screenshots to the repository root or a temp directory
2. Update the paths below to match your screenshot locations
3. Run: uv run python scripts/crop_screenshots.py

The script will create optimized, cropped images in docs/images/
""")

    # Example crop configurations (adjust based on actual screenshots)
    # Format: (left, top, right, bottom) in pixels
    crop_configs = {
        "screenshot_home.png": (150, 50, 1450, 1000),  # Remove sidebar, focus on main content
        "screenshot_backtest_settings.png": (200, 150, 1400, 950),
        "screenshot_equity_curve.png": (200, 350, 1450, 750),  # Just the chart
        "screenshot_drawdown.png": (200, 350, 1450, 750),
        "screenshot_yearly_returns.png": (200, 350, 1450, 850),
    }

    print("\nCrop configurations ready. Add actual file processing when screenshots are available.")


if __name__ == "__main__":
    main()
