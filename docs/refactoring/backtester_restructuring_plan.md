# Backtester 모듈 구조화 리팩토링 계획

**작성일**: 2026년 1월 8일  
**목표**: 1750줄 engine.py 파일을 명확한 역할별로 분리하여 유지보수성 향상

---

## 📋 현재 문제점

### 1. **파일 크기 및 복잡도**
- `engine.py`: **1750줄** - 벡터화 엔진치고는 너무 큼
- `simple_engine.py`: 400줄 - 이름이 비직관적 ("simple"이 무엇을 의미하는지 불명확)

### 2. **중복 코드**
- `engine.py`에 BacktestConfig, Trade, BacktestResult 정의
- `models.py`에도 동일한 dataclass 존재 → 중복 정의

### 3. **네이밍 문제**
- `SimpleBacktestEngine` → "simple"이 무엇을 의미? (event-driven 방식을 표현하지 못함)
- `BacktestEngine` vs `VectorizedBacktestEngine` → 혼란

---

## 🎯 리팩토링 목표

### 아키텍처 개선
```
src/backtester/
├── engine/                     # 백테스트 엔진 (NEW)
│   ├── __init__.py            # 통합 exports + backward compatibility
│   ├── event_driven.py        # EventDrivenBacktestEngine (~400줄)
│   └── vectorized.py          # VectorizedBacktestEngine (~1400줄)
├── models.py                  # 공통 dataclass (200줄) ✅
├── metrics.py                 # 성능 지표 계산 (180줄) ✅
├── __init__.py                # Package exports
└── [삭제 예정]
    ├── engine.py              # → engine/vectorized.py로 이동
    └── simple_engine.py       # → engine/event_driven.py로 이동
```

### 명확한 네이밍
| 기존 | 변경 후 | 의미 |
|------|---------|------|
| `SimpleBacktestEngine` | `EventDrivenBacktestEngine` | 이벤트 기반 (day-by-day 처리) |
| `BacktestEngine` (alias) | `VectorizedBacktestEngine` | 벡터화 방식 (numpy 기반) |

---

## 📝 단계별 실행 계획

### ✅ Phase 1: 공통 모듈 분리 (완료)
**상태**: ✅ 완료

1. ✅ `models.py` 생성
   - BacktestConfig
   - Trade
   - BacktestResult
   - 200줄, 모든 엔진에서 공유

2. ✅ `metrics.py` 생성
   - calculate_metrics()
   - calculate_trade_metrics()
   - 180줄, 성능 지표 계산 로직 중앙화

**결과**: 각 엔진에서 50+ 줄의 중복 코드 제거

---

### ✅ Phase 2: Engine 디렉토리 구조 생성 (완료)
**상태**: ✅ 완료

1. ✅ `src/backtester/engine/` 디렉토리 생성
2. ✅ `engine/__init__.py` 작성
   ```python
   from src.backtester.engine.event_driven import EventDrivenBacktestEngine
   from src.backtester.engine.vectorized import VectorizedBacktestEngine
   
   # Backward compatibility aliases
   SimpleBacktestEngine = EventDrivenBacktestEngine
   BacktestEngine = VectorizedBacktestEngine
   
   __all__ = [
       "EventDrivenBacktestEngine",
       "VectorizedBacktestEngine",
       "SimpleBacktestEngine",  # Deprecated
       "BacktestEngine",  # Deprecated
   ]
   ```

3. ✅ `engine/event_driven.py` 생성
   - simple_engine.py 내용 이동
   - 클래스명 변경: SimpleBacktestEngine → EventDrivenBacktestEngine
   - imports 업데이트 (models.py, metrics.py 사용)

---

### 🔄 Phase 3: Vectorized Engine 분리 (진행 중)
**상태**: 🔄 진행 중

**작업**:
1. `engine/vectorized.py` 생성
   - engine.py에서 VectorizedBacktestEngine 클래스만 추출
   - BacktestConfig, Trade, BacktestResult는 **제외** (models.py 사용)
   - ~1400줄 예상

2. Import 업데이트
   ```python
   # vectorized.py
   from src.backtester.models import BacktestConfig, Trade, BacktestResult
   from src.backtester.metrics import calculate_metrics
   ```

3. 파일 크기
   - 기존 engine.py: 1750줄
   - 추출 후: ~1400줄 (dataclass 정의 300줄 제거)

**주의사항**:
- run_backtest() 헬퍼 함수도 함께 이동
- 모든 메서드 시그니처 유지
- 기존 테스트가 깨지지 않도록 주의

---

### ⏳ Phase 4: Import 경로 업데이트
**상태**: ⏳ 대기 중

**영향 받는 파일들**:

#### Test Scripts (3개)
- `scripts/test_orb_simple_engine.py`
- `scripts/compare_engines.py`  
- `examples/orb_backtest.py`

