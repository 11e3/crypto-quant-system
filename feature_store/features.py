"""
Feature Definitions for Crypto Trading Platform
================================================
This module defines all features used in the crypto trading platform.

Features are organized into feature views:
1. price_features - Price-based technical indicators
2. volume_features - Volume-based indicators
3. regime_features - Market regime classification features
4. trading_signals - Trading signal features

Usage:
    from feast import FeatureStore
    store = FeatureStore(repo_path=".")

    # Get historical features for training
    features = store.get_historical_features(
        entity_df=entity_df,
        features=["price_features:return_20d", "price_features:volatility"],
    )

    # Get online features for inference
    features = store.get_online_features(
        features=["price_features:return_20d"],
        entity_rows=[{"symbol": "BTC"}],
    )
"""

from datetime import timedelta

from feast import Entity, Feature, FeatureView, Field, FileSource, ValueType
from feast.types import Float32, Float64, Int64, String


# =============================================================================
# Entities
# =============================================================================

# Symbol entity - represents a cryptocurrency
symbol_entity = Entity(
    name="symbol",
    description="Cryptocurrency symbol (e.g., BTC, ETH)",
    value_type=ValueType.STRING,
    join_keys=["symbol"],
)


# =============================================================================
# Data Sources
# =============================================================================

# Price features source (from processed Parquet files)
price_source = FileSource(
    name="price_features_source",
    path="../data/processed/features/*.parquet",
    timestamp_field="timestamp",
    description="Price-based technical indicators calculated from OHLCV data",
)

# Regime labels source
regime_source = FileSource(
    name="regime_labels_source",
    path="../data/processed/regime_labels.parquet",
    timestamp_field="timestamp",
    description="Market regime classification labels",
)

# Trading signals source
signals_source = FileSource(
    name="trading_signals_source",
    path="../data/processed/trading_signals.parquet",
    timestamp_field="timestamp",
    description="Trading signals from VBO strategy",
)


# =============================================================================
# Feature Views
# =============================================================================

# Price Features View
price_features = FeatureView(
    name="price_features",
    description="Price-based technical indicators for regime classification",
    entities=[symbol_entity],
    ttl=timedelta(days=1),
    schema=[
        # Returns
        Field(name="return_1d", dtype=Float64, description="1-day return"),
        Field(name="return_5d", dtype=Float64, description="5-day return"),
        Field(name="return_20d", dtype=Float64, description="20-day return"),

        # Moving Averages
        Field(name="ma_5", dtype=Float64, description="5-day moving average"),
        Field(name="ma_20", dtype=Float64, description="20-day moving average"),
        Field(name="ma_60", dtype=Float64, description="60-day moving average"),

        # MA Ratios
        Field(name="ma_5_20_ratio", dtype=Float64, description="MA5/MA20 ratio"),
        Field(name="ma_20_60_ratio", dtype=Float64, description="MA20/MA60 ratio"),
        Field(name="price_ma_20_ratio", dtype=Float64, description="Price/MA20 ratio"),

        # Volatility
        Field(name="volatility_20d", dtype=Float64, description="20-day volatility"),
        Field(name="volatility_60d", dtype=Float64, description="60-day volatility"),

        # RSI
        Field(name="rsi_14", dtype=Float64, description="14-day RSI"),

        # Bollinger Bands
        Field(name="bb_width", dtype=Float64, description="Bollinger Band width"),
        Field(name="bb_position", dtype=Float64, description="Position within BB"),

        # ATR
        Field(name="atr_14", dtype=Float64, description="14-day ATR"),
        Field(name="atr_ratio", dtype=Float64, description="ATR/Price ratio"),

        # Trend
        Field(name="ma_alignment", dtype=Float64, description="MA alignment score"),
    ],
    source=price_source,
    online=True,
    tags={"team": "ml", "category": "price"},
)


# Volume Features View
volume_features = FeatureView(
    name="volume_features",
    description="Volume-based indicators",
    entities=[symbol_entity],
    ttl=timedelta(days=1),
    schema=[
        Field(name="volume_ma_20", dtype=Float64, description="20-day volume MA"),
        Field(name="volume_ratio", dtype=Float64, description="Volume/MA ratio"),
        Field(name="volume_trend", dtype=Float64, description="Volume trend indicator"),
    ],
    source=price_source,
    online=True,
    tags={"team": "ml", "category": "volume"},
)


# Regime Features View
regime_features = FeatureView(
    name="regime_features",
    description="Market regime classification features and labels",
    entities=[symbol_entity],
    ttl=timedelta(days=1),
    schema=[
        Field(name="regime_label", dtype=String, description="Current regime (BULL/BEAR/SIDEWAYS)"),
        Field(name="regime_probability", dtype=Float64, description="Regime classification probability"),
        Field(name="regime_duration", dtype=Int64, description="Days in current regime"),
    ],
    source=regime_source,
    online=True,
    tags={"team": "ml", "category": "regime"},
)


# Trading Signals View
trading_signals = FeatureView(
    name="trading_signals",
    description="VBO trading signals",
    entities=[symbol_entity],
    ttl=timedelta(hours=1),  # More frequent updates for trading
    schema=[
        Field(name="target_price", dtype=Float64, description="VBO target entry price"),
        Field(name="can_buy", dtype=Int64, description="Buy signal (1=yes, 0=no)"),
        Field(name="should_sell", dtype=Int64, description="Sell signal (1=yes, 0=no)"),
        Field(name="signal_strength", dtype=Float64, description="Signal confidence score"),
    ],
    source=signals_source,
    online=True,
    tags={"team": "trading", "category": "signals"},
)


# =============================================================================
# Feature Services (for grouping features)
# =============================================================================

from feast import FeatureService

# ML Training Feature Service
ml_training_service = FeatureService(
    name="ml_training_features",
    description="Features used for ML model training",
    features=[
        price_features[["return_20d", "volatility_20d", "rsi_14", "ma_alignment", "bb_position"]],
        volume_features[["volume_ratio"]],
    ],
    tags={"team": "ml", "purpose": "training"},
)

# Real-time Trading Feature Service
trading_service = FeatureService(
    name="trading_features",
    description="Features used for real-time trading decisions",
    features=[
        price_features[["ma_5_20_ratio", "rsi_14", "atr_ratio"]],
        volume_features[["volume_ratio"]],
        trading_signals,
        regime_features[["regime_label", "regime_probability"]],
    ],
    tags={"team": "trading", "purpose": "inference"},
)

# Regime Classification Feature Service
regime_classification_service = FeatureService(
    name="regime_classification_features",
    description="Features used for regime classification model",
    features=[
        price_features[["return_20d", "volatility_20d", "ma_alignment", "rsi_14", "bb_position"]],
    ],
    tags={"team": "ml", "purpose": "regime_classification"},
)
