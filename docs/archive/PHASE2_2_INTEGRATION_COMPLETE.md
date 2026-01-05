# Phase 2.2 통합 완료: 이벤트 시스템 통합

## 완료된 작업

### ✅ 1. OrderManager 이벤트 발행
- `place_buy_order()`: `ORDER_PLACED` 이벤트 발행
- `place_sell_order()`: `ORDER_PLACED` 이벤트 발행
- `get_order_status()`: 주문 상태 변경 시 이벤트 발행
  - `ORDER_FILLED`: 주문 체결
  - `ORDER_CANCELLED`: 주문 취소
  - `ORDER_FAILED`: 주문 실패

### ✅ 2. PositionManager 이벤트 발행
- `add_position()`: `POSITION_OPENED` 이벤트 발행
- `remove_position()`: `POSITION_CLOSED` 이벤트 발행
- PnL 정보 포함

### ✅ 3. SignalHandler 이벤트 발행
- `check_entry_signal()`: `ENTRY_SIGNAL` 이벤트 발행
- `check_exit_signal()`: `EXIT_SIGNAL` 이벤트 발행

### ✅ 4. TradingBotFacade 통합
- EventBus 초기화
- TradeHandler 자동 등록
- NotificationHandler 자동 등록
- `daily_reset()`: `DAILY_RESET` 이벤트 발행
- `_recalculate_targets()`: `TARGET_RECALCULATED` 이벤트 발행

## 주요 개선사항

### 1. 이벤트 기반 통신
- 모든 Manager가 이벤트를 발행
- 핸들러가 자동으로 이벤트 처리
- 컴포넌트 간 느슨한 결합

### 2. 선택적 이벤트 발행
- `publish_events` 파라미터로 제어 가능
- 테스트 시 이벤트 비활성화 가능
- 기본값은 True (이벤트 활성화)

### 3. 자동 핸들러 등록
- TradingBotFacade 초기화 시 핸들러 자동 등록
- 사용자가 별도로 등록할 필요 없음

## 이벤트 흐름

### 주문 플로우
```
OrderManager.place_buy_order()
  → ORDER_PLACED 이벤트 발행
    → TradeHandler: 로깅
    → NotificationHandler: Telegram 알림
```

### 포지션 플로우
```
PositionManager.add_position()
  → POSITION_OPENED 이벤트 발행
    → TradeHandler: 로깅
    → NotificationHandler: Telegram 알림
```

### 시그널 플로우
```
SignalHandler.check_entry_signal()
  → ENTRY_SIGNAL 이벤트 발행
    → NotificationHandler: Telegram 알림
```

## 사용 예시

### 기본 사용 (이벤트 자동 활성화)
```python
from src.execution.bot_facade import create_bot

bot = create_bot()
# 이벤트 시스템이 자동으로 활성화됨
bot.run()
```

### 이벤트 비활성화 (테스트)
```python
from src.execution.bot_facade import TradingBotFacade
from src.execution.order_manager import OrderManager
from src.execution.position_manager import PositionManager

# 이벤트 없이 Manager 생성
order_manager = OrderManager(exchange, publish_events=False)
position_manager = PositionManager(exchange, publish_events=False)

bot = TradingBotFacade(
    order_manager=order_manager,
    position_manager=position_manager,
)
```

### 커스텀 핸들러 추가
```python
from src.execution.event_bus import get_event_bus
from src.execution.events import Event, EventType

event_bus = get_event_bus()

@event_bus.subscribe(EventType.ORDER_PLACED)
def custom_handler(event: Event):
    print(f"Custom handler: {event}")
```

## 파일 구조

```
src/execution/
├── bot_facade.py          # 이벤트 시스템 통합
├── order_manager.py       # ORDER_* 이벤트 발행
├── position_manager.py    # POSITION_* 이벤트 발행
├── signal_handler.py      # ENTRY/EXIT_SIGNAL 이벤트 발행
├── events.py              # 이벤트 정의
├── event_bus.py           # 이벤트 버스
└── handlers/
    ├── trade_handler.py   # 주문/포지션 이벤트 처리
    └── notification_handler.py  # 알림 이벤트 처리
```

## 다음 단계

Phase 2.2 통합 완료! Phase 2 전체 완료!

다음은:
- **Phase 4: 테스트 인프라 구축** (선택사항)
- 또는 추가 개선사항 적용

## 참고사항

- 이벤트 시스템은 선택적 사용 가능
- `publish_events=False`로 비활성화 가능
- 기존 코드와 완전 호환
- 점진적 마이그레이션 지원
