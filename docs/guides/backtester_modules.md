# Backtester 모듈 구조

백테스팅 엔진의 모듈화된 구조입니다.

## 파일 구조

```
src/backtester/
├── __init__.py           # 패키지 exports
├── models.py             # 데이터 모델 (BacktestConfig, Trade, BacktestResult)
├── metrics.py            # 성능 메트릭 계산
├── engine.py             # VectorizedBacktestEngine (고속, VBO 전용)
├── simple_engine.py      # SimpleBacktestEngine (범용, Event-driven)
├── report.py             # 리포트 생성
├── optimization.py       # 파라미터 최적화
├── monte_carlo.py        # Monte Carlo 시뮬레이션
├── walk_forward.py       # Walk-Forward 분석
└── parallel.py           # 병렬 백테스트
```

## 모듈 설명

### models.py
**공통 데이터 구조**

- `BacktestConfig`: 백테스트 설정
  - initial_capital, fee_rate, slippage_rate
  - max_slots, position_sizing
  - stop_loss_pct, take_profit_pct, trailing_stop_pct

- `Trade`: 거래 기록
  - ticker, entry_date, entry_price
  - exit_date, exit_price, amount
  - pnl, pnl_pct, exit_reason

- `BacktestResult`: 백테스트 결과
  - 성능 지표 (CAGR, MDD, Sharpe, Calmar)
  - 거래 통계 (total_trades, win_rate, profit_factor)
  - 시계열 데이터 (equity_curve, dates)

### metrics.py
**성능 메트릭 계산**

- `calculate_metrics()`: 백테스트 결과에서 모든 메트릭 계산
  - CAGR, MDD, Sharpe Ratio, Calmar Ratio
  - 거래 통계 (승률, Profit Factor)
  - 포트폴리오 리스크 메트릭

- `calculate_trade_metrics()`: 거래별 상세 통계
  - 평균 수익/손실
  - 최대 수익/손실
  - 승률, Profit Factor

### engine.py
**VectorizedBacktestEngine**

- 고속 벡터화 처리 (pandas/numpy)
- VBO 전략 전용
- 복잡한 포트폴리오 최적화
- 대량 데이터 분석용

### simple_engine.py
**SimpleBacktestEngine**

- Event-driven 방식 (날짜별 순회)
- 모든 전략과 호환
- 명확한 로직, 디버깅 용이
- 전략 개발/테스트용

## 사용 예제

### 기본 사용

```python
from src.backtester.models import BacktestConfig
from src.backtester.simple_engine import SimpleBacktestEngine
from src.strategies.opening_range_breakout.orb import ORBStrategy

# 설정
config = BacktestConfig(
    initial_capital=10_000_000,
    fee_rate=0.0005,
    max_slots=4,
    trailing_stop_pct=0.05,
)

# 전략
strategy = ORBStrategy(
    breakout_mode="atr",
    k_multiplier=0.5,
)

# 백테스트
engine = SimpleBacktestEngine(config)
result = engine.run(strategy, data_files)

# 결과
print(result.summary())
print(f"Trades: {result.total_trades}")
print(f"CAGR: {result.cagr:.2f}%")
```

### 메트릭 직접 계산

```python
from src.backtester.metrics import calculate_metrics

result = calculate_metrics(
    equity_curve=equity_curve,
    dates=dates,
    trades=trades_list,
    config=config,
    strategy_name="MyStrategy",
)
```

### 모델 재사용

```python
from src.backtester.models import Trade

# 수동으로 Trade 생성
trade = Trade(
    ticker="KRW-BTC",
    entry_date=date(2023, 1, 1),
    entry_price=30_000_000,
    exit_date=date(2023, 1, 10),
    exit_price=35_000_000,
    amount=0.1,
    pnl=500_000,
    pnl_pct=16.67,
    exit_reason="trailing_stop",
)

print(f"Trade closed: {trade.is_closed}")
```

## 장점

### 1. 코드 재사용성
- 공통 데이터 모델을 여러 엔진에서 공유
- 메트릭 계산 로직 중복 제거
- 쉬운 확장 (새로운 엔진 추가)

### 2. 테스트 용이성
- 각 모듈을 독립적으로 테스트
- Mock 데이터로 메트릭 계산 테스트
- 엔진 간 결과 비교 간편

### 3. 유지보수성
- 명확한 책임 분리
- 버그 수정이 간단
- 새로운 메트릭 추가 용이

### 4. 하위 호환성
- `__init__.py`에서 기존 import 지원
- 기존 코드 수정 불필요

```python
# 기존 방식 (여전히 작동)
from src.backtester.engine import BacktestConfig

# 새로운 방식 (권장)
from src.backtester.models import BacktestConfig
```

## 마이그레이션 가이드

### 기존 코드 업데이트

**Before:**
```python
from src.backtester.engine import BacktestConfig, Trade, BacktestResult
```

**After (권장):**
```python
from src.backtester.models import BacktestConfig, Trade, BacktestResult
```

또는 패키지 레벨에서 import:
```python
from src.backtester import BacktestConfig, Trade, BacktestResult
```

### SimpleBacktestEngine 추가

**기존:**
```python
from src.backtester.engine import VectorizedBacktestEngine

engine = VectorizedBacktestEngine(config)
result = engine.run(strategy, data_files)
```

**새로운:**
```python
from src.backtester.simple_engine import SimpleBacktestEngine

engine = SimpleBacktestEngine(config)
result = engine.run(strategy, data_files)
```

## 엔진 선택 가이드

| 상황 | 권장 엔진 |
|------|----------|
| VBO 전략 백테스트 | VectorizedBacktestEngine |
| ORB/기타 전략 백테스트 | SimpleBacktestEngine |
| 대량 데이터 (수년 × 수십 자산) | VectorizedBacktestEngine |
| 전략 개발/디버깅 | SimpleBacktestEngine |
| 명확한 Trade 기록 필요 | SimpleBacktestEngine |
| 최고 성능 필요 | VectorizedBacktestEngine |

## 확장 가이드

### 새로운 엔진 추가

1. `BaseBacktestEngine` 클래스 생성 (선택사항)
2. `run()` 메서드 구현
3. `calculate_metrics()` 사용하여 결과 생성

```python
from src.backtester.metrics import calculate_metrics
from src.backtester.models import BacktestConfig, BacktestResult

class MyCustomEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
    
    def run(self, strategy, data_files) -> BacktestResult:
        # 백테스트 실행
        equity_curve, dates, trades = self._execute_backtest(...)
        
        # 메트릭 계산 (재사용)
        return calculate_metrics(
            equity_curve=equity_curve,
            dates=dates,
            trades=trades,
            config=self.config,
            strategy_name=strategy.name,
        )
```

### 새로운 메트릭 추가

`metrics.py`의 `calculate_metrics()` 함수 수정:

```python
def calculate_metrics(...) -> BacktestResult:
    # 기존 메트릭 계산
    result = BacktestResult(...)
    
    # 새로운 메트릭 추가
    result.sortino_ratio = calculate_sortino(...)
    result.omega_ratio = calculate_omega(...)
    
    return result
```

## 테스트

```bash
# 단일 자산 테스트
python scripts/test_orb_simple_engine.py

# 다중 자산 테스트
python examples/orb_backtest.py

# 엔진 비교
python scripts/compare_engines.py
```

## 관련 문서

- [SimpleBacktestEngine 가이드](simple_backtest_engine.md)
- [VectorizedBacktestEngine 가이드](../api/backtester.md)
- [백테스팅 개요](../README.md)
