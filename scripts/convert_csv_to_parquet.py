"""
Script entry point for CSV to Parquet conversion.

This script uses the conversion utilities from src.data.converters.
"""

from pathlib import Path

from src.config import DATA_DIR
from src.data.converters import convert_csv_directory
from src.utils.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main() -> None:
    """Main entry point for CSV to parquet conversion."""
    # Define paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "data" / "upbit"
    output_dir = DATA_DIR / "raw"

    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return

    logger.info(f"Converting CSV files from {source_dir} to {output_dir}")
    processed_count = convert_csv_directory(source_dir, output_dir)
    logger.info(f"Conversion complete. Total files converted: {processed_count}")


if __name__ == "__main__":
    main()
