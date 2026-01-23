# Feature Store

Feast-based feature store for the crypto trading platform.

## Overview

This feature store provides:
- **Offline features** for ML model training
- **Online features** for real-time inference
- **Feature versioning** and lineage tracking
- **Feature sharing** across projects

## Quick Start

```bash
# Install Feast
pip install feast

# Apply feature definitions
cd feature_store
feast apply

# Materialize features to online store
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

## Feature Views

| Feature View | Description | TTL | Online |
|--------------|-------------|-----|--------|
| `price_features` | Price-based technical indicators | 1 day | Yes |
| `volume_features` | Volume-based indicators | 1 day | Yes |
| `regime_features` | Market regime labels | 1 day | Yes |
| `trading_signals` | VBO trading signals | 1 hour | Yes |

## Feature Services

| Service | Purpose | Features |
|---------|---------|----------|
| `ml_training_features` | ML model training | return_20d, volatility, rsi, ma_alignment |
| `trading_features` | Real-time trading | signals, regime, price indicators |
| `regime_classification_features` | Regime model | Ultra-5 features |

## Usage

### Get Historical Features (Training)

```python
from feature_repo import get_training_features, create_entity_df
from datetime import datetime

# Create entity DataFrame
entity_df = create_entity_df(
    symbols=["BTC", "ETH"],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1),
)

# Get features
features = get_training_features(entity_df, "ml_training_features")
```

### Get Online Features (Inference)

```python
from feature_repo import get_online_features

features = get_online_features(
    symbols=["BTC", "ETH"],
    feature_refs=["price_features:rsi_14", "regime_features:regime_label"],
)
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Data Sources  │────>│   Feature Store  │────>│   Consumers     │
│   (Parquet)     │     │   (Feast)        │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────▼─────┐       ┌───────▼───────┐
              │  Offline  │       │    Online     │
              │  Store    │       │    Store      │
              │ (Parquet) │       │   (SQLite)    │
              └───────────┘       └───────────────┘
```

## Data Flow

1. **Airflow DAG** calculates features from raw OHLCV data
2. **Feature Store** registers and manages features
3. **ML Pipeline** retrieves historical features for training
4. **Trading Bot** retrieves online features for inference
