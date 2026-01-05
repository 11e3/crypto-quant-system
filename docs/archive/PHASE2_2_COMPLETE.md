# Phase 2.2 완료: 이벤트 기반 아키텍처 도입

## 완료된 작업

### ✅ 1. 이벤트 타입 정의
- **파일**: `src/execution/events.py`
- `EventType` enum: 모든 이벤트 타입 정의
- `Event` base class: 기본 이벤트 클래스
- 특화된 이벤트 클래스:
  - `SignalEvent`: 시그널 이벤트
  - `OrderEvent`: 주문 이벤트
  - `PositionEvent`: 포지션 이벤트
  - `MarketEvent`: 시장 데이터 이벤트
  - `SystemEvent`: 시스템 이벤트
  - `ErrorEvent`: 에러 이벤트

### ✅ 2. 이벤트 버스 구현
- **파일**: `src/execution/event_bus.py`
- `EventBus` 클래스:
  - `subscribe()`: 이벤트 구독 (데코레이터 또는 직접 호출)
  - `unsubscribe()`: 이벤트 구독 해제
  - `publish()`: 이벤트 발행
  - `clear()`: 모든 구독자 제거
- Global event bus: `get_event_bus()` 함수로 전역 인스턴스 제공

### ✅ 3. 이벤트 핸들러 구현
- **파일**: `src/execution/handlers/`
- `TradeHandler`: 주문 및 포지션 이벤트 처리
- `NotificationHandler`: 알림 이벤트 처리 (Telegram 통합)

## 주요 개선사항

### 1. 느슨한 결합 (Loose Coupling)
- 컴포넌트 간 직접 의존성 제거
- 이벤트를 통한 간접 통신
- 컴포넌트 독립성 향상

### 2. 확장 가능성
- 새로운 이벤트 타입 추가 용이
- 새로운 핸들러 추가 용이
- 기존 코드 수정 없이 기능 확장

### 3. 관찰자 패턴 (Observer Pattern)
- Publish-Subscribe 패턴 구현
- 다중 구독자 지원
- 이벤트 기반 비동기 처리 가능

## 이벤트 타입

### Signal Events
- `ENTRY_SIGNAL`: 진입 시그널 발생
- `EXIT_SIGNAL`: 청산 시그널 발생
- `SIGNAL_GENERATED`: 시그널 생성 완료

### Order Events
- `ORDER_PLACED`: 주문 접수
- `ORDER_FILLED`: 주문 체결
- `ORDER_CANCELLED`: 주문 취소
- `ORDER_FAILED`: 주문 실패

### Position Events
- `POSITION_OPENED`: 포지션 오픈
- `POSITION_CLOSED`: 포지션 클로즈
- `POSITION_UPDATED`: 포지션 업데이트

### Market Events
- `PRICE_UPDATE`: 가격 업데이트
- `TICKER_UPDATE`: 티커 업데이트

### System Events
- `DAILY_RESET`: 일일 리셋
- `TARGET_RECALCULATED`: 타겟 재계산
- `ERROR`: 에러 발생

## 사용 예시

### 이벤트 발행
```python
from src.execution.events import EventType, OrderEvent
from src.execution.event_bus import get_event_bus

event_bus = get_event_bus()

event = OrderEvent(
    event_type=EventType.ORDER_PLACED,
    source="OrderManager",
    order_id="123",
    ticker="KRW-BTC",
    side="buy",
    amount=100000.0,
    price=50000000.0,
)
event_bus.publish(event)
```

### 이벤트 구독 (데코레이터)
```python
from src.execution.event_bus import get_event_bus
from src.execution.events import Event, EventType, OrderEvent

event_bus = get_event_bus()

@event_bus.subscribe(EventType.ORDER_PLACED)
def handle_order(event: Event):
    if isinstance(event, OrderEvent):
        print(f"Order placed: {event.ticker}")
```

### 이벤트 구독 (직접 호출)
```python
def handle_order(event: Event):
    print(f"Order: {event}")

event_bus.subscribe(EventType.ORDER_PLACED, handle_order)
```

## 파일 구조

```
src/execution/
├── events.py              # 이벤트 정의
├── event_bus.py           # 이벤트 버스
└── handlers/
    ├── __init__.py
    ├── trade_handler.py   # 주문/포지션 핸들러
    └── notification_handler.py  # 알림 핸들러
```

## 다음 단계

Phase 2.2 완료! 다음은:

1. **Phase 2.2 통합**: TradingBotFacade에 이벤트 시스템 통합
   - Manager들이 이벤트 발행하도록 수정
   - 핸들러 자동 등록
   - 이벤트 기반 통신으로 전환

2. **Phase 3: 스크립트 통합 및 정리**
   - 스크립트 분류 및 통합
   - CLI 인터페이스 통합

## 참고사항

- 이벤트 시스템은 선택적 사용 가능
- 기존 코드와 공존 가능
- 점진적 마이그레이션 지원
