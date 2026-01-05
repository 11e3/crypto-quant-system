# Phase 5.1: 커스텀 예외 정의 완료

## 완료된 작업

### 1. 예외 계층 구조 정의

중앙화된 예외 구조를 `src/exceptions/` 디렉토리에 생성:

```
src/exceptions/
├── __init__.py          # 모든 예외 export
├── base.py              # TradingSystemError (기본 예외)
├── exchange.py          # Exchange 관련 예외
├── data.py              # DataSource 관련 예외
├── order.py             # Order 관련 예외
└── strategy.py          # Strategy 관련 예외
```

**예외 계층 구조:**
```
TradingSystemError (base)
├── ExchangeError
│   ├── ExchangeConnectionError
│   ├── ExchangeAuthenticationError
│   └── ExchangeOrderError
│       └── InsufficientBalanceError
├── DataSourceError
│   ├── DataSourceConnectionError
│   └── DataSourceNotFoundError
├── OrderError
│   ├── OrderNotFoundError
│   └── OrderExecutionError
└── StrategyError
    ├── StrategyConfigurationError
    └── StrategyExecutionError
```

### 2. 기존 예외 처리 리팩토링

- `src/exchange/base.py`: 예외 정의 제거, import로 변경
- `src/data/base.py`: 예외 정의 제거, import로 변경
- `src/exchange/__init__.py`: 예외를 `src.exceptions.exchange`에서 import
- `src/data/__init__.py`: 예외를 `src.exceptions.data`에서 import
- `src/exchange/upbit.py`: 예외 import 경로 업데이트
- `src/data/upbit_source.py`: 예외 import 경로 업데이트
- `tests/fixtures/mock_exchange.py`: 예외 import 경로 업데이트
- `tests/unit/test_exchange/test_mock_exchange.py`: 예외 import 경로 업데이트
- `tests/unit/test_execution/test_order_manager.py`: 예외 import 경로 업데이트

### 3. 예외 기능 개선

- **TradingSystemError**: 기본 예외 클래스에 `details` 딕셔너리 추가
- **InsufficientBalanceError**: `currency`, `required`, `available` 필드 추가
- **OrderNotFoundError**: `order_id` 필드 추가
- **OrderExecutionError**: `order_id`, `reason` 필드 추가
- **StrategyConfigurationError**: `strategy_name`, `parameter` 필드 추가
- **StrategyExecutionError**: `strategy_name`, `ticker` 필드 추가
- **DataSourceNotFoundError**: `source` 필드 추가

### 4. 하위 호환성 유지

기존 코드에서 `from src.exchange import ExchangeError` 형태로 import하던 코드가 계속 작동하도록 `src/exchange/__init__.py`에서 예외를 re-export합니다.

## 테스트 결과

- ✅ 모든 테스트 통과 (52개)
- ✅ 코드 커버리지: 27% (예외 모듈 포함)
- ✅ 린터 오류 없음

## 다음 단계

Phase 5.2: 로깅 표준화
- 로그 포맷 표준화
- 컨텍스트 로깅 추가
- 성능 로깅 추가
