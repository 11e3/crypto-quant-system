# 코드 포맷팅 및 린팅 요약

## 완료된 작업 (2026-01-XX)

### ✅ Ruff 포맷터 적용
- **38개 파일 포맷팅**: 전체 코드베이스에 Ruff 포맷터 적용
- **62개 파일 변경 없음**: 이미 올바른 포맷팅

### ✅ Ruff 린터 자동 수정
- **131개 오류 자동 수정**: `ruff check --fix`로 자동 수정
- **57개 오류 남음**: 수동 수정 필요

## 남은 린팅 오류 분석

### 주요 카테고리

1. **F841 - 사용되지 않는 변수** (약 10개)
   - 예: `target_price`, `result`, `loader`, `cache` 등
   - **해결**: 변수 제거 또는 사용

2. **SIM117 - 중첩된 with 문** (약 20개)
   - 예: `with patch(...): with patch(...):` 패턴
   - **해결**: 단일 `with` 문으로 결합
   ```python
   # Before
   with patch(...):
       with patch(...):
           ...
   
   # After
   with patch(...), patch(...):
       ...
   ```

3. **E402 - 모듈 레벨 import 위치** (약 8개)
   - `tests/conftest.py`에서 발생
   - **참고**: `sys.path` 조작 후 import는 의도적이므로 무시 가능

4. **B904 - Exception chaining** (1개)
   - `src/cli/commands/run_bot.py:55`
   - **해결**: `raise ... from e` 사용

5. **SIM105 - contextlib.suppress** (2개)
   - `src/execution/bot.py:440`, `bot_facade.py:460`
   - **해결**: `try-except-pass`를 `contextlib.suppress`로 변경

6. **SIM110 - all() 사용** (1개)
   - `src/strategies/volatility_breakout/conditions.py:268`
   - **해결**: for 루프를 `all()` 표현식으로 변경

7. **SIM118 - dict.keys() 제거** (3개)
   - `src/data/cache.py:245`, `src/execution/bot.py:238`, `bot_facade.py:219`
   - **해결**: `for k in dict.keys()` → `for k in dict`

8. **F811 - 중복 정의** (1개)
   - `tests/unit/test_utils/test_logger.py:147`
   - **해결**: 중복 클래스 정의 제거

## 권장 수정 순서

### 우선순위 1 (빠른 수정)
1. **F841 - 사용되지 않는 변수**: 변수 제거 또는 사용
2. **SIM118 - dict.keys() 제거**: 간단한 변경
3. **F811 - 중복 정의**: 중복 클래스 제거

### 우선순위 2 (코드 품질 개선)
4. **SIM117 - 중첩된 with 문**: 단일 with로 결합
5. **SIM110 - all() 사용**: for 루프를 all()로 변경
6. **SIM105 - contextlib.suppress**: try-except-pass 개선

### 우선순위 3 (예외 처리 개선)
7. **B904 - Exception chaining**: `raise ... from e` 사용

### 우선순위 4 (의도적 무시)
8. **E402 - 모듈 레벨 import**: `tests/conftest.py`는 의도적이므로 `# noqa: E402` 추가

## 수정 예시

### SIM117 - 중첩된 with 문
```python
# Before
with patch("src.execution.bot.UpbitExchange", return_value=mock_exchange):
    with patch("src.execution.bot.get_config") as mock_get_config:
        ...

# After
with (
    patch("src.execution.bot.UpbitExchange", return_value=mock_exchange),
    patch("src.execution.bot.get_config") as mock_get_config,
):
    ...
```

### SIM105 - contextlib.suppress
```python
# Before
try:
    wm.terminate()
except Exception:
    pass

# After
from contextlib import suppress

with suppress(Exception):
    wm.terminate()
```

### SIM110 - all() 사용
```python
# Before
for i in range(1, len(closes)):
    if closes[i] <= closes[i - 1]:
        return False
return True

# After
return all(closes[i] > closes[i - 1] for i in range(1, len(closes)))
```

### SIM118 - dict.keys() 제거
```python
# Before
for ticker in positions.keys():
    ...

# After
for ticker in positions:
    ...
```

### B904 - Exception chaining
```python
# Before
except Exception as e:
    logger.error(f"Bot error: {e}", exc_info=True)
    raise click.ClickException(f"Failed to start bot: {e}")

# After
except Exception as e:
    logger.error(f"Bot error: {e}", exc_info=True)
    raise click.ClickException(f"Failed to start bot: {e}") from e
```

## 다음 단계

1. **자동 수정 가능한 항목 처리**: `--unsafe-fixes` 옵션으로 추가 수정 시도
2. **수동 수정**: 우선순위에 따라 순차적으로 수정
3. **테스트 실행**: 수정 후 모든 테스트 통과 확인
4. **커밋**: 포맷팅 변경사항과 린팅 수정사항을 별도 커밋으로 분리

## 참고사항

- **E402 오류**: `tests/conftest.py`의 import 위치는 `sys.path` 조작을 위해 의도적입니다. `# noqa: E402` 주석으로 무시 가능합니다.
- **SIM117 오류**: 많은 테스트 파일에서 발생하지만, 가독성을 위해 중첩된 with를 유지하는 것도 선택지입니다.
- **F841 오류**: 일부는 테스트에서 의도적으로 사용되지 않는 변수일 수 있습니다. 필요시 `# noqa: F841` 주석으로 무시 가능합니다.
