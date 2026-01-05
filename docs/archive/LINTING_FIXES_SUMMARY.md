# 린팅 오류 수정 요약

## 완료된 작업 (2026-01-XX)

### ✅ Ruff 포맷터 적용
- **38개 파일 포맷팅**: 전체 코드베이스에 Ruff 포맷터 적용 완료
- **62개 파일 변경 없음**: 이미 올바른 포맷팅

### ✅ Ruff 린터 자동 수정
- **1차 자동 수정**: 131개 오류 자동 수정 (`ruff check --fix`)
- **2차 자동 수정**: 추가 20개 오류 수정 (`--unsafe-fixes`)
- **수동 수정**: 39개 → 0개 오류로 감소

### ✅ 수정된 오류 유형

1. **F841 - 사용되지 않는 변수** (약 10개)
   - 변수 제거 또는 사용으로 수정

2. **SIM117 - 중첩된 with 문** (약 28개)
   - 중첩된 `with` 문을 단일 `with` 문으로 결합
   - Python 3.10+ 괄호 문법 사용: `with (patch(...), patch(...)):`

3. **B904 - Exception chaining** (1개)
   - `raise ... from e` 사용으로 수정

4. **F811 - 중복 정의** (1개)
   - 중복된 `TestSetupLogging` 클래스 제거

5. **F821 - Undefined name** (1개)
   - `conftest.py`의 타입 힌트에 `# noqa: F821` 추가

6. **E402 - 모듈 레벨 import 위치** (8개)
   - `conftest.py`의 의도적 import에 `# noqa: E402` 추가

7. **F401 - 사용되지 않는 import** (2개)
   - `tempfile`, `Path` import 제거

8. **I001 - Import 정렬** (1개)
   - 자동으로 수정됨

## 수정된 파일

### 주요 파일
- `tests/unit/test_execution/test_bot.py`: 17개 중첩된 with 문 수정
- `tests/unit/test_execution/test_signal_handler.py`: 3개 중첩된 with 문 수정
- `tests/unit/test_backtester/test_engine.py`: 2개 중첩된 with 문 수정
- `tests/unit/test_exchange/test_upbit.py`: 3개 중첩된 with 문 수정
- `tests/unit/test_utils/test_logger.py`: 중복 클래스 제거, 중첩된 with 문 수정
- `src/cli/commands/run_bot.py`: Exception chaining 수정
- `tests/conftest.py`: E402, F821 오류 처리

## 최종 결과

### Ruff 검사
- **오류 수**: 39개 → **0개** ✅
- **포맷팅**: 모든 파일 포맷팅 완료 ✅

### 테스트 실행
- **통과**: 614개
- **실패**: 9개 (기존 실패, 린팅과 무관)
- **경고**: 12개

## 주요 변경 패턴

### Before (중첩된 with 문)
```python
with patch("src.execution.bot.UpbitExchange", return_value=mock_exchange):
    with patch("src.execution.bot.get_config") as mock_get_config:
        ...
```

### After (단일 with 문)
```python
with (
    patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
    patch("src.execution.bot.get_config") as mock_get_config,
):
    ...
```

## 다음 단계

1. ✅ **Ruff 포맷터 적용**: 완료
2. ✅ **Ruff 린터 오류 수정**: 완료
3. **테스트 실패 확인**: 9개 실패 테스트 확인 (기존 실패, 린팅과 무관)
4. **커밋 준비**: 포맷팅 및 린팅 수정사항 커밋

## 참고사항

- **코드 포맷팅 변경**: Black → Ruff 포맷터 전환으로 일부 스타일이 달라졌을 수 있음
- **중첩된 with 문**: Python 3.10+ 괄호 문법을 사용하여 가독성 향상
- **테스트 실패**: 9개 실패는 기존에 있던 것으로, 린팅 수정과는 무관
