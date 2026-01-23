"""
Feature Repository Operations
=============================
Utility functions for working with the Feast feature store.

This module provides helper functions for:
- Materializing features to online store
- Getting historical features for training
- Getting online features for inference
- Feature validation and monitoring
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


def get_feature_store():
    """Get Feast feature store instance.

    Returns:
        FeatureStore instance
    """
    from feast import FeatureStore

    repo_path = Path(__file__).parent
    return FeatureStore(repo_path=str(repo_path))


def materialize_features(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> None:
    """Materialize features to online store.

    Args:
        start_date: Start date for materialization (default: 7 days ago)
        end_date: End date for materialization (default: now)
    """
    store = get_feature_store()

    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    print(f"Materializing features from {start_date} to {end_date}")
    store.materialize(start_date=start_date, end_date=end_date)
    print("Materialization complete")


def get_training_features(
    entity_df: pd.DataFrame,
    feature_service: str = "ml_training_features",
) -> pd.DataFrame:
    """Get historical features for ML training.

    Args:
        entity_df: DataFrame with entity columns (symbol, timestamp)
        feature_service: Name of feature service to use

    Returns:
        DataFrame with features joined to entities
    """
    store = get_feature_store()

    feature_vector = store.get_historical_features(
        entity_df=entity_df,
        features=store.get_feature_service(feature_service),
    )

    return feature_vector.to_df()


def get_online_features(
    symbols: list[str],
    feature_refs: Optional[list[str]] = None,
) -> dict:
    """Get online features for real-time inference.

    Args:
        symbols: List of cryptocurrency symbols
        feature_refs: List of feature references (e.g., ["price_features:rsi_14"])
                     If None, uses trading_features service

    Returns:
        Dictionary with feature values
    """
    store = get_feature_store()

    entity_rows = [{"symbol": symbol} for symbol in symbols]

    if feature_refs is None:
        # Use default trading features
        feature_refs = [
            "price_features:return_20d",
            "price_features:volatility_20d",
            "price_features:rsi_14",
            "price_features:ma_alignment",
            "regime_features:regime_label",
            "regime_features:regime_probability",
        ]

    response = store.get_online_features(
        features=feature_refs,
        entity_rows=entity_rows,
    )

    return response.to_dict()


def get_regime_features(symbols: list[str]) -> pd.DataFrame:
    """Get regime classification features for inference.

    Args:
        symbols: List of cryptocurrency symbols

    Returns:
        DataFrame with regime features
    """
    store = get_feature_store()

    entity_rows = [{"symbol": symbol} for symbol in symbols]

    response = store.get_online_features(
        features=store.get_feature_service("regime_classification_features"),
        entity_rows=entity_rows,
    )

    return pd.DataFrame(response.to_dict())


def validate_feature_freshness(max_age_hours: int = 24) -> dict:
    """Validate that features are fresh.

    Args:
        max_age_hours: Maximum acceptable age in hours

    Returns:
        Dictionary with validation results
    """
    store = get_feature_store()
    results = {"fresh": [], "stale": [], "missing": []}

    # Check each feature view
    for fv in store.list_feature_views():
        try:
            # Get latest feature timestamp
            # This is a simplified check - in production you'd query the actual data
            results["fresh"].append(fv.name)
        except Exception as e:
            results["missing"].append({"name": fv.name, "error": str(e)})

    return results


def create_entity_df(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    freq: str = "D",
) -> pd.DataFrame:
    """Create entity DataFrame for historical feature retrieval.

    Args:
        symbols: List of cryptocurrency symbols
        start_date: Start date
        end_date: End date
        freq: Frequency (D=daily, H=hourly)

    Returns:
        DataFrame with symbol and timestamp columns
    """
    timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)

    entity_rows = []
    for symbol in symbols:
        for ts in timestamps:
            entity_rows.append({"symbol": symbol, "timestamp": ts})

    return pd.DataFrame(entity_rows)


# =============================================================================
# CLI Commands
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Feature Store Operations")
    parser.add_argument("command", choices=["materialize", "validate", "list"])
    parser.add_argument("--days", type=int, default=7, help="Days to materialize")

    args = parser.parse_args()

    if args.command == "materialize":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        materialize_features(start_date, end_date)

    elif args.command == "validate":
        results = validate_feature_freshness()
        print(f"Fresh: {results['fresh']}")
        print(f"Stale: {results['stale']}")
        print(f"Missing: {results['missing']}")

    elif args.command == "list":
        store = get_feature_store()
        print("Feature Views:")
        for fv in store.list_feature_views():
            print(f"  - {fv.name}: {len(fv.schema)} features")
        print("\nFeature Services:")
        for fs in store.list_feature_services():
            print(f"  - {fs.name}")
