# Deprecation Guide

이 문서는 프로젝트에서 deprecated된 파일, 클래스, 함수에 대한 가이드를 제공합니다.

## Deprecated 항목 목록

### 1. `src/strategies/volatility_breakout/filters.py`

**상태**: Deprecated (v0.1.0)

**대체 방법**: `src.strategies.volatility_breakout.conditions` 모듈의 Condition 클래스 사용

**변경 사항**:
- `TrendFilter` → `TrendCondition`
- `NoiseFilter` → `NoiseCondition`
- `NoiseThresholdFilter` → `NoiseThresholdCondition`
- `VolatilityFilter` → `VolatilityRangeCondition`
- `VolumeFilter` → `VolumeCondition`
- `DayOfWeekFilter` → `DayOfWeekCondition`
- `MarketRegimeFilter` → `MarketRegimeCondition`

**예시**:
```python
# ❌ Deprecated
from src.strategies.volatility_breakout.filters import TrendFilter, NoiseFilter

# ✅ 권장
from src.strategies.volatility_breakout.conditions import TrendCondition, NoiseCondition
```

**참고**: 하위 호환성을 위해 별칭(aliases)이 제공되지만, 사용 시 DeprecationWarning이 발생합니다.

---

### 2. `src/execution/bot.py` - `TradingBot` 클래스

**상태**: Deprecated (v0.1.0)

**대체 방법**: `src.execution.bot_facade.TradingBotFacade` 사용

**변경 사항**:
- `TradingBot` → `TradingBotFacade`
- `TradingBot()` → `create_bot()`

**예시**:
```python
# ❌ Deprecated
from src.execution import TradingBot
bot = TradingBot(config_path=Path("config/settings.yaml"))
bot.run()

# ✅ 권장
from src.execution.bot_facade import create_bot
bot = create_bot(config_path=Path("config/settings.yaml"))
bot.run()
```

**이유**: Facade 패턴을 적용하여 더 나은 의존성 주입과 테스트 가능성을 제공합니다.

---

### 3. `src/execution/bot.py` - `main()` 함수

**상태**: Deprecated (v0.1.0)

**대체 방법**: CLI 명령어 `upbit-quant run-bot` 사용 또는 `TradingBotFacade` 직접 사용

**예시**:
```python
# ❌ Deprecated
from src.execution.bot import main
main()

# ✅ 권장 (CLI)
# upbit-quant run-bot

# ✅ 권장 (Python)
from src.execution.bot_facade import create_bot
bot = create_bot()
bot.run()
```

---

## Deprecation Warning 처리

### Python에서 경고 표시

```python
import warnings

# 모든 DeprecationWarning 표시
warnings.filterwarnings("default", category=DeprecationWarning)

# 또는 특정 모듈만
warnings.filterwarnings("default", category=DeprecationWarning, module="src.execution")
```

### 경고 무시 (권장하지 않음)

```python
import warnings

# DeprecationWarning 무시 (권장하지 않음)
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

---

## 마이그레이션 체크리스트

- [ ] `filters.py` import를 `conditions.py`로 변경
- [ ] `TrendFilter`, `NoiseFilter` 등을 `TrendCondition`, `NoiseCondition`으로 변경
- [ ] `TradingBot` 사용을 `TradingBotFacade`로 변경
- [ ] `strategy.filters.filters` 사용을 `strategy.entry_conditions.conditions`로 변경
- [ ] `remove_filter()`, `add_filter()` 사용을 `remove_entry_condition()`, `add_entry_condition()`으로 변경

---

## 추가 정보

- Deprecated 항목은 향후 버전에서 제거될 예정입니다.
- 가능한 한 빨리 새로운 API로 마이그레이션하는 것을 권장합니다.
- 문제가 있으면 이슈를 등록해주세요.
