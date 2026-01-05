# Phase 2.1 완료: TradingBot 재설계 (Facade 패턴)

## 완료된 작업

### ✅ 1. TradingBotFacade 생성
- **파일**: `src/execution/bot_facade.py`
- Facade 패턴 적용
- 모든 Manager와 Exchange를 통합하는 단일 인터페이스 제공
- 복잡한 내부 구조를 숨기고 간단한 API 제공

### ✅ 2. 의존성 주입 구조
- 생성자에서 모든 의존성을 주입 가능
- 테스트 시 Mock 객체 주입 가능
- 기본값 제공으로 사용 편의성 유지

### ✅ 3. Factory 함수
- `create_bot()`: 기본 설정으로 TradingBotFacade 생성
- 간편한 인스턴스 생성

### ✅ 4. 기존 TradingBot 유지
- `src/execution/bot.py`는 하위 호환성을 위해 유지
- Deprecation 주석 추가
- 점진적 마이그레이션 지원

## 주요 개선사항

### 1. Facade 패턴
- 복잡한 하위 시스템을 단일 인터페이스로 통합
- 클라이언트 코드 단순화
- 내부 구조 변경 시 외부 영향 최소화

### 2. 의존성 주입 (DI)
- 생성자 주입으로 모든 의존성 관리
- 테스트 용이성 향상
- 느슨한 결합 (Loose Coupling)

### 3. 단일 책임 원칙
- TradingBotFacade는 오케스트레이션만 담당
- 구체적인 로직은 각 Manager에 위임

## 변경 전후 비교

### 변경 전 (TradingBot)
```python
class TradingBot:
    def __init__(self, config_path: Path | None = None):
        # 모든 의존성을 직접 생성
        self.exchange = UpbitExchange(...)
        self.position_manager = PositionManager(self.exchange)
        self.order_manager = OrderManager(self.exchange)
        # ...
```

### 변경 후 (TradingBotFacade)
```python
class TradingBotFacade:
    def __init__(
        self,
        exchange: Exchange | None = None,  # 주입 가능
        position_manager: PositionManager | None = None,  # 주입 가능
        order_manager: OrderManager | None = None,  # 주입 가능
        # ...
    ):
        # 주입된 의존성 사용 또는 기본값 생성
        self.exchange = exchange or UpbitExchange(...)
        # ...
```

## 사용 예시

### 기본 사용
```python
from src.execution import create_bot

bot = create_bot()
bot.run()
```

### 의존성 주입 (테스트)
```python
from src.execution import TradingBotFacade
from src.exchange import Exchange

# Mock Exchange 주입
mock_exchange = MockExchange()
bot = TradingBotFacade(exchange=mock_exchange)
```

### 커스텀 설정
```python
from src.execution import TradingBotFacade
from pathlib import Path

bot = TradingBotFacade(config_path=Path("custom_config.yaml"))
bot.run()
```

## 파일 구조

```
src/execution/
├── __init__.py          # Export all classes
├── bot.py               # 기존 TradingBot (유지, deprecated)
├── bot_facade.py        # 새로운 TradingBotFacade
├── position_manager.py
├── order_manager.py
└── signal_handler.py
```

## 다음 단계

Phase 2.1 완료! 다음은:

1. **Phase 2.2: 이벤트 기반 아키텍처 도입**
   - 이벤트 타입 정의
   - 이벤트 버스 구현
   - 핸들러 등록 시스템

2. **또는 기존 TradingBot 마이그레이션**
   - `bot.py`를 `bot_facade.py`로 완전 전환
   - 레거시 코드 정리

## 참고사항

- `TradingBot`과 `TradingBotFacade`는 현재 공존
- 새로운 코드는 `TradingBotFacade` 사용 권장
- 기존 코드는 점진적으로 마이그레이션 가능