**변경 전**:
```python
from src.backtester.simple_engine import SimpleBacktestEngine
```

**변경 후** (Option 1 - 권장):
```python
from src.backtester.engine import EventDrivenBacktestEngine
```

**변경 후** (Option 2 - 호환성):
```python
from src.backtester.engine import SimpleBacktestEngine  # Deprecated alias
```

#### Examples (10개 파일)
- `examples/basic_backtest.py`
- `examples/custom_strategy.py`
- `examples/live_trading_simulator.py`
- `examples/live_trading.py`
- `examples/performance_analysis.py`
- `examples/performance_benchmark.py`
- `examples/portfolio_optimization.py`
- `examples/strategy_benchmark.py`
- `examples/strategy_comparison.py`

**변경 전**:
```python
from src.backtester.engine import BacktestEngine, run_backtest
```

**변경 후**:
```python
from src.backtester.engine import VectorizedBacktestEngine, run_backtest
# Or use alias for backward compatibility:
from src.backtester.engine import BacktestEngine  # Still works
```

#### Package Init
- `src/backtester/__init__.py`

**변경 전**:
```python
from src.backtester.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestResult,
    Trade,
    run_backtest,
)
from src.backtester.simple_engine import SimpleBacktestEngine
```

**변경 후**:
```python
from src.backtester.engine import (
    EventDrivenBacktestEngine,
    VectorizedBacktestEngine,
    SimpleBacktestEngine,  # Deprecated alias
    BacktestEngine,  # Deprecated alias
    run_backtest,
)
from src.backtester.models import (
    BacktestConfig,
    BacktestResult,
    Trade,
)
```

---

### ⏳ Phase 5: 기존 파일 제거
**상태**: ⏳ 대기 중

**삭제 대상**:
1. `src/backtester/engine.py` (1750줄)
   - → `engine/vectorized.py`로 이동 완료 후
   
2. `src/backtester/simple_engine.py` (400줄)
   - → `engine/event_driven.py`로 이동 완료 후

**삭제 전 체크리스트**:
- [ ] 모든 imports 업데이트 완료
- [ ] 모든 테스트 통과 확인
- [ ] Examples 실행 확인
- [ ] Backward compatibility 작동 확인

---

### ⏳ Phase 6: 문서 업데이트
**상태**: ⏳ 대기 중

**업데이트 대상**:
1. `docs/guides/simple_backtest_engine.md`
   - 제목: "Simple Backtest Engine" → "Event-Driven Backtest Engine"
   - 클래스명 변경 반영
   - Import 경로 업데이트

2. `docs/guides/backtester_modules.md`
   - 새 디렉토리 구조 반영
   - 모듈별 역할 설명 업데이트

3. `README.md`
   - Examples 코드 업데이트
   - 새 구조 설명 추가

4. Deprecation Notices 추가
   ```python
   """
   .. deprecated:: 2026.01.08
       Use `EventDrivenBacktestEngine` instead.
       `SimpleBacktestEngine` is kept for backward compatibility.
   """
   ```

---

## 🔍 Backward Compatibility 전략

### Alias 제공
```python
# engine/__init__.py
SimpleBacktestEngine = EventDrivenBacktestEngine  # Old name
BacktestEngine = VectorizedBacktestEngine  # Old alias
```

### Import 호환성
기존 코드가 계속 작동:
```python
# Old imports still work
from src.backtester.engine import BacktestEngine
from src.backtester.simple_engine import SimpleBacktestEngine

# New imports (recommended)
from src.backtester.engine import VectorizedBacktestEngine
from src.backtester.engine import EventDrivenBacktestEngine
```

### Deprecation 경고
```python
import warnings

class SimpleBacktestEngine(EventDrivenBacktestEngine):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "SimpleBacktestEngine is deprecated. "
            "Use EventDrivenBacktestEngine instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

---

## 📊 예상 효과

### Before
```
src/backtester/
├── engine.py                  (1750줄) ❌ 너무 큼
├── simple_engine.py           (400줄)  ❌ 이름 불명확
├── models.py                  (200줄)  ✅
└── metrics.py                 (180줄)  ✅
```

### After
```
src/backtester/
├── engine/
│   ├── __init__.py            (30줄)   ✅ 명확한 exports
│   ├── event_driven.py        (400줄)  ✅ 역할 명확
│   └── vectorized.py          (1400줄) ✅ 크기 적절
├── models.py                  (200줄)  ✅ 중복 제거
└── metrics.py                 (180줄)  ✅ 중앙화
```

### 개선 효과
| 항목 | Before | After | 개선 |
|------|--------|-------|------|
| 최대 파일 크기 | 1750줄 | 1400줄 | ▼ 20% |
| 중복 dataclass | 2곳 | 1곳 | ▼ 50% |
| 네이밍 명확성 | 애매함 | 명확함 | ✅ |
| 디렉토리 구조 | 평면 | 계층적 | ✅ |
| 역할 분리 | 불명확 | 명확 | ✅ |

---

## ✅ 테스트 계획

### Unit Tests
```bash
# 모든 기존 테스트가 통과해야 함
pytest tests/backtester/ -v

