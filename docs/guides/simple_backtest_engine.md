# SimpleBacktestEngine

간단하고 명확한 Event-driven 백테스트 엔진입니다.

## 특징

### 장점
- ✅ **디버깅 용이**: 날짜별로 순회하며 명확한 로직
- ✅ **범용성**: 모든 전략과 호환 (ORB, VBO, 모멘텀 등)
- ✅ **명확한 거래 실행**: Entry/Exit 신호를 직접 처리
- ✅ **Trade 기록 정확**: 모든 거래가 기록됨

### 단점
- ❌ **느린 속도**: 벡터화가 아닌 루프 기반 처리
- ❌ **기본 포지션 사이징**: 단순 균등 배분 (고급 최적화 없음)

## 사용법

### 기본 사용

```python
from datetime import date
from pathlib import Path

from src.backtester.engine import BacktestConfig
from src.backtester.simple_engine import SimpleBacktestEngine
from src.strategies.opening_range_breakout.orb import ORBStrategy

# 전략 생성
strategy = ORBStrategy(
    breakout_mode="atr",
    k_multiplier=0.5,
    atr_window=14,
    vol_target=0.02,
)

# 데이터 파일
data_files = {
    "KRW-BTC": Path("data/raw/KRW-BTC_minute240.parquet"),
    "KRW-ETH": Path("data/raw/KRW-ETH_minute240.parquet"),
}

# 백테스트 설정
config = BacktestConfig(
    initial_capital=10_000_000,
    fee_rate=0.0005,
    slippage_rate=0.0005,
    max_slots=2,
    trailing_stop_pct=0.05,
)

# 엔진 생성 및 실행
engine = SimpleBacktestEngine(config)
result = engine.run(
    strategy=strategy,
    data_files=data_files,
    start_date=date(2023, 3, 1),
    end_date=None,
)

# 결과 출력
print(result.summary())
print(f"Total Trades: {len(result.trades)}")
```

### 결과 예시

```
==================================================
Strategy: orb
==================================================
CAGR: 27.91%
MDD: 20.87%
Calmar Ratio: 1.34
Sharpe Ratio: 0.90
Win Rate: 41.49%
Total Trades: 94
Final Equity: 20163290.0000
==================================================
```

## 동작 원리

### 처리 흐름

1. **데이터 로드**
   - 각 자산별 OHLCV 데이터 로드
   - 전략의 `calculate_indicators()` 호출
   - 전략의 `generate_signals()` 호출

2. **날짜별 순회** (Event-driven)
   ```
   for each date:
       ├─ EXIT LOGIC (먼저 처리)
       │  ├─ 청산 시그널 확인
       │  ├─ Trailing stop 확인
       │  ├─ Stop loss 확인
       │  └─ Take profit 확인
       │
       ├─ ENTRY LOGIC
       │  ├─ 진입 시그널 확인
       │  ├─ 슬롯 가용성 확인
       │  └─ 포지션 오픈
       │
       └─ EQUITY 계산
          └─ cash + portfolio_value
   ```

3. **메트릭 계산**
   - CAGR, MDD, Sharpe, Calmar 등
   - 거래 통계 (승률, Profit Factor)

## VectorizedBacktestEngine과 비교

| 항목 | SimpleBacktestEngine | VectorizedBacktestEngine |
|------|---------------------|--------------------------|
| **속도** | 느림 (루프 기반) | 빠름 (벡터화) |
| **호환성** | 모든 전략 ✅ | VBO 전용 ⚠️ |
| **디버깅** | 쉬움 ✅ | 어려움 |
| **거래 실행** | 명확함 ✅ | 복잡함 |
| **Trade 기록** | 정확함 ✅ | 불완전할 수 있음 |
| **권장 용도** | 전략 개발/테스트 | 대량 데이터 분석 |

## 예제

### 1. 단일 자산 백테스트

```python
# 단일 자산으로 빠른 테스트
data_files = {"KRW-BTC": Path("data/raw/KRW-BTC_minute240.parquet")}
config = BacktestConfig(initial_capital=10_000_000, max_slots=1)

engine = SimpleBacktestEngine(config)
result = engine.run(strategy, data_files)

print(f"CAGR: {result.cagr:.2f}%")
print(f"MDD: {result.mdd:.2f}%")
print(f"Trades: {len(result.trades)}")
```

### 2. 다중 자산 포트폴리오

```python
# 4개 자산으로 포트폴리오 백테스트
data_files = {
    "KRW-BTC": Path("data/raw/KRW-BTC_minute240.parquet"),
    "KRW-ETH": Path("data/raw/KRW-ETH_minute240.parquet"),
    "KRW-XRP": Path("data/raw/KRW-XRP_minute240.parquet"),
    "KRW-TRX": Path("data/raw/KRW-TRX_minute240.parquet"),
}

config = BacktestConfig(
    initial_capital=10_000_000,
    max_slots=4,
    trailing_stop_pct=0.05,
)

engine = SimpleBacktestEngine(config)
result = engine.run(strategy, data_files, start_date=date(2023, 3, 1))

# 거래 상세 출력
for trade in result.trades[:10]:
    print(f"{trade.ticker} {trade.entry_date} -> {trade.exit_date}: {trade.pnl_pct:+.2f}%")
```

### 3. 엔진 비교 테스트

```python
from src.backtester.engine import VectorizedBacktestEngine

# 동일 설정으로 두 엔진 비교
simple = SimpleBacktestEngine(config)
vectorized = VectorizedBacktestEngine(config)

result_simple = simple.run(strategy, data_files)
result_vectorized = vectorized.run(strategy, data_files)

print(f"Simple Trades: {result_simple.total_trades}")
print(f"Vectorized Trades: {result_vectorized.total_trades}")
print(f"Simple CAGR: {result_simple.cagr:.2f}%")
print(f"Vectorized CAGR: {result_vectorized.cagr:.2f}%")
```

## 내부 구조

### Position 클래스

```python
@dataclass
class Position:
    ticker: str
    entry_date: date
    entry_price: float
    amount: float
    highest_price: float  # Trailing stop 추적용
```

### 핵심 메서드

1. **`run()`**: 메인 백테스트 실행
2. **`_load_data()`**: 데이터 로드 및 전처리
3. **`_calculate_metrics()`**: 성능 지표 계산

## 팁

### 디버깅

```python
# 로깅 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# SimpleBacktestEngine은 상세 로그 출력
# - 각 진입/청산 시그널
# - 포지션 상태 변화
# - 현금 흐름
```

### 성능 개선

- 날짜 범위 제한: `start_date`, `end_date` 활용
- 적은 자산으로 먼저 테스트
- 지표 계산 최적화 (전략 내)

### 주의사항

- ⚠️ 대량 데이터 (수년, 다수 자산)는 느릴 수 있음
- ⚠️ VectorizedBacktestEngine 대비 10-100배 느림
- ⚠️ 프로덕션 대량 분석은 VectorizedBacktestEngine 권장

## 관련 문서

- [ORBStrategy](../strategies/opening_range_breakout/README.md)
- [BacktestConfig](engine.py)
- [BacktestResult](engine.py)
- [예제: orb_backtest.py](../../examples/orb_backtest.py)
