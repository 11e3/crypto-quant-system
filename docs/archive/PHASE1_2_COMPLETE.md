# Phase 1.2 완료: Order Manager 분리

## 완료된 작업

### ✅ 1. PositionManager 생성
- **파일**: `src/execution/position_manager.py`
- `Position` 클래스: 단일 포지션 표현
- `PositionManager` 클래스:
  - 포지션 추가/제거
  - 포지션 조회
  - PnL 계산 (절대값 및 퍼센트)
  - 현재가 기반 포지션 가치 계산

### ✅ 2. OrderManager 생성
- **파일**: `src/execution/order_manager.py`
- `OrderManager` 클래스:
  - `place_buy_order()`: 시장가 매수 주문
  - `place_sell_order()`: 시장가 매도 주문
  - `sell_all()`: 전체 매도
  - `get_order_status()`: 주문 상태 조회
  - `cancel_order()`: 주문 취소
  - 최소 주문 금액 검증
  - 에러 처리 (InsufficientBalanceError, ExchangeOrderError)

### ✅ 3. SignalHandler 생성
- **파일**: `src/execution/signal_handler.py`
- `SignalHandler` 클래스:
  - `get_ohlcv_data()`: OHLCV 데이터 조회
  - `check_entry_signal()`: 진입 시그널 체크
  - `check_exit_signal()`: 청산 시그널 체크
  - `calculate_metrics()`: 전략 메트릭 계산
  - Strategy와 Exchange를 통합하여 시그널 생성

### ✅ 4. TradingBot 통합
- **파일**: `src/execution/bot.py`
- Manager들을 사용하도록 리팩토링:
  - `PositionManager`로 포지션 관리
  - `OrderManager`로 주문 실행
  - `SignalHandler`로 시그널 체크 및 메트릭 계산
- 기존 로직을 Manager로 위임:
  - `calculate_metrics()` → `signal_handler.calculate_metrics()`
  - `check_entry_conditions()` → `signal_handler.check_entry_signal()`
  - `check_exit_conditions()` → `signal_handler.check_exit_signal()`
  - `sell_all()` → `order_manager.sell_all()`
  - `_execute_buy_order()` → `order_manager.place_buy_order()`
  - `has_bought` → `position_manager.has_position()`

## 주요 개선사항

### 1. 단일 책임 원칙 (SRP)
- 각 Manager가 명확한 책임을 가짐
- `PositionManager`: 포지션 추적 및 PnL 계산
- `OrderManager`: 주문 실행 및 관리
- `SignalHandler`: 시그널 생성 및 메트릭 계산

### 2. 관심사 분리 (SoC)
- TradingBot은 오케스트레이션만 담당
- 구체적인 로직은 각 Manager에 위임
- 테스트 및 유지보수 용이성 향상

### 3. 재사용성
- Manager들은 독립적으로 사용 가능
- 다른 봇이나 스크립트에서도 활용 가능

### 4. 에러 처리 개선
- 각 Manager에서 구체적인 에러 처리
- `InsufficientBalanceError` 등 특수 예외 처리

## 변경 전후 비교

### 변경 전
```python
# bot.py에 모든 로직이 집중
def calculate_metrics(self, ticker: str):
    # 직접 OHLCV 조회, 지표 계산
    df = self.get_ohlcv_safe(ticker)
    df = self.strategy.calculate_indicators(df)
    # ...

def sell_all(self, ticker: str):
    # 직접 주문 실행
    order = self.exchange.sell_market_order(...)
    # ...
```

### 변경 후
```python
# Manager로 위임
def initialize_targets(self):
    metrics = self.signal_handler.calculate_metrics(ticker, required_period)
    # ...

def sell_all(self, ticker: str):
    order = self.order_manager.sell_all(ticker, min_amount)
    # ...
```

## 파일 구조

```
src/execution/
├── __init__.py
├── bot.py                 # 오케스트레이션만 담당
├── position_manager.py    # 포지션 관리
├── order_manager.py       # 주문 관리
└── signal_handler.py      # 시그널 처리
```

## 다음 단계

Phase 1.2 완료! 다음은:

1. **Phase 1.3: Data Source 추상화**
   - `DataSource` 추상 클래스 정의
   - `UpbitDataSource` 구현
   - 기존 `collector.py` 로직 통합

2. **Phase 2: Bot 리팩토링**
   - TradingBot을 Facade 패턴으로 재구성
   - 의존성 주입 구조로 변경
   - 이벤트 기반 아키텍처 도입

## 테스트

```python
# Manager 독립 테스트
from src.execution.position_manager import PositionManager
from src.execution.order_manager import OrderManager
from src.execution.signal_handler import SignalHandler

# Integration test
from src.execution.bot import TradingBot
# TradingBot now uses all managers
```
