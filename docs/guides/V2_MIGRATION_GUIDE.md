# V2 Module Migration Guide

**Status**: ⚠️ v2 modules are deprecated as of 2026-01-08  
**Removal Date**: v2.0.0 (planned Q2 2026)  
**Migration Deadline**: 3-6 months (Q1 2026)

## Overview

Phase 2 v2 modules (`vbo_v2.py`, `indicators_v2.py`, `slippage_model_v2.py`) introduced improved features but created code duplication. All v2 functionality has been integrated into the main modules with feature flags for backward compatibility.

## Why Migrate?

1. **Single Source of Truth**: Maintain one codebase instead of two
2. **Git-based Versioning**: Use Git instead of filename suffixes
3. **Backward Compatible**: Existing code works without changes
4. **Future-Proof**: v2 modules will be removed in v2.0.0

## Migration Steps

### 1. VanillaVBO_v2 → VanillaVBO with Flags

**Before (deprecated)**:
```python
from src.strategies.volatility_breakout.vbo_v2 import VanillaVBO_v2

strategy = VanillaVBO_v2(
    name="MyStrategy",
    sma_period=4,
    trend_sma_period=8,
    # ... other parameters
)
```

**After (recommended)**:
```python
from src.strategies.volatility_breakout.vbo import VanillaVBO

strategy = VanillaVBO(
    name="MyStrategy",
    sma_period=4,
    trend_sma_period=8,
    # Enable Phase 2 improvements
    use_improved_noise=True,     # ATR-normalized noise
    use_adaptive_k=True,          # Dynamic K-value
    atr_period=14,                # ATR calculation period
    base_k=0.5,                   # Base K value
)
```

### 2. ImprovedNoiseIndicator → Function-based API

**Before (deprecated)**:
```python
from src.utils.indicators_v2 import ImprovedNoiseIndicator

noise_indicator = ImprovedNoiseIndicator(atr_period=14)
atr = noise_indicator.calculate_atr(df)
natr = noise_indicator.calculate_natr(df)
short_noise, long_noise = noise_indicator.calculate_adaptive_noise(df)
```

**After (recommended)**:
```python
from src.utils.indicators import (
    atr,
    calculate_natr,
    calculate_adaptive_noise,
)

atr_values = atr(df["high"], df["low"], df["close"], period=14)
natr = calculate_natr(df["high"], df["low"], df["close"], period=14)
short_noise, long_noise = calculate_adaptive_noise(
    df["high"], df["low"], df["close"], 
    short_period=4, 
    long_period=8,
    atr_period=14
)
```

### 3. AdaptiveKValue → calculate_adaptive_k_value()

**Before (deprecated)**:
```python
from src.utils.indicators_v2 import AdaptiveKValue

k_calculator = AdaptiveKValue(base_k=0.5)
k_values = k_calculator.calculate_k_value(df)
```

**After (recommended)**:
```python
from src.utils.indicators import calculate_adaptive_k_value

k_values = calculate_adaptive_k_value(
    df["high"], 
    df["low"], 
    df["close"],
    base_k=0.5,
    atr_period=14
)
```

### 4. apply_improved_indicators() → add_improved_indicators()

**Before (deprecated)**:
```python
from src.utils.indicators_v2 import apply_improved_indicators

df = apply_improved_indicators(df, short_period=4, long_period=8)
```

**After (recommended)**:
```python
from src.utils.indicators import add_improved_indicators

df = add_improved_indicators(
    df, 
    short_period=4, 
    long_period=8,
    atr_period=14,
    base_k=0.5
)
```

### 5. DynamicSlippageModel (slippage_model_v2)

**Status**: Will be moved to main `slippage_model.py` in future release

**Current Workaround**: Continue using `slippage_model_v2` with deprecation warning  
**Planned**: Integration into main slippage_model module (Q2 2026)

```python
# Current (with deprecation warning)
from src.backtester.slippage_model_v2 import DynamicSlippageModel

# Future (planned for v2.0.0)
from src.backtester.slippage_model import DynamicSlippageModel
```

## Feature Flags Reference

### VanillaVBO Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `use_improved_noise` | `False` | Use ATR-normalized noise (Phase 2) |
| `use_adaptive_k` | `False` | Use dynamic K-value adjustment (Phase 2) |
| `atr_period` | `14` | ATR calculation period |
| `base_k` | `0.5` | Base K value for adaptive calculation |

**Example Configurations**:

```python
# Phase 1 (Original)
strategy = VanillaVBO()

# Phase 2 (Full v2 features)
strategy = VanillaVBO(
    use_improved_noise=True,
    use_adaptive_k=True
)

# Custom (Selective features)
strategy = VanillaVBO(
    use_improved_noise=True,    # Enable only improved noise
    use_adaptive_k=False,        # Keep original K-value
    atr_period=20                # Custom ATR period
)
```

## Scripts Migration

### Affected Scripts (8 files)

1. `scripts/debug_bootstrap.py`
2. `scripts/real_time_monitor.py`
3. `scripts/run_phase1_real_data.py`
4. `scripts/run_phase1_revalidation.py`
5. `scripts/run_phase2_integration.py`
6. `scripts/run_phase3_statistical_reliability.py`
7. `scripts/test_bootstrap_stability.py`
8. `scripts/test_sl_tp.py`

**Migration Pattern**:

```python
# Find
from src.strategies.volatility_breakout.vbo_v2 import VanillaVBO_v2
strategy = VanillaVBO_v2(...)

# Replace with
from src.strategies.volatility_breakout.vbo import VanillaVBO
strategy = VanillaVBO(
    use_improved_noise=True,
    use_adaptive_k=True,
    ...
)
```

## Testing Your Migration

### 1. Import Test
```python
# Should emit DeprecationWarning
from src.strategies.volatility_breakout.vbo_v2 import VanillaVBO_v2

# Should work without warning
from src.strategies.volatility_breakout.vbo import VanillaVBO
```

### 2. Behavior Test
```python
import pandas as pd
from src.strategies.volatility_breakout.vbo import VanillaVBO

# Create test data
df = pd.DataFrame({
    'open': [100] * 20,
    'high': [102] * 20,
    'low': [98] * 20,
    'close': [101] * 20,
    'volume': [1000] * 20
})

# Test standard mode
s1 = VanillaVBO()
r1 = s1.calculate_indicators(df)

# Test v2 mode
s2 = VanillaVBO(use_improved_noise=True, use_adaptive_k=True)
r2 = s2.calculate_indicators(df)

# Verify
assert 'target' in r1.columns
assert 'k_value_adaptive' in r2.columns
assert 'short_noise_adaptive' in r2.columns
print("Migration successful!")
```

### 3. Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run VBO-specific tests
pytest tests/ -k "vbo or vanilla" -v
```

## Benefits of Migration

### Before (v2 modules)
- ❌ Code duplication (742 lines duplicated)
- ❌ Bug fixes need two changes
- ❌ Version confusion (which file to use?)
- ❌ Git history split across files

### After (feature flags)
- ✅ Single source of truth
- ✅ Bugs fixed once
- ✅ Clear feature activation
- ✅ Unified Git history
- ✅ Backward compatible
- ✅ Gradual adoption

## Timeline

```
2026-01-08: v2 modules marked deprecated
2026-01-15: Documentation published
2026-02-01: Begin script migration
2026-03-01: CI warnings for v2 usage
2026-04-01: Migration deadline reminder
Q2 2026:    v2.0.0 release (v2 modules removed)
```

## Deprecation Warnings

When you import v2 modules, you'll see:

```
DeprecationWarning: vbo_v2 module is deprecated and will be removed in v2.0.0.
Use VanillaVBO with use_improved_noise=True, use_adaptive_k=True, 
use_dynamic_slippage=True, and use_cost_calculator=True instead.
```

**To silence warnings temporarily**:
```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

**However**, we recommend migrating instead of silencing!

## Getting Help

- **Documentation**: `docs/planning/V2_MODULE_CONSOLIDATION_PLAN.md`
- **Code Examples**: `examples/` directory
- **Issues**: Create GitHub issue with `migration` label
- **Questions**: Team discussion in #crypto-quant channel

## FAQ

### Q: Can I use both v2 modules and feature flags?
**A**: Yes, but not recommended. Choose one approach for consistency.

### Q: Will my existing code break immediately?
**A**: No. v2 modules will work until v2.0.0 (with deprecation warnings).

### Q: What if I don't migrate?
**A**: Code will break when v2 modules are removed in v2.0.0.

### Q: Is there performance difference?
**A**: No. Feature flags have zero overhead when disabled.

### Q: Can I mix Phase 1 and Phase 2 features?
**A**: Yes! Feature flags allow selective adoption:
```python
VanillaVBO(
    use_improved_noise=True,   # Use Phase 2 noise
    use_adaptive_k=False       # Use Phase 1 K-value
)
```

### Q: How do I know which features are Phase 2?
**A**: All flags starting with `use_*` are Phase 2 features:
- `use_improved_noise` → ATR-normalized noise
- `use_adaptive_k` → Dynamic K-value
- `use_dynamic_slippage` → (planned) Market-aware slippage
- `use_cost_calculator` → (planned) Advanced cost modeling

## Appendix: Full API Mapping

### indicators_v2 → indicators

| v2 Class/Method | Main Module Function |
|----------------|---------------------|
| `ImprovedNoiseIndicator.calculate_atr()` | `atr()` |
| `ImprovedNoiseIndicator.calculate_natr()` | `calculate_natr()` |
| `ImprovedNoiseIndicator.calculate_volatility_regime()` | `calculate_volatility_regime()` |
| `ImprovedNoiseIndicator.calculate_adaptive_noise()` | `calculate_adaptive_noise()` |
| `ImprovedNoiseIndicator.calculate_noise_ratio()` | `calculate_noise_ratio()` |
| `AdaptiveKValue.calculate_k_value()` | `calculate_adaptive_k_value()` |
| `apply_improved_indicators()` | `add_improved_indicators()` |

### vbo_v2 → vbo

| v2 Module | Main Module | Feature Flags |
|-----------|-------------|---------------|
| `VanillaVBO_v2` | `VanillaVBO` | `use_improved_noise=True`<br>`use_adaptive_k=True` |

### slippage_model_v2 → slippage_model

| v2 Module | Status |
|-----------|--------|
| `DynamicSlippageModel` | Planned for main module (Q2 2026) |
| `MarketCondition` | Planned for main module (Q2 2026) |

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-08  
**Authors**: Code Quality Review Team  
**Status**: Active
