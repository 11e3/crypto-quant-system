# Phase 5.2: 로깅 표준화 완료

## 완료된 작업

### 1. 로그 포맷 표준화

- 기존 로그 포맷 유지: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 파일 로깅 시 UTF-8 인코딩 지원
- 콘솔과 파일 핸들러에 일관된 포맷 적용

### 2. 컨텍스트 로깅 추가

**ContextLogger 클래스** 구현:
- `get_context_logger()` 함수로 컨텍스트 정보를 포함한 로거 생성
- 모든 로그 메시지에 자동으로 컨텍스트 정보 추가
- 예: `[ticker=KRW-BTC | order_id=123] Order placed`

**사용 예시:**
```python
from src.utils.logger import get_context_logger

logger = get_context_logger(__name__, ticker="KRW-BTC", order_id="123")
logger.info("Order placed")  # Logs: [ticker=KRW-BTC | order_id=123] Order placed
```

### 3. 성능 로깅 추가

**PerformanceLogger 클래스 및 `log_performance()` 컨텍스트 매니저** 구현:
- 작업 시작/종료 시간 자동 측정
- 경과 시간을 밀리초 단위로 로깅
- 컨텍스트 정보와 함께 성능 메트릭 기록

**사용 예시:**
```python
from src.utils.logger import get_logger, log_performance

logger = get_logger(__name__)
with log_performance(logger, "fetch_ohlcv", ticker="KRW-BTC"):
    data = exchange.get_ohlcv("KRW-BTC")
# Logs: [PERF] Starting fetch_ohlcv [ticker=KRW-BTC]
#       [PERF] Completed fetch_ohlcv in 0.123s [ticker=KRW-BTC]
```

### 4. 순환 import 해결

- `src/utils/logger.py`에서 `src.config.constants` import 제거
- 로그 포맷 상수를 `logger.py` 내부에 직접 정의
- 순환 import 문제 해결

### 5. 향상된 기능

- `setup_logging()`에 `enable_performance_logging` 파라미터 추가
- 성능 로깅 활성화 시 자동으로 DEBUG 레벨로 설정
- 파일 핸들러에 UTF-8 인코딩 명시

## 테스트 결과

- ✅ 모든 테스트 통과 (52개)
- ✅ 코드 커버리지: 27% (로거 모듈 포함)
- ✅ 린터 오류 없음
- ✅ 순환 import 문제 해결

## 다음 단계

Phase 5 완료! 다음은 Phase 6: 문서화 및 타입 안정성입니다.