# 특히 engine 관련 테스트
pytest tests/backtester/test_engine.py
pytest tests/backtester/test_vectorized_engine.py
```

### Integration Tests
```bash
# Examples 실행 확인
python examples/orb_backtest.py
python examples/basic_backtest.py
python examples/strategy_comparison.py

# Scripts 실행 확인
python scripts/test_orb_simple_engine.py
python scripts/compare_engines.py
```

### Backward Compatibility Tests
```python
# 기존 import가 여전히 작동하는지 확인
def test_backward_compatibility():
    # Old imports
    from src.backtester.engine import BacktestEngine
    from src.backtester.simple_engine import SimpleBacktestEngine
    
    # New imports
    from src.backtester.engine import VectorizedBacktestEngine
    from src.backtester.engine import EventDrivenBacktestEngine
    
    # Aliases work correctly
    assert BacktestEngine is VectorizedBacktestEngine
    assert SimpleBacktestEngine is EventDrivenBacktestEngine
```

---

## 🚀 실행 순서

### 1단계: 준비 (완료)
- [x] models.py 생성
- [x] metrics.py 생성
- [x] engine/ 디렉토리 생성
- [x] engine/__init__.py 작성
- [x] engine/event_driven.py 생성

### 2단계: Vectorized Engine 이동
- [ ] engine/vectorized.py 생성
- [ ] engine.py에서 VectorizedBacktestEngine 추출
- [ ] imports 업데이트
- [ ] 로컬 테스트

### 3단계: Import 업데이트
- [ ] src/backtester/__init__.py 업데이트
- [ ] test scripts 업데이트 (3개)
- [ ] examples 업데이트 (10개)
- [ ] 전체 테스트 실행

### 4단계: 정리
- [ ] engine.py 삭제
- [ ] simple_engine.py 삭제
- [ ] 최종 테스트 실행

### 5단계: 문서화
- [ ] 가이드 문서 업데이트 (2개)
- [ ] README 업데이트
- [ ] Deprecation 경고 추가
- [ ] CHANGELOG 작성

---

## 📌 주의사항

### 1. Git History 유지
```bash
# 파일 이동 시 git mv 사용 (history 보존)
git mv src/backtester/simple_engine.py src/backtester/engine/event_driven.py

# 대량 변경 시 커밋 분리
git commit -m "refactor: extract vectorized engine to engine/vectorized.py"
git commit -m "refactor: update imports to use new engine structure"
git commit -m "refactor: remove deprecated engine.py and simple_engine.py"
```

### 2. Breaking Changes 최소화
- 모든 기존 imports는 여전히 작동
- Alias를 통한 backward compatibility
- Deprecation warning으로 점진적 마이그레이션 유도

### 3. 테스트 커버리지 유지
```bash
# 리팩토링 전후 커버리지 비교
pytest --cov=src.backtester --cov-report=html tests/
```

---

## 🎯 성공 기준

### 필수 조건
- [ ] 모든 기존 테스트 통과
- [ ] 모든 examples 정상 실행
- [ ] Import 호환성 유지
- [ ] 파일 크기 감소 (engine.py: 1750 → 1400줄)

### 선택 조건
- [ ] 새 구조로 문서 업데이트
- [ ] Deprecation 경고 추가
- [ ] Type hint 100% 커버리지

---

## 📅 타임라인

| Phase | 작업 | 예상 시간 | 상태 |
|-------|------|-----------|------|
| 1 | 공통 모듈 분리 | 1시간 | ✅ 완료 |
| 2 | Engine 디렉토리 구조 | 30분 | ✅ 완료 |
| 3 | Vectorized 분리 | 1시간 | 🔄 진행 중 |
| 4 | Import 업데이트 | 1시간 | ⏳ 대기 |
| 5 | 기존 파일 제거 | 15분 | ⏳ 대기 |
| 6 | 문서 업데이트 | 1시간 | ⏳ 대기 |

**총 예상 시간**: 약 4.75시간

---

## 🔗 관련 문서

- [Event-Driven Engine Guide](../guides/simple_backtest_engine.md)
- [Backtester Modules Architecture](../guides/backtester_modules.md)
- [CHANGELOG](../../CHANGELOG.md)
- [Migration Guide](./migration_guide.md) (작성 예정)

---

**작성자**: GitHub Copilot  
**검토자**: TBD  
**승인자**: TBD  
**최종 업데이트**: 2026년 1월 8일
